"""
Session store abstraction.

Provides a single API to create, read, and update interview sessions and
feedback reports.  Writes go to both the in-memory cache (for fast access
during the live interview) and the SQL database (for persistence).

Usage from routers:
    from backend.db.session_store import session_store
    await session_store.save_session(session)
    session = await session_store.get_session(session_id)
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select

from backend.db.engine import async_session_factory
from backend.db.models import ReportRow, SessionRow
from backend.models.schemas import (
    FeedbackReport,
    InterviewSession,
    InterviewType,
    SessionStatus,
    TranscriptEntry,
    FaceSnapshot,
    ToneSnapshot,
)

logger = logging.getLogger(__name__)


class SessionStore:
    """Dual-write store: in-memory dict + async SQL database."""

    def __init__(self) -> None:
        self._cache: dict[str, InterviewSession] = {}

    # ------------------------------------------------------------------
    # Session CRUD
    # ------------------------------------------------------------------

    async def save_session(self, session: InterviewSession) -> None:
        """Persist a session to both cache and database."""
        self._cache[session.session_id] = session
        try:
            await self._upsert_session_row(session)
        except Exception:
            logger.exception("Failed to persist session %s to DB", session.session_id)

    async def get_session(self, session_id: str) -> InterviewSession | None:
        """Retrieve a session, preferring cache, falling back to DB."""
        if session_id in self._cache:
            return self._cache[session_id]
        return await self._load_session_from_db(session_id)

    async def update_session(self, session: InterviewSession) -> None:
        """Alias for save_session -- overwrites existing."""
        await self.save_session(session)

    # ------------------------------------------------------------------
    # Report CRUD
    # ------------------------------------------------------------------

    async def save_report(self, report: FeedbackReport) -> None:
        """Persist a feedback report to the database."""
        try:
            async with async_session_factory() as db:
                row = ReportRow(
                    session_id=report.session_id,
                    overall_score=report.overall_score,
                )
                row.set_report(report.model_dump(mode="json"))
                db.add(row)
                await db.commit()
                logger.info("Saved report for session %s (score=%.1f)", report.session_id, report.overall_score)
        except Exception:
            logger.exception("Failed to persist report for session %s", report.session_id)

    async def get_report(self, session_id: str) -> FeedbackReport | None:
        """Load the most recent report for a session from the database."""
        try:
            async with async_session_factory() as db:
                stmt = (
                    select(ReportRow)
                    .where(ReportRow.session_id == session_id)
                    .order_by(ReportRow.created_at.desc())
                    .limit(1)
                )
                result = await db.execute(stmt)
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                return FeedbackReport(**row.get_report())
        except Exception:
            logger.exception("Failed to load report for session %s", session_id)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _upsert_session_row(self, session: InterviewSession) -> None:
        """Insert or update the session row in the database."""
        async with async_session_factory() as db:
            stmt = select(SessionRow).where(SessionRow.session_id == session.session_id)
            result = await db.execute(stmt)
            row = result.scalar_one_or_none()

            if row is None:
                row = SessionRow(session_id=session.session_id)
                db.add(row)

            row.interview_type = session.interview_type.value
            row.role = session.role
            row.company = session.company
            row.difficulty = session.difficulty
            row.num_questions = session.num_questions
            row.status = session.status.value

            row.set_transcript([e.model_dump(mode="json") for e in session.transcript])
            row.set_face_data([s.model_dump(mode="json") for s in session.face_data])
            row.set_tone_data([s.model_dump(mode="json") for s in session.tone_data])

            await db.commit()

    async def _load_session_from_db(self, session_id: str) -> InterviewSession | None:
        """Load a session from the database into an InterviewSession Pydantic model."""
        try:
            async with async_session_factory() as db:
                stmt = select(SessionRow).where(SessionRow.session_id == session_id)
                result = await db.execute(stmt)
                row = result.scalar_one_or_none()
                if row is None:
                    return None

                session = InterviewSession(
                    session_id=row.session_id,
                    interview_type=InterviewType(row.interview_type),
                    role=row.role,
                    company=row.company,
                    difficulty=row.difficulty,
                    num_questions=row.num_questions,
                    status=SessionStatus(row.status),
                    created_at=row.created_at or datetime.utcnow(),
                    transcript=[TranscriptEntry(**e) for e in row.get_transcript()],
                    face_data=[FaceSnapshot(**s) for s in row.get_face_data()],
                    tone_data=[ToneSnapshot(**s) for s in row.get_tone_data()],
                )
                self._cache[session_id] = session
                return session
        except Exception:
            logger.exception("Failed to load session %s from DB", session_id)
            return None


# Singleton instance used across the app
session_store = SessionStore()
