"""
Interview session endpoints -- start sessions, send audio responses, receive AI follow-ups.
"""

from __future__ import annotations

import asyncio
import base64
import logging

from cachetools import TTLCache
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.db.session_store import session_store
from backend.models.schemas import (
    FaceDataBatch,
    InterviewSession,
    InterviewSetupRequest,
    RespondResponse,
    SessionStatus,
    TranscriptEntry,
)
from backend.providers.factory import get_llm_provider, get_stt_provider, get_tts_provider
from backend.services.interview_agent import InterviewAgent
from backend.services.tone_analyzer import ToneAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory agent cache with bounded size and TTL eviction.
# maxsize=100 prevents unbounded growth; ttl=3600 (1 hour) evicts stale agents.
_agents: TTLCache[str, InterviewAgent] = TTLCache(maxsize=100, ttl=3600)


async def _get_or_rebuild_agent(session_id: str) -> tuple[InterviewSession, InterviewAgent] | None:
    """Look up agent from cache; on miss, rebuild from the persisted session.

    Returns (session, agent) or None if the session does not exist in the DB either.
    This allows interviews to survive backend restarts: the transcript and tone data
    are persisted in PostgreSQL, so the agent can be reconstructed on demand.
    """
    session = await session_store.get_session(session_id)
    if session is None:
        return None

    agent = _agents.get(session_id)
    if agent is not None:
        return session, agent

    # Cache miss -- rebuild agent from DB-persisted session
    llm = get_llm_provider()
    agent = InterviewAgent.from_persisted_session(llm=llm, session=session)
    _agents[session_id] = agent
    logger.info("Rebuilt agent for session %s after cache miss", session_id)
    return session, agent


@router.post("/start", response_model=InterviewSession)
async def start_interview(req: InterviewSetupRequest):
    """Create a new interview session and return the first question as audio."""
    session = InterviewSession(
        interview_type=req.interview_type,
        role=req.role,
        company=req.company,
        difficulty=req.difficulty,
        num_questions=req.num_questions,
        status=SessionStatus.in_progress,
    )

    llm = get_llm_provider()
    agent = InterviewAgent(llm=llm, session=session)
    _agents[session.session_id] = agent

    # Generate the opening question (timeout prevents infinite frontend hang)
    try:
        opening = await asyncio.wait_for(agent.generate_opening(), timeout=60.0)
    except asyncio.TimeoutError:
        logger.error("Opening question generation timed out after 60s")
        raise HTTPException(
            status_code=504,
            detail="Interview generation timed out. Please try again.",
        )
    tts = get_tts_provider()
    audio_bytes = await tts.synthesize(opening)
    audio_b64 = base64.b64encode(audio_bytes).decode()

    session.transcript.append(
        TranscriptEntry(role="interviewer", text=opening)
    )

    # Persist to database
    await session_store.save_session(session)

    return session


@router.get("/session/{session_id}", response_model=InterviewSession)
async def get_session(session_id: str):
    """Retrieve current session state."""
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/respond/{session_id}", response_model=RespondResponse)
async def respond(
    session_id: str,
    audio: UploadFile = File(...),
):
    """
    Process a candidate audio response:
    1. Transcribe audio (STT provider)
    2. Analyze tone (librosa)
    3. Generate interviewer follow-up (LLM provider)
    4. Synthesize follow-up audio (TTS provider)
    """
    result = await _get_or_rebuild_agent(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session, agent = result

    if session.status == SessionStatus.completed:
        raise HTTPException(status_code=400, detail="Interview already completed")

    audio_bytes = await audio.read()

    # STT -- transcribe candidate response (30s timeout)
    stt = get_stt_provider()
    try:
        candidate_text = await asyncio.wait_for(
            stt.transcribe(audio_bytes), timeout=30.0
        )
    except asyncio.TimeoutError:
        logger.error("STT timed out after 30s for session %s", session_id)
        raise HTTPException(
            status_code=504,
            detail="Speech transcription timed out. Please try again.",
        )
    logger.info("STT result: %s", candidate_text[:120])

    # Tone analysis
    tone_analyzer = ToneAnalyzer()
    tone_snapshot = tone_analyzer.analyze(audio_bytes)
    session.tone_data.append(tone_snapshot)

    # Record candidate turn
    session.transcript.append(
        TranscriptEntry(
            role="candidate",
            text=candidate_text,
            audio_duration_sec=tone_snapshot.duration_sec,
        )
    )

    # Determine if this is the last question
    question_count = sum(1 for t in session.transcript if t.role == "interviewer")
    is_final = question_count >= session.num_questions

    # LLM -- generate follow-up or closing (45s timeout)
    try:
        if is_final:
            interviewer_text = await asyncio.wait_for(
                agent.generate_closing(), timeout=45.0
            )
            session.status = SessionStatus.completed
        else:
            interviewer_text = await asyncio.wait_for(
                agent.generate_followup(
                    candidate_response=candidate_text,
                    tone_snapshot=tone_snapshot,
                ),
                timeout=45.0,
            )
    except asyncio.TimeoutError:
        logger.error("LLM timed out after 45s for session %s", session_id)
        raise HTTPException(
            status_code=504,
            detail="Response generation timed out. Please try again.",
        )

    # Record interviewer turn
    session.transcript.append(
        TranscriptEntry(role="interviewer", text=interviewer_text)
    )

    # TTS -- synthesize interviewer response (30s timeout)
    tts = get_tts_provider()
    try:
        audio_response = await asyncio.wait_for(
            tts.synthesize(interviewer_text), timeout=30.0
        )
    except asyncio.TimeoutError:
        logger.error("TTS timed out after 30s for session %s", session_id)
        raise HTTPException(
            status_code=504,
            detail="Audio synthesis timed out. Please try again.",
        )
    audio_b64 = base64.b64encode(audio_response).decode()

    # Persist updated session
    await session_store.update_session(session)

    # Evict the agent from cache once the interview is done
    if is_final:
        _agents.pop(session_id, None)

    return RespondResponse(
        session_id=session_id,
        transcript_text=candidate_text,
        interviewer_text=interviewer_text,
        interviewer_audio_url=f"data:audio/mp3;base64,{audio_b64}",
        question_number=question_count,
        is_final=is_final,
        tone_snapshot=tone_snapshot,
    )


@router.post("/face-data/{session_id}")
async def submit_face_data(session_id: str, batch: FaceDataBatch):
    """Receive batched facial expression data from the frontend."""
    session = await session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.face_data.extend(batch.snapshots)
    await session_store.update_session(session)
    return {"received": len(batch.snapshots), "total": len(session.face_data)}


@router.get("/opening-audio/{session_id}")
async def get_opening_audio(session_id: str):
    """Get the TTS audio for the first interviewer question."""
    result = await _get_or_rebuild_agent(session_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session, _agent = result

    opening_text = ""
    for entry in session.transcript:
        if entry.role == "interviewer":
            opening_text = entry.text
            break

    if not opening_text:
        raise HTTPException(status_code=400, detail="No opening question found")

    tts = get_tts_provider()
    audio_bytes = await tts.synthesize(opening_text)
    audio_b64 = base64.b64encode(audio_bytes).decode()

    return {
        "text": opening_text,
        "audio": f"data:audio/mp3;base64,{audio_b64}",
    }
