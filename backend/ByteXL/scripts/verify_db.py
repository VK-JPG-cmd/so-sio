"""Database connectivity verification utility for BrandShield AI."""

import asyncio
import sys
from app.core.config import get_settings
from app.db.session import check_db_health


async def main() -> None:
    settings = get_settings()
    print(f"Testing connection to: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    ok, err = await check_db_health(timeout_seconds=5.0)
    if ok:
        print("[SUCCESS] PostgreSQL database is reachable and accepting queries.")
        sys.exit(0)
    else:
        print(f"[FAILURE] PostgreSQL connection failed: {err}")
        print("\nTroubleshooting tips:")
        print("1. Ensure PostgreSQL is running (e.g. docker compose up -d db or local service)")
        print("2. Check host, port, user, and password in your .env file")
        print("3. Verify the target database exists")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
