import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_default_settings_valid() -> None:
    """Verify default settings instantiate correctly."""
    settings = Settings()
    assert settings.APP_NAME == "BrandShield AI Backend"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS


def test_database_url_normalization() -> None:
    """Verify postgresql:// is automatically normalized to postgresql+asyncpg://."""
    s1 = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/testdb")
    assert s1.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/testdb"

    s2 = Settings(DATABASE_URL="postgres://user:pass@localhost:5432/testdb")
    assert s2.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/testdb"


def test_invalid_database_dialect_rejected() -> None:
    """Verify non-PostgreSQL dialects (e.g. SQLite, MySQL) are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(DATABASE_URL="sqlite:///test.db")
    assert "BrandShield AI requires PostgreSQL" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info2:
        Settings(DATABASE_URL="mysql://user:pass@localhost/db")
    assert "BrandShield AI requires PostgreSQL" in str(exc_info2.value)


def test_cors_parsing_from_strings() -> None:
    """Verify CORS origins can be parsed from comma-separated string and JSON array."""
    s_csv = Settings(BACKEND_CORS_ORIGINS="https://app.brandshield.ai, https://admin.brandshield.ai")
    assert s_csv.BACKEND_CORS_ORIGINS == [
        "https://app.brandshield.ai",
        "https://admin.brandshield.ai",
    ]

    s_json = Settings(
        BACKEND_CORS_ORIGINS='["https://app.brandshield.ai", "https://api.brandshield.ai"]'
    )
    assert s_json.BACKEND_CORS_ORIGINS == [
        "https://app.brandshield.ai",
        "https://api.brandshield.ai",
    ]


def test_production_cors_security_enforcement() -> None:
    """Verify production environment strictly disallows wildcard CORS origins and empty origins."""
    with pytest.raises(ValidationError) as exc_wildcard:
        Settings(
            ENVIRONMENT="production",
            BACKEND_CORS_ORIGINS=["*"],
        )
    assert "Wildcard CORS origin ('*') is strictly forbidden in production" in str(
        exc_wildcard.value
    )

    with pytest.raises(ValidationError) as exc_empty:
        Settings(
            ENVIRONMENT="production",
            BACKEND_CORS_ORIGINS=[],
        )
    assert "BACKEND_CORS_ORIGINS cannot be empty in production" in str(exc_empty.value)

    # Valid production settings
    prod_valid = Settings(
        ENVIRONMENT="production",
        BACKEND_CORS_ORIGINS=["https://brandshield.ai"],
        OTP_PROVIDER="console",
        DNS_RESOLVER_MODE="system",
        JWT_SECRET_KEY="a-very-secure-custom-production-key-that-is-long-enough-32-chars",
    )
    assert prod_valid.ENVIRONMENT == "production"
    assert prod_valid.BACKEND_CORS_ORIGINS == ["https://brandshield.ai"]


def test_production_otp_and_jwt_security_enforcement() -> None:
    """Verify production strictly disallows Mock OTP provider and default insecure secret keys."""
    # Mock OTP provider forbidden in production
    with pytest.raises(ValidationError) as exc_mock:
        Settings(
            ENVIRONMENT="production",
            BACKEND_CORS_ORIGINS=["https://brandshield.ai"],
            OTP_PROVIDER="mock",
            JWT_SECRET_KEY="a-very-secure-custom-production-key-that-is-long-enough-32-chars",
        )
    assert "Mock OTP provider is strictly forbidden in production" in str(exc_mock.value)

    # Insecure default key forbidden in production
    with pytest.raises(ValidationError) as exc_jwt:
        Settings(
            ENVIRONMENT="production",
            BACKEND_CORS_ORIGINS=["https://brandshield.ai"],
            OTP_PROVIDER="console",
        )
    assert "Default development JWT_SECRET_KEY cannot be used in production" in str(exc_jwt.value)

    # Short JWT key rejected regardless of environment
    with pytest.raises(ValidationError) as exc_short:
        Settings(JWT_SECRET_KEY="too-short")
    assert "String should have at least 32 characters" in str(exc_short.value)

