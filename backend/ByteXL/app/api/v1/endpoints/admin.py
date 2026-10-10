from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.brand_application import AdminReviewRequest, AdminReviewResponse
from app.schemas.discovery import (
    DiscoveredIndicatorResponse,
    DiscoveryHealthResponse,
    DiscoveryRunNowResponse,
    DiscoveryStatsResponse,
    SourceHealthSummary,
)
from app.services.brand_service import BrandService

router = APIRouter(prefix="/admin", tags=["Admin Operations"])
brand_service = BrandService()


@router.post(
    "/brand-applications/{id}/review",
    response_model=AdminReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Administrative application review",
    description="Enforces manual business review to approve or reject a brand application.",
)
async def review_brand_application(
    id: uuid.UUID,
    payload: AdminReviewRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminReviewResponse:
    return await brand_service.admin_review(
        db=db,
        application_id=id,
        decision=payload.decision,
        admin_user=current_admin,
        notes=payload.notes,
    )


# ==============================================================================
# Continuous Threat Discovery & Monitoring Operational Endpoints
# ==============================================================================


@router.get(
    "/discovery/health",
    response_model=DiscoveryHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Discovery pipeline health and telemetry",
    description="Returns authoritative health status of all registered threat intelligence connectors.",
)
async def get_discovery_health(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DiscoveryHealthResponse:
    from app.core.config import get_settings
    from app.repositories.discovery_repo import DiscoveryCheckpointRepository
    from app.services.discovery.worker import discovery_worker

    settings = get_settings()
    cp_repo = DiscoveryCheckpointRepository()
    checkpoints = {cp.source_id: cp for cp in await cp_repo.list_all(db)}

    source_summaries: list[SourceHealthSummary] = []
    has_error = False

    for connector in discovery_worker.connectors:
        cp = checkpoints.get(connector.source_id)
        is_conf = connector.is_configured()

        status_str = "NOT_CONFIGURED" if not is_conf else (cp.status if cp else "IDLE")
        if cp and cp.status == "ERROR":
            has_error = True

        source_summaries.append(
            SourceHealthSummary(
                source_id=connector.source_id,
                source_name=connector.source_name,
                is_configured=is_conf,
                status=status_str,
                last_poll_at=cp.last_poll_at if cp else None,
                last_success_at=cp.last_success_at if cp else None,
                last_error_at=cp.last_error_at if cp else None,
                last_error_message=cp.last_error_message if cp else None,
                indicators_fetched_total=cp.indicators_fetched_total if cp else 0,
                indicators_accepted_total=cp.indicators_accepted_total if cp else 0,
                indicators_rejected_total=cp.indicators_rejected_total if cp else 0,
                poll_count=cp.poll_count if cp else 0,
                checkpoint_value=cp.checkpoint_value if cp else None,
            )
        )

    if not settings.THREAT_DISCOVERY_WORKER_ENABLED and not any(s.is_configured for s in source_summaries):
        overall = "NOT_CONFIGURED"
    elif not settings.THREAT_DISCOVERY_WORKER_ENABLED:
        overall = "DISABLED"
    elif has_error:
        overall = "DEGRADED"
    else:
        overall = "HEALTHY"

    return DiscoveryHealthResponse(
        worker_running=discovery_worker.is_running,
        worker_enabled=settings.THREAT_DISCOVERY_WORKER_ENABLED,
        overall_status=overall,
        poll_interval_seconds=settings.THREAT_DISCOVERY_POLL_INTERVAL_SECONDS,
        batch_size=settings.THREAT_DISCOVERY_BATCH_SIZE,
        configured_sources=sum(1 for s in source_summaries if s.is_configured),
        active_sources=len(source_summaries),
        sources=source_summaries,
    )


@router.get(
    "/discovery/stats",
    response_model=DiscoveryStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Discovery indicator statistics",
    description="Returns aggregate counts of discovered indicators by status.",
)
async def get_discovery_stats(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DiscoveryStatsResponse:
    from app.repositories.discovery_repo import DiscoveredIndicatorRepository
    from app.services.discovery.worker import discovery_worker

    repo = DiscoveredIndicatorRepository()
    counts = await repo.count_by_status(db)
    total = sum(counts.values())

    return DiscoveryStatsResponse(
        total_indicators=total,
        status_counts=counts,
        sources_count=len(discovery_worker.connectors),
    )


@router.post(
    "/discovery/run-now",
    response_model=DiscoveryRunNowResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute on-demand threat discovery cycle",
    description="Triggers a synchronous discovery polling and correlation cycle across all configured feeds.",
)
async def trigger_discovery_cycle(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> DiscoveryRunNowResponse:
    from app.services.discovery.worker import discovery_worker

    summary = await discovery_worker.run_discovery_cycle(db_override=db)
    return DiscoveryRunNowResponse(
        status=summary.get("status", "SUCCESS"),
        duration_seconds=summary.get("duration_seconds"),
        connectors_processed=summary.get("connectors_processed", 0),
        total_fetched=summary.get("total_fetched", 0),
        total_valid=summary.get("total_valid", 0),
        total_rejected=summary.get("total_rejected", 0),
        details=summary.get("details", []),
    )


@router.get(
    "/discovery/indicators",
    response_model=List[DiscoveredIndicatorResponse],
    status_code=status.HTTP_200_OK,
    summary="List recent discovered indicators",
    description="Query external threat observations with optional filtering by source or status.",
)
async def list_discovered_indicators(
    source_id: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[DiscoveredIndicatorResponse]:
    from app.repositories.discovery_repo import DiscoveredIndicatorRepository
    repo = DiscoveredIndicatorRepository()
    items = await repo.list_recent(db, source_id=source_id, status=status_filter, limit=limit, offset=offset)
    return [DiscoveredIndicatorResponse.model_validate(i) for i in items]

