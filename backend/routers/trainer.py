"""
Trainer (flashcard) endpoints. Identity is a client-generated UUID sent as the
'learner_id' query or body param -- no password auth in PR 1.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.engine import get_db
from backend.db.models import FlashcardRow, ReviewRow
from backend.providers.factory import get_llm_provider
from backend.services import trainer_engine

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LearnerRegisterRequest(BaseModel):
    learner_id: str = Field(min_length=8, max_length=64)
    display_name: str = ""


class LearnerOut(BaseModel):
    learner_id: str
    display_name: str


class FlashcardOut(BaseModel):
    id: int
    deck: str
    topic: str
    question: str
    reference_answer: str
    difficulty: str


class NextCardOut(BaseModel):
    card: FlashcardOut | None
    remaining_new: int
    remaining_review: int


class AnswerRequest(BaseModel):
    learner_id: str
    user_answer: str
    time_spent_ms: int = 0


class AnswerResponse(BaseModel):
    card_id: int
    score: int
    grade: int
    feedback: str
    missing_concepts: list[str]
    reference_answer: str


class ProgressOut(BaseModel):
    total_reviews: int
    accuracy: float
    streak_days: int
    mastered: int
    learning: int
    struggling: int
    new: int
    total_cards: int
    recent_reviews: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/learner", response_model=LearnerOut)
async def register_learner(
    req: LearnerRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Idempotent: get-or-create a learner by the client-provided UUID."""
    row = await trainer_engine.get_or_create_learner(
        db, req.learner_id, req.display_name
    )
    return LearnerOut(
        learner_id=row.learner_id, display_name=row.display_name or ""
    )


@router.get("/decks/{deck}/next", response_model=NextCardOut)
async def next_card(
    deck: str,
    learner_id: str = Query(..., min_length=8),
    db: AsyncSession = Depends(get_db),
):
    """Return the next card the learner should study, using weakest-first."""
    await trainer_engine.get_or_create_learner(db, learner_id)
    card = await trainer_engine.pick_next_card(db, learner_id, deck=deck)

    cards = await trainer_engine.list_cards_for_learner(db, learner_id, deck)
    stats = await trainer_engine.recent_grade_by_card(db, learner_id)
    remaining_new = sum(1 for c in cards if c.id not in stats)
    remaining_review = sum(
        1 for c in cards if c.id in stats and stats[c.id][0] < 4)

    if card is None:
        return NextCardOut(
            card=None, remaining_new=0, remaining_review=remaining_review
        )

    return NextCardOut(
        card=FlashcardOut(
            id=card.id,
            deck=card.deck,
            topic=card.topic,
            question=card.question,
            reference_answer=card.reference_answer,
            difficulty=card.difficulty,
        ),
        remaining_new=remaining_new,
        remaining_review=remaining_review,
    )


@router.get("/decks/{deck}/cards", response_model=list[FlashcardOut])
async def list_cards(
    deck: str,
    learner_id: str = Query(..., min_length=8),
    db: AsyncSession = Depends(get_db),
):
    cards = await trainer_engine.list_cards_for_learner(db, learner_id, deck)
    return [
        FlashcardOut(
            id=c.id,
            deck=c.deck,
            topic=c.topic,
            question=c.question,
            reference_answer=c.reference_answer,
            difficulty=c.difficulty,
        )
        for c in cards
    ]


@router.post("/cards/{card_id}/answer", response_model=AnswerResponse)
async def submit_answer(
    card_id: int,
    req: AnswerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Grade an answer with the LLM and append to the review ledger."""
    card = await db.scalar(select(FlashcardRow).where(FlashcardRow.id == card_id))
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.learner_id not in ("", req.learner_id):
        raise HTTPException(
            status_code=403, detail="Card belongs to another learner")

    await trainer_engine.get_or_create_learner(db, req.learner_id)

    llm = get_llm_provider()
    result = await trainer_engine.grade_answer(llm, card, req.user_answer)

    review = ReviewRow(
        card_id=card.id,
        learner_id=req.learner_id,
        grade=int(result["score"]),
        user_answer=req.user_answer.strip(),
        llm_score=float(result["score"]),
        llm_feedback=result["feedback"],
        time_spent_ms=max(0, int(req.time_spent_ms)),
    )
    review.set_missing_concepts(result["missing_concepts"])
    db.add(review)
    await db.commit()

    return AnswerResponse(
        card_id=card.id,
        score=int(result["score"]),
        grade=int(result["score"]),
        feedback=result["feedback"],
        missing_concepts=result["missing_concepts"],
        reference_answer=card.reference_answer,
    )


@router.get("/progress", response_model=ProgressOut)
async def get_progress(
    learner_id: str = Query(..., min_length=8),
    db: AsyncSession = Depends(get_db),
):
    await trainer_engine.get_or_create_learner(db, learner_id)
    return await trainer_engine.progress_summary(db, learner_id)
