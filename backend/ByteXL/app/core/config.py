from functools import lru_cache
import json
from typing import Any, List, Literal, Optional
from typing_extensions import Self
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentType = Literal["development", "staging", "production", "test"]
LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = Field(
        default="BrandShield AI Backend",
        description="Name of the application",
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Current runtime environment (development, staging, production, test)",
    )
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="Base routing prefix for API v1",
    )
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/brandshield_ai_dev",
        description="PostgreSQL connection string with asyncpg driver",
    )
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000", "http://localhost:5173", "http://127.0.0.1:5173"],
        description="List of allowed CORS origins",
    )
    LOG_LEVEL: LogLevelType = Field(
        default="INFO",
        description="Structured logging severity level",
    )

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = Field(
        default="brandshield-ai-super-secret-key-for-development-must-be-changed-in-production-min-32-chars",
        description="Cryptographic secret key for signing JWT tokens",
        min_length=32,
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        description="Access token lifespan in minutes",
        gt=0,
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token lifespan in days",
        gt=0,
    )
    JWT_ISSUER: str = Field(
        default="brandshield-ai",
        description="Expected JWT issuer claim (iss)",
    )
    JWT_AUDIENCE: str = Field(
        default="brandshield-users",
        description="Expected JWT audience claim (aud)",
    )

    # OTP Authentication Settings
    OTP_PROVIDER: Literal["mock", "console", "twilio", "fast2sms"] = Field(
        default="mock",
        description="Provider strategy for OTP delivery (mock, console, twilio, fast2sms)",
    )
    FAST2SMS_API_KEY: Optional[str] = Field(
        default=None,
        description="Fast2SMS API authorization key for Indian mobile SMS delivery",
    )
    OTP_CODE_LENGTH: int = Field(
        default=6,
        description="Length of numeric OTP",
        ge=4,
        le=8,
    )
    OTP_EXPIRATION_SECONDS: int = Field(
        default=300,
        description="OTP validity period in seconds (default 5 minutes)",
        gt=0,
    )
    OTP_MAX_ATTEMPTS: int = Field(
        default=3,
        description="Maximum failed verification attempts allowed per OTP",
        gt=0,
    )
    OTP_RESEND_COOLDOWN_SECONDS: int = Field(
        default=60,
        description="Minimum seconds required between successive OTP requests",
        gt=0,
    )
    OTP_MAX_REQUESTS_PER_HOUR: int = Field(
        default=5,
        description="Maximum OTP requests permitted per phone number per hour",
        gt=0,
    )
    TWILIO_ACCOUNT_SID: Any = Field(
        default=None,
        description="Twilio Account SID (must start with AC...)",
    )
    TWILIO_AUTH_TOKEN: Any = Field(
        default=None,
        description="Twilio Auth Token",
    )
    TWILIO_API_KEY: Any = Field(
        default=None,
        description="Twilio API Key SID (must start with SK...)",
    )
    TWILIO_API_KEY_SID: Any = Field(
        default=None,
        description="Twilio API Key SID alias (must start with SK...)",
    )
    TWILIO_API_SECRET: Any = Field(
        default=None,
        description="Twilio API Key Secret",
    )
    TWILIO_VERIFY_SERVICE_SID: Any = Field(
        default=None,
        description="Twilio Verify Service SID (must start with VA...)",
    )
    TWILIO_FROM_NUMBER: Any = Field(
        default=None,
        description="Twilio Sender Phone Number or Messaging Service SID",
    )

    # Domain Verification Settings
    DOMAIN_CHALLENGE_EXPIRE_HOURS: int = Field(
        default=24,
        description="Lifespan of domain ownership challenge in hours",
        gt=0,
    )
    DOMAIN_CHALLENGE_MAX_ATTEMPTS: int = Field(
        default=5,
        description="Maximum failed attempts permitted per domain challenge",
        gt=0,
    )
    DNS_RESOLVER_MODE: Literal["system", "mock"] = Field(
        default="system",
        description="DNS resolution strategy (system or mock)",
    )

    # Evidence and File Upload Settings
    EVIDENCE_STORAGE_DIR: str = Field(
        default="data/evidence",
        description="Base storage directory for secure threat evidence files",
    )
    MAX_EVIDENCE_FILE_SIZE_BYTES: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum evidence file size in bytes (default 10 MB)",
        gt=0,
    )
    ALLOWED_EVIDENCE_EXTENSIONS: List[str] = Field(
        default=[".png", ".jpg", ".jpeg", ".webp", ".pdf", ".txt", ".json", ".log"],
        description="Allowlist of approved file extensions for evidence uploads",
    )

    # Threat Discovery and Continuous Monitoring Settings
    THREAT_DISCOVERY_WORKER_ENABLED: bool = Field(
        default=False,
        description="Enable continuous background polling worker for external threat discovery",
    )
    THREAT_DISCOVERY_POLL_INTERVAL_SECONDS: int = Field(
        default=300,
        description="Polling cycle interval in seconds (default 5 minutes)",
        gt=0,
    )
    THREAT_DISCOVERY_BATCH_SIZE: int = Field(
        default=50,
        description="Maximum indicators to ingest per connector per polling cycle",
        gt=0,
        le=500,
    )

    # URLhaus Threat Intelligence Connector Settings
    URLHAUS_ENABLED: bool = Field(
        default=True,
        description="Enable abuse.ch URLhaus threat intelligence connector",
    )
    URLHAUS_API_URL: str = Field(
        default="https://urlhaus-api.abuse.ch/v1",
        description="Base API endpoint URL for abuse.ch URLhaus feed",
    )
    URLHAUS_AUTH_KEY: Any = Field(
        default=None,
        description="Optional Auth-Key token for abuse.ch API (URLHAUS_AUTH_KEY)",
    )
    URLHAUS_TIMEOUT_SECONDS: float = Field(
        default=10.0,
        description="HTTP request timeout for URLhaus API queries in seconds",
        gt=0.0,
    )
    URLHAUS_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum retry attempts on transient network or rate-limit failures",
        ge=0,
        le=5,
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Enforce PostgreSQL connection scheme and normalize to async driver."""
        if not v or not isinstance(v, str):
            raise ValueError("DATABASE_URL must be a non-empty string.")

        if v.startswith("sqlite://"):
            raise ValueError(
                "BrandShield AI requires PostgreSQL. Dialect 'sqlite://' is unsupported for persistent storage."
            )

        valid_prefixes = ("postgresql://", "postgresql+asyncpg://", "postgres://", "sqlite+aiosqlite://")
        if not v.startswith(valid_prefixes):
            raise ValueError(
                f"Invalid database dialect in '{v}'. BrandShield AI requires PostgreSQL ('postgresql+asyncpg://')."
            )

        # Normalize driver for asyncpg
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)

        # Handle asyncpg compatibility with Neon / cloud postgres connection strings
        if "asyncpg" in v:
            import re
            v = re.sub(r"[?&]channel_binding=[^&]+", "", v)
            v = v.replace("sslmode=require", "ssl=require")
            if "?" not in v and "&" in v:
                v = v.replace("&", "?", 1)

        return v

    @property
    def effective_twilio_api_key(self) -> Optional[str]:
        val = self.TWILIO_API_KEY or self.TWILIO_API_KEY_SID
        return str(val).strip() if val else None

    def validate_twilio_verify_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate Twilio Verify configuration without revealing secret values.
        Returns (is_valid, error_reason).
        """
        acc_sid = str(self.TWILIO_ACCOUNT_SID).strip() if self.TWILIO_ACCOUNT_SID else ""
        api_key = self.effective_twilio_api_key or ""
        api_secret = str(self.TWILIO_API_SECRET).strip() if self.TWILIO_API_SECRET else ""
        auth_token = str(self.TWILIO_AUTH_TOKEN).strip() if self.TWILIO_AUTH_TOKEN else ""
        service_sid = str(self.TWILIO_VERIFY_SERVICE_SID).strip() if self.TWILIO_VERIFY_SERVICE_SID else ""

        if not acc_sid:
            return False, "Twilio configuration incomplete: TWILIO_ACCOUNT_SID is required and must start with 'AC'. Add it to backend/.env."
        if not acc_sid.startswith("AC"):
            return False, f"Twilio configuration invalid: TWILIO_ACCOUNT_SID must start with 'AC' (got prefix: {acc_sid[:2]})."

        has_api_key = bool(api_key and api_secret)
        has_auth_token = bool(auth_token)

        if not (has_api_key or has_auth_token):
            return False, "Twilio authentication requires either (TWILIO_API_KEY + TWILIO_API_SECRET) or TWILIO_AUTH_TOKEN."

        if has_api_key and not api_key.startswith("SK"):
            return False, f"TWILIO_API_KEY must start with 'SK' (got prefix: {api_key[:2]})."

        if not service_sid:
            return False, "Twilio Verify configuration incomplete: TWILIO_VERIFY_SERVICE_SID is required and must start with 'VA'. Create a Verify Service in Twilio Console and add its SID to backend/.env."
        if not service_sid.startswith("VA"):
            return False, f"TWILIO_VERIFY_SERVICE_SID must start with 'VA' (got prefix: {service_sid[:2]})."

        return True, None

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Support parsing CORS origins from list, JSON string, or comma-separated string."""
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        if isinstance(v, str):
            stripped = v.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return []

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, v: Any) -> str:
        """Ensure uppercase log level."""
        if isinstance(v, str):
            return v.upper()
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> Self:
        """Validate security constraints for production environments."""
        is_production = self.ENVIRONMENT.lower() == "production"
        if is_production:
            if not self.BACKEND_CORS_ORIGINS:
                raise ValueError("BACKEND_CORS_ORIGINS cannot be empty in production.")
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("Wildcard CORS origin ('*') is strictly forbidden in production.")
            if self.OTP_PROVIDER == "mock":
                raise ValueError("Mock OTP provider is strictly forbidden in production.")
            if self.OTP_PROVIDER == "twilio" and not (
                self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN and self.TWILIO_FROM_NUMBER
            ):
                raise ValueError(
                    "Twilio credentials must be fully configured when using twilio OTP provider in production."
                )
            if "super-secret-key-for-development" in self.JWT_SECRET_KEY:
                raise ValueError("Default development JWT_SECRET_KEY cannot be used in production.")
            if self.DNS_RESOLVER_MODE == "mock":
                raise ValueError("Mock DNS resolver is strictly forbidden in production.")
        return self


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()
