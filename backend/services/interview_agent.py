"""
Interview conversation agent.
Manages the flow of an interview session using an LLM provider.
Generates opening questions, follow-ups, and closing statements.
Uses curated question topics, a static question bank, and a Neo4j
knowledge graph (RAG) for grounded, company-specific suggestions.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path

from backend.models.schemas import InterviewSession, InterviewType
from backend.prompts import behavioral, case_study, technical
from backend.providers.base import LLMProvider

logger = logging.getLogger(__name__)

# Load static question bank once at import time
_QUESTION_BANK: dict = {}
_BANK_PATH = Path(__file__).resolve().parent.parent / "data" / "question_bank.json"
if _BANK_PATH.exists():
    with open(_BANK_PATH) as f:
        _QUESTION_BANK = json.load(f)
    logger.info("Loaded question bank from %s", _BANK_PATH)


def _get_prompts(interview_type: InterviewType):
    """Return the correct prompt module for the interview type."""
    match interview_type:
        case InterviewType.behavioral:
            return behavioral
        case InterviewType.technical:
            return technical
        case InterviewType.case_study:
            return case_study
        case _:
            return behavioral


def _get_topic_suggestions(interview_type: InterviewType, role: str) -> str:
    """
    Build a topic suggestion block from the curated question topics.
    Selects a random subset so the LLM has variety across sessions.
    """
    prompts_mod = _get_prompts(interview_type)

    topics: list[str] = []
    if interview_type == InterviewType.case_study:
        raw = getattr(prompts_mod, "CASE_TOPICS", [])
        topics = list(raw)
    elif interview_type == InterviewType.technical:
        raw = getattr(prompts_mod, "QUESTION_TOPICS", {})
        if isinstance(raw, dict):
            # Pick the most relevant sub-category based on role
            role_lower = role.lower()
            if any(kw in role_lower for kw in ("data", "ml", "machine learning", "analyst")):
                topics = list(raw.get("data_science", []))
            elif any(kw in role_lower for kw in ("software", "backend", "frontend", "full")):
                topics = list(raw.get("software_engineering", []))
            else:
                # Mix both
                for v in raw.values():
                    topics.extend(v)
        else:
            topics = list(raw)
    else:
        raw = getattr(prompts_mod, "QUESTION_TOPICS", [])
        topics = list(raw)

    if not topics:
        return ""

    # Select a random subset of 5-6 topics for this session
    sample_size = min(6, len(topics))
    selected = random.sample(topics, sample_size)
    topic_list = "\n".join(f"- {t}" for t in selected)
    return f"\nSuggested topics to cover during this interview:\n{topic_list}\n"


def _get_sample_questions(interview_type: InterviewType, role: str) -> str:
    """
    Pull 2-3 sample questions from the question bank to guide the LLM.
    The LLM should use these as inspiration, not read them verbatim.
    """
    type_key = interview_type.value  # "behavioral", "technical", "case_study"
    bank = _QUESTION_BANK.get(type_key, {})
    if not bank:
        return ""

    all_questions: list[str] = []
    if isinstance(bank, dict):
        # For technical: pick role-relevant category
        role_lower = role.lower()
        if type_key == "technical":
            if any(kw in role_lower for kw in ("data", "ml", "machine learning", "analyst")):
                all_questions = list(bank.get("data_science", []))
                all_questions.extend(bank.get("sql", []))
            elif any(kw in role_lower for kw in ("software", "backend", "frontend", "full")):
                all_questions = list(bank.get("software_engineering", []))
            else:
                for v in bank.values():
                    all_questions.extend(v)
        else:
            for v in bank.values():
                all_questions.extend(v)

    if not all_questions:
        return ""

    sample_size = min(3, len(all_questions))
    selected = random.sample(all_questions, sample_size)
    q_list = "\n".join(f"- {q}" for q in selected)
    return (
        f"\nHere are example questions for reference (adapt these, do not read verbatim):\n"
        f"{q_list}\n"
    )


class InterviewAgent:
    """
    Manages a single interview conversation using the configured LLM provider.
    Tracks conversation history and generates contextual follow-ups.

    When Neo4j is available, enriches the system prompt with RAG context:
    company-specific questions, role-targeted examples, and semantic matches.
    Falls back gracefully to static question bank when Neo4j is unavailable.
    """

    def __init__(self, llm: LLMProvider, session: InterviewSession):
        self._llm = llm
        self._session = session
        self._messages: list[dict[str, str]] = []
        self._prompts = _get_prompts(session.interview_type)
        self._rag_context_text: str = ""

        company_clause = f" at {session.company}" if session.company else ""
        topic_suggestions = _get_topic_suggestions(session.interview_type, session.role)
        sample_questions = _get_sample_questions(session.interview_type, session.role)

        self._base_system_prompt = self._prompts.SYSTEM_PROMPT.format(
            role=session.role,
            company_clause=company_clause,
            difficulty=session.difficulty,
        ) + topic_suggestions + sample_questions

        # Full prompt is assembled in generate_opening after RAG retrieval
        self._system_prompt = self._base_system_prompt

    async def _enrich_with_rag(self) -> None:
        """Fetch RAG context from Neo4j and append to system prompt."""
        try:
            from backend.knowledge.retriever import rag_retriever

            ctx = await rag_retriever.get_interview_context(
                interview_type=self._session.interview_type.value,
                role=self._session.role,
                company=self._session.company,
                query_text=f"{self._session.interview_type.value} interview for {self._session.role}",
            )
            self._rag_context_text = ctx.format_for_prompt()
            if self._rag_context_text:
                self._system_prompt = (
                    self._base_system_prompt
                    + "\n\n--- Knowledge Graph Context ---\n"
                    + self._rag_context_text
                )
                logger.info("RAG context injected (%d chars)", len(self._rag_context_text))
            else:
                logger.info("RAG returned empty context, using static prompt only")
        except Exception:
            logger.warning("RAG enrichment failed, continuing with static prompt", exc_info=True)

    async def generate_opening(self) -> str:
        """Generate the first interview question, enriched with RAG context."""
        # Enrich system prompt with knowledge graph context
        await self._enrich_with_rag()

        company_clause = f" at {self._session.company}" if self._session.company else ""
        user_msg = self._prompts.OPENING_TEMPLATE.format(
            role=self._session.role,
            company_clause=company_clause,
            difficulty=self._session.difficulty,
        )
        self._messages.append({"role": "user", "content": user_msg})

        response = await self._llm.chat(
            messages=self._messages,
            system_prompt=self._system_prompt,
            temperature=0.7,
        )
        self._messages.append({"role": "assistant", "content": response})
        logger.info("Opening question generated (%d chars)", len(response))
        return response

    async def generate_followup(self, candidate_response: str) -> str:
        """Generate a follow-up question based on the candidate's response."""
        user_msg = self._prompts.FOLLOWUP_TEMPLATE.format(
            candidate_response=candidate_response,
        )
        self._messages.append({"role": "user", "content": user_msg})

        response = await self._llm.chat(
            messages=self._messages,
            system_prompt=self._system_prompt,
            temperature=0.7,
        )
        self._messages.append({"role": "assistant", "content": response})
        logger.info("Follow-up generated (%d chars)", len(response))
        return response

    async def generate_closing(self) -> str:
        """Generate a closing statement to end the interview."""
        user_msg = self._prompts.CLOSING_TEMPLATE
        self._messages.append({"role": "user", "content": user_msg})

        response = await self._llm.chat(
            messages=self._messages,
            system_prompt=self._system_prompt,
            temperature=0.5,
        )
        self._messages.append({"role": "assistant", "content": response})
        logger.info("Closing statement generated")
        return response

    def get_full_transcript_text(self) -> str:
        """Return the full conversation as a formatted string for feedback analysis."""
        lines: list[str] = []
        for entry in self._session.transcript:
            speaker = "Interviewer" if entry.role == "interviewer" else "Candidate"
            lines.append(f"{speaker}: {entry.text}")
        return "\n\n".join(lines)
