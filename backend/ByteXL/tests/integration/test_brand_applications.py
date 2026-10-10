from datetime import datetime, timedelta, timezone
import uuid
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.brand_application import BrandApplication
from app.models.domain_challenge import DomainChallenge
from app.models.enums import ApplicationStatus, UserRole
from app.models.user import User
from app.services.dns_resolver import MockDNSResolver
from app.services.otp_provider import MockOTPProvider


async def _create_authenticated_user(
    client: AsyncClient, mock_otp: MockOTPProvider, phone: str
) -> tuple[str, str]:
    """Helper to register and authenticate a user returning (user_id, access_token)."""
    await client.post("/api/v1/auth/otp/start", json={"phone_number": phone})
    code = mock_otp.get_last_code(phone)
    verify_res = await client.post("/api/v1/auth/otp/verify", json={"phone_number": phone, "code": code})
    data = verify_res.json()
    return data["user"]["id"], data["access_token"]


async def test_brand_application_creation_and_normalization(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify application creation normalizes the domain and records owner metadata."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155554001")

    # Pass un-normalized domain with uppercase and leading https://
    res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "business_name": "Acme Widgets Inc",
            "official_domain": "HTTPS://AcmeWidgets.COM/",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["business_name"] == "Acme Widgets Inc"
    assert data["official_domain"] == "acmewidgets.com"
    assert data["application_status"] == "PENDING_DOMAIN_VERIFICATION"
    assert "id" in data


async def test_brand_application_invalid_domains_rejected(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify malformed domains and IP addresses fail validation with 422."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155554002")

    # IP address
    res_ip = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "IP Corp", "official_domain": "192.168.1.1"},
    )
    assert res_ip.status_code == 422

    # Malformed domain
    res_bad = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "Bad Domain", "official_domain": "bad..domain"},
    )
    assert res_bad.status_code == 422


async def test_view_my_applications(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify owner can view their submitted applications."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155554003")

    await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "App One", "official_domain": "app-one.org"},
    )
    await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "App Two", "official_domain": "app-two.org"},
    )

    my_apps_res = await client.get(
        "/api/v1/brand-applications/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert my_apps_res.status_code == 200
    apps = my_apps_res.json()
    assert len(apps) == 2
    domains = [a["official_domain"] for a in apps]
    assert "app-one.org" in domains
    assert "app-two.org" in domains


async def test_domain_challenge_and_dns_txt_verification(
    client: AsyncClient, mock_otp: MockOTPProvider, mock_dns: MockDNSResolver
) -> None:
    """Verify domain challenge generation and authoritative DNS TXT verification."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155554004")

    # 1. Submit application
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "SecureCorp", "official_domain": "securecorp.io"},
    )
    app_id = app_res.json()["id"]

    # 2. Generate challenge
    challenge_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/domain-challenge",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert challenge_res.status_code == 200
    cdata = challenge_res.json()
    record_host = cdata["record_host"]
    expected_value = cdata["expected_record_value"]
    challenge_token = cdata["challenge_token"]
    assert record_host == "_brandshield-challenge.securecorp.io"
    assert "brandshield-verification=" in expected_value

    # 3. Verification attempt before DNS propagation must fail
    fail_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/verify-domain",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": challenge_token},
    )
    assert fail_res.status_code == 400
    assert "DNS verification failed" in fail_res.json()["error"]["message"]

    # 4. Simulate DNS TXT record propagation in Mock DNS
    mock_dns.set_txt_records(record_host, [expected_value])

    # 5. Verify domain with matching DNS record
    verify_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/verify-domain",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": challenge_token},
    )
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["verified"] is True
    assert vdata["application_status"] == "PENDING_REVIEW"
    assert vdata["verified_at"] is not None


async def test_domain_verification_bypass_and_forged_tokens_prevented(
    client: AsyncClient, mock_otp: MockOTPProvider, mock_dns: MockDNSResolver
) -> None:
    """Verify arbitrary client attempts to bypass verification or pass wrong tokens are rejected."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155554005")

    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "Bypass Test", "official_domain": "bypasstest.com"},
    )
    app_id = app_res.json()["id"]

    # Client tries to verify without generating challenge or with bogus token
    forged_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/verify-domain",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": "totally-fake-token-attempting-bypass-00000000"},
    )
    assert forged_res.status_code == 400
    assert "No active domain challenge exists" in forged_res.json()["error"]["message"]


async def test_domain_verification_attempt_exhaustion(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify exceeding maximum DNS verification attempts locks the challenge."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155554006")

    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "Lockout Inc", "official_domain": "lockoutinc.com"},
    )
    app_id = app_res.json()["id"]

    c_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/domain-challenge",
        headers={"Authorization": f"Bearer {token}"},
    )
    challenge_token = c_res.json()["challenge_token"]

    # Exhaust 5 attempts with missing DNS records
    for i in range(5):
        res = await client.post(
            f"/api/v1/brand-applications/{app_id}/verify-domain",
            headers={"Authorization": f"Bearer {token}"},
            json={"token": challenge_token},
        )
        assert res.status_code == 400

    # 6th attempt is locked
    res_locked = await client.post(
        f"/api/v1/brand-applications/{app_id}/verify-domain",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": challenge_token},
    )
    assert res_locked.status_code == 400
    assert "Maximum verification attempts exceeded" in res_locked.json()["error"]["message"]


