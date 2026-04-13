#!/usr/bin/env python3
"""
reset_db.py — drop and recreate all tables in the local dev database.

Use this after adding new columns to SQLAlchemy models.
WARNING: deletes all data. Dev use only.

Usage:
    cd backend && python ../scripts/reset_db.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.database import engine, Base
# Import all models so they register with Base.metadata
import app.models.user         # noqa: F401
import app.models.mission      # noqa: F401
import app.models.job          # noqa: F401
import app.models.eval_report  # noqa: F401
import app.models.api_key      # noqa: F401


async def reset() -> None:
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Recreating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("Done. Database reset complete.")


if __name__ == "__main__":
    confirm = input("This will DELETE all data. Type 'yes' to continue: ")
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        sys.exit(0)
    asyncio.run(reset())
