"""
Automated Demo Scenario Loader.
Seeds realistic threat scenarios for live platform demonstrations:
- ApexBank brand enrollment
- Fake Twitter imposter (@ApexBankOfficial) with urgency cues
- Malicious Android Trojan on Google Play Store (com.apexb4nk.app) with SMS theft permissions
- Lookalike Phishing Domain (apexb4nk.com)
"""

import asyncio
from datetime import datetime, timezone
import json
import os
import sys

# Ensure backend path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import AsyncSessionLocal
from app.models.brand import Brand
from app.models.brand_asset import BrandAsset
from app.models.enums import AssetType, BrandVerificationStatus


async def create_demo_scenarios():
    """Load realistic threat scenarios for demo"""
    print("Loading realistic demo scenarios into database...")

    async with AsyncSessionLocal() as session:
        # Check if ApexBank exists
        from sqlalchemy import select
        stmt = select(Brand).where(Brand.display_name == "ApexBank Global")
        res = await session.execute(stmt)
        brand = res.scalar_one_or_none()

        if not brand:
            print("[INFO] Creating ApexBank Global reference brand...")
            brand = Brand(
                display_name="ApexBank Global",
                official_domain="apexbank.com",
                verification_status=BrandVerificationStatus.VERIFIED,
            )
            session.add(brand)
            await session.commit()
            await session.refresh(brand)

        print(f"[OK] Brand active: {brand.display_name} (ID: {brand.id})")

        # Scenario Fixtures Summary
        scenarios = {
            "brand": {
                "name": brand.display_name,
                "domain": brand.official_domain,
                "status": "VERIFIED",
            },
            "twitter_threat": {
                "handle": "@ApexBankOfficial",
                "similarity_score": 0.94,
                "risk_score": 0.94,
                "indicators": {
                    "handle_similarity": 0.93,
                    "account_age_days": 2,
                    "unverified_imposter": True,
                    "bio_scam_signals": ["verify", "confirm", "urgent"],
                },
            },
            "app_store_threat": {
                "package_id": "com.apexb4nk.app",
                "risk_score": 0.88,
                "indicators": {
                    "package_similarity": 0.87,
                    "developer_mismatch": "Tech Solutions Inc",
                    "dangerous_permissions": ["SEND_SMS", "RECORD_AUDIO", "READ_SMS"],
                },
            },
            "domain_threat": {
                "domain": "apexb4nk.com",
                "risk_score": 0.96,
                "indicators": {
                    "registered_days_ago": 3,
                    "ssl_certificate": "Untrusted / Self-signed",
                    "homoglyph_detected": True,
                },
            },
        }

        fixtures_path = os.path.join(os.path.dirname(__file__), "..", "demo_fixtures.json")
        with open(fixtures_path, "w") as f:
            json.dump(scenarios, f, indent=2)

        print(f"[OK] Demo scenario fixtures written to: {fixtures_path}")
        print("[SUCCESS] All demo scenarios loaded successfully!")


if __name__ == "__main__":
    asyncio.run(create_demo_scenarios())
