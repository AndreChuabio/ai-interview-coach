"""
Card generator for class-material decks.

Pipeline (called by class_ingestion.embed_then_generate):
  1. Load all embedded chunks for the class.
  2. Sample up to target * 1.5 diverse chunks via farthest-point selection
     on the embedding matrix. Avoids one-file domination.
  3. Pass 1 - concept extraction: batch 6 chunks per LLM call, extract
     teachable concepts, map them back to chunks, dedupe by term.
  4. Pass 2 - card synthesis: one concept per LLM call, limited concurrency
     (Semaphore(3)) to dodge provider rate limits.
  5. Write FlashcardRow rows with deck='class:<id>', source_snippet=chunk
     text, source_chunk_id=chunk.id. ClassRow.card_count gets the final
     total.
"""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.engine import async_session_factory
from backend.db.models import ClassChunkRow, ClassRow, FlashcardRow
from backend.prompts.class_cards import (
    CARD_SYNTHESIS_SYSTEM,
    CARD_SYNTHESIS_USER,
    CONCEPT_EXTRACTION_SYSTEM,
    CONCEPT_EXTRACTION_USER,
)
from backend.providers.base import LLMProvider
from backend.providers.factory import get_llm_provider

logger = logging.getLogger(__name__)


DEFAULT_TARGET = 40
HARD_CAP = 200
CONCEPT_BATCH = 6
SYNTHESIS_CONCURRENCY = 3


# ---------------------------------------------------------------------------
# Sampling: farthest-point in cosine space
# ---------------------------------------------------------------------------

def _unpack(row: ClassChunkRow) -> np.ndarray:
    return np.frombuffer(row.embedding, dtype=np.float32)


def _normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    return mat / norms


def sample_diverse_chunks(
    chunks: list[ClassChunkRow], target: int
) -> list[ClassChunkRow]:
    """Greedy farthest-point in cosine space, with a per-file balance cap."""
    if not chunks:
        return []
    budget = max(1, int(math.ceil(target * 1.5)))
    if len(chunks) <= budget:
        return list(chunks)

    mat = np.vstack([_unpack(c) for c in chunks]).astype(np.float32)
    norm_mat = _normalize(mat)

    # Per-file cap prevents one dominant file from hoarding picks. We give a
    # little slack on top of the even-split so small files don't get padded
    # with junk, but not so much that one file can eat the whole sample.
    file_counts: dict[str, int] = {}
    files_seen = {c.filename for c in chunks}
    per_file_cap = max(
        2,
        int(math.ceil(budget / max(1, len(files_seen)))) + 1,
    )

    # Start from the chunk closest to the mean direction (most "central").
    mean_dir = norm_mat.mean(axis=0)
    mean_dir /= np.linalg.norm(mean_dir) + 1e-12
    first = int(np.argmax(norm_mat @ mean_dir))
    selected_idx = [first]
    file_counts[chunks[first].filename] = 1

    # Running max similarity to the selected set.
    sims = norm_mat @ norm_mat[first]

    while len(selected_idx) < budget:
        # min cosine dist to selected = 1 - max cosine sim
        # pick the chunk with smallest max-sim (farthest), respecting per-file cap
        order = np.argsort(sims)  # ascending similarity
        picked = -1
        for cand in order:
            cand_i = int(cand)
            if cand_i in selected_idx:
                continue
            fname = chunks[cand_i].filename
            if file_counts.get(fname, 0) >= per_file_cap:
                continue
            picked = cand_i
            break
        if picked == -1:
            break
        selected_idx.append(picked)
        file_counts[chunks[picked].filename] = \
            file_counts.get(chunks[picked].filename, 0) + 1
        sims = np.maximum(sims, norm_mat @ norm_mat[picked])

    return [chunks[i] for i in selected_idx]


# ---------------------------------------------------------------------------
# Pass 1: concept extraction (batched)
# ---------------------------------------------------------------------------

def _build_snippets_block(batch: list[ClassChunkRow]) -> str:
    blocks: list[str] = []
    for i, row in enumerate(batch):
        header = f"[{i}] (filename={row.filename}"
        if row.page:
            header += f", page={row.page}"
        if row.heading:
            header += f", heading={row.heading}"
        header += ")"
        # Cap per-snippet text to avoid blowing context.
        body = row.text[:2400]
        blocks.append(f"{header}\n{body}")
    return "\n\n".join(blocks)


async def _extract_concepts_batch(
    llm: LLMProvider,
    batch: list[ClassChunkRow],
) -> list[dict[str, Any]]:
    prompt = CONCEPT_EXTRACTION_USER.format(
        snippets_block=_build_snippets_block(batch))
    try:
        parsed = await llm.chat_json(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=CONCEPT_EXTRACTION_SYSTEM,
            temperature=0.2,
        )
    except Exception as exc:
        logger.warning("Concept extraction LLM failed: %s", exc)
        return []
    concepts = parsed.get("concepts") if isinstance(parsed, dict) else None
    if not isinstance(concepts, list):
        return []

    out: list[dict[str, Any]] = []
    for c in concepts:
        if not isinstance(c, dict):
            continue
        term = str(c.get("term", "")).strip()
        definition = str(c.get("definition", "")).strip()
        try:
            src_idx = int(c.get("source_index", -1))
        except (TypeError, ValueError):
            src_idx = -1
        if not term or not definition or not (0 <= src_idx < len(batch)):
            continue
        chunk = batch[src_idx]
        out.append({
            "term": term[:160],
            "definition": definition[:500],
            "chunk": chunk,
        })
    return out


