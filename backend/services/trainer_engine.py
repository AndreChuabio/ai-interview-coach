"""
Flashcard trainer engine: seeds the curated ML deck, grades short-answer
responses via the LLM provider, and selects the next card using a simple
weakest-first heuristic (SM-2 scheduling is a later PR).

The "progress ledger" is the reviews table; all per-learner stats are derived
from it.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.engine import async_session_factory
from backend.db.models import FlashcardRow, LearnerRow, ReviewRow
from backend.prompts.trainer import GRADE_SYSTEM_PROMPT, GRADE_USER_TEMPLATE
from backend.providers.base import LLMProvider

logger = logging.getLogger(__name__)

CURATED_DECK = "ml_fundamentals"
_SEED_PATH = Path(__file__).resolve().parent.parent / \
    "data" / "ml_concepts.json"


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

async def seed_curated_deck_if_empty() -> int:
    """Load the curated ML deck from JSON into the DB if it isn't there yet.

    Returns the number of cards inserted. Safe to call on every startup.
    """
    async with async_session_factory() as db:
        existing = await db.scalar(
            select(func.count(FlashcardRow.id)).where(
                FlashcardRow.deck == CURATED_DECK,
                FlashcardRow.is_curated.is_(True),
            )
        )
        if existing and existing > 0:
            return 0

        try:
            raw = json.loads(_SEED_PATH.read_text())
        except FileNotFoundError:
            logger.warning("Curated ML seed file not found at %s", _SEED_PATH)
            return 0

        for card in raw:
            db.add(FlashcardRow(
                learner_id="",
                deck=CURATED_DECK,
                topic=card.get("topic", ""),
                question=card["question"],
                reference_answer=card["reference_answer"],
                difficulty=card.get("difficulty", "medium"),
                is_curated=True,
            ))
        await db.commit()
        logger.info(
            "Seeded %d curated ML flashcards into deck=%s", len(raw), CURATED_DECK)
        return len(raw)


# ---------------------------------------------------------------------------
# Learner lookup
# ---------------------------------------------------------------------------

async def get_or_create_learner(
    db: AsyncSession, learner_id: str, display_name: str = ""
) -> LearnerRow:
    row = await db.scalar(
        select(LearnerRow).where(LearnerRow.learner_id == learner_id)
    )
    if row is not None:
        if display_name and not row.display_name:
            row.display_name = display_name
            await db.commit()
        return row

    row = LearnerRow(learner_id=learner_id, display_name=display_name)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


# ---------------------------------------------------------------------------
# Card selection (weakest-first)
# ---------------------------------------------------------------------------

async def list_cards_for_learner(
    db: AsyncSession, learner_id: str, deck: str = CURATED_DECK
) -> list[FlashcardRow]:
    """All cards visible to this learner in the given deck.

    Curated cards (learner_id='') are visible to everyone; user-generated
    cards are filtered to the learner themselves.
    """
    stmt = select(FlashcardRow).where(
        FlashcardRow.deck == deck,
        FlashcardRow.learner_id.in_(["", learner_id]),
    )
    result = await db.execute(stmt)
    return list(result.scalars())


async def recent_grade_by_card(
    db: AsyncSession, learner_id: str
) -> dict[int, tuple[float, int, datetime]]:
    """For each card this learner has reviewed, return
    (avg_grade_last_3, review_count, last_reviewed_at).
    """
    stmt = select(ReviewRow).where(
        ReviewRow.learner_id == learner_id
    ).order_by(ReviewRow.reviewed_at.desc())
    result = await db.execute(stmt)
    rows = list(result.scalars())

    by_card: dict[int, list[ReviewRow]] = {}
    for r in rows:
        by_card.setdefault(r.card_id, []).append(r)

    out: dict[int, tuple[float, int, datetime]] = {}
    for card_id, reviews in by_card.items():
        last3 = reviews[:3]
        avg = sum(r.grade for r in last3) / max(len(last3), 1)
        out[card_id] = (avg, len(reviews), reviews[0].reviewed_at)
    return out


async def pick_next_card(
    db: AsyncSession, learner_id: str, deck: str = CURATED_DECK
) -> FlashcardRow | None:
    """Weakest-first: unreviewed cards first, then lowest avg-of-last-3 grade,
    tiebreak by least recently reviewed.
    """
    cards = await list_cards_for_learner(db, learner_id, deck)
    if not cards:
        return None

    stats = await recent_grade_by_card(db, learner_id)

    def sort_key(card: FlashcardRow):
        if card.id not in stats:
            return (0, 0.0, datetime.min)
        avg, _count, last = stats[card.id]
        return (1, avg, last)

    cards.sort(key=sort_key)
    return cards[0]


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

async def grade_answer(
    llm: LLMProvider,
    card: FlashcardRow,
    user_answer: str,
) -> dict[str, Any]:
    """Ask the LLM to grade the learner's answer against the reference.

    Returns a dict with 'score' (0-5 int), 'missing_concepts' (list[str]),
    'feedback' (str). Falls back to a conservative zero score on LLM failure.
    """
    user_answer = (user_answer or "").strip()
    if not user_answer:
        return {
            "score": 0,
            "missing_concepts": ["(blank answer)"],
            "feedback": "You didn't write an answer -- try again and put down everything you can recall.",
        }

    prompt = GRADE_USER_TEMPLATE.format(
        question=card.question,
        reference_answer=card.reference_answer,
        user_answer=user_answer,
    )

    try:
        parsed = await llm.chat_json(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=GRADE_SYSTEM_PROMPT,
            temperature=0.2,
        )
    except Exception as exc:
        logger.error("Grader LLM call failed: %s", exc)
        return {
            "score": 0,
            "missing_concepts": [],
            "feedback": "Grader unavailable right now -- your answer was recorded but not scored.",
        }

    score = parsed.get("score", 0)
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(5, score))

    missing = parsed.get("missing_concepts") or []
    if not isinstance(missing, list):
        missing = [str(missing)]
    missing = [str(m) for m in missing][:8]

    feedback = str(parsed.get("feedback", "")).strip()[:500]

    return {"score": score, "missing_concepts": missing, "feedback": feedback}


# ---------------------------------------------------------------------------
# Progress stats
# ---------------------------------------------------------------------------

async def progress_summary(
    db: AsyncSession,
    learner_id: str,
    deck: str | None = None,
) -> dict[str, Any]:
    """Compute the learner's progress dashboard payload.

    When ``deck`` is provided, cards and reviews are filtered to that deck
    so per-class dashboards show class-scoped progress only. Without it,
    behaves exactly as before for the default ML trainer.
    """
    reviews_stmt = select(ReviewRow).where(
        ReviewRow.learner_id == learner_id
    )
    if deck is not None:
        # Scope reviews to cards in the requested deck.
        deck_card_ids = list((await db.execute(
            select(FlashcardRow.id).where(
                FlashcardRow.deck == deck,
                FlashcardRow.learner_id.in_(["", learner_id]),
            )
        )).scalars())
        if deck_card_ids:
            reviews_stmt = reviews_stmt.where(
                ReviewRow.card_id.in_(deck_card_ids))
        else:
            reviews_stmt = reviews_stmt.where(ReviewRow.card_id.is_(None))
    reviews_stmt = reviews_stmt.order_by(ReviewRow.reviewed_at.desc())
    reviews = list((await db.execute(reviews_stmt)).scalars())

    total_reviews = len(reviews)
    total_correct = sum(1 for r in reviews if r.grade >= 3)
    accuracy = (total_correct / total_reviews) if total_reviews else 0.0

    if deck is not None:
        cards_stmt = select(FlashcardRow).where(
            FlashcardRow.deck == deck,
            FlashcardRow.learner_id.in_(["", learner_id]),
        )
        cards = list((await db.execute(cards_stmt)).scalars())
    else:
        cards = await list_cards_for_learner(db, learner_id)

    stats = await recent_grade_by_card(db, learner_id)
    # When filtering by deck, only consider cards in that deck.
    deck_card_id_set = {c.id for c in cards}
    scoped_stats = {
        cid: v for cid, v in stats.items() if cid in deck_card_id_set
    } if deck is not None else stats

    mastered = sum(
        1 for c in cards if c.id in scoped_stats and scoped_stats[c.id][0] >= 4)
    learning = sum(
        1 for c in cards if c.id in scoped_stats and 2 <= scoped_stats[c.id][0] < 4)
    struggling = sum(
        1 for c in cards if c.id in scoped_stats and scoped_stats[c.id][0] < 2)
    new_cards = sum(1 for c in cards if c.id not in scoped_stats)

    # Study streak: consecutive days (UTC) ending today with >=1 review.
    streak = 0
    if reviews:
        review_dates = sorted({
            r.reviewed_at.date() for r in reviews if r.reviewed_at is not None
        }, reverse=True)
        today = datetime.now(timezone.utc).date()
        cursor = today
        for d in review_dates:
            if d == cursor:
                streak += 1
                cursor = cursor - timedelta(days=1)
            elif d == cursor + timedelta(days=1):
                continue
            else:
                break

    recent = [
        {
            "card_id": r.card_id,
            "grade": r.grade,
            "llm_score": r.llm_score,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        }
        for r in reviews[:20]
    ]

    return {
        "total_reviews": total_reviews,
        "accuracy": round(accuracy, 3),
        "streak_days": streak,
        "mastered": mastered,
        "learning": learning,
        "struggling": struggling,
        "new": new_cards,
        "total_cards": len(cards),
        "recent_reviews": recent,
    }
