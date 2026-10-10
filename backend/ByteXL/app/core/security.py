from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any, Dict, Optional, Tuple
import uuid
import jwt
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError

settings = get_settings()


def mask_phone_number(phone_number: str) -> str:
    """Mask phone number for safe structured logging."""
    if len(phone_number) <= 6:
        return "***"
    return f"{phone_number[:2]}***{phone_number[-4:]}"


def generate_otp_code(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def generate_salt(length: int = 16) -> str:
    """Generate cryptographically secure random hexadecimal salt."""
    return secrets.token_hex(length)


def hash_otp(code: str, salt: str) -> str:
    """Compute HMAC-SHA256 digest of an OTP with salt."""
    key = settings.JWT_SECRET_KEY.encode("utf-8")
    message = f"{salt}:{code}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def verify_otp_hash(code: str, salt: str, expected_hash: str) -> bool:
    """Constant-time verification of OTP against stored hash."""
    computed_hash = hash_otp(code, salt)
    return hmac.compare_digest(computed_hash, expected_hash)


def generate_refresh_token() -> str:
    """Generate an unguessable high-entropy URL-safe refresh token string."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Compute SHA-256 hash of refresh token for secure database persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, int]:
    """
    Issue a signed short-lived JWT access token.
    Returns (token_string, expires_in_seconds).
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
        expires_in = int(expires_delta.total_seconds())
    else:
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        expire = now + timedelta(seconds=expires_in)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "typ": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, expires_in


import threading

_revoked_tokens: Dict[str, int] = {}
_blacklist_lock = threading.Lock()


def revoke_access_token(jti: str, exp: int) -> None:
    """Add a JWT JTI to the revocation list until its expiration timestamp."""
    with _blacklist_lock:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        expired = [k for k, v in _revoked_tokens.items() if v <= now_ts]
        for k in expired:
            _revoked_tokens.pop(k, None)
        _revoked_tokens[jti] = exp


def is_access_token_revoked(jti: str) -> bool:
    """Check if a token JTI has been revoked."""
    with _blacklist_lock:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        exp = _revoked_tokens.get(jti)
        if exp is not None:
            if exp <= now_ts:
                _revoked_tokens.pop(jti, None)
                return False
            return True
        return False


def clear_revoked_tokens() -> None:
    """Clear revocation store (used for test isolation)."""
    with _blacklist_lock:
        _revoked_tokens.clear()


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Validate signature, expiration, issuer, audience, and claims of an access token.
    Raises AuthenticationError on any validation failure or if revoked.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={
                "require": ["exp", "iss", "aud", "sub", "typ"],
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )

        if payload.get("typ") != "access":
            raise AuthenticationError("Invalid token type. Access token expected.")

        jti = payload.get("jti")
        if jti and is_access_token_revoked(jti):
            raise AuthenticationError("Authentication token has been revoked.")

        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Authentication token has expired.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid authentication token: {str(exc)}")
