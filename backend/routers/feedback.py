"""
Feedback report endpoints -- generate comprehensive post-interview reports.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException

from backend.db.session_store import session_store
from backend.models.schemas import FeedbackReport, SessionStatus
from backend.providers.factory import get_llm_provider
from backend.services.feedback_engine import FeedbackEngine
from backend.services.progress_service import update_progress

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate/{session_id}", response_model=FeedbackReport)
async def generate_feedback(
    session_id: str,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """
    Generate a comprehensive feedback report for a completed interview session.
    Aggregates content analysis, communication metrics, and body language data.
    When X-User-Id header is sent, updates Duo-style progress and attaches
    xp_earned, total_xp, level, streak_days, xp_today to the response.
    """
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.completed:
        raise HTTPException(
            status_code=400,
            detail="Interview must be completed before generating feedback",
        )

    llm = get_llm_provider()
    engine = FeedbackEngine(llm=llm)
    report = await engine.generate_report(session)

    if x_user_id and x_user_id.strip():
        try:
            progress = await update_progress(x_user_id.strip(), session, report)
            report.xp_earned = progress["xp_earned"]
            report.total_xp = progress["total_xp"]
            report.level = progress["level"]
            report.streak_days = progress["streak_days"]
            report.xp_today = progress["xp_today"]
            report.sessions_today = progress.get("sessions_today")
        except Exception:
            logger.exception("Progress update failed for user_id=%s", x_user_id[:8])

    await session_store.save_report(report)

    logger.info(
        "Generated feedback for session %s: overall_score=%.1f",
        session_id,
        report.overall_score,
    )
    return report


@router.get("/report/{session_id}", response_model=FeedbackReport)
async def get_feedback(session_id: str):
    """
    Retrieve a previously generated feedback report.
    Returns cached report if available, otherwise generates a new one.
    """
    existing = await session_store.get_report(session_id)
    if existing:
        return existing
    return await generate_feedback(session_id)


@router.get("/progress")
async def get_progress_endpoint(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    """
    Return Duo-style progress for the given user_id (X-User-Id header).
    Returns 200 with { total_xp, level, streak_days, xp_today, last_practice_date }
    or 200 with { total_xp: 0, level: 1, streak_days: 0, xp_today: 0 } when new user.
    """
    from backend.services.progress_service import get_progress as get_progress_svc

    if not x_user_id or not x_user_id.strip():
        return {
            "total_xp": 0,
            "level": 1,
            "streak_days": 0,
            "xp_today": 0,
            "last_practice_date": "",
        }
    progress = await get_progress_svc(x_user_id.strip())
    if not progress:
        return {
            "total_xp": 0,
            "level": 1,
            "streak_days": 0,
            "xp_today": 0,
            "last_practice_date": "",
        }
    return progress
