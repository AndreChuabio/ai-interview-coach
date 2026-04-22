"""
Class materials endpoints. A "class" is one learner's uploaded folder of
course content (PDFs, markdown, plain text in PR 6; DOCX/PPTX/IPYNB in PR 9).

Identity matches the rest of the trainer: a client-generated learner_id UUID
passed as form/query param -- no password auth.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.engine import async_session_factory, get_db
from backend.db.models import ClassChunkRow, ClassRow, FlashcardRow, ReviewRow
from backend.services import class_ingestion, trainer_engine

logger = logging.getLogger(__name__)
router = APIRouter()


MAX_FILE_BYTES = 20 * 1024 * 1024       # 20 MB per file
MAX_TOTAL_BYTES = 50 * 1024 * 1024      # 50 MB per upload
MAX_FILES_PER_UPLOAD = 30


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ClassSummary(BaseModel):
    class_id: str
    title: str
    deck: str
    status: str
    file_count: int
    chunk_count: int
    card_count: int
    error_message: str = ""


class UploadClassResponse(BaseModel):
    class_id: str
    title: str
    deck: str
    status: str
    file_count: int
    chunk_count: int
    skipped_files: list[str] = Field(default_factory=list)


class ClassStatusResponse(BaseModel):
    class_id: str
    title: str
    deck: str
    status: str
    file_count: int
    chunk_count: int
    embedded_chunks: int
    progress: float
    card_count: int
    error_message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _owned(db: AsyncSession, class_id: str, learner_id: str) -> ClassRow:
    row = await db.scalar(
        select(ClassRow).where(ClassRow.class_id == class_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Class not found")
    if row.learner_id != learner_id:
        raise HTTPException(status_code=403, detail="Not your class")
    return row


def _schedule_pipeline(class_id: str) -> None:
    """Kick off embed_then_generate as a detached asyncio task.

    Used from the startup self-heal (we don't have a BackgroundTasks instance
    there). The task runs in the same event loop; failures are logged and
    mark the class failed.
    """
    try:
        asyncio.create_task(class_ingestion.embed_then_generate(class_id))
    except RuntimeError:
        logger.exception(
            "Could not schedule ingestion task for class %s", class_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadClassResponse)
async def upload_class(
    background: BackgroundTasks,
    learner_id: str = Form(..., min_length=8, max_length=64),
    title: str = Form(..., min_length=1, max_length=200),
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Create a class and stage its chunks.

    Parsing runs synchronously (fast). Embedding + card generation run as a
    FastAPI BackgroundTask so the caller gets a response in a couple of
    seconds. The client polls ``/{class_id}/status`` for progress.
    """
    await trainer_engine.get_or_create_learner(db, learner_id)

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files (max {MAX_FILES_PER_UPLOAD})",
        )

    # Create the ClassRow first so we have its class_id before flushing chunks.
    cls = ClassRow(
        learner_id=learner_id,
        title=title.strip()[:200],
        deck="",  # filled in once class_id is generated
        status="parsing",
    )
    db.add(cls)
    await db.flush()
    cls.deck = f"class:{cls.class_id}"

    chunk_rows: list[ClassChunkRow] = []
    skipped: list[str] = []
    total_bytes = 0
    filenames_seen: set[str] = set()

    for uf in files:
        filename = uf.filename or "unnamed"
        parser = class_ingestion.pick_parser(filename)
        if parser is None:
            skipped.append(f"{filename} (unsupported extension)")
            continue

        data = await uf.read()
        size = len(data)
        if size > MAX_FILE_BYTES:
            skipped.append(f"{filename} (>{MAX_FILE_BYTES // (1024 * 1024)} MB)")
            continue
        if total_bytes + size > MAX_TOTAL_BYTES:
            skipped.append(f"{filename} (upload cap reached)")
            continue
        total_bytes += size

        try:
            segments = list(parser.parse(filename, data))
        except Exception as exc:
            logger.warning("Parser failed for %s: %s", filename, exc)
            skipped.append(f"{filename} (parse error)")
            continue

        produced_any = False
        for chunk in class_ingestion.chunk_segments(segments):
            chunk_rows.append(ClassChunkRow(
                class_id=cls.class_id,
                filename=chunk.filename,
                page=chunk.page,
                heading=chunk.heading,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                token_estimate=chunk.token_estimate,
                embedding=None,
            ))
            produced_any = True
        if produced_any:
            filenames_seen.add(filename)
        else:
            skipped.append(f"{filename} (no extractable text)")

    db.add_all(chunk_rows)
    cls.file_count = len(filenames_seen)
    cls.chunk_count = len(chunk_rows)

    if not chunk_rows:
        cls.status = "failed"
        cls.error_message = (
            "No text extracted. Check that your PDFs contain selectable text "
            "(not scans) and that files are under the size cap."
        )
    else:
        cls.status = "embedding"

    await db.commit()

    if chunk_rows:
        background.add_task(class_ingestion.embed_then_generate, cls.class_id)

    return UploadClassResponse(
        class_id=cls.class_id,
        title=cls.title,
        deck=cls.deck,
        status=cls.status,
        file_count=cls.file_count,
        chunk_count=cls.chunk_count,
        skipped_files=skipped,
    )


