"""
AI Interview Coach -- FastAPI application entry point.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import feedback, interview, trainer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# Suppress noisy third-party debug loggers
for _noisy in ("numba", "httpcore", "httpx", "google_genai", "urllib3"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Practice interviews with an AI coach that analyzes your responses, tone, and facial expressions.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS origins: %s", settings.cors_origins)

app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(trainer.router, prefix="/api/trainer", tags=["trainer"])


@app.on_event("startup")
async def startup():
    """Initialize database tables. Heavy models are lazy-loaded on first use
    to keep startup fast and avoid OOM on constrained hosts (Azure B1)."""
    # 1. Create database tables
    from backend.db.engine import init_db
    await init_db()
    logger.info("Database tables initialized")

    # 1b. Seed the curated ML flashcard deck if it's empty.
    try:
        from backend.services.trainer_engine import seed_curated_deck_if_empty
        inserted = await seed_curated_deck_if_empty()
        if inserted:
            logger.info("Seeded %d curated ML flashcards", inserted)
    except Exception as exc:
        logger.warning(
            "Could not seed curated ML deck (non-fatal): %s", exc)

    # 2. STT / embedding models are loaded lazily on first request.
    #    Pre-loading them here exceeds the 1.75 GB RAM on Azure B1
    #    and causes the startup probe to time out.

    # 3. Warm up Neo4j connection (non-blocking, logs warning if unavailable)
    try:
        from backend.knowledge.graph import neo4j_manager
        if neo4j_manager.is_configured():
            await neo4j_manager.verify_connection()
    except Exception as exc:
        logger.warning("Neo4j not available at startup (non-fatal): %s", exc)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "providers": {
            "llm": settings.llm_provider,
            "stt": settings.stt_provider,
            "tts": settings.tts_provider,
        },
    }
