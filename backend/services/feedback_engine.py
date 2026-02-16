"""
Feedback report engine.
Aggregates content analysis (LLM), communication metrics (tone), and body language (face)
into a comprehensive post-interview feedback report.
"""

from __future__ import annotations

import json
import logging

from backend.models.schemas import (
    BodyLanguageScore,
    CommunicationScore,
    ContentScore,
    FeedbackReport,
    InterviewSession,
    ToneSnapshot,
)
from backend.providers.base import LLMProvider
from backend.services.face_aggregator import FaceAggregator

logger = logging.getLogger(__name__)

CONTENT_ANALYSIS_PROMPT = """You are an expert interview coach. Analyze the following interview transcript
and provide a detailed content evaluation.

Interview type: {interview_type}
Role: {role}
Company: {company}

Transcript:
{transcript}
{rag_context}
Evaluate the candidate's responses and return JSON with this exact structure:
{{
  "overall_score": <float 0-10>,
  "relevance": <float 0-10>,
  "specificity": <float 0-10>,
  "structure": <float 0-10>,
  "strengths": ["strength1", "strength2", "strength3"],
  "improvements": ["improvement1", "improvement2", "improvement3"],
  "example_responses": ["A better response to question 1 would be: ...", "For question 2, consider: ..."]
}}

Scoring guide:
- 0-3: Poor (vague, off-topic, no structure)
- 4-5: Below average (some relevant points but lacking depth)
- 6-7: Good (clear, relevant, reasonably structured)
- 8-9: Very good (specific, well-structured, insightful)
- 10: Exceptional (compelling, unique, perfectly structured)

Be specific in strengths and improvements. Quote the candidate where helpful.
If reference answers are provided above, use them as a quality benchmark -- the candidate
does not need to match them exactly, but compare depth, specificity, and structure.
"""


