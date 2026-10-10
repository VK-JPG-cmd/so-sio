"""Detection services package."""

from app.services.detection.apk_analysis import APKAnalysisResult, APKAnalysisService
from app.services.detection.brand_intelligence import (
    BrandIntelligenceService,
    VerifiedBrandProfile,
)
from app.services.detection.domain_analysis import (
    DomainAnalysisResult,
    DomainAnalysisService,
)
from app.services.detection.homoglyphs import HomoglyphDetector
from app.services.detection.image_similarity import (
    ImageComparisonResult,
    ImageHashResult,
    ImageSimilarityService,
    ImageValidationResult,
)
from app.services.detection.jobs import (
    AnalysisJobRecord,
    JobStatus,
    JobTrackerService,
    job_tracker,
)
from app.services.detection.profile_analysis import (
    ProfileAnalysisResult,
    ProfileAnalysisService,
    SocialProfileInput,
)
from app.services.detection.scam_text import (
    ModelMetadata,
    ScamTextAnalysisResult,
    ScamTextClassifier,
)
from app.services.detection.sources import (
    BaseSourceAdapter,
    DiscoveredIndicator,
    DiscoverySourceType,
)
from app.services.detection.url_analysis import (
    IPValidationResult,
    SecureURLAnalysisService,
    URLAnalysisResult,
)

__all__ = [
    "DiscoverySourceType",
    "DiscoveredIndicator",
    "BaseSourceAdapter",
    "VerifiedBrandProfile",
    "BrandIntelligenceService",
    "HomoglyphDetector",
    "DomainAnalysisResult",
    "DomainAnalysisService",
    "IPValidationResult",
    "URLAnalysisResult",
    "SecureURLAnalysisService",
    "ScamTextClassifier",
    "ScamTextAnalysisResult",
    "ModelMetadata",
    "SocialProfileInput",
    "ProfileAnalysisResult",
    "ProfileAnalysisService",
    "ImageValidationResult",
    "ImageHashResult",
    "ImageComparisonResult",
    "ImageSimilarityService",
    "APKAnalysisResult",
    "APKAnalysisService",
    "JobStatus",
    "AnalysisJobRecord",
    "JobTrackerService",
    "job_tracker",
]
