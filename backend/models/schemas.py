"""
Pydantic models for request/response schemas across the application.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class InterviewType(str, Enum):
    behavioral = "behavioral"
    technical = "technical"
    case_study = "case_study"


class SessionStatus(str, Enum):
    setup = "setup"
    in_progress = "in_progress"
    completed = "completed"


class Emotion(str, Enum):
    neutral = "neutral"
    happy = "happy"
    confident = "confident"
    nervous = "nervous"
    confused = "confused"
    surprised = "surprised"
    focused = "focused"


# ---------------------------------------------------------------------------
# Interview Setup
# ---------------------------------------------------------------------------

class InterviewSetupRequest(BaseModel):
    """Request to start a new interview session."""
    interview_type: InterviewType = InterviewType.behavioral
    role: str = Field(default="Software Engineer",
                      description="Target job role")
    company: str = Field(default="", description="Target company (optional)")
    difficulty: str = Field(default="medium", description="easy, medium, hard")
    num_questions: int = Field(default=5, ge=1, le=15)
    practice_mode: Optional[str] = Field(
        default=None, description="quick (2-3 questions) or full"
    )
    topic: Optional[str] = Field(
        default=None, description="Single topic for quick practice (e.g. Conflict Resolution)"
    )


class InterviewSession(BaseModel):
    """Represents an active interview session."""
    session_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    interview_type: InterviewType
    role: str
    company: str
    difficulty: str
    num_questions: int
    status: SessionStatus = SessionStatus.setup
    practice_mode: Optional[str] = Field(default=None, description="quick or full")
    topic: Optional[str] = Field(default=None, description="Single topic for quick practice")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    transcript: list[TranscriptEntry] = Field(default_factory=list)
    face_data: list[FaceSnapshot] = Field(default_factory=list)
    tone_data: list[ToneSnapshot] = Field(default_factory=list)
    # Raw LLM conversation history (prompt-level messages including tone signals
    # and RAG blocks). Excluded from API responses but persisted to DB so the
    # agent can be perfectly reconstructed after a server restart.
    agent_messages: list[dict[str, str]] = Field(
        default_factory=list, exclude=True)


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

class TranscriptEntry(BaseModel):
    """A single turn in the interview conversation."""
    role: str = Field(description="interviewer or candidate")
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audio_duration_sec: Optional[float] = None


class RespondRequest(BaseModel):
    """Request body when the candidate sends an audio response."""
    session_id: str


class RespondResponse(BaseModel):
    """Response returned after processing a candidate turn."""
    session_id: str
    transcript_text: str = Field(
        description="What the candidate said (STT output)")
    interviewer_text: str = Field(description="The interviewer follow-up text")
    interviewer_audio_url: str = Field(
        default="", description="URL or base64 of TTS audio")
    question_number: int
    is_final: bool = Field(
        default=False, description="True if interview is complete")
    tone_snapshot: Optional[ToneSnapshot] = None


# ---------------------------------------------------------------------------
# Facial Expression Data
# ---------------------------------------------------------------------------

class FaceSnapshot(BaseModel):
    """Aggregated facial expression data from a time window."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dominant_emotion: Emotion = Emotion.neutral
    emotion_scores: dict[str, float] = Field(default_factory=dict)
    eye_contact: bool = True
    head_pitch: float = 0.0
    head_yaw: float = 0.0


class FaceDataBatch(BaseModel):
    """Batch of facial snapshots sent from the frontend."""
    session_id: str
    snapshots: list[FaceSnapshot]


# ---------------------------------------------------------------------------
# Tone / Audio Analysis
# ---------------------------------------------------------------------------

class ToneSnapshot(BaseModel):
    """Audio analysis results for a single candidate turn."""
    speaking_pace_wpm: float = Field(
        default=0.0, description="Words per minute")
    filler_word_count: int = Field(default=0)
    filler_words: list[str] = Field(default_factory=list)
    avg_pitch_hz: float = Field(default=0.0)
    pitch_variation: float = Field(default=0.0)
    pitch_range_hz: float = Field(
        default=0.0, description="Max minus min pitch in Hz")
    rising_intonation_ratio: float = Field(
        default=0.0,
        description="Fraction of speech segments ending with rising pitch")
    monotone_flag: bool = Field(
        default=False,
        description="True when pitch variation is very low relative to mean")
    jitter: float = Field(
        default=0.0,
        description="Cycle-to-cycle pitch variation (vocal stability)")
    shimmer: float = Field(
        default=0.0,
        description="Cycle-to-cycle amplitude variation (vocal stability)")
    energy_level: float = Field(default=0.0, description="Normalized 0-1")
    silence_ratio: float = Field(
        default=0.0, description="Fraction of audio that is silence")
    duration_sec: float = Field(default=0.0)


# ---------------------------------------------------------------------------
# Feedback Report
# ---------------------------------------------------------------------------

class ContentScore(BaseModel):
    """Evaluation of the candidate's response content."""
    overall_score: float = Field(ge=0, le=10)
    relevance: float = Field(ge=0, le=10)
    specificity: float = Field(ge=0, le=10)
    structure: float = Field(ge=0, le=10)
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    example_responses: list[str] = Field(default_factory=list)


class CommunicationScore(BaseModel):
    """Evaluation of the candidate's verbal communication."""
    overall_score: float = Field(ge=0, le=10)
    pace_score: float = Field(ge=0, le=10)
    clarity_score: float = Field(ge=0, le=10)
    filler_score: float = Field(ge=0, le=10)
    confidence_score: float = Field(ge=0, le=10)
    avg_wpm: float = 0.0
    total_fillers: int = 0
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class BodyLanguageScore(BaseModel):
    """Evaluation of the candidate's body language from facial data."""
    overall_score: float = Field(ge=0, le=10)
    eye_contact_pct: float = Field(ge=0, le=100)
    emotion_distribution: dict[str, float] = Field(default_factory=dict)
    fidgeting_score: float = Field(ge=0, le=10, description="Lower is better")
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class FeedbackReport(BaseModel):
    """Comprehensive post-interview feedback report."""
    session_id: str
    interview_type: InterviewType
    role: str
    company: str
    overall_score: float = Field(ge=0, le=10)
    content: ContentScore
    communication: CommunicationScore
    body_language: BodyLanguageScore
    top_strengths: list[str] = Field(default_factory=list)
    top_improvements: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    # Duo-style progress (set when X-User-Id header is sent)
    xp_earned: Optional[int] = None
    total_xp: Optional[int] = None
    level: Optional[int] = None
    streak_days: Optional[int] = None
    xp_today: Optional[int] = None
    sessions_today: Optional[int] = None
    # Practice weak skills: recommend next topic for quick practice
    recommended_topic: Optional[str] = None
    recommended_interview_type: Optional[str] = None


# ---------------------------------------------------------------------------
# Forward reference resolution
# ---------------------------------------------------------------------------

InterviewSession.model_rebuild()
