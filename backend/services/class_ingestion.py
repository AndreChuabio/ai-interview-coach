"""
Class materials ingestion: parse uploaded files, chunk them, embed chunks
with the existing MiniLM embedder, and (after PR 7) kick off card
generation.

Design notes:
- Parsers are streaming-friendly generators so we never hold more than one
  file's extracted text in memory.
- Chunks are word-level sliding windows within a single ParsedSegment so
  filename/page/heading metadata is preserved for citations (PR 9).
- Embeddings are stored as np.float32(dim).tobytes() in a LargeBinary column;
  portable across SQLite / Postgres with no pgvector dep.
- Ingestion runs inside FastAPI BackgroundTasks; we never block HTTP handlers
  on embedding (30-60 s for a moderate class on Azure B1).
"""

from __future__ import annotations

import gc
import io
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol, Sequence

import numpy as np
from sqlalchemy import select

from backend.db.engine import async_session_factory
from backend.db.models import ClassChunkRow, ClassRow
from backend.knowledge.embedder import get_embedder

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parser interface
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ParsedSegment:
    """One self-contained unit of text from a source file."""
    filename: str
    page: int          # 1-based for PDF, 0 otherwise
    heading: str       # markdown heading path, slide title, etc.
    text: str


@dataclass(slots=True)
class ChunkCandidate:
    filename: str
    page: int
    heading: str
    chunk_index: int
    text: str
    token_estimate: int


class Parser(Protocol):
    extensions: tuple[str, ...]

    def parse(self, filename: str, data: bytes) -> Iterator[ParsedSegment]:
        ...


# ---------------------------------------------------------------------------
# PDF parser
# ---------------------------------------------------------------------------

class PdfParser:
    extensions = (".pdf",)

    def parse(self, filename: str, data: bytes) -> Iterator[ParsedSegment]:
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.error("pypdf not installed; skipping %s", filename)
            return
        try:
            reader = PdfReader(io.BytesIO(data))
        except Exception as exc:
            logger.warning("Could not open PDF %s: %s", filename, exc)
            return
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                logger.warning("PDF page %d of %s failed: %s",
                               i + 1, filename, exc)
                continue
            text = text.strip()
            if not text:
                continue
            yield ParsedSegment(
                filename=filename,
                page=i + 1,
                heading="",
                text=text,
            )


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


class MarkdownParser:
    extensions = (".md", ".markdown")

    def parse(self, filename: str, data: bytes) -> Iterator[ParsedSegment]:
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Could not decode %s: %s", filename, exc)
            return

        current_path: list[tuple[int, str]] = []  # (level, heading)
        buffer: list[str] = []
        buffer_heading = ""
        emitted_any = False

        def heading_path() -> str:
            return " > ".join(h for _, h in current_path)

        for line in text.splitlines():
            m = _HEADING_RE.match(line)
            if m:
                body = "\n".join(buffer).strip()
                if body:
                    emitted_any = True
                    yield ParsedSegment(
                        filename=filename, page=0,
                        heading=buffer_heading, text=body,
                    )
                buffer = []
                level = len(m.group(1))
                heading = m.group(2).strip()
                current_path = [(l, h) for l, h in current_path if l < level]
                current_path.append((level, heading))
                buffer_heading = heading_path()
            else:
                buffer.append(line)

        body = "\n".join(buffer).strip()
        if body:
            emitted_any = True
            yield ParsedSegment(
                filename=filename, page=0,
                heading=buffer_heading, text=body,
            )

        if not emitted_any:
            stripped = text.strip()
            if stripped:
                yield ParsedSegment(
                    filename=filename, page=0, heading="", text=stripped,
                )


# ---------------------------------------------------------------------------
# Plain text parser
# ---------------------------------------------------------------------------

