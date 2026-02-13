"""
Neo4j connection manager and graph operations.

Manages the connection to Neo4j AuraDB and provides methods for:
  - Creating the graph schema (constraints, indexes)
  - Inserting knowledge nodes (companies, questions, example answers)
  - Querying by graph traversal
  - Vector similarity search (using Neo4j built-in vector index)

Read operations have a 5-second timeout so the RAG layer fails fast
when AuraDB is paused or unreachable, instead of blocking for 30s+.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from backend.config import settings

# Timeout for read queries (seconds). Keeps RAG fallback fast when
# AuraDB free tier is paused or network is unreachable.
_READ_TIMEOUT_SEC = 5.0

logger = logging.getLogger(__name__)


class Neo4jManager:
    """Async Neo4j driver wrapper with lifecycle management."""

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None

    def is_configured(self) -> bool:
        """Return True if Neo4j credentials are present in config."""
        return bool(settings.neo4j_uri and settings.neo4j_password)

    async def _get_driver(self) -> AsyncDriver:
        """Lazily create and return the async Neo4j driver."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )
        return self._driver

    async def close(self) -> None:
        """Close the driver connection."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    async def verify_connection(self) -> bool:
        """Verify that we can reach Neo4j and log server info."""
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS ping")
            record = await result.single()
            logger.info("Neo4j connection verified (ping=%s)", record["ping"])
            return True

    # ------------------------------------------------------------------
    # Schema setup
    # ------------------------------------------------------------------

    async def create_schema(self) -> None:
        """
        Create constraints, indexes, and the vector index for embeddings.
        Idempotent -- safe to call on every startup or seed run.
        """
        driver = await self._get_driver()
        async with driver.session() as session:
            # Uniqueness constraints
            await session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE"
            )
            await session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE"
            )
            await session.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE"
            )

            # Text index for fast lookups
            await session.run(
                "CREATE INDEX IF NOT EXISTS FOR (q:Question) ON (q.text)"
            )

            # Vector index for semantic search on Question embeddings
            # all-MiniLM-L6-v2 produces 384-dimensional vectors
            try:
                await session.run("""
                    CREATE VECTOR INDEX question_embeddings IF NOT EXISTS
                    FOR (q:Question)
                    ON (q.embedding)
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 384,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                """)
                logger.info("Vector index 'question_embeddings' ensured")
            except Exception as exc:
                # Older Neo4j versions or AuraDB free tier may not support vector indexes
                logger.warning("Could not create vector index (may already exist): %s", exc)

            # Vector index for ExampleAnswer embeddings
            try:
                await session.run("""
                    CREATE VECTOR INDEX answer_embeddings IF NOT EXISTS
                    FOR (a:ExampleAnswer)
                    ON (a.embedding)
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 384,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                """)
                logger.info("Vector index 'answer_embeddings' ensured")
            except Exception as exc:
                logger.warning("Could not create answer vector index: %s", exc)

        logger.info("Neo4j schema created/verified")

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def merge_company(self, name: str, industry: str = "", description: str = "") -> None:
        """Create or update a Company node."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MERGE (c:Company {name: $name})
                SET c.industry = $industry, c.description = $description
                """,
                name=name, industry=industry, description=description,
            )

    async def merge_role(self, name: str, level: str = "mid") -> None:
        """Create or update a Role node."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                "MERGE (r:Role {name: $name}) SET r.level = $level",
                name=name, level=level,
            )

    async def merge_topic(self, name: str, category: str = "") -> None:
        """Create or update a Topic node."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                "MERGE (t:Topic {name: $name}) SET t.category = $category",
                name=name, category=category,
            )

    async def merge_question(
        self,
        text: str,
        interview_type: str,
        difficulty: str = "medium",
        embedding: list[float] | None = None,
    ) -> None:
        """Create or update a Question node with optional embedding."""
        driver = await self._get_driver()
        async with driver.session() as session:
            params: dict[str, Any] = {
                "text": text,
                "interview_type": interview_type,
                "difficulty": difficulty,
            }
            cypher = """
                MERGE (q:Question {text: $text})
                SET q.interview_type = $interview_type, q.difficulty = $difficulty
            """
            if embedding is not None:
                cypher += ", q.embedding = $embedding"
                params["embedding"] = embedding
            await session.run(cypher, **params)

    async def merge_example_answer(
        self,
        question_text: str,
        answer_text: str,
        quality: str = "strong",
        embedding: list[float] | None = None,
    ) -> None:
        """Create an ExampleAnswer node linked to its Question."""
        driver = await self._get_driver()
        async with driver.session() as session:
            params: dict[str, Any] = {
                "question_text": question_text,
                "answer_text": answer_text,
                "quality": quality,
            }
            cypher = """
                MATCH (q:Question {text: $question_text})
                MERGE (a:ExampleAnswer {text: $answer_text})
                SET a.quality = $quality
                MERGE (a)-[:ANSWERS]->(q)
            """
            if embedding is not None:
                cypher = """
                    MATCH (q:Question {text: $question_text})
                    MERGE (a:ExampleAnswer {text: $answer_text})
                    SET a.quality = $quality, a.embedding = $embedding
                    MERGE (a)-[:ANSWERS]->(q)
                """
                params["embedding"] = embedding
            await session.run(cypher, **params)

    async def link_question_to_topic(self, question_text: str, topic_name: str) -> None:
        """Create RELATES_TO relationship between Question and Topic."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (q:Question {text: $question_text})
                MATCH (t:Topic {name: $topic_name})
                MERGE (q)-[:RELATES_TO]->(t)
                """,
                question_text=question_text, topic_name=topic_name,
            )

    async def link_question_to_role(self, question_text: str, role_name: str) -> None:
        """Create TARGETS relationship between Question and Role."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (q:Question {text: $question_text})
                MATCH (r:Role {name: $role_name})
                MERGE (q)-[:TARGETS]->(r)
                """,
                question_text=question_text, role_name=role_name,
            )

    async def link_question_to_company(self, question_text: str, company_name: str) -> None:
        """Create ASKED_AT relationship between Question and Company."""
        driver = await self._get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (q:Question {text: $question_text})
                MATCH (c:Company {name: $company_name})
                MERGE (q)-[:ASKED_AT]->(c)
                """,
                question_text=question_text, company_name=company_name,
            )

    # ------------------------------------------------------------------
    # Read operations (graph traversal)
    # ------------------------------------------------------------------

    async def _run_read_query(self, cypher: str, **params) -> list[dict]:
        """
        Execute a read query with a timeout.
        Returns a list of record dicts, or empty list on timeout.
        """
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await asyncio.wait_for(
                session.run(cypher, **params),
                timeout=_READ_TIMEOUT_SEC,
            )
            return [dict(r) async for r in result]

    async def get_questions_for_context(
        self,
        interview_type: str,
        role: str = "",
        company: str = "",
        limit: int = 5,
    ) -> list[dict]:
        """
        Retrieve relevant questions using graph relationships.
        Prioritizes questions linked to the specified company and role,
        then falls back to type + topic matches.
        Times out after 5s to keep startup fast when AuraDB is paused.
        """
        try:
            # Try company + role specific first
            if company:
                records = await self._run_read_query(
                    """
                    MATCH (q:Question)-[:ASKED_AT]->(c:Company {name: $company})
                    WHERE q.interview_type = $interview_type
                    OPTIONAL MATCH (q)-[:TARGETS]->(r:Role)
                    OPTIONAL MATCH (q)-[:RELATES_TO]->(t:Topic)
                    RETURN q.text AS text, q.difficulty AS difficulty,
                           collect(DISTINCT t.name) AS topics,
                           collect(DISTINCT r.name) AS roles
                    LIMIT $limit
                    """,
                    company=company, interview_type=interview_type, limit=limit,
                )
                if records:
                    return records

            # Fall back to role-based
            if role:
                records = await self._run_read_query(
                    """
                    MATCH (q:Question)-[:TARGETS]->(r:Role)
                    WHERE q.interview_type = $interview_type
                      AND toLower(r.name) CONTAINS toLower($role)
                    OPTIONAL MATCH (q)-[:RELATES_TO]->(t:Topic)
                    RETURN q.text AS text, q.difficulty AS difficulty,
                           collect(DISTINCT t.name) AS topics
                    LIMIT $limit
                    """,
                    interview_type=interview_type, role=role, limit=limit,
                )
                if records:
                    return records

            # Final fallback: any questions of the right type
            return await self._run_read_query(
                """
                MATCH (q:Question)
                WHERE q.interview_type = $interview_type
                OPTIONAL MATCH (q)-[:RELATES_TO]->(t:Topic)
                RETURN q.text AS text, q.difficulty AS difficulty,
                       collect(DISTINCT t.name) AS topics
                LIMIT $limit
                """,
                interview_type=interview_type, limit=limit,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            logger.warning("Neo4j read timed out or failed (%s), returning empty", type(exc).__name__)
            return []

    async def vector_search_questions(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        interview_type: str = "",
    ) -> list[dict]:
        """
        Semantic search over question embeddings using Neo4j vector index.
        Returns the top_k most similar questions.
        """
        try:
            return await self._run_read_query(
                """
                CALL db.index.vector.queryNodes('question_embeddings', $top_k, $embedding)
                YIELD node, score
                WHERE ($interview_type = '' OR node.interview_type = $interview_type)
                OPTIONAL MATCH (node)-[:RELATES_TO]->(t:Topic)
                RETURN node.text AS text, node.interview_type AS interview_type,
                       node.difficulty AS difficulty, score,
                       collect(DISTINCT t.name) AS topics
                ORDER BY score DESC
                """,
                embedding=query_embedding,
                top_k=top_k,
                interview_type=interview_type,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            logger.warning("Neo4j vector search timed out (%s), returning empty", type(exc).__name__)
            return []

    async def vector_search_answers(
        self,
        query_embedding: list[float],
        top_k: int = 3,
    ) -> list[dict]:
        """
        Semantic search over example answer embeddings.
        Returns the top_k most relevant example answers.
        """
        try:
            return await self._run_read_query(
                """
                CALL db.index.vector.queryNodes('answer_embeddings', $top_k, $embedding)
                YIELD node, score
                OPTIONAL MATCH (node)-[:ANSWERS]->(q:Question)
                RETURN node.text AS answer_text, node.quality AS quality,
                       q.text AS question_text, score
                ORDER BY score DESC
                """,
                embedding=query_embedding,
                top_k=top_k,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            logger.warning("Neo4j answer search timed out (%s), returning empty", type(exc).__name__)
            return []

    async def get_example_answers(self, question_text: str, limit: int = 2) -> list[dict]:
        """Get example answers for a specific question via graph traversal."""
        try:
            return await self._run_read_query(
                """
                MATCH (a:ExampleAnswer)-[:ANSWERS]->(q:Question {text: $question_text})
                RETURN a.text AS answer_text, a.quality AS quality
                LIMIT $limit
                """,
                question_text=question_text, limit=limit,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            logger.warning("Neo4j example answers timed out (%s), returning empty", type(exc).__name__)
            return []


# Singleton instance
neo4j_manager = Neo4jManager()
