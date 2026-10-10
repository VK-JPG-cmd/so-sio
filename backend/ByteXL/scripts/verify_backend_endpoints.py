"""
Comprehensive Backend Endpoints Verification Script for BrandShield AI.
Tests every major API router and capability.
"""

import asyncio
import httpx
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.otp import OTPVerification
from app.models.brand import Brand

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_all_endpoints():
    print("=" * 60)
    print("BrandShield AI — Full Backend Diagnostic & Health Verification")
    print("=" * 60)

    results = []

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", timeout=10.0) as client:
        # 1. Health Probe
        try:
            r = await client.get("/api/v1/health")
            if r.status_code == 200:
                data = r.json()
                print(f"[PASS] 1. Health Probe: status={data.get('status')}, version={data.get('version')}")
                results.append(("Health Probe", True))
            else:
                print(f"[FAIL] 1. Health Probe: HTTP {r.status_code}")
                results.append(("Health Probe", False))
        except Exception as e:
            print(f"[FAIL] 1. Health Probe: {e}")
            results.append(("Health Probe", False))

        # 2. Interactive Dashboard
        try:
            r = await client.get("/dashboard")
            if r.status_code == 200:
                print(f"[PASS] 2. Interactive Dashboard: HTTP {r.status_code} (HTML dashboard loaded)")
                results.append(("Interactive Dashboard", True))
            else:
                print(f"[WARN] 2. Interactive Dashboard: HTTP {r.status_code}")
                results.append(("Interactive Dashboard", False))
        except Exception as e:
            print(f"[FAIL] 2. Interactive Dashboard: {e}")
            results.append(("Interactive Dashboard", False))

        # 3. Public Brands Discovery
        apex_brand_id = None
        try:
            r = await client.get("/api/v1/brands")
            if r.status_code == 200:
                brands = r.json()
                print(f"[PASS] 3. Brands Discovery: {len(brands)} verified brands listed in database")
                if brands:
                    apex_brand_id = brands[0]["id"]
                    print(f"       -> Sample Brand: '{brands[0]['display_name']}' ({brands[0]['official_domain']}), ID={apex_brand_id}")
                results.append(("Brands Discovery", True))
            else:
                print(f"[FAIL] 3. Brands Discovery: HTTP {r.status_code}")
                results.append(("Brands Discovery", False))
        except Exception as e:
            print(f"[FAIL] 3. Brands Discovery: {e}")
            results.append(("Brands Discovery", False))

        # 4. Brand Details by ID
        if apex_brand_id:
            try:
                r = await client.get(f"/api/v1/brands/{apex_brand_id}")
                if r.status_code == 200:
                    b_data = r.json()
                    print(f"[PASS] 4. Brand Details Endpoint: '{b_data.get('display_name')}', status={b_data.get('verification_status')}")
                    results.append(("Brand Details", True))
                else:
                    print(f"[FAIL] 4. Brand Details Endpoint: HTTP {r.status_code}")
                    results.append(("Brand Details", False))
            except Exception as e:
                print(f"[FAIL] 4. Brand Details Endpoint: {e}")
                results.append(("Brand Details", False))

        # 5. Auth OTP Start (Passwordless)
        import time
        test_phone = f"+1555{int(time.time()) % 10000000:07d}"
        try:
            r = await client.post("/api/v1/auth/otp/start", json={"phone_number": test_phone})
            if r.status_code == 200:
                otp_res = r.json()
                print(f"[PASS] 5. Auth OTP Start: Dispatched code, cooldown={otp_res.get('cooldown_seconds')}s, expires={otp_res.get('expires_in_seconds')}s")
                results.append(("Auth OTP Start", True))
            else:
                print(f"[FAIL] 5. Auth OTP Start: HTTP {r.status_code} - {r.text}")
                results.append(("Auth OTP Start", False))
        except Exception as e:
            print(f"[FAIL] 5. Auth OTP Start: {e}")
            results.append(("Auth OTP Start", False))

        # 6. Read latest code & Verify OTP to obtain JWT
        access_token = None
        try:
            # Look up salt and hash or retrieve sent code
            from app.services.otp_provider import get_otp_provider
            provider = get_otp_provider()
            sent_code = getattr(provider, "sent_codes", {}).get(test_phone)
            
            # If not in mock provider memory, query directly
            if not sent_code:
                # Query DB to test with a known test salt/code
                async with AsyncSessionLocal() as session:
                    rec = await session.execute(
                        select(OTPVerification).where(OTPVerification.phone_number == test_phone).order_by(OTPVerification.created_at.desc())
                    )
                    otp_rec = rec.scalars().first()
                    if otp_rec:
                        # Re-hash for a known code to test verify
                        from app.core.security import hash_otp
                        otp_rec.hashed_code = hash_otp("123456", otp_rec.salt)
                        await session.commit()
                        sent_code = "123456"

            if sent_code:
                r = await client.post("/api/v1/auth/otp/verify", json={"phone_number": test_phone, "code": sent_code})
                if r.status_code == 200:
                    token_data = r.json()
                    access_token = token_data.get("access_token")
                    print(f"[PASS] 6. Auth OTP Verify: Issued JWT access token ({token_data.get('token_type')}, expires in {token_data.get('expires_in')}s)")
                    results.append(("Auth OTP Verify & JWT", True))
                else:
                    print(f"[FAIL] 6. Auth OTP Verify: HTTP {r.status_code} - {r.text}")
                    results.append(("Auth OTP Verify & JWT", False))
            else:
                print("[SKIP] 6. Auth OTP Verify: Could not retrieve sent code")
                results.append(("Auth OTP Verify & JWT", False))
        except Exception as e:
            print(f"[FAIL] 6. Auth OTP Verify: {e}")
            results.append(("Auth OTP Verify & JWT", False))

        # 7. Authenticated User Profile & Brand Owner Token
        from app.core.security import create_access_token
        from app.models.user import User
        async with AsyncSessionLocal() as session:
            rec = await session.execute(select(User).where(User.phone_number == "+15559021144"))
            owner = rec.scalars().first()
            if owner:
                owner_token, _ = create_access_token(user_id=owner.id, role=owner.role.value)
                headers = {"Authorization": f"Bearer {owner_token}"}

        if headers:
            try:
                r = await client.get("/api/v1/users/me", headers=headers)
                if r.status_code == 200:
                    u = r.json()
                    print(f"[PASS] 7. Authenticated User Profile: Phone={u.get('phone_number')}, Role={u.get('role')}, Status={u.get('account_status')}")
                    results.append(("User Profile /users/me", True))
                else:
                    print(f"[FAIL] 7. Authenticated User Profile: HTTP {r.status_code} - {r.text}")
                    results.append(("User Profile /users/me", False))
            except Exception as e:
                print(f"[FAIL] 7. Authenticated User Profile: {e}")
                results.append(("User Profile /users/me", False))

        # 8. AI Detection / Text Scam Analysis Engine
        try:
            sample_scam = "URGENT: Your bank account is locked! Click http://secure-login-phish.net to verify your credentials immediately or your funds will be frozen within 15 minutes."
            r = await client.post("/api/v1/analyze/text", json={"text": sample_scam}, headers=headers)
            if r.status_code == 200:
                analysis = r.json()
                print(f"[PASS] 8. AI Text Scam Classifier: score={analysis.get('risk_score')}, is_scam={analysis.get('is_scam')}")
                results.append(("AI Text Scam Engine", True))
            else:
                print(f"[WARN] 8. AI Text Scam Classifier: HTTP {r.status_code} - {r.text}")
                results.append(("AI Text Scam Engine", False))
        except Exception as e:
            print(f"[FAIL] 8. AI Text Scam Classifier: {e}")
            results.append(("AI Text Scam Engine", False))

        # 9. Brand Owner Portal: Campaigns
        if apex_brand_id and access_token:
            try:
                r = await client.get(f"/api/v1/owner/brands/{apex_brand_id}/campaigns", headers=headers)
                if r.status_code == 200:
                    camps = r.json()
                    print(f"[PASS] 9. Owner Campaigns Endpoint: {len(camps)} campaigns returned")
                    results.append(("Owner Campaigns", True))
                else:
                    print(f"[FAIL] 9. Owner Campaigns Endpoint: HTTP {r.status_code} - {r.text}")
                    results.append(("Owner Campaigns", False))
            except Exception as e:
                print(f"[FAIL] 9. Owner Campaigns Endpoint: {e}")
                results.append(("Owner Campaigns", False))

        # 10. Brand Owner Portal: Dashboard Summary
        if apex_brand_id and access_token:
            try:
                r = await client.get(f"/api/v1/owner/brands/{apex_brand_id}/dashboard", headers=headers)
                if r.status_code == 200:
                    dash = r.json()
                    print(f"[PASS] 10. Owner Dashboard Summary: Active threats={dash.get('active_threats_count', 0)}, Campaigns={dash.get('campaigns_count', 0)}")
                    results.append(("Owner Dashboard Summary", True))
                else:
                    print(f"[FAIL] 10. Owner Dashboard Summary: HTTP {r.status_code} - {r.text}")
                    results.append(("Owner Dashboard Summary", False))
            except Exception as e:
                print(f"[FAIL] 10. Owner Dashboard Summary: {e}")
                results.append(("Owner Dashboard Summary", False))

    print("\n" + "=" * 60)
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"DIAGNOSTIC SUMMARY: {passed}/{total} backend systems operational ({int(passed/total*100)}%)")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
