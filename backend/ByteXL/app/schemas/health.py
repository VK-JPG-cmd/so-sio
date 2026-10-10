from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for basic process liveness response."""

    status: str = Field(default="healthy", description="Process liveness status")
    app_name: str = Field(..., description="Application name")
    environment: str = Field(..., description="Current deployment environment")
    version: str = Field(..., description="Application semantic version")
    timestamp: datetime = Field(..., description="UTC timestamp of the check")


class DependencyStatus(BaseModel):
    """Schema for individual dependency status."""

    status: str = Field(..., description="Dependency status: connected or disconnected")
    engine: str = Field(..., description="Dependency type/engine name")
    error: Optional[str] = Field(default=None, description="Error details if connection failed")


class ReadinessResponse(BaseModel):
    """Schema for comprehensive application readiness probe."""

    status: str = Field(..., description="Overall readiness: ready or not_ready")
    timestamp: datetime = Field(..., description="UTC timestamp of the probe")
    dependencies: Dict[str, DependencyStatus] = Field(
        ..., description="Health status of all external services"
    )
