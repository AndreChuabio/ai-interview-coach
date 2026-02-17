"""
RAG retriever combining Neo4j graph traversal with vector similarity search.

Provides two main capabilities:
  1. get_interview_context() -- retrieves relevant questions and company context
     for the interview agent to use when generating questions.
  2. get_feedback_context() -- retrieves example answers similar to the candidate's
     response for the feedback engine to benchmark against.

Falls back gracefully when Neo4j is unavailable (returns empty context).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from backend.knowledge.embedder import get_embedder
from backend.knowledge.graph import neo4j_manager

logger = logging.getLogger(__name__)


@dataclass
class InterviewContext:
    """Context retrieved from the knowledge graph for interview generation."""
    graph_questions: list[dict] = field(default_factory=list)
    vector_questions: list[dict] = field(default_factory=list)
    company_info: str = ""

    def format_for_prompt(self) -> str:
        """Format the retrieved context as a text block for LLM injection."""
        sections: list[str] = []

        if self.company_info:
            sections.append(f"Company context:\n{self.company_info}")

        # Deduplicate questions across graph and vector results
        seen_texts: set[str] = set()
        all_questions: list[dict] = []

        for q in self.graph_questions:
            text = q.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                all_questions.append(q)

        for q in self.vector_questions:
            text = q.get("text", "")
            if text and text not in seen_texts:
                seen_texts.add(text)
                all_questions.append(q)

        if all_questions:
            lines = []
            for q in all_questions[:8]:
                topic_str = ""
                topics = q.get("topics", [])
                if topics:
                    topic_str = f" (topics: {', '.join(topics)})"
                lines.append(f"- {q['text']}{topic_str}")
            sections.append(
                "Relevant questions from our knowledge base (adapt these, "
                "do not read verbatim):\n" + "\n".join(lines)
            )

        if not sections:
            return ""
        return "\n\n".join(sections)


@dataclass
class FeedbackContext:
    """Context retrieved from the knowledge graph for feedback generation."""
    example_answers: list[dict] = field(default_factory=list)
    similar_questions: list[dict] = field(default_factory=list)

    def format_for_prompt(self) -> str:
        """Format example answers as a benchmark block for the feedback LLM."""
        if not self.example_answers:
            return ""

        lines = []
        for ans in self.example_answers[:3]:
            q_text = ans.get("question_text", "Related question")
            a_text = ans.get("answer_text", "")
            quality = ans.get("quality", "strong")
            lines.append(f"Question: {q_text}\nExample ({quality} answer): {a_text}")

        return (
            "Reference answers from our knowledge base for benchmarking "
            "(use as quality baseline, not exact match):\n\n"
            + "\n\n---\n\n".join(lines)
        )


class RAGRetriever:
    """
    Hybrid retriever that combines graph traversal and vector similarity.

    Graph traversal exploits the structured relationships (Company -> Question,
    Role -> Question, Topic -> Question) for precise context.

    Vector similarity finds semantically related questions and answers even
    when there is no direct graph relationship.
    """

    async def get_interview_context(
        self,
        interview_type: str,
        role: str = "",
        company: str = "",
        topic: str = "",
        query_text: str = "",
    ) -> InterviewContext:
        """
        Retrieve context for the interview agent.

        Args:
            interview_type: behavioral, technical, or case_study.
            role: Target job role.
            company: Target company (optional).
            topic: Single topic for quick practice (optional).
            query_text: Optional text query for semantic search.

        Returns:
            InterviewContext with graph and vector search results.
        """
        ctx = InterviewContext()

        if not neo4j_manager.is_configured():
            logger.debug("Neo4j not configured, returning empty context")
            return ctx

        try:
            # 1. Graph traversal: get questions linked to topic, company/role/type
            ctx.graph_questions = await neo4j_manager.get_questions_for_context(
                interview_type=interview_type,
                role=role,
                company=company,
                topic=topic,
                limit=5,
            )
            logger.info(
                "Graph retrieval: %d questions for type=%s role=%s company=%s topic=%s",
                len(ctx.graph_questions), interview_type, role, company, topic or "(any)",
            )

            # 2. Vector similarity: find semantically similar questions.
            #    Skip if the embedding model is still loading (avoids 30-60s
            #    block on the first request on constrained hosts).
            if query_text:
                embedder = get_embedder()
                if embedder.is_ready:
                    query_embedding = embedder.encode_single(query_text)
                    ctx.vector_questions = await neo4j_manager.vector_search_questions(
                        query_embedding=query_embedding,
                        top_k=5,
                        interview_type=interview_type,
                    )
                    logger.info(
                        "Vector retrieval: %d questions for query '%s'",
                        len(ctx.vector_questions), query_text[:60],
                    )
                else:
                    # Trigger background load so the model is ready for the
                    # next request.  This request proceeds with graph-only context.
                    embedder.start_background_load()
                    logger.info(
                        "Embedder not ready, skipping vector search (loading in background)"
                    )

            # 3. Company context string
            if company:
                ctx.company_info = (
                    f"The candidate is interviewing at {company}. "
                    "Tailor questions to reflect this company's culture, "
                    "products, and typical interview style."
                )

        except Exception:
            logger.exception("RAG retrieval failed, returning partial context")

        return ctx

    async def get_feedback_context(
        self,
        candidate_text: str,
        interview_type: str = "",
    ) -> FeedbackContext:
        """
        Retrieve example answers similar to what the candidate said.

        Used by the feedback engine to benchmark the candidate's response
        quality against known strong answers.

        Args:
            candidate_text: The candidate's transcribed response.
            interview_type: Optional filter by interview type.

        Returns:
            FeedbackContext with relevant example answers.
        """
        ctx = FeedbackContext()

        if not neo4j_manager.is_configured():
            return ctx

        try:
            embedder = get_embedder()
            if not embedder.is_ready:
                embedder.start_background_load()
                logger.info("Embedder not ready for feedback retrieval, skipping")
                return ctx

            query_embedding = embedder.encode_single(candidate_text)

            # Find similar example answers
            ctx.example_answers = await neo4j_manager.vector_search_answers(
                query_embedding=query_embedding,
                top_k=3,
            )

            # Also find similar questions for broader context
            ctx.similar_questions = await neo4j_manager.vector_search_questions(
                query_embedding=query_embedding,
                top_k=3,
                interview_type=interview_type,
            )

            logger.info(
                "Feedback retrieval: %d example answers, %d similar questions",
                len(ctx.example_answers), len(ctx.similar_questions),
            )

        except Exception:
            logger.exception("Feedback RAG retrieval failed, returning empty context")

        return ctx


# Singleton instance
rag_retriever = RAGRetriever()
