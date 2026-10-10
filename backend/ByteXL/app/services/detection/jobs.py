"""
Asynchronous Job Management and Status Tracking Service.
Provides authentic job scheduling, state transitions, and result retrieval for
longer-running analysis workloads (such as APK static inspection).

Design Invariant:
Never claims a job is completed if the worker has not genuinely executed the task.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional
import uuid
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger("app.services.detection.jobs")


class JobStatus(str, Enum):
    """Lifecycle states for background threat analysis tasks."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisJobRecord(BaseModel):
    """Authoritative execution and tracking record for an asynchronous analysis task."""

    job_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    job_type: str
    creator_user_id: Optional[uuid.UUID] = None
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class JobTrackerService:
    """Thread-safe background job execution and registry service."""

    def __init__(self) -> None:
        self._jobs: Dict[uuid.UUID, AnalysisJobRecord] = {}
        self._lock = asyncio.Lock()

    async def create_job(
        self, job_type: str, creator_user_id: Optional[uuid.UUID] = None
    ) -> AnalysisJobRecord:
        """Create and register a new pending job record."""
        async with self._lock:
            record = AnalysisJobRecord(
                job_id=uuid.uuid4(),
                job_type=job_type,
                creator_user_id=creator_user_id,
                status=JobStatus.PENDING,
            )
            self._jobs[record.job_id] = record
            return record

    async def get_job(self, job_id: uuid.UUID) -> Optional[AnalysisJobRecord]:
        """Fetch current tracking status and result of a job."""
        async with self._lock:
            return self._jobs.get(job_id)

    async def run_async_task(
        self,
        job_id: uuid.UUID,
        coro_or_func: Callable[[], Any],
    ) -> None:
        """
        Execute the target task, transitioning status authentically from PENDING
        to PROCESSING, and then COMPLETED or FAILED based on actual execution outcome.
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)

        try:
            # Execute synchronously or asynchronously
            if asyncio.iscoroutinefunction(coro_or_func):
                result = await coro_or_func()
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, coro_or_func)

            async with self._lock:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)
                if hasattr(result, "model_dump"):
                    job.result = result.model_dump(mode="json")
                elif isinstance(result, dict):
                    job.result = result
                else:
                    job.result = {"data": str(result)}

            logger.info(f"Job {job_id} ({job.job_type}) completed successfully.")

        except Exception as e:
            logger.exception(f"Job {job_id} failed during execution: {e}")
            async with self._lock:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                job.error_message = str(e)


# Global singleton instance
job_tracker = JobTrackerService()
