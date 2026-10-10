from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.enums import RiskSeverity
from app.models.risk_assessment import RiskAssessment


class RiskAssessmentRepository:
    """Data access repository for RiskAssessment entities."""

    async def create(
        self,
        db: AsyncSession,
        report_id: Optional[uuid.UUID],
        model_version: str,
        risk_score: float,
        severity: RiskSeverity,
        explanation_json: Dict[str, Any],
        indicators_json: List[Dict[str, Any]],
        recommendation_json: List[Dict[str, Any]],
        entity_id: Optional[str] = None,
        confidence: Optional[float] = None,
    ) -> RiskAssessment:
        """Create and persist a new explainable risk assessment."""
        assessment = RiskAssessment(
            id=uuid.uuid4(),
            report_id=report_id,
            entity_id=entity_id,
            model_version=model_version,
            risk_score=round(float(risk_score), 2),
            severity=severity,
            confidence=confidence,
            explanation_json=explanation_json,
            indicators_json=indicators_json,
            recommendation_json=recommendation_json,
        )
        db.add(assessment)
        await db.flush()
        await db.refresh(assessment)
        return assessment

    async def get_by_id(
        self,
        db: AsyncSession,
        assessment_id: uuid.UUID,
    ) -> Optional[RiskAssessment]:
        """Fetch risk assessment by primary key."""
        stmt = (
            select(RiskAssessment)
            .options(selectinload(RiskAssessment.report))
            .where(RiskAssessment.id == assessment_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_by_report_id(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
    ) -> Optional[RiskAssessment]:
        """Fetch the most recent risk assessment for a given threat report."""
        stmt = (
            select(RiskAssessment)
            .options(selectinload(RiskAssessment.report))
            .where(RiskAssessment.report_id == report_id)
            .order_by(desc(RiskAssessment.created_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_report_id(
        self,
        db: AsyncSession,
        report_id: uuid.UUID,
    ) -> List[RiskAssessment]:
        """Fetch all historical assessments for a threat report."""
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.report_id == report_id)
            .order_by(desc(RiskAssessment.created_at))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
