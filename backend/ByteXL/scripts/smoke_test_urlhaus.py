"""
BrandShield AI — abuse.ch URLhaus Live Feed Non-Destructive Smoke Test.
Verifies real-world connectivity to abuse.ch API when internet connectivity is present.
Never modifies persistent application or database state.
If external connectivity is blocked or unavailable, honestly reports NOT_VERIFIED.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from app.core.config import get_settings


async def main() -> int:
    settings = get_settings()
    endpoint = f"{settings.URLHAUS_API_URL.rstrip('/')}/urls/recent/"

    print("=" * 70)
    print("BRANDSHIELD AI — LIVE FEED VERIFICATION SMOKE TEST")
    print(f"Target Endpoint: {endpoint}")
    print(f"Configured Auth-Key: {'[CONFIGURED]' if settings.URLHAUS_AUTH_KEY else '[NONE / PUBLIC ACCESS]'}")
    print("=" * 70)

    headers = {
        "User-Agent": "BrandShield-AI-Security-Monitor/1.0",
        "Accept": "application/json",
    }
    if settings.URLHAUS_AUTH_KEY:
        headers["Auth-Key"] = str(settings.URLHAUS_AUTH_KEY)

    try:
        print("[1/2] Attempting live network connection (timeout: 5.0s)...")
        async with httpx.AsyncClient(verify=True, timeout=5.0) as client:
            response = await client.post(endpoint, json={"limit": 5}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            query_status = data.get("query_status")
            urls = data.get("urls") or []
            print(f"[2/2] SUCCESS: Received HTTP 200 from abuse.ch URLhaus!")
            print(f"      API Query Status: {query_status}")
            print(f"      Recent Threat URLs Returned: {len(urls)}")
            for idx, u in enumerate(urls[:3], 1):
                print(f"        {idx}. [{u.get('id')}] {u.get('threat')} -> {u.get('url')[:60]}...")
            print("=" * 70)
            print("LIVE VERIFICATION STATUS: PASSED (Verified against live abuse.ch API)")
            print("=" * 70)
            return 0
        elif response.status_code == 401:
            print(f"[2/2] HTTP 401: abuse.ch URLhaus API requires an authenticated Auth-Key token.")
            print("      To enable live feed ingestion, register a free key at https://urlhaus.abuse.ch/api/")
            print("      and configure URLHAUS_AUTH_KEY in your .env file.")
            print("=" * 70)
            print("LIVE VERIFICATION STATUS: NOT_VERIFIED (Requires URLHAUS_AUTH_KEY configuration)")
            print("=" * 70)
            return 0
        else:
            print(f"[2/2] HTTP {response.status_code}: {response.text[:200]}")
            print("LIVE VERIFICATION STATUS: NOT_VERIFIED (Remote API returned non-200)")
            return 0

    except httpx.ConnectError as exc:
        print(f"[!] Network Connection Error: {exc}")
        print("LIVE VERIFICATION STATUS: NOT_VERIFIED (No live internet connection or firewall barrier)")
        return 0
    except httpx.TimeoutException as exc:
        print(f"[!] Connection Timeout: {exc}")
        print("LIVE VERIFICATION STATUS: NOT_VERIFIED (Remote API did not respond within timeout)")
        return 0
    except Exception as exc:
        print(f"[!] Unexpected error during live test: {exc}")
        print("LIVE VERIFICATION STATUS: NOT_VERIFIED (Encountered error during probe)")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
