from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.services.detection.jobs import JobStatus


class TextAnalysisRequest(BaseModel):
    """Payload to request scam text classification and heuristic analysis."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text message, email snippet, or communication to evaluate",
    )
    brand_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional verified brand ID for target context",
    )


class URLAnalysisRequest(BaseModel):
    """Payload to request safe URL structural and domain threat analysis."""

    url: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        description="URL to analyze for domain impersonation, SSRF targets, and phishing paths",
    )
    brand_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional verified brand ID to measure lexical and homoglyph similarity against",
    )


class ProfileAnalysisRequest(BaseModel):
    """Payload to analyze a candidate social media profile for brand impersonation."""

    platform: str = Field(..., description="Platform name (e.g. Twitter, Instagram, LinkedIn, Telegram)")
    username: str = Field(..., description="Account handle or username (e.g. @brand_support)")
    display_name: Optional[str] = None
    bio: Optional[str] = None
    profile_url: Optional[str] = None
    external_links: List[str] = Field(default_factory=list)
    avatar_hash: Optional[str] = None
    brand_id: Optional[uuid.UUID] = None


class JobSubmissionResponse(BaseModel):
    """Acknowledgement returned upon submitting a background analysis task (HTTP 202)."""

    job_id: uuid.UUID
    job_type: str
    status: JobStatus
    created_at: datetime
    message: str


class JobStatusResponse(BaseModel):
    """Authoritative status and outcome report for an asynchronous analysis task."""

    job_id: uuid.UUID
    job_type: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
