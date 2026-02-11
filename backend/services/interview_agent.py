"""
Interview conversation agent.
Manages the flow of an interview session using an LLM provider.
Generates opening questions, follow-ups, and closing statements.
"""

from __future__ import annotations

import logging

from backend.models.schemas import InterviewSession, InterviewType
from backend.prompts import behavioral, case_study, technical
from backend.providers.base import LLMProvider

logger = logging.getLogger(__name__)


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


class InterviewAgent:
    """
    Manages a single interview conversation using the configured LLM provider.
    Tracks conversation history and generates contextual follow-ups.
    """

    def __init__(self, llm: LLMProvider, session: InterviewSession):
        self._llm = llm
        self._session = session
        self._messages: list[dict[str, str]] = []
        self._prompts = _get_prompts(session.interview_type)

        company_clause = f" at {session.company}" if session.company else ""
        self._system_prompt = self._prompts.SYSTEM_PROMPT.format(
            role=session.role,
            company_clause=company_clause,
            difficulty=session.difficulty,
        )

    async def generate_opening(self) -> str:
        """Generate the first interview question."""
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
