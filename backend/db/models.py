"""
SQLAlchemy ORM models for persistent session and report storage.

These mirror the Pydantic schemas in backend.models.schemas but are designed
for relational storage.  The session_store module handles conversion between
the two representations.
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, LargeBinary, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.engine import Base


def _new_id() -> str:
    return uuid4().hex[:12]


class SessionRow(Base):
    """Persistent record of an interview session."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(24), unique=True, index=True, default=_new_id)

    interview_type: Mapped[str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(256))
    company: Mapped[str] = mapped_column(String(256), default="")
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    num_questions: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(16), default="setup")
    practice_mode: Mapped[str] = mapped_column(String(16), default="")
    topic: Mapped[str] = mapped_column(String(256), default="")

    # Transcript stored as JSON text -- list of {role, text, timestamp, audio_duration_sec}
    transcript_json: Mapped[str] = mapped_column(Text, default="[]")

    # Face data stored as JSON text -- list of FaceSnapshot dicts
    face_data_json: Mapped[str] = mapped_column(Text, default="[]")

    # Tone data stored as JSON text -- list of ToneSnapshot dicts
    tone_data_json: Mapped[str] = mapped_column(Text, default="[]")

    # Raw LLM conversation history -- list of {role, content} dicts
    # Preserves prompt-level structure (tone signals, RAG blocks) for
    # perfect agent reconstruction after server restarts.
    agent_messages_json: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    # --- helpers ---

    def set_transcript(self, entries: list[dict]) -> None:
        self.transcript_json = json.dumps(entries, default=str)

    def get_transcript(self) -> list[dict]:
        return json.loads(self.transcript_json) if self.transcript_json else []

    def set_face_data(self, snapshots: list[dict]) -> None:
        self.face_data_json = json.dumps(snapshots, default=str)

    def get_face_data(self) -> list[dict]:
        return json.loads(self.face_data_json) if self.face_data_json else []

    def set_tone_data(self, snapshots: list[dict]) -> None:
        self.tone_data_json = json.dumps(snapshots, default=str)

    def get_tone_data(self) -> list[dict]:
        return json.loads(self.tone_data_json) if self.tone_data_json else []

    def set_agent_messages(self, messages: list[dict]) -> None:
        self.agent_messages_json = json.dumps(messages, default=str)

    def get_agent_messages(self) -> list[dict]:
        try:
            return json.loads(self.agent_messages_json) if self.agent_messages_json else []
        except (json.JSONDecodeError, AttributeError):
            return []


class ReportRow(Base):
    """Persistent record of a generated feedback report."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(24), index=True)

    overall_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Full report stored as JSON (the entire FeedbackReport dict)
    report_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())

    def set_report(self, report_dict: dict) -> None:
        self.report_json = json.dumps(report_dict, default=str)

    def get_report(self) -> dict:
        return json.loads(self.report_json) if self.report_json else {}


class UserProgressRow(Base):
    """Device-scoped user progress for Duo-style XP, level, and streaks."""

    __tablename__ = "user_progress"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_practice_date: Mapped[str] = mapped_column(String(10), default="")
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    xp_today: Mapped[int] = mapped_column(Integer, default=0)
    sessions_today: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())


class UserProfileRow(Base):
    """User account profile: age and selected career path (Duolingo-style profession)."""

    __tablename__ = "user_profile"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    age: Mapped[int] = mapped_column(Integer, default=18)
    profession: Mapped[str] = mapped_column(String(64), default="data_scientist")
    completed_lessons_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    def get_completed_lessons(self) -> list[dict]:
        try:
            return json.loads(self.completed_lessons_json) if self.completed_lessons_json else []
        except (json.JSONDecodeError, AttributeError):
            return []

    def set_completed_lessons(self, lessons: list[dict]) -> None:
        self.completed_lessons_json = json.dumps(lessons, default=str)


class LearnerRow(Base):
    """A trainer learner. Identified by a client-generated UUID stored in
    localStorage; no password auth in PR 1."""

    __tablename__ = "learners"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())


class FlashcardRow(Base):
    """A single flashcard.

    Curated cards (deck='ml_fundamentals') have learner_id='' so every learner
    sees them. User-generated cards are scoped to a single learner_id.
    """

    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[str] = mapped_column(
        String(64), index=True, default="")
    deck: Mapped[str] = mapped_column(String(64), index=True)
    topic: Mapped[str] = mapped_column(String(128), index=True, default="")
    question: Mapped[str] = mapped_column(Text)
    reference_answer: Mapped[str] = mapped_column(Text)
    source_snippet: Mapped[str] = mapped_column(Text, default="")
    source_chunk_id: Mapped[int | None] = mapped_column(
        Integer, index=True, nullable=True, default=None)
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    is_curated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())


class ReviewRow(Base):
    """One graded attempt at a flashcard. The progress ledger."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(Integer, index=True)
    learner_id: Mapped[str] = mapped_column(String(64), index=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True)
    grade: Mapped[int] = mapped_column(Integer, default=0)
    user_answer: Mapped[str] = mapped_column(Text, default="")
    llm_score: Mapped[float] = mapped_column(Float, default=0.0)
    llm_feedback: Mapped[str] = mapped_column(Text, default="")
    missing_concepts_json: Mapped[str] = mapped_column(Text, default="[]")
    time_spent_ms: Mapped[int] = mapped_column(Integer, default=0)

    def set_missing_concepts(self, concepts: list[str]) -> None:
        self.missing_concepts_json = json.dumps(concepts)

    def get_missing_concepts(self) -> list[str]:
        try:
            return json.loads(self.missing_concepts_json) if self.missing_concepts_json else []
        except (json.JSONDecodeError, AttributeError):
            return []


class ClassRow(Base):
    """An uploaded folder of class materials owned by one learner."""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    class_id: Mapped[str] = mapped_column(
        String(24), unique=True, index=True, default=_new_id)
    learner_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200))
    deck: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    status: Mapped[str] = mapped_column(String(24), default="parsing")
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    card_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())


class ClassChunkRow(Base):
    """One chunk of text extracted from a source file in a class."""

    __tablename__ = "class_chunks"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    class_id: Mapped[str] = mapped_column(String(24), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    page: Mapped[int] = mapped_column(Integer, default=0)
    heading: Mapped[str] = mapped_column(String(256), default="")
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
