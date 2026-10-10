import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict


REDACTION_PATTERNS = [
    # JWT tokens (header.payload.signature)
    (re.compile(r"ey[A-Za-z0-9-_=]+\.ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+"), "[REDACTED_JWT]"),
    # Bearer tokens
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-_.]+"), "Bearer [REDACTED_TOKEN]"),
    # Sensitive key-value pairs (password, secret, api_key, etc.)
    (
        re.compile(r"(?i)\b(password|passwd|secret|jwt_secret_key|api_key|auth_token|token_hash)\s*[:=]\s*['\"]?[^\s,'\"}]+"),
        r"\1=[REDACTED]",
    ),
    # Database URLs with passwords
    (re.compile(r"(?i)(postgres(?:ql)?(?:\+asyncpg)?://[^:]+:)([^@]+)(@)"), r"\1***\3"),
    # OTP codes when explicitly formatted as key=value or key value
    (re.compile(r"(?i)\b(otp|otp_code|verification_code)\s*[:=\s]\s*['\"]?\d{4,8}['\"]?"), r"\1=[REDACTED_OTP]"),
    # Plaintext unmasked 10-15 digit phone numbers with optional leading +
    (re.compile(r"(?<!\w)\+?[1-9]\d{9,14}(?!\w)"), "[REDACTED_PHONE]"),
]


def redact_sensitive_text(text: str) -> str:
    """Sanitize secrets, tokens, OTPs, and personal data from log strings."""
    if not isinstance(text, str):
        text = str(text)
    for pattern, replacement in REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def sanitize_data_structure(data: Any) -> Any:
    """Recursively scrub sensitive keys and values from dictionary/list data structures."""
    sensitive_keys = {
        "password", "secret", "jwt_secret_key", "token", "access_token",
        "refresh_token", "api_key", "auth_token", "code", "otp", "salt",
        "hashed_code", "token_hash", "credentials", "authorization"
    }
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if str(k).lower() in sensitive_keys:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_data_structure(v)
        return sanitized
    elif isinstance(data, (list, tuple)):
        return [sanitize_data_structure(item) for item in data]
    elif isinstance(data, str):
        return redact_sensitive_text(data)
    return data


class RedactionFilter(logging.Filter):
    """Logging filter ensuring log records do not leak secrets, tokens, or personal info."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_data_structure(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_text(str(a)) if isinstance(a, str) else a for a in record.args
                )
        return True


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production and monitoring pipelines with automated redaction."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive_text(record.getMessage()),
        }

        if record.exc_info:
            log_entry["exception"] = redact_sensitive_text(self.formatException(record.exc_info))

        # Include custom structured extras if present
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_entry.update(sanitize_data_structure(record.extra))

        return json.dumps(log_entry)


class TextFormatter(logging.Formatter):
    """Human-readable log formatter for local development with automated redaction."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return redact_sensitive_text(formatted)


def setup_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """Configure root logger with structured formatting based on environment and active redaction."""
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.addFilter(RedactionFilter())

    if environment.lower() in ("production", "staging"):
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    # Quiet overly chatty loggers if necessary
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name)

