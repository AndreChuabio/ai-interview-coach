"""
AI Interview Coach -- FastAPI application entry point.
"""

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import classes, feedback, interview, trainer, user

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
app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(trainer.router, prefix="/api/trainer", tags=["trainer"])
app.include_router(classes.router, prefix="/api/classes", tags=["classes"])


_STARTUP_HOOK_TIMEOUT_SEC = 15


async def _run_startup_hook(name: str, coro):
    """Run a startup awaitable with a hard timeout. Any hang, timeout, or
    exception is logged but never blocks app startup. Critical for Azure B1
    where Neon Postgres cold starts and the startup probe deadline can race.
    """
    try:
        return await asyncio.wait_for(coro, timeout=_STARTUP_HOOK_TIMEOUT_SEC)
    except asyncio.TimeoutError:
        logger.warning(
            "Startup hook %r timed out after %ds; continuing without it",
            name, _STARTUP_HOOK_TIMEOUT_SEC)
    except Exception as exc:
        logger.warning("Startup hook %r failed (non-fatal): %s", name, exc)
    return None


@app.on_event("startup")
async def startup():
    """Initialize database tables. Heavy models are lazy-loaded on first use
    to keep startup fast and avoid OOM on constrained hosts (Azure B1).

    All startup hooks are wrapped with a timeout so a slow DB cold start or
    a single hanging await cannot push past the platform's startup probe
    deadline and trigger a crashloop.
    """
    # 1. Create database tables (cannot serve traffic without this).
    from backend.db.engine import init_db
    try:
        await asyncio.wait_for(init_db(), timeout=_STARTUP_HOOK_TIMEOUT_SEC)
        logger.info("Database tables initialized")
    except asyncio.TimeoutError:
        logger.error(
            "init_db timed out after %ds; app will start but DB-backed endpoints will likely fail",
            _STARTUP_HOOK_TIMEOUT_SEC)
    except Exception as exc:
        logger.error("init_db failed (continuing degraded): %s", exc)

    # 1b. Seed the curated ML flashcard deck if it's empty.
    from backend.services.trainer_engine import seed_curated_deck_if_empty
    inserted = await _run_startup_hook("seed_curated_deck", seed_curated_deck_if_empty())
    if inserted:
        logger.info("Seeded %d curated ML flashcards", inserted)

    # 1c. Re-queue any class ingestions that were mid-pipeline when the
    #     server was last shut down.
    from backend.services.class_ingestion import resume_stuck_classes
    from backend.routers.classes import _schedule_pipeline
    resumed = await _run_startup_hook(
        "resume_stuck_classes", resume_stuck_classes(_schedule_pipeline))
    if resumed:
        logger.info("Re-queued %d stuck class ingestions", resumed)

    # 2. STT / embedding models are loaded lazily on first request.
    #    Pre-loading them here exceeds the 1.75 GB RAM on Azure B1
    #    and causes the startup probe to time out.

    # 3. Warm up Neo4j connection.
    from backend.knowledge.graph import neo4j_manager
    if neo4j_manager.is_configured():
        await _run_startup_hook("neo4j_warmup", neo4j_manager.verify_connection())


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
