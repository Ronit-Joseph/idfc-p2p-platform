"""Create a superuser account interactively.

Usage: python scripts/create_superuser.py
"""
import asyncio
import sys
from pathlib import Path

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database import engine, async_session
from backend.base_model import Base
from backend.modules.auth.models import User
from backend.modules.auth.service import hash_password


async def main():
    # Create tables if needed
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    email = input("Email: ").strip()
    full_name = input("Full name: ").strip()
    password = input("Password: ").strip()

    async with async_session() as session:
        from sqlalchemy import select
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalars().first():
            print(f"User {email} already exists.")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role="ADMIN",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Superuser {email} created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