class TextParser:
    extensions = (".txt",)

    def parse(self, filename: str, data: bytes) -> Iterator[ParsedSegment]:
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Could not decode %s: %s", filename, exc)
            return

        # Group paragraphs until each group is >= 200 chars to avoid an
        # explosion of tiny segments.
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        buf: list[str] = []
        size = 0
        for para in paragraphs:
            buf.append(para)
            size += len(para)
            if size >= 200:
                yield ParsedSegment(
                    filename=filename, page=0, heading="", text="\n\n".join(buf))
                buf, size = [], 0
        if buf:
            yield ParsedSegment(
                filename=filename, page=0, heading="", text="\n\n".join(buf))


# ---------------------------------------------------------------------------
# Parser dispatch
# ---------------------------------------------------------------------------

_PARSERS: list[Parser] = [PdfParser(), MarkdownParser(), TextParser()]


def register_parser(parser: Parser) -> None:
    """Let PR 9 add DOCX / PPTX / IPYNB without editing this module."""
    _PARSERS.append(parser)


def pick_parser(filename: str) -> Parser | None:
    ext = Path(filename).suffix.lower()
    for p in _PARSERS:
        if ext in p.extensions:
            return p
    return None


def supported_extensions() -> tuple[str, ...]:
    seen: list[str] = []
    for p in _PARSERS:
        for ext in p.extensions:
            if ext not in seen:
                seen.append(ext)
    return tuple(seen)


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------

def est_tokens(text: str) -> int:
    """Cheap token estimator: word count * 1.3."""
    return int(len(text.split()) * 1.3)


def chunk_segments(
    segments: Iterable[ParsedSegment],
    target_tokens: int = 320,
    overlap_tokens: int = 64,
) -> Iterator[ChunkCandidate]:
    """Word-level sliding window inside each segment.

    Each segment produces one or more chunks; chunks never cross segment
    boundaries, preserving filename/page/heading metadata on every chunk.
    """
    target = max(32, target_tokens)
    overlap = max(0, min(overlap_tokens, target - 16))

    # Convert token budget to an approximate word budget (1 token ~ 0.77 words)
    word_budget = int(target / 1.3)
    word_overlap = int(overlap / 1.3)

    for seg in segments:
        words = seg.text.split()
        if not words:
            continue

        if len(words) <= word_budget:
            text = " ".join(words).strip()
            if text:
                yield ChunkCandidate(
                    filename=seg.filename,
                    page=seg.page,
                    heading=seg.heading,
                    chunk_index=0,
                    text=text,
                    token_estimate=est_tokens(text),
                )
            continue

        step = max(1, word_budget - word_overlap)
        idx = 0
        chunk_i = 0
        while idx < len(words):
            window = words[idx: idx + word_budget]
            text = " ".join(window).strip()
            if text:
                yield ChunkCandidate(
                    filename=seg.filename,
                    page=seg.page,
                    heading=seg.heading,
                    chunk_index=chunk_i,
                    text=text,
                    token_estimate=est_tokens(text),
                )
                chunk_i += 1
            if idx + word_budget >= len(words):
                break
            idx += step


# ---------------------------------------------------------------------------
# Embedding loop (background task)
# ---------------------------------------------------------------------------

EMBED_BATCH = 32


def _pack_vector(vec) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes()


def _unpack_vector(buf: bytes) -> np.ndarray:
    return np.frombuffer(buf, dtype=np.float32)


async def _embed_pending(class_id: str) -> None:
    """Embed chunks with embedding IS NULL in batches."""
    embedder = get_embedder()
    while True:
        async with async_session_factory() as db:
            result = await db.execute(
                select(ClassChunkRow)
                .where(
                    ClassChunkRow.class_id == class_id,
                    ClassChunkRow.embedding.is_(None),
                )
                .limit(EMBED_BATCH)
            )
            rows = list(result.scalars())
            if not rows:
                return
            texts = [r.text for r in rows]
            try:
                vecs = embedder.encode(texts)
            except Exception as exc:
                logger.exception(
                    "Embedding batch failed for class %s: %s", class_id, exc)
                # Mark the class as failed so the frontend can surface it.
                cls = await db.scalar(
                    select(ClassRow).where(ClassRow.class_id == class_id))
                if cls is not None:
                    cls.status = "failed"
                    cls.error_message = f"Embedding error: {exc}"[:500]
                await db.commit()
                return
            for row, vec in zip(rows, vecs):
                row.embedding = _pack_vector(vec)
            await db.commit()
        gc.collect()


