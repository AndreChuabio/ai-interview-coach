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

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.engine import Base


def _new_id() -> str:
    return uuid4().hex[:12]


class SessionRow(Base):
    """Persistent record of an interview session."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(24), unique=True, index=True, default=_new_id)

    interview_type: Mapped[str] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(256))
    company: Mapped[str] = mapped_column(String(256), default="")
    difficulty: Mapped[str] = mapped_column(String(16), default="medium")
    num_questions: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(16), default="setup")

    # Transcript stored as JSON text -- list of {role, text, timestamp, audio_duration_sec}
    transcript_json: Mapped[str] = mapped_column(Text, default="[]")

    # Face data stored as JSON text -- list of FaceSnapshot dicts
    face_data_json: Mapped[str] = mapped_column(Text, default="[]")

    # Tone data stored as JSON text -- list of ToneSnapshot dicts
    tone_data_json: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

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


class ReportRow(Base):
    """Persistent record of a generated feedback report."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(24), index=True)

    overall_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Full report stored as JSON (the entire FeedbackReport dict)
    report_json: Mapped[str] = mapped_column(Text, default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def set_report(self, report_dict: dict) -> None:
        self.report_json = json.dumps(report_dict, default=str)

    def get_report(self) -> dict:
        return json.loads(self.report_json) if self.report_json else {}
