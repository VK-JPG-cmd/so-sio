from enum import Enum


class UserRole(str, Enum):
    """Authorized application roles."""

    CUSTOMER = "CUSTOMER"
    BRAND_OWNER = "BRAND_OWNER"
    ADMIN = "ADMIN"


class AccountStatus(str, Enum):
    """Lifecycle statuses for user accounts."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class ApplicationStatus(str, Enum):
    """Lifecycle statuses for a brand application."""

    PENDING_DOMAIN_VERIFICATION = "PENDING_DOMAIN_VERIFICATION"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BrandVerificationStatus(str, Enum):
    """Public verification status of a brand profile."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class AssetType(str, Enum):
    """Categories of official brand assets."""

    LOGO = "LOGO"
    ICON = "ICON"
    BANNER = "BANNER"
    TRADEMARK_DOCUMENT = "TRADEMARK_DOCUMENT"


class AssetVerificationStatus(str, Enum):
    """Lifecycle verification status of registered brand assets."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class SocialPlatform(str, Enum):
    """Supported social media platforms."""

    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    LINKEDIN = "LINKEDIN"
    X = "X"
    YOUTUBE = "YOUTUBE"
    TIKTOK = "TIKTOK"
    TELEGRAM = "TELEGRAM"
    OTHER = "OTHER"


class MobilePlatform(str, Enum):
    """Supported mobile app platforms."""

    ANDROID = "ANDROID"
    IOS = "IOS"


class ReviewStatus(str, Enum):
    """Moderation status of customer reviews."""

    PENDING_MODERATION = "PENDING_MODERATION"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"


class TargetType(str, Enum):
    """Target attack surface types for threat reports."""

    DOMAIN = "DOMAIN"
    URL = "URL"
    SOCIAL_PROFILE = "SOCIAL_PROFILE"
    SCAM_TEXT = "SCAM_TEXT"
    MOBILE_APP = "MOBILE_APP"


class ThreatReportStatus(str, Enum):
    """Investigation and verification lifecycle status for threat reports."""

    SUBMITTED = "SUBMITTED"
    ANALYZING = "ANALYZING"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONFIRMED = "CONFIRMED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvidenceType(str, Enum):
    """Categories of evidence attached to threat reports."""

    SCREENSHOT = "SCREENSHOT"
    DOCUMENT = "DOCUMENT"
    EMAIL_HEADER = "EMAIL_HEADER"
    SCAM_SAMPLE = "SCAM_SAMPLE"
    LOG = "LOG"
    OTHER = "OTHER"


class RiskSeverity(str, Enum):
    """Risk severity categorization for explainable assessments."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EntityType(str, Enum):
    """Normalized categories for threat entities."""

    DOMAIN = "DOMAIN"
    URL = "URL"
    IP_ADDRESS = "IP_ADDRESS"
    SOCIAL_PROFILE = "SOCIAL_PROFILE"
    SCAM_TEXT_HASH = "SCAM_TEXT_HASH"
    IMAGE_HASH = "IMAGE_HASH"
    APK_PACKAGE = "APK_PACKAGE"


class RelationshipType(str, Enum):
    """Defensible technical connection types between threat entities."""

    SHARED_DESTINATION = "SHARED_DESTINATION"
    SIMILAR_DOMAIN = "SIMILAR_DOMAIN"
    REUSED_IMAGE_HASH = "REPEATED_IMAGE_HASH"
    REPEATED_SCAM_PATTERN = "REPEATED_SCAM_PATTERN"
    THREAT_INTEL_CLUSTER = "THREAT_INTEL_CLUSTER"
    SHARED_INFRASTRUCTURE = "SHARED_INFRASTRUCTURE"


class RelationshipStatus(str, Enum):
    """Investigation status of an entity relationship."""

    CANDIDATE = "CANDIDATE"
    INVESTIGATED = "INVESTIGATED"
    CONFIRMED = "CONFIRMED"


class CampaignStatus(str, Enum):
    """Lifecycle stages for correlated threat campaigns."""

    ACTIVE = "ACTIVE"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED = "MITIGATED"
    ARCHIVED = "ARCHIVED"


class AlertStatus(str, Enum):
    """Incident resolution statuses for brand threat alerts."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"



