"""
Duo-style progress: XP, level, and streaks.

Device-scoped identity (user_id from frontend) is used to persist
progress without full auth. Called when a feedback report is generated.
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from sqlalchemy import select

from backend.db.engine import async_session_factory
from backend.db.models import UserProgressRow
from backend.models.schemas import FeedbackReport, InterviewSession

logger = logging.getLogger(__name__)

# XP formula: base + per-question + score bonus
XP_BASE = 20
XP_PER_QUESTION = 10
XP_SCORE_MULTIPLIER = 3  # overall_score (0-10) * this

# Level from total_xp: level 1 = 0-99, level 2 = 100-249, level 3 = 250-499, ...
def level_from_xp(total_xp: int) -> int:
    if total_xp < 100:
        return 1
    if total_xp < 250:
        return 2
    if total_xp < 500:
        return 3
    if total_xp < 1000:
        return 4
    return 5 + (total_xp - 1000) // 500


def compute_xp(session: InterviewSession, report: FeedbackReport) -> int:
    """Compute XP earned for this session."""
    num_q = session.num_questions
    score_bonus = int(report.overall_score * XP_SCORE_MULTIPLIER)
    return XP_BASE + (XP_PER_QUESTION * num_q) + score_bonus


async def update_progress(
    user_id: str,
    session: InterviewSession,
    report: FeedbackReport,
) -> dict:
    """
    Update user progress after a completed session and return progress snapshot.

    Updates streak (consecutive days), total_xp, xp_today (resets when day changes),
    and level. Returns dict with xp_earned, total_xp, level, streak_days, xp_today.
    """
    today = date.today().isoformat()
    xp_earned = compute_xp(session, report)

    async with async_session_factory() as db:
        stmt = select(UserProgressRow).where(UserProgressRow.user_id == user_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            row = UserProgressRow(
                user_id=user_id,
                last_practice_date=today,
                streak_days=1,
                total_xp=xp_earned,
                xp_today=xp_earned,
                sessions_today=1,
            )
            db.add(row)
        else:
            last = row.last_practice_date or ""
            if last != today:
                # New day: update streak and reset daily counters
                try:
                    last_date = date.fromisoformat(last)
                    days_diff = (date.today() - last_date).days
                    if days_diff == 1:
                        row.streak_days = (row.streak_days or 0) + 1
                    else:
                        row.streak_days = 1
                except (ValueError, TypeError):
                    row.streak_days = 1
                row.last_practice_date = today
                row.xp_today = xp_earned
                row.sessions_today = 1
            else:
                row.xp_today = (row.xp_today or 0) + xp_earned
                row.sessions_today = (row.sessions_today or 0) + 1

            row.total_xp = (row.total_xp or 0) + xp_earned

        await db.commit()
        await db.refresh(row)

    total_xp = row.total_xp or 0
    return {
        "xp_earned": xp_earned,
        "total_xp": total_xp,
        "level": level_from_xp(total_xp),
        "streak_days": row.streak_days or 0,
        "xp_today": row.xp_today or 0,
        "sessions_today": row.sessions_today or 0,
    }


async def get_progress(user_id: str) -> dict | None:
    """Return current progress for user_id, or None if never practiced."""
    async with async_session_factory() as db:
        stmt = select(UserProgressRow).where(UserProgressRow.user_id == user_id)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
    if not row:
        return None
    return {
        "total_xp": row.total_xp or 0,
        "level": level_from_xp(row.total_xp or 0),
        "streak_days": row.streak_days or 0,
        "xp_today": row.xp_today or 0,
        "sessions_today": row.sessions_today or 0,
        "last_practice_date": row.last_practice_date or "",
    }
