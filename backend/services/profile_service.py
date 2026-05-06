"""
User profile service: age and career path (profession).

Used for Duolingo-style "learn a profession" and age-adaptive difficulty/language.
"""

from __future__ import annotations

import logging
from sqlalchemy import select

from backend.db.engine import async_session_factory
from backend.db.models import UserProfileRow

logger = logging.getLogger(__name__)

# Age buckets for prompt adaptation (language and difficulty)
def age_to_bucket(age: int) -> str:
    if age < 12:
        return "child"
    if age < 18:
        return "teen"
    return "adult"


def get_age_instruction(age_bucket: str) -> str:
    """Return instruction for the LLM on how to phrase questions and explanations."""
    if age_bucket == "child":
        return (
            "Use simple, short words. Be warm and encouraging. Avoid jargon. "
            "Explain ideas in a fun way. Keep questions short (one idea at a time)."
        )
    if age_bucket == "teen":
        return (
            "Use clear language. Be friendly but not condescending. "
            "Explain terms when needed. Keep questions focused and concise."
        )
    return (
        "Use professional interview language. Be warm but businesslike. "
        "Standard difficulty and terminology for an adult candidate."
    )


async def get_profile(user_id: str) -> dict | None:
    """Return profile for user_id, or None if not set."""
    async with async_session_factory() as db:
        stmt = select(UserProfileRow).where(UserProfileRow.user_id == user_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
    if not row:
        return None
    return {
        "user_id": row.user_id,
        "age": row.age,
        "profession": row.profession,
        "age_bucket": age_to_bucket(row.age),
        "completed_lessons": row.get_completed_lessons(),
    }


async def upsert_profile(user_id: str, age: int, profession: str) -> dict:
    """Create or update profile. Returns profile dict."""
    if age < 5 or age > 120:
        age = 18
    async with async_session_factory() as db:
        stmt = select(UserProfileRow).where(UserProfileRow.user_id == user_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = UserProfileRow(user_id=user_id, age=age, profession=profession)
            db.add(row)
        else:
            row.age = age
            row.profession = profession
        await db.commit()
        await db.refresh(row)
    return {
        "user_id": row.user_id,
        "age": row.age,
        "profession": row.profession,
        "age_bucket": age_to_bucket(row.age),
        "completed_lessons": row.get_completed_lessons(),
    }


async def record_lesson_complete(
    user_id: str, profession: str, skill_id: str, lesson_id: str
) -> None:
    """Mark a lesson as completed for the user (idempotent)."""
    async with async_session_factory() as db:
        stmt = select(UserProfileRow).where(UserProfileRow.user_id == user_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            row = UserProfileRow(
                user_id=user_id,
                age=18,
                profession=profession,
            )
            db.add(row)
            await db.flush()
        completed = row.get_completed_lessons()
        key = {"profession": profession, "skill_id": skill_id, "lesson_id": lesson_id}
        if key not in completed:
            completed.append(key)
            row.set_completed_lessons(completed)
        await db.commit()
