from datetime import datetime
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.exceptions import ValidationError
from app.models.enums import MobilePlatform, RiskSeverity

ANDROID_PACKAGE_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$")
IOS_IDENTIFIER_REGEX = re.compile(r"^(?:id\d+|\d+|[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)+)$")


class AppMetadataAnalysisRequest(BaseModel):
    """Payload to request app store listing metadata threat analysis."""

    brand_id: uuid.UUID = Field(..., description="Target verified brand ID for comparison")
    app_name: str = Field(..., min_length=1, max_length=255, description="Candidate application name")
    platform: str = Field(..., description="Mobile platform (ANDROID or IOS)")
    app_identifier: str = Field(..., min_length=1, max_length=255, description="Package name or platform-specific identifier")
    publisher_name: Optional[str] = Field(None, max_length=255, description="Candidate publisher or developer name")
    description: Optional[str] = Field(None, max_length=10000, description="Store listing description text")
    store_url: Optional[str] = Field(None, max_length=512, description="Store listing URL")
    logo_hash: Optional[str] = Field(None, max_length=128, description="Perceptual or cryptographic hash of application icon")
    source: Optional[str] = Field(None, max_length=128, description="Origin source of metadata submission")

    @field_validator("app_name", mode="before")
    @classmethod
    def validate_app_name(cls, v: str) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValidationError("Candidate application name cannot be empty.")
        return v.strip()

    @field_validator("platform", mode="before")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValidationError("Mobile platform is required.")
        norm = v.strip().upper()
        if norm not in (MobilePlatform.ANDROID.value, MobilePlatform.IOS.value):
            raise ValidationError(f"Invalid mobile platform '{v}'. Must be 'ANDROID' or 'IOS'.")
        return norm

    @field_validator("app_identifier")
    @classmethod
    def validate_identifier(cls, v: str, info) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValidationError("Application identifier cannot be empty.")
        identifier = v.strip()
        platform_str = info.data.get("platform", "").upper()
        if platform_str == MobilePlatform.ANDROID.value:
            if not ANDROID_PACKAGE_REGEX.match(identifier):
                raise ValidationError(
                    f"Invalid Android package name format '{identifier}'. Must follow standard convention (e.g. 'com.example.app')."
                )
        elif platform_str == MobilePlatform.IOS.value:
            if not IOS_IDENTIFIER_REGEX.match(identifier):
                raise ValidationError(
                    f"Invalid iOS application identifier format '{identifier}'. Must be a bundle identifier or App Store ID."
                )
        return identifier

    @field_validator("store_url")
    @classmethod
    def validate_store_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if not isinstance(v, str) or not v.strip():
            return None
        parsed = urlparse(v.strip())
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValidationError("Store listing URL must be a valid HTTP/HTTPS URL.")
        return v.strip()


class AppMetadataIndicator(BaseModel):
    """Specific technical indicator detected during metadata analysis."""

    category: str
    signal_type: str
    points: float
    description: str
    evidence_context: Dict[str, Any] = Field(default_factory=dict)


class AppMetadataAnalysisResponse(BaseModel):
    """Complete explainable app-store listing metadata assessment."""

    model_config = ConfigDict(protected_namespaces=())

    brand_id: uuid.UUID
    brand_name: str
    candidate_app_name: str
    platform: str
    app_identifier: str
    publisher_name: Optional[str] = None
    store_url: Optional[str] = None
    description: Optional[str] = None

    # Assessment outcome
    matched_official_app_id: Optional[uuid.UUID] = None
    is_official_match: bool = False
    assessment_status: str  # "OFFICIAL_ASSET_MATCH", "LIKELY_IMPERSONATION", "NEEDS_INVESTIGATION", "BENIGN_UNRELATED", "INSUFFICIENT_INFORMATION"

    # Explainable risk scoring
    risk_score: float = Field(..., ge=0.0, le=100.0)
    severity: RiskSeverity
    model_version: str

    contributing_indicators: List[AppMetadataIndicator] = Field(default_factory=list)
    explanations: List[str] = Field(default_factory=list)
    available_evidence: Dict[str, Any] = Field(default_factory=dict)
    missing_signals: List[Dict[str, str]] = Field(default_factory=list)
    recommended_actions: List[Dict[str, Any]] = Field(default_factory=list)
    assessment_timestamp: datetime = Field(default_factory=datetime.utcnow)
