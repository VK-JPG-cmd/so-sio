from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.brand_application import BrandApplication
from app.models.enums import ApplicationStatus


class BrandApplicationRepository:
    """Data access repository for BrandApplication entities."""

    async def create(
        self,
        db: AsyncSession,
        owner_user_id: uuid.UUID,
        business_name: str,
        official_domain: str,
    ) -> BrandApplication:
        """Create and persist a new brand application."""
        app = BrandApplication(
            id=uuid.uuid4(),
            owner_user_id=owner_user_id,
            business_name=business_name,
            official_domain=official_domain,
            application_status=ApplicationStatus.PENDING_DOMAIN_VERIFICATION,
        )
        db.add(app)
        await db.flush()
        await db.refresh(app)
        return app

    async def get_by_id(
        self,
        db: AsyncSession,
        application_id: uuid.UUID,
    ) -> Optional[BrandApplication]:
        """Retrieve brand application by UUID."""
        stmt = select(BrandApplication).where(BrandApplication.id == application_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner_id(
        self,
        db: AsyncSession,
        owner_user_id: uuid.UUID,
    ) -> List[BrandApplication]:
        """Retrieve all applications submitted by an owner."""
        stmt = (
            select(BrandApplication)
            .where(BrandApplication.owner_user_id == owner_user_id)
            .order_by(BrandApplication.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_domain_active(
        self,
        db: AsyncSession,
        domain: str,
    ) -> Optional[BrandApplication]:
        """Check for active or approved application with identical official domain."""
        stmt = (
            select(BrandApplication)
            .where(BrandApplication.official_domain == domain)
            .where(BrandApplication.application_status.in_([
                ApplicationStatus.PENDING_DOMAIN_VERIFICATION,
                ApplicationStatus.PENDING_REVIEW,
                ApplicationStatus.APPROVED,
            ]))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self,
        db: AsyncSession,
        application: BrandApplication,
        new_status: ApplicationStatus,
        reviewed_at: Optional[datetime] = None,
    ) -> BrandApplication:
        """Transition application status."""
        application.application_status = new_status
        if reviewed_at:
            application.reviewed_at = reviewed_at
        await db.flush()
        await db.refresh(application)
        return application
