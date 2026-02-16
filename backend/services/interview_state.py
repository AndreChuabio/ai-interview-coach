"""
Mid-interview state tracker.
Maintains a running picture of how the interview is going so the agent
can adapt difficulty, track topic coverage, and respond to candidate signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.models.schemas import ToneSnapshot


@dataclass
class InterviewState:
    """Lightweight state that is updated after every turn and injected into prompts."""

    questions_asked: int = 0
    questions_remaining: int = 0
    topics_covered: list[str] = field(default_factory=list)
    topics_remaining: list[str] = field(default_factory=list)
    current_difficulty: str = "medium"
    tone_snapshots: list[ToneSnapshot] = field(default_factory=list)

    # Running averages (recomputed on each update)
    avg_wpm: float = 0.0
    total_fillers: int = 0
    avg_energy: float = 0.0
    tone_trend: str = "stable"

    def update_tone(self, snapshot: ToneSnapshot) -> None:
        """Incorporate a new tone snapshot and recompute running stats."""
        self.tone_snapshots.append(snapshot)
        n = len(self.tone_snapshots)

        wpms = [t.speaking_pace_wpm for t in self.tone_snapshots if t.speaking_pace_wpm > 0]
        self.avg_wpm = round(sum(wpms) / len(wpms), 1) if wpms else 0.0
        self.total_fillers = sum(t.filler_word_count for t in self.tone_snapshots)
        self.avg_energy = round(
            sum(t.energy_level for t in self.tone_snapshots) / n, 3
        )

        # Detect trend: compare first half to second half
        if n >= 2:
            mid = n // 2
            first_energy = sum(t.energy_level for t in self.tone_snapshots[:mid]) / mid
            second_energy = sum(t.energy_level for t in self.tone_snapshots[mid:]) / (n - mid)
            diff = second_energy - first_energy
            if diff > 0.05:
                self.tone_trend = "improving"
            elif diff < -0.05:
                self.tone_trend = "declining"
            else:
                self.tone_trend = "stable"

    def record_question(self, topic_hint: str = "") -> None:
        """Called after the agent asks a new question."""
        self.questions_asked += 1
        if self.questions_remaining > 0:
            self.questions_remaining -= 1
        if topic_hint and topic_hint not in self.topics_covered:
            self.topics_covered.append(topic_hint)
            if topic_hint in self.topics_remaining:
                self.topics_remaining.remove(topic_hint)

    def adjust_difficulty(self, answer_quality: str) -> None:
        """
        Adjust difficulty based on LLM-assessed answer quality.

        Args:
            answer_quality: One of 'strong', 'adequate', 'weak'.
        """
        levels = ["easy", "medium", "hard"]
        idx = levels.index(self.current_difficulty) if self.current_difficulty in levels else 1

        if answer_quality == "strong" and idx < 2:
            self.current_difficulty = levels[idx + 1]
        elif answer_quality == "weak" and idx > 0:
            self.current_difficulty = levels[idx - 1]

    def format_for_prompt(self) -> str:
        """Return a concise text block for injection into the LLM system prompt."""
        lines = [
            "--- Interview State ---",
            f"Progress: question {self.questions_asked} of {self.questions_asked + self.questions_remaining}",
            f"Current difficulty: {self.current_difficulty}",
        ]
        if self.topics_covered:
            lines.append(f"Topics covered so far: {', '.join(self.topics_covered)}")
        if self.topics_remaining:
            lines.append(f"Topics still to cover: {', '.join(self.topics_remaining[:4])}")
        if self.tone_trend != "stable":
            lines.append(f"Candidate energy trend: {self.tone_trend}")
        return "\n".join(lines)

    def format_tone_for_followup(self, latest: ToneSnapshot) -> str:
        """
        Format the latest tone snapshot as a context block for the follow-up prompt.
        Gives the LLM real-time signals about how the candidate is doing.
        """
        lines = [
            "[Candidate signals for this turn -- use to calibrate your next question]",
            f"- Speaking pace: {latest.speaking_pace_wpm} WPM (ideal: 130-160)",
            f"- Filler words this turn: {latest.filler_word_count}",
            f"- Energy level: {latest.energy_level} (0=flat, 1=animated)",
            f"- Silence ratio: {latest.silence_ratio} (high = long pauses)",
        ]
        if latest.energy_level < 0.3:
            lines.append("The candidate seems low-energy or nervous. Consider a slightly easier or more encouraging follow-up.")
        elif latest.filler_word_count >= 4:
            lines.append("High filler word usage suggests the candidate is uncertain. Probe gently.")
        elif latest.speaking_pace_wpm > 180:
            lines.append("The candidate is speaking very fast, possibly anxious. Allow them space.")
        elif latest.energy_level > 0.6 and latest.filler_word_count <= 1:
            lines.append("The candidate sounds confident. You can probe deeper or increase difficulty.")
        return "\n".join(lines)