class FeedbackEngine:
    """Generate comprehensive feedback reports from interview session data."""

    def __init__(self, llm: LLMProvider):
        self._llm = llm

    async def generate_report(self, session: InterviewSession) -> FeedbackReport:
        """
        Generate a complete feedback report for a finished interview session.

        Combines:
        1. Content analysis (LLM-powered evaluation of responses)
        2. Communication analysis (aggregated tone data)
        3. Body language analysis (aggregated face data)
        """
        # Build transcript text
        transcript_lines = []
        for entry in session.transcript:
            speaker = "Interviewer" if entry.role == "interviewer" else "Candidate"
            transcript_lines.append(f"{speaker}: {entry.text}")
        transcript_text = "\n\n".join(transcript_lines)

        # 1. Content analysis via LLM
        content = await self._analyze_content(session, transcript_text)

        # 2. Communication analysis from tone data
        communication = self._analyze_communication(session.tone_data)

        # 3. Body language analysis from face data
        face_agg = FaceAggregator()
        body_language = face_agg.aggregate(session.face_data)

        # 4. Compute overall score (weighted average)
        overall = round(
            content.overall_score * 0.5
            + communication.overall_score * 0.25
            + body_language.overall_score * 0.25,
            1,
        )

        # 5. Aggregate top-level feedback
        all_strengths = content.strengths + communication.strengths + body_language.strengths
        all_improvements = content.improvements + communication.improvements + body_language.improvements

        # Pick top 3 of each
        top_strengths = all_strengths[:3] if all_strengths else ["Completed the interview"]
        top_improvements = all_improvements[:3] if all_improvements else ["Continue practicing"]

        action_items = self._generate_action_items(content, communication, body_language)

        return FeedbackReport(
            session_id=session.session_id,
            interview_type=session.interview_type,
            role=session.role,
            company=session.company,
            overall_score=overall,
            content=content,
            communication=communication,
            body_language=body_language,
            top_strengths=top_strengths,
            top_improvements=top_improvements,
            action_items=action_items,
        )

    async def _analyze_content(
        self, session: InterviewSession, transcript: str
    ) -> ContentScore:
        """Use the LLM to evaluate response content quality, enriched with RAG examples."""
        # Retrieve example answers from knowledge graph for benchmarking
        rag_context_text = ""
        try:
            from backend.knowledge.retriever import rag_retriever
            # Use candidate responses as the query for semantic similarity
            candidate_texts = [
                e.text for e in session.transcript if e.role == "candidate"
            ]
            combined_text = " ".join(candidate_texts) if candidate_texts else ""
            if combined_text:
                feedback_ctx = await rag_retriever.get_feedback_context(
                    candidate_text=combined_text,
                    interview_type=session.interview_type.value,
                )
                rag_context_text = feedback_ctx.format_for_prompt()
                if rag_context_text:
                    logger.info("Feedback RAG context: %d chars", len(rag_context_text))
        except Exception:
            logger.warning("Could not retrieve RAG feedback context", exc_info=True)

        rag_block = ""
        if rag_context_text:
            rag_block = f"\n\n{rag_context_text}\n"

        prompt = CONTENT_ANALYSIS_PROMPT.format(
            interview_type=session.interview_type.value,
            role=session.role,
            company=session.company or "Not specified",
            transcript=transcript,
            rag_context=rag_block,
        )

        try:
            result = await self._llm.chat_json(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are an expert interview evaluator. Return valid JSON only.",
                temperature=0.3,
            )

            return ContentScore(
                overall_score=min(10, max(0, float(result.get("overall_score", 5)))),
                relevance=min(10, max(0, float(result.get("relevance", 5)))),
                specificity=min(10, max(0, float(result.get("specificity", 5)))),
                structure=min(10, max(0, float(result.get("structure", 5)))),
                strengths=result.get("strengths", [])[:5],
                improvements=result.get("improvements", [])[:5],
                example_responses=result.get("example_responses", [])[:3],
            )
        except Exception:
            logger.exception("Content analysis failed, returning defaults")
            return ContentScore(
                overall_score=5.0,
                relevance=5.0,
                specificity=5.0,
                structure=5.0,
                strengths=["Completed all questions"],
                improvements=["Content analysis unavailable -- try again"],
            )

    def _analyze_communication(self, tone_data: list[ToneSnapshot]) -> CommunicationScore:
        """Aggregate tone snapshots into a communication score."""
        if not tone_data:
            return CommunicationScore(
                overall_score=5.0,
                pace_score=5.0,
                clarity_score=5.0,
                filler_score=5.0,
                confidence_score=5.0,
                strengths=["No audio data available for analysis"],
                improvements=["Enable microphone for communication feedback"],
            )

        # Aggregate metrics across all turns
        wpms = [t.speaking_pace_wpm for t in tone_data if t.speaking_pace_wpm > 0]
        avg_wpm = sum(wpms) / len(wpms) if wpms else 0.0
        total_fillers = sum(t.filler_word_count for t in tone_data)
        avg_energy = sum(t.energy_level for t in tone_data) / len(tone_data)
        avg_silence = sum(t.silence_ratio for t in tone_data) / len(tone_data)

        # Pace scoring (ideal: 130-160 WPM)
        if 130 <= avg_wpm <= 160:
            pace_score = 9.0
        elif 110 <= avg_wpm <= 180:
            pace_score = 7.0
        elif avg_wpm > 0:
            pace_score = 4.0
        else:
            pace_score = 5.0

        # Filler scoring
        total_duration = sum(t.duration_sec for t in tone_data)
        fillers_per_min = (total_fillers / total_duration * 60) if total_duration > 0 else 0
        if fillers_per_min <= 2:
            filler_score = 9.0
        elif fillers_per_min <= 5:
            filler_score = 7.0
        elif fillers_per_min <= 10:
            filler_score = 5.0
        else:
            filler_score = 3.0

        # Clarity scoring (based on energy + silence ratio)
        clarity_score = min(10.0, max(0.0, (avg_energy * 10 + (1 - avg_silence) * 5)))

        # Confidence scoring (based on pitch variation and energy)
        avg_pitch_var = sum(t.pitch_variation for t in tone_data) / len(tone_data)
        confidence_raw = avg_energy * 5 + min(1.0, avg_pitch_var / 100) * 5
        confidence_score = min(10.0, max(0.0, confidence_raw))

        overall = round(
            pace_score * 0.25 + filler_score * 0.25 + clarity_score * 0.25 + confidence_score * 0.25,
            1,
        )

        strengths: list[str] = []
        improvements: list[str] = []

        if pace_score >= 7:
            strengths.append(f"Good speaking pace ({avg_wpm:.0f} WPM)")
        else:
            speed = "fast" if avg_wpm > 160 else "slow"
            improvements.append(
                f"Speaking pace was too {speed} ({avg_wpm:.0f} WPM). Aim for 130-160 WPM."
            )

        if filler_score >= 7:
            strengths.append(f"Minimal filler words ({total_fillers} total)")
        else:
            improvements.append(
                f"Used {total_fillers} filler words ({fillers_per_min:.1f}/min). "
                "Practice pausing instead of using um/uh/like."
            )

        if confidence_score >= 7:
            strengths.append("Voice projected confidence and energy")
        elif avg_energy < 0.3:
            improvements.append("Voice energy was low. Speak with more projection and enthusiasm.")

        # Temporal trend analysis: compare first half vs second half
        if len(tone_data) >= 2:
            mid = len(tone_data) // 2
            first_half = tone_data[:mid]
            second_half = tone_data[mid:]

            first_energy = sum(t.energy_level for t in first_half) / len(first_half)
            second_energy = sum(t.energy_level for t in second_half) / len(second_half)
            energy_diff = second_energy - first_energy

            first_fillers = sum(t.filler_word_count for t in first_half)
            second_fillers = sum(t.filler_word_count for t in second_half)

            if energy_diff > 0.08:
                strengths.append(
                    "Your confidence and energy grew over the course of the interview"
                )
            elif energy_diff < -0.08:
                improvements.append(
                    "Your energy dropped toward the end of the interview. "
                    "Practice maintaining engagement throughout longer sessions."
                )

            if second_fillers > first_fillers * 1.5 and first_fillers > 0:
                improvements.append(
                    "Filler word usage increased in the second half, suggesting fatigue. "
                    "Practice sustaining clarity under pressure."
                )
            elif first_fillers > second_fillers * 1.5 and second_fillers >= 0:
                strengths.append(
                    "You reduced filler words as the interview progressed"
                )

        return CommunicationScore(
            overall_score=overall,
            pace_score=round(pace_score, 1),
            clarity_score=round(clarity_score, 1),
            filler_score=round(filler_score, 1),
            confidence_score=round(confidence_score, 1),
            avg_wpm=round(avg_wpm, 1),
            total_fillers=total_fillers,
            strengths=strengths or ["Communication was adequate"],
            improvements=improvements or ["Continue refining your delivery"],
        )

    def _generate_action_items(
        self,
        content: ContentScore,
        communication: CommunicationScore,
        body_language: BodyLanguageScore,
    ) -> list[str]:
        """Generate specific, actionable improvement recommendations."""
        items: list[str] = []

        if content.overall_score < 6:
            items.append(
                "Practice the STAR method: Structure every answer with Situation, Task, Action, Result."
            )
        if content.specificity < 6:
            items.append(
                "Add specific metrics and outcomes to your answers (numbers, percentages, timelines)."
            )

        if communication.pace_score < 6:
            items.append(
                "Record yourself answering questions and time your responses. Target 130-160 WPM."
            )
        if communication.filler_score < 6:
            items.append(
                "Practice replacing filler words with pauses. Silence is more powerful than 'um'."
            )

        if body_language.eye_contact_pct < 60:
            items.append(
                "Place a small sticker near your webcam as a focal point to improve eye contact."
            )
        if body_language.fidgeting_score > 5:
            items.append(
                "Practice sitting still with your hands folded. Minimize head and body movement."
            )

        if not items:
            items.append("Great performance overall. Keep practicing to maintain your edge.")

        return items[:5]
