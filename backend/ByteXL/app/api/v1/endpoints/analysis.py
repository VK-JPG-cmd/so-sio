import asyncio
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import get_current_active_user
from app.core.exceptions import NotFoundError, ValidationError
from app.db.session import get_db
from app.models.user import User
from app.schemas.detection import (
    JobStatusResponse,
    JobSubmissionResponse,
    ProfileAnalysisRequest,
    TextAnalysisRequest,
    URLAnalysisRequest,
)
from app.schemas.app_metadata import (
    AppMetadataAnalysisRequest,
    AppMetadataAnalysisResponse,
)
from app.services.detection.apk_analysis import APKAnalysisResult, APKAnalysisService
from app.services.detection.app_metadata_analysis import AppMetadataAnalysisService
from app.services.detection.brand_intelligence import (
    BrandIntelligenceService,
    VerifiedBrandProfile,
)
from app.services.detection.jobs import job_tracker
from app.services.detection.profile_analysis import (
    ProfileAnalysisResult,
    ProfileAnalysisService,
    SocialProfileInput,
)
from app.services.detection.scam_text import (
    ScamTextAnalysisResult,
    ScamTextClassifier,
)
from app.services.detection.url_analysis import (
    SecureURLAnalysisService,
    URLAnalysisResult,
)

router = APIRouter(prefix="/analyze", tags=["Threat Detection Engine"])

brand_intel_service = BrandIntelligenceService()
url_analysis_service = SecureURLAnalysisService()
scam_classifier = ScamTextClassifier()
profile_analysis_service = ProfileAnalysisService()
apk_analysis_service = APKAnalysisService()
app_metadata_analysis_service = AppMetadataAnalysisService()


async def _resolve_reference_brands(
    db: AsyncSession, brand_id: Optional[uuid.UUID] = None
) -> List[VerifiedBrandProfile]:
    """Retrieve verified brand reference intelligence."""
    if brand_id:
        brand = await brand_intel_service.get_verified_brand(db, brand_id)
        return [brand] if brand else []
    return await brand_intel_service.list_all_verified_brands(db)


@router.post(
    "/text",
    response_model=ScamTextAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analyze text for scam or phishing content",
    description=(
        "Evaluates input message text using a TF-IDF + LogisticRegression baseline model "
        "and transparent rule-based indicators for urgency, financial lures, and credential requests."
    ),
)
async def analyze_text(
    payload: TextAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ScamTextAnalysisResult:
    return scam_classifier.classify_text(payload.text)


@router.post(
    "/url",
    response_model=URLAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Secure URL and domain threat analysis",
    description=(
        "Analyzes a URL using Public Suffix List parsing, RapidFuzz similarity, homoglyph detection, "
        "and strict SSRF protections. Direct HTTP connection to the destination is disabled in the API process."
    ),
)
async def analyze_url(
    payload: URLAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> URLAnalysisResult:
    verified_brands = await _resolve_reference_brands(db, payload.brand_id)
    return url_analysis_service.analyze_url(payload.url, verified_brands)


@router.post(
    "/profile",
    response_model=ProfileAnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Analyze social profile for brand impersonation",
    description=(
        "Compares candidate social media profile indicators against verified brand reference data. "
        "Missing profile information does NOT increase the risk score."
    ),
)
async def analyze_profile(
    payload: ProfileAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileAnalysisResult:
    verified_brands = await _resolve_reference_brands(db, payload.brand_id)
    profile_input = SocialProfileInput(
        platform=payload.platform,
        username=payload.username,
        display_name=payload.display_name,
        bio=payload.bio,
        profile_url=payload.profile_url,
        external_links=payload.external_links,
        avatar_hash=payload.avatar_hash,
    )
    return profile_analysis_service.analyze_profile(profile_input, verified_brands)


@router.post(
    "/app-metadata",
    response_model=AppMetadataAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze app-store listing metadata for brand impersonation",
    description=(
        "Evaluates candidate mobile application metadata against verified brand official mobile assets. "
        "Calculates explainable risk scores without fetching external URLs or executing APK binaries."
    ),
)
async def analyze_app_metadata(
    payload: AppMetadataAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AppMetadataAnalysisResponse:
    brand = await brand_intel_service.get_verified_brand(db, payload.brand_id)
    if not brand:
        raise NotFoundError(f"Verified brand with ID '{payload.brand_id}' not found.")
    return app_metadata_analysis_service.analyze_metadata(payload, brand)


import os
import re
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.models.enums import UserRole


@router.post(
    "/apk",
    response_model=JobSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit Android APK for static analysis",
    description=(
        "Accepts an uploaded APK package for static analysis using Androguard. "
        "Runs in an isolated background worker with timeouts and resource limits. "
        "Never executes code. Returns HTTP 202 with tracking job_id."
    ),
)
async def analyze_apk(
    file: UploadFile = File(..., description="Android APK package file"),
    brand_id: Optional[uuid.UUID] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> JobSubmissionResponse:
    raw_filename = file.filename or "application.apk"
    base_name = os.path.basename(raw_filename.replace("\\", "/")).strip()
    sanitized_filename = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
    if not sanitized_filename.lower().endswith(".apk"):
        raise ValidationError("Uploaded file must have a .apk extension.")

    # Stream read with strict max size bound (50 MB) to prevent memory exhaustion
    max_size = 50 * 1024 * 1024
    apk_content = bytearray()
    chunk_size = 64 * 1024
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        apk_content.extend(chunk)
        if len(apk_content) > max_size:
            raise ValidationError("APK file size exceeds maximum allowed 50 MB.")

    if not apk_content:
        raise ValidationError("Uploaded APK file is empty.")

    apk_bytes = bytes(apk_content)
    verified_brands = await _resolve_reference_brands(db, brand_id)

    # Register job record with ownership for IDOR defense
    job_record = await job_tracker.create_job(
        "APK_STATIC_ANALYSIS", creator_user_id=current_user.id
    )

    # Define the worker function that genuinely executes static analysis
    def run_worker() -> APKAnalysisResult:
        return apk_analysis_service.analyze_apk(
            apk_bytes=apk_bytes,
            file_name=sanitized_filename,
            verified_brands=verified_brands,
        )

    # Spawn real background execution
    asyncio.create_task(job_tracker.run_async_task(job_record.job_id, run_worker))

    return JobSubmissionResponse(
        job_id=job_record.job_id,
        job_type=job_record.job_type,
        status=job_record.status,
        created_at=job_record.created_at,
        message="APK static analysis job queued. Poll /api/v1/analyze/jobs/{job_id} for progress.",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Track asynchronous analysis job status",
    description="Returns the authentic execution status, timings, errors, and results of a background analysis job.",
)
async def get_analysis_job_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
) -> JobStatusResponse:
    job = await job_tracker.get_job(job_id)
    if not job:
        raise NotFoundError(f"Analysis job '{job_id}' not found.")

    # IDOR / cross-user data access prevention
    if (
        job.creator_user_id is not None
        and current_user.role != UserRole.ADMIN
        and job.creator_user_id != current_user.id
    ):
        raise AuthorizationError("Access forbidden: You do not have permission to view this analysis job.")

    return JobStatusResponse(
        job_id=job.job_id,
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        result=job.result,
        error_message=job.error_message,
    )
