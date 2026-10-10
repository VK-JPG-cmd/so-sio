"""
Seed demo data script for BrandShield AI.
Populates the database with initial verified brands, assets, campaigns, and threats.
"""

import asyncio
from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.enums import (
    AccountStatus,
    ApplicationStatus,
    AssetType,
    AssetVerificationStatus,
    BrandVerificationStatus,
    CampaignStatus,
    TargetType,
    ThreatReportStatus,
    UserRole,
)
from app.models.user import User
from app.models.brand_application import BrandApplication
from app.models.brand import Brand
from app.models.official_social_asset import BrandSocialAsset
from app.models.official_mobile_asset import BrandMobileApp
from app.models.campaign import Campaign
from app.models.threat_report import ThreatReport

async def seed_data() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if users already seeded
        result = await session.execute(select(User).where(User.phone_number == "+15559021144"))
        existing_owner = result.scalars().first()
        
        if existing_owner:
            print("[INFO] Database already contains seed data. Skipping seed.")
            return

        print("[INFO] Seeding initial users...")
        now = datetime.now(timezone.utc)

        # 1. Users
        owner_user = User(
            id=uuid.uuid4(),
            phone_number="+15559021144",
            phone_verified_at=now,
            role=UserRole.BRAND_OWNER,
            account_status=AccountStatus.ACTIVE,
        )
        admin_user = User(
            id=uuid.uuid4(),
            phone_number="+15551234567",
            phone_verified_at=now,
            role=UserRole.ADMIN,
            account_status=AccountStatus.ACTIVE,
        )
        customer_user = User(
            id=uuid.uuid4(),
            phone_number="+15559876543",
            phone_verified_at=now,
            role=UserRole.CUSTOMER,
            account_status=AccountStatus.ACTIVE,
        )
        session.add_all([owner_user, admin_user, customer_user])
        await session.flush()

        print("[INFO] Seeding brand applications and brands...")
        # 2. Brands
        brands_data = [
            ("ApexBank Global", "apexbank.com"),
            ("AuraPay Checkout", "aurapay.io"),
            ("Lumina Cloud", "luminacloud.com"),
        ]

        apex_brand = None
        for name, domain in brands_data:
            app = BrandApplication(
                id=uuid.uuid4(),
                owner_user_id=owner_user.id,
                business_name=name,
                official_domain=domain,
                application_status=ApplicationStatus.APPROVED,
                reviewed_at=now,
            )
            session.add(app)
            await session.flush()

            brand = Brand(
                id=uuid.uuid4(),
                application_id=app.id,
                owner_user_id=owner_user.id,
                display_name=name,
                official_domain=domain,
                verification_status=BrandVerificationStatus.VERIFIED,
            )
            session.add(brand)
            await session.flush()

            if domain == "apexbank.com":
                apex_brand = brand

        # 3. ApexBank Assets
        if apex_brand:
            print("[INFO] Seeding ApexBank verified assets & campaign...")
            twitter_asset = BrandSocialAsset(
                id=uuid.uuid4(),
                brand_id=apex_brand.id,
                platform="twitter",
                handle="@ApexBank",
                canonical_url="https://x.com/ApexBank",
                verification_status=AssetVerificationStatus.VERIFIED,
            )
            insta_asset = BrandSocialAsset(
                id=uuid.uuid4(),
                brand_id=apex_brand.id,
                platform="instagram",
                handle="@ApexBankOfficial",
                canonical_url="https://instagram.com/ApexBankOfficial",
                verification_status=AssetVerificationStatus.VERIFIED,
            )
            mobile_app = BrandMobileApp(
                id=uuid.uuid4(),
                brand_id=apex_brand.id,
                app_name="ApexBank Mobile Banking",
                platform="android",
                app_identifier="com.apexbank.mobile",
                publisher_name="Apex Financial Corp",
                store_url="https://play.google.com/store/apps/details?id=com.apexbank.mobile",
                verification_status=AssetVerificationStatus.VERIFIED,
            )
            session.add_all([twitter_asset, insta_asset, mobile_app])

            # 4. Correlated Campaign
            campaign = Campaign(
                id=uuid.uuid4(),
                brand_id=apex_brand.id,
                title="Operation PhishVault 2026 Credential Syndicate",
                status=CampaignStatus.ACTIVE,
                risk_score=94.5,
                description="Coordinated multi-vector campaign deploying typosquatted domains, rogue Android malware APKs, and automated SMS lures aimed at harvesting banking 2FA passcodes.",
            )
            session.add(campaign)

            # 5. Threat Reports
            report1 = ThreatReport(
                id=uuid.uuid4(),
                reporter_id=customer_user.id,
                brand_id=apex_brand.id,
                target_type=TargetType.URL,
                target_value="https://apex-bank-secure-login.net/verify",
                description="Cloned login portal with deceptive domain structure harvesting 2FA tokens.",
                status=ThreatReportStatus.UNDER_REVIEW,
            )
            report2 = ThreatReport(
                id=uuid.uuid4(),
                reporter_id=customer_user.id,
                brand_id=apex_brand.id,
                target_type=TargetType.SOCIAL_PROFILE,
                target_value="@ApexBankHelp_Official",
                description="Fake automated support handle DMing customers with scam cash prizes.",
                status=ThreatReportStatus.CONFIRMED,
            )
            session.add_all([report1, report2])

        await session.commit()
        print("[SUCCESS] Seed demo data populated successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