async def embed_then_generate(class_id: str, target_cards: int = 40) -> None:
    """Full background pipeline: embed pending chunks, then generate cards.

    PR 6 ships with a no-op card generator so the status advances all the way
    to 'ready' even before PR 7 lands.
    """
    logger.info("Starting ingestion pipeline for class %s", class_id)
    try:
        await _embed_pending(class_id)
    except Exception as exc:
        logger.exception(
            "embed_then_generate failed during embedding for %s: %s",
            class_id, exc)
        await _mark_failed(class_id, f"Embedding pipeline error: {exc}")
        return

    async with async_session_factory() as db:
        cls = await db.scalar(
            select(ClassRow).where(ClassRow.class_id == class_id))
        if cls is None:
            return
        if cls.status == "failed":
            return
        cls.status = "generating"
        await db.commit()

    # Card generation (PR 7 implements this; PR 6 has a stub that simply flips
    # status to 'ready' with card_count=0).
    try:
        from backend.services import card_generator  # lazy import
    except ImportError:
        card_generator = None  # type: ignore[assignment]

    if card_generator is not None and hasattr(card_generator, "generate_cards_for_class"):
        try:
            await card_generator.generate_cards_for_class(class_id, target=target_cards)
        except Exception as exc:
            logger.exception(
                "Card generation failed for class %s: %s", class_id, exc)
            await _mark_failed(class_id, f"Card generation error: {exc}")
            return

    async with async_session_factory() as db:
        cls = await db.scalar(
            select(ClassRow).where(ClassRow.class_id == class_id))
        if cls is None or cls.status == "failed":
            return
        cls.status = "ready"
        await db.commit()
    logger.info("Ingestion pipeline finished for class %s", class_id)


async def _mark_failed(class_id: str, message: str) -> None:
    async with async_session_factory() as db:
        cls = await db.scalar(
            select(ClassRow).where(ClassRow.class_id == class_id))
        if cls is None:
            return
        cls.status = "failed"
        cls.error_message = message[:500]
        await db.commit()


# ---------------------------------------------------------------------------
# Numpy cosine search helper (used by PR 7 for concept grounding)
# ---------------------------------------------------------------------------

def cosine_search(
    query_vec: np.ndarray,
    chunk_rows: Sequence[ClassChunkRow],
    top_k: int = 5,
) -> list[tuple[ClassChunkRow, float]]:
    """Return the top-k (chunk, cosine_similarity) pairs."""
    if not chunk_rows:
        return []
    mat = np.vstack([
        _unpack_vector(r.embedding) for r in chunk_rows if r.embedding
    ])
    if mat.size == 0:
        return []
    q = query_vec / (np.linalg.norm(query_vec) + 1e-12)
    m = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12)
    sims = m @ q
    k = min(top_k, len(chunk_rows))
    idx = np.argsort(-sims)[:k]
    return [(chunk_rows[i], float(sims[i])) for i in idx]


# ---------------------------------------------------------------------------
# Self-heal: re-queue classes stuck in intermediate status after a restart.
# ---------------------------------------------------------------------------

async def resume_stuck_classes(background_runner) -> int:
    """Restart ingestion for any class that was mid-pipeline when the server
    went down. ``background_runner`` is a callable like
    ``asyncio.create_task(embed_then_generate(class_id))``.

    Returns how many classes were re-queued.
    """
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    count = 0
    async with async_session_factory() as db:
        result = await db.execute(
            select(ClassRow).where(
                ClassRow.status.in_(("parsing", "embedding", "generating"))
            )
        )
        rows = list(result.scalars())
    for cls in rows:
        # cls.updated_at is TZ-naive when stored by SQLAlchemy's server_default;
        # treat it as UTC.
        updated = cls.updated_at
        if updated is not None and updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        if updated is None or updated < cutoff:
            try:
                background_runner(cls.class_id)
                count += 1
            except Exception as exc:
                logger.warning(
                    "Could not re-queue class %s: %s", cls.class_id, exc)
    return count