@router.get("/{class_id}/status", response_model=ClassStatusResponse)
async def class_status(
    class_id: str,
    learner_id: str = Query(..., min_length=8),
    db: AsyncSession = Depends(get_db),
):
    cls = await _owned(db, class_id, learner_id)

    embedded = await db.scalar(
        select(func.count(ClassChunkRow.id)).where(
            ClassChunkRow.class_id == class_id,
            ClassChunkRow.embedding.isnot(None),
        )
    ) or 0
    total = cls.chunk_count
    progress = (embedded / total) if total else 0.0

    return ClassStatusResponse(
        class_id=cls.class_id,
        title=cls.title,
        deck=cls.deck,
        status=cls.status,
        file_count=cls.file_count,
        chunk_count=total,
        embedded_chunks=int(embedded),
        progress=round(progress, 3),
        card_count=cls.card_count,
        error_message=cls.error_message or "",
    )


@router.get("/", response_model=list[ClassSummary])
async def list_classes(
    learner_id: str = Query(..., min_length=8),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClassRow)
        .where(ClassRow.learner_id == learner_id)
        .order_by(ClassRow.created_at.desc())
    )
    return [
        ClassSummary(
            class_id=r.class_id,
            title=r.title,
            deck=r.deck,
            status=r.status,
            file_count=r.file_count,
            chunk_count=r.chunk_count,
            card_count=r.card_count,
            error_message=r.error_message or "",
        )
        for r in result.scalars()
    ]


@router.post("/{class_id}/generate-cards", response_model=ClassStatusResponse)
async def generate_more_cards(
    class_id: str,
    background: BackgroundTasks,
    learner_id: str = Query(..., min_length=8),
    count: int = Query(40, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Top up cards for a class that's already ``ready``. Runs in the
    background so the call returns immediately; poll /status."""
    cls = await _owned(db, class_id, learner_id)
    if cls.status not in ("ready", "failed"):
        raise HTTPException(
            status_code=409,
            detail=f"Class is {cls.status}; wait for it to finish first",
        )
    previous_card_count = int(cls.card_count or 0)
    cls.status = "generating"
    cls.error_message = ""
    await db.commit()

    async def _run():
        from backend.services import card_generator, class_ingestion
        try:
            await card_generator.generate_cards_for_class(
                class_id, target=previous_card_count + count,
            )
            async with async_session_factory() as db2:
                row = await db2.scalar(
                    select(ClassRow).where(ClassRow.class_id == class_id))
                if row is not None and row.status != "failed":
                    row.status = "ready"
                    await db2.commit()
        except Exception as exc:
            logger.exception(
                "generate-cards background failed for %s: %s", class_id, exc)
            await class_ingestion._mark_failed(
                class_id, f"Card generation error: {exc}")

    background.add_task(_run)
    return await class_status(class_id, learner_id, db)


@router.delete("/{class_id}")
async def delete_class(
    class_id: str,
    learner_id: str = Query(..., min_length=8),
    db: AsyncSession = Depends(get_db),
):
    cls = await _owned(db, class_id, learner_id)

    # Collect card ids for this deck so we can wipe their reviews too.
    card_ids = list((await db.execute(
        select(FlashcardRow.id).where(
            FlashcardRow.deck == cls.deck,
            FlashcardRow.learner_id == learner_id,
        )
    )).scalars())

    if card_ids:
        await db.execute(
            delete(ReviewRow).where(ReviewRow.card_id.in_(card_ids))
        )
    await db.execute(
        delete(FlashcardRow).where(
            FlashcardRow.deck == cls.deck,
            FlashcardRow.learner_id == learner_id,
        )
    )
    await db.execute(
        delete(ClassChunkRow).where(ClassChunkRow.class_id == class_id)
    )
    await db.delete(cls)
    await db.commit()
    return {"deleted": class_id}