async def test_domain_challenge_expiration(
    client: AsyncClient, db_session: AsyncSession, mock_otp: MockOTPProvider, mock_dns: MockDNSResolver
) -> None:
    """Verify expired domain challenge is rejected even if DNS matches."""
    _, token = await _create_authenticated_user(client, mock_otp, "+14155554007")

    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"business_name": "Expired Test", "official_domain": "expiredtest.net"},
    )
    app_id = app_res.json()["id"]

    c_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/domain-challenge",
        headers={"Authorization": f"Bearer {token}"},
    )
    challenge_token = c_res.json()["challenge_token"]
    record_host = c_res.json()["record_host"]

    # Set TXT record in DNS
    mock_dns.set_txt_records(record_host, [f"brandshield-verification={challenge_token}"])

    # Force expiration in DB
    past = datetime.now(timezone.utc) - timedelta(hours=25)
    await db_session.execute(
        update(DomainChallenge)
        .where(DomainChallenge.application_id == uuid.UUID(app_id))
        .values(expires_at=past)
    )
    await db_session.commit()

    # Verify attempt rejected due to expiration
    res = await client.post(
        f"/api/v1/brand-applications/{app_id}/verify-domain",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": challenge_token},
    )
    assert res.status_code == 400
    assert "expired" in res.json()["error"]["message"].lower()


async def test_cross_owner_application_access_forbidden(
    client: AsyncClient, mock_otp: MockOTPProvider
) -> None:
    """Verify brand owner A cannot generate challenges or verify brand owner B's application."""
    _, token_a = await _create_authenticated_user(client, mock_otp, "+14155554008")
    _, token_b = await _create_authenticated_user(client, mock_otp, "+14155554009")

    # User A creates application
    app_a = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"business_name": "Owner A Corp", "official_domain": "ownera.com"},
    )
    app_a_id = app_a.json()["id"]

    # User B attempts to generate challenge for A's application -> 403 Forbidden
    res_hack = await client.post(
        f"/api/v1/brand-applications/{app_a_id}/domain-challenge",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_hack.status_code == 403
    assert res_hack.json()["error"]["code"] == "ACCESS_FORBIDDEN"

    # User B attempts to verify A's application -> 403 Forbidden
    verify_hack = await client.post(
        f"/api/v1/brand-applications/{app_a_id}/verify-domain",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"token": "some-token-value-here-00000000"},
    )
    assert verify_hack.status_code == 403


async def test_admin_review_workflow_and_role_upgrade(
    client: AsyncClient, db_session: AsyncSession, mock_otp: MockOTPProvider, mock_dns: MockDNSResolver
) -> None:
    """
    Verify complete review workflow:
    1. User applies and verifies domain (moves to PENDING_REVIEW).
    2. Non-admin cannot review (403).
    3. Admin approves -> Creates verified Brand and upgrades owner role to BRAND_OWNER.
    """
    user_id, token_user = await _create_authenticated_user(client, mock_otp, "+14155554010")

    # 1. Apply and verify domain
    app_res = await client.post(
        "/api/v1/brand-applications",
        headers={"Authorization": f"Bearer {token_user}"},
        json={"business_name": "Globex Corp", "official_domain": "globex.com"},
    )
    app_id = app_res.json()["id"]

    c_res = await client.post(
        f"/api/v1/brand-applications/{app_id}/domain-challenge",
        headers={"Authorization": f"Bearer {token_user}"},
    )
    mock_dns.set_txt_records(c_res.json()["record_host"], [c_res.json()["expected_record_value"]])
    await client.post(
        f"/api/v1/brand-applications/{app_id}/verify-domain",
        headers={"Authorization": f"Bearer {token_user}"},
        json={"token": c_res.json()["challenge_token"]},
    )

    # 2. Non-admin attempts to review -> 403 Forbidden
    review_attempt = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {token_user}"},
        json={"decision": "APPROVE"},
    )
    assert review_attempt.status_code == 403

    # 3. Create ADMIN user
    admin_id, token_admin = await _create_authenticated_user(client, mock_otp, "+14155554011")
    await db_session.execute(
        update(User).where(User.id == uuid.UUID(admin_id)).values(role=UserRole.ADMIN)
    )
    await db_session.commit()

    # 4. Admin approves
    admin_review_res = await client.post(
        f"/api/v1/admin/brand-applications/{app_id}/review",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"decision": "APPROVE", "notes": "Corporate registry documents verified"},
    )
    assert admin_review_res.status_code == 200
    rdata = admin_review_res.json()
    assert rdata["application_status"] == "APPROVED"
    assert rdata["brand_id"] is not None

    # 5. Check owner role was promoted to BRAND_OWNER
    profile_res = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token_user}"})
    assert profile_res.json()["role"] == "BRAND_OWNER"