async def extract_concepts(
    llm: LLMProvider,
    sampled: list[ClassChunkRow],
    budget: int,
) -> list[dict[str, Any]]:
    """Extract up to ``budget`` unique concepts across the sampled chunks."""
    concepts: list[dict[str, Any]] = []
    seen_terms: set[str] = set()

    for i in range(0, len(sampled), CONCEPT_BATCH):
        if len(concepts) >= budget:
            break
        batch = sampled[i: i + CONCEPT_BATCH]
        batch_concepts = await _extract_concepts_batch(llm, batch)
        for c in batch_concepts:
            key = c["term"].casefold()
            if key in seen_terms:
                continue
            seen_terms.add(key)
            concepts.append(c)
            if len(concepts) >= budget:
                break
    return concepts


# ---------------------------------------------------------------------------
# Pass 2: card synthesis (parallel, bounded)
# ---------------------------------------------------------------------------

async def _synthesize_one(
    llm: LLMProvider, concept: dict[str, Any]
) -> dict[str, Any] | None:
    chunk: ClassChunkRow = concept["chunk"]
    prompt = CARD_SYNTHESIS_USER.format(
        term=concept["term"],
        definition=concept["definition"],
        chunk_text=chunk.text[:3000],
    )
    try:
        parsed = await llm.chat_json(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=CARD_SYNTHESIS_SYSTEM,
            temperature=0.4,
        )
    except Exception as exc:
        logger.warning("Card synthesis LLM failed for %r: %s",
                       concept["term"], exc)
        return None
    if not isinstance(parsed, dict):
        return None
    question = str(parsed.get("question", "")).strip()
    answer = str(parsed.get("reference_answer", "")).strip()
    if not question or not answer:
        return None
    topic = str(parsed.get("topic", "")).strip()[:128] or concept["term"][:128]
    difficulty = str(parsed.get("difficulty", "medium")).strip().lower()
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"
    return {
        "question": question,
        "reference_answer": answer,
        "topic": topic,
        "difficulty": difficulty,
        "chunk": chunk,
    }


async def _synthesize_all(
    llm: LLMProvider, concepts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    sem = asyncio.Semaphore(SYNTHESIS_CONCURRENCY)

    async def _one(c):
        async with sem:
            return await _synthesize_one(llm, c)

    results = await asyncio.gather(*[_one(c) for c in concepts])
    return [r for r in results if r]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def _load_class_and_chunks(
    db: AsyncSession, class_id: str
) -> tuple[ClassRow | None, list[ClassChunkRow]]:
    cls = await db.scalar(
        select(ClassRow).where(ClassRow.class_id == class_id))
    if cls is None:
        return None, []
    result = await db.execute(
        select(ClassChunkRow)
        .where(
            ClassChunkRow.class_id == class_id,
            ClassChunkRow.embedding.isnot(None),
        )
        .order_by(ClassChunkRow.id)
    )
    return cls, list(result.scalars())


async def generate_cards_for_class(
    class_id: str,
    target: int = DEFAULT_TARGET,
    llm: LLMProvider | None = None,
) -> int:
    """Generate up to ``target`` flashcards for the class (hard-capped at
    HARD_CAP). Returns the number of cards actually written.

    Idempotent: if cards already exist for this deck, we only top up to
    ``target`` and never exceed HARD_CAP.
    """
    target = max(1, min(int(target), HARD_CAP))
    llm = llm or get_llm_provider()

    async with async_session_factory() as db:
        cls, chunks = await _load_class_and_chunks(db, class_id)
        if cls is None:
            logger.warning("generate_cards_for_class: unknown class %s",
                           class_id)
            return 0
        if not chunks:
            logger.warning("generate_cards_for_class: no embedded chunks for %s",
                           class_id)
            return 0

        existing = int(cls.card_count or 0)
        if existing >= target:
            return 0
        to_generate = min(target - existing, HARD_CAP - existing)
        if to_generate <= 0:
            return 0

        sampled = sample_diverse_chunks(chunks, target=to_generate)
        concepts = await extract_concepts(llm, sampled, budget=to_generate)
        if not concepts:
            logger.info("No concepts extracted for class %s", class_id)
            return 0

        cards = await _synthesize_all(llm, concepts)
        if not cards:
            logger.info("No cards synthesized for class %s", class_id)
            return 0

        deck = cls.deck
        learner_id = cls.learner_id
        written = 0
        for card in cards:
            chunk: ClassChunkRow = card["chunk"]
            db.add(FlashcardRow(
                learner_id=learner_id,
                deck=deck,
                topic=card["topic"],
                question=card["question"],
                reference_answer=card["reference_answer"],
                source_snippet=chunk.text[:2000],
                source_chunk_id=chunk.id,
                difficulty=card["difficulty"],
                is_curated=False,
            ))
            written += 1

        cls.card_count = existing + written
        await db.commit()
        logger.info("Generated %d cards for class %s (total %d)",
                    written, class_id, cls.card_count)
        return written
