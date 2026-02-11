"""
AI Interview Coach -- FastAPI application entry point.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import interview, feedback

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

app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])


@app.on_event("startup")
async def startup():
    """Initialize database tables and pre-load heavy models at startup."""
    # 1. Create database tables
    from backend.db.engine import init_db
    await init_db()
    logger.info("Database tables initialized")

    # 2. Pre-load STT model (Whisper) so the first request is fast
    try:
        from backend.providers.factory import get_stt_provider
        stt = get_stt_provider()
        if hasattr(stt, "_load_model"):
            stt._load_model()
        logger.info("STT provider ready: %s", type(stt).__name__)
    except Exception as exc:
        logger.warning("Failed to pre-load STT provider: %s", exc)

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
