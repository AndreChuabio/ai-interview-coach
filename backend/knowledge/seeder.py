"""
Neo4j knowledge graph seeder.

Loads curated seed data (companies, roles, topics, questions, example answers)
into the Neo4j graph database with embeddings for vector search.

Usage:
    python -m backend.knowledge.seeder
"""

from __future__ import annotations

import asyncio
import logging

from backend.knowledge.embedder import get_embedder
from backend.knowledge.graph import neo4j_manager
from backend.knowledge.seed_data import COMPANIES, QUESTIONS_WITH_CONTEXT, ROLES, TOPICS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def seed() -> None:
    """Run the full seeding pipeline."""
    if not neo4j_manager.is_configured():
        logger.error("Neo4j is not configured. Set NEO4J_URI and NEO4J_PASSWORD in .env")
        return

    logger.info("Verifying Neo4j connection...")
    await neo4j_manager.verify_connection()

    logger.info("Creating schema (constraints, indexes)...")
    await neo4j_manager.create_schema()

    embedder = get_embedder()

    # 1. Seed companies
    logger.info("Seeding %d companies...", len(COMPANIES))
    for c in COMPANIES:
        await neo4j_manager.merge_company(**c)

    # 2. Seed roles
    logger.info("Seeding %d roles...", len(ROLES))
    for r in ROLES:
        await neo4j_manager.merge_role(**r)

    # 3. Seed topics
    logger.info("Seeding %d topics...", len(TOPICS))
    for t in TOPICS:
        await neo4j_manager.merge_topic(**t)

    # 4. Seed questions with embeddings and relationships
    logger.info("Seeding %d questions with embeddings...", len(QUESTIONS_WITH_CONTEXT))
    for q_data in QUESTIONS_WITH_CONTEXT:
        text = q_data["text"]
        embedding = embedder.encode_single(text)

        await neo4j_manager.merge_question(
            text=text,
            interview_type=q_data["interview_type"],
            difficulty=q_data["difficulty"],
            embedding=embedding,
        )

        # Link to topics
        for topic_name in q_data.get("topics", []):
            await neo4j_manager.link_question_to_topic(text, topic_name)

        # Link to roles
        for role_name in q_data.get("roles", []):
            await neo4j_manager.link_question_to_role(text, role_name)

        # Link to companies
        for company_name in q_data.get("companies", []):
            await neo4j_manager.link_question_to_company(text, company_name)

        # Seed example answers
        for answer_data in q_data.get("answers", []):
            answer_embedding = embedder.encode_single(answer_data["text"])
            await neo4j_manager.merge_example_answer(
                question_text=text,
                answer_text=answer_data["text"],
                quality=answer_data.get("quality", "strong"),
                embedding=answer_embedding,
            )

        logger.info("  Seeded: %s", text[:80])

    logger.info("Seeding complete.")
    await neo4j_manager.close()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
