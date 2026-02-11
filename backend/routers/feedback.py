"""
Feedback report endpoints -- generate comprehensive post-interview reports.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.db.session_store import session_store
from backend.models.schemas import FeedbackReport, SessionStatus
from backend.providers.factory import get_llm_provider
from backend.services.feedback_engine import FeedbackEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate/{session_id}", response_model=FeedbackReport)
async def generate_feedback(session_id: str):
    """
    Generate a comprehensive feedback report for a completed interview session.
    Aggregates content analysis, communication metrics, and body language data.
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

    # Persist report to database
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
