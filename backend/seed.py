"""Seed script — creates test user and sample completed jobs.

Usage:
    cd backend
    python seed.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import async_session, init_db
from app.models.user import User
from app.models.job import Job


async def seed():
    await init_db()

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == "admin@gyansetu.ai"))
        existing = result.scalar_one_or_none()
        if existing:
            existing.password_hash = hash_password("12345678")
            await db.commit()
            print(f"Updated password for {existing.email}")
            return

        admin = User(
            id=str(uuid.uuid4()),
            name="Admin",
            email="admin@gyansetu.ai",
            password_hash=hash_password("12345678"),
            role="admin",
        )
        db.add(admin)
        await db.flush()

        for i, (name, status, stages) in enumerate([
            ("physics_kinematics.pdf", "completed", 10),
            ("history_ancient.pdf", "completed", 10),
            ("biology_cells.pdf", "failed", 4),
        ]):
            job = Job(
                id=str(uuid.uuid4()),
                user_id=admin.id,
                status=status,
                current_stage=stages,
                file_name=name,
                file_path=f"uploads/{admin.id}/{name}",
                config={"grade_level": "high", "subject": name.split("_")[0]},
                tkp_path=f"outputs/tkp_{name.replace('.pdf', '.json')}" if status == "completed" else None,
                error_message="Stage 5: Knowledge Extractor timed out" if status == "failed" else None,
                created_at=datetime.now(timezone.utc) - timedelta(hours=i * 2),
                completed_at=datetime.now(timezone.utc) - timedelta(hours=i * 2 - 1) if status == "completed" else None,
            )
            db.add(job)

        await db.commit()
        print(f"Seeded admin user + {3} sample jobs")


if __name__ == "__main__":
    asyncio.run(seed())
