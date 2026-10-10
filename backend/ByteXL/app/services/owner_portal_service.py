from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationError, BadRequestError, NotFoundError
from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.brand import Brand
from app.models.campaign import Campaign
from app.models.enums import AlertStatus, ReviewStatus, RiskSeverity, ThreatReportStatus, UserRole
from app.models.review import Review
from app.models.review_response import ReviewResponse
from app.models.risk_assessment import RiskAssessment
from app.models.threat_report import ThreatReport
from app.models.user import User
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.correlation_repo import AlertRepository, CampaignRepository
from app.repositories.review_response_repo import ReviewResponseRepository
from app.schemas.correlation import AlertResponse
from app.schemas.owner_portal import (
    BrandDashboardSummaryResponse,
    BrandMetadataUpdate,
    ReviewOwnerResponseCreate,
    RiskTrendPointResponse,
)

logger = get_logger("app.services.owner_portal_service")


class OwnerPortalService:
    """Service handling brand owner portal operations, metrics, reviews, and audit trails."""

    def __init__(self) -> None:
        self.alert_repo = AlertRepository()
        self.campaign_repo = CampaignRepository()
        self.review_response_repo = ReviewResponseRepository()
        self.audit_repo = AuditLogRepository()

    async def verify_brand_ownership(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        current_user: User,
    ) -> Brand:
        """
        Enforce strict brand ownership authorization.
        A brand owner can access only their own brand. Platform administrators have global access.
        """
        stmt = select(Brand).where(Brand.id == brand_id)
        result = await db.execute(stmt)
        brand = result.scalar_one_or_none()
        if not brand:
            raise NotFoundError(f"Brand with id '{brand_id}' not found.")

        is_owner = brand.owner_user_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not is_owner and not is_admin:
            logger.warning(
                f"Unauthorized brand access attempt: user {current_user.id} tried accessing brand {brand_id}"
            )
            raise AuthorizationError("You do not have permission to access data for this brand.")

        return brand

    async def get_dashboard_summary(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
    ) -> BrandDashboardSummaryResponse:
        """
        Aggregate live database metrics for the brand owner dashboard:
        - Total threat reports
        - Threat counts by severity tier
        - Threat counts by lifecycle status
        - Recent alerts (up to 5)
        - Open investigations
        - Total correlated campaigns
        - Historical risk-score trends
        """
        # 1. Total threat reports
        total_stmt = select(func.count(ThreatReport.id)).where(ThreatReport.brand_id == brand_id)
        total_reports = (await db.execute(total_stmt)).scalar() or 0

        # 2. Threat counts by status
        status_stmt = (
            select(ThreatReport.status, func.count(ThreatReport.id))
            .where(ThreatReport.brand_id == brand_id)
            .group_by(ThreatReport.status)
        )
        status_res = await db.execute(status_stmt)
        threats_by_status = {s.value: 0 for s in ThreatReportStatus}
        for st, count in status_res.all():
            threats_by_status[st.value] = count

        # 3. Open investigations (SUBMITTED, ANALYZING, UNDER_REVIEW)
        open_inv_stmt = select(func.count(ThreatReport.id)).where(
            ThreatReport.brand_id == brand_id,
            ThreatReport.status.in_([
                ThreatReportStatus.SUBMITTED,
                ThreatReportStatus.ANALYZING,
                ThreatReportStatus.UNDER_REVIEW,
            ]),
        )
        open_investigations = (await db.execute(open_inv_stmt)).scalar() or 0

        # 4. Total campaigns
        camp_stmt = select(func.count(Campaign.id)).where(Campaign.brand_id == brand_id)
        campaign_count = (await db.execute(camp_stmt)).scalar() or 0

        # 5. Threats by severity tier (based on assessments for brand threat reports)
        severity_stmt = (
            select(RiskAssessment.severity, func.count(RiskAssessment.id))
            .join(ThreatReport, RiskAssessment.report_id == ThreatReport.id)
            .where(ThreatReport.brand_id == brand_id)
            .group_by(RiskAssessment.severity)
        )
        severity_res = await db.execute(severity_stmt)
        threats_by_severity = {sev.value: 0 for sev in RiskSeverity}
        for sev, count in severity_res.all():
            threats_by_severity[sev.value] = count

        # 6. Recent alerts
        recent_alert_models = await self.alert_repo.list_by_brand(db, brand_id=brand_id, limit=5)
        recent_alerts = [AlertResponse.model_validate(a) for a in recent_alert_models]

        # 7. Recent risk-score trends (daily aggregated data)
        trend_stmt = (
            select(RiskAssessment.risk_score, RiskAssessment.created_at)
            .join(ThreatReport, RiskAssessment.report_id == ThreatReport.id)
            .where(ThreatReport.brand_id == brand_id)
            .order_by(desc(RiskAssessment.created_at))
            .limit(100)
        )
        trend_res = await db.execute(trend_stmt)
        daily_scores: Dict[str, List[float]] = defaultdict(list)
        for score, dt in trend_res.all():
            day_str = dt.strftime("%Y-%m-%d")
            daily_scores[day_str].append(score)

        recent_trends: List[RiskTrendPointResponse] = []
        for day_str in sorted(daily_scores.keys(), reverse=True)[:14]:
            scores = daily_scores[day_str]
            recent_trends.append(
                RiskTrendPointResponse(
                    date=day_str,
                    assessment_count=len(scores),
                    average_risk_score=round(sum(scores) / len(scores), 1),
                    max_risk_score=round(max(scores), 1),
                )
            )

        return BrandDashboardSummaryResponse(
            brand_id=brand_id,
            total_threat_reports=total_reports,
            threats_by_severity=threats_by_severity,
            threats_by_status=threats_by_status,
            recent_alerts=recent_alerts,
            open_investigations=open_investigations,
            campaign_count=campaign_count,
            recent_risk_score_trends=recent_trends,
        )

    async def list_brand_threats(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        severity: Optional[RiskSeverity] = None,
        status: Optional[ThreatReportStatus] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> Tuple[List[ThreatReport], int]:
        """
        List threat reports targeting the brand with pagination, sorting, and multi-criteria filtering.
        Returns (threat_reports, total_count).
        """
        query = select(ThreatReport).where(ThreatReport.brand_id == brand_id)
        count_query = select(func.count(func.distinct(ThreatReport.id))).where(ThreatReport.brand_id == brand_id)

        if status:
            query = query.where(ThreatReport.status == status)
            count_query = count_query.where(ThreatReport.status == status)

        if created_after:
            query = query.where(ThreatReport.created_at >= created_after)
            count_query = count_query.where(ThreatReport.created_at >= created_after)

        if created_before:
            query = query.where(ThreatReport.created_at <= created_before)
            count_query = count_query.where(ThreatReport.created_at <= created_before)

        if severity:
            query = query.join(ThreatReport.assessments).where(RiskAssessment.severity == severity)
            count_query = count_query.join(ThreatReport.assessments).where(RiskAssessment.severity == severity)

        total_count = (await db.execute(count_query)).scalar() or 0

        # Sorting
        sort_col = ThreatReport.created_at
        if sort_by == "status":
            sort_col = ThreatReport.status
        elif sort_by == "target_value":
            sort_col = ThreatReport.target_value
        elif sort_by == "target_type":
            sort_col = ThreatReport.target_type

        order_fn = desc if sort_order.lower() == "desc" else asc
        query = (
            query.options(
                selectinload(ThreatReport.evidences),
                selectinload(ThreatReport.reporter),
                selectinload(ThreatReport.assessments),
            )
            .order_by(order_fn(sort_col))
            .offset(offset)
            .limit(limit)
        )

        result = await db.execute(query)
        reports = list(result.scalars().unique().all())
        return reports, total_count

    async def update_alert_status(
        self,
        db: AsyncSession,
        alert_id: uuid.UUID,
        new_status: AlertStatus,
        current_user: User,
        notes: Optional[str] = None,
    ) -> Alert:
        """
        Update an alert's incident status with strict brand ownership enforcement and audit trail.
        """
        alert = await self.alert_repo.get_by_id(db, alert_id)
        if not alert:
            raise NotFoundError(f"Alert with id '{alert_id}' not found.")

        # Enforce brand ownership
        await self.verify_brand_ownership(db, alert.brand_id, current_user)

        old_status = alert.status.value
        updated_alert = await self.alert_repo.update_status(db, alert, new_status)

        # Record immutable audit log
        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            brand_id=alert.brand_id,
            action="ALERT_STATUS_UPDATE",
            entity_type="ALERT",
            entity_id=str(alert.id),
            details={
                "old_status": old_status,
                "new_status": new_status.value,
                "notes": notes,
            },
        )
        return updated_alert

    async def update_brand_metadata(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        payload: BrandMetadataUpdate,
        current_user: User,
    ) -> Brand:
        """
        Allow authorized brand owners to manage official brand metadata.
        Strict invariant: Does NOT allow changing verification status directly.
        """
        brand = await self.verify_brand_ownership(db, brand_id, current_user)

        old_display_name = brand.display_name
        diff: Dict[str, Any] = {}

        if payload.display_name is not None:
            brand.display_name = payload.display_name.strip()
            diff["display_name"] = {"old": old_display_name, "new": brand.display_name}

        if diff:
            await self.audit_repo.create_log(
                db=db,
                actor_user_id=current_user.id,
                brand_id=brand.id,
                action="BRAND_METADATA_UPDATE",
                entity_type="BRAND",
                entity_id=str(brand.id),
                details=diff,
            )
            await db.flush()
            await db.refresh(brand)

        return brand

    async def respond_to_review(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        review_id: uuid.UUID,
        payload: ReviewOwnerResponseCreate,
        current_user: User,
    ) -> ReviewResponse:
        """
        Allow brand owners to respond to customer reviews using a separate ReviewResponse model.
        Invariant: Brand owners must not delete or rewrite customer reviews.
        """
        await self.verify_brand_ownership(db, brand_id, current_user)

        stmt = select(Review).where(Review.id == review_id)
        res = await db.execute(stmt)
        review = res.scalar_one_or_none()
        if not review:
            raise NotFoundError(f"Review with id '{review_id}' not found.")

        if review.brand_id != brand_id:
            raise AuthorizationError("Review does not belong to the specified brand.")

        owner_reply = await self.review_response_repo.create_or_update(
            db=db,
            review_id=review_id,
            brand_id=brand_id,
            responder_user_id=current_user.id,
            response_text=payload.response_text.strip(),
        )

        # Audit log entry
        await self.audit_repo.create_log(
            db=db,
            actor_user_id=current_user.id,
            brand_id=brand_id,
            action="REVIEW_RESPONSE_CREATE",
            entity_type="REVIEW",
            entity_id=str(review_id),
            details={
                "review_id": str(review_id),
                "response_id": str(owner_reply.id),
                "text_length": len(payload.response_text),
            },
        )
        return owner_reply

    async def list_brand_reviews(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        status: Optional[ReviewStatus] = None,
        min_rating: Optional[int] = None,
    ) -> List[Review]:
        """
        List reviews targeting the brand along with any attached official owner responses.
        """
        stmt = (
            select(Review)
            .options(
                selectinload(Review.owner_response),
                selectinload(Review.customer),
            )
            .where(Review.brand_id == brand_id)
            .order_by(desc(Review.created_at))
            .offset(offset)
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Review.status == status)
        if min_rating:
            stmt = stmt.where(Review.rating >= min_rating)

        result = await db.execute(stmt)
        return list(result.scalars().all())
