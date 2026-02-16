"""
Face data aggregator.
Processes batched facial expression snapshots from the frontend (MediaPipe)
and computes aggregate metrics for the feedback report.
"""

from __future__ import annotations

import logging
from collections import Counter

from backend.models.schemas import BodyLanguageScore, Emotion, FaceSnapshot

logger = logging.getLogger(__name__)


class FaceAggregator:
    """Aggregate facial expression data into body language metrics."""

    def aggregate(self, snapshots: list[FaceSnapshot]) -> BodyLanguageScore:
        """
        Compute body language metrics from facial expression snapshots.

        Args:
            snapshots: List of FaceSnapshot objects captured during the interview.

        Returns:
            BodyLanguageScore with eye contact, emotion distribution, and fidgeting metrics.
        """
        if not snapshots:
            return BodyLanguageScore(
                overall_score=5.0,
                eye_contact_pct=0.0,
                emotion_distribution={},
                fidgeting_score=5.0,
                strengths=["No facial data captured"],
                improvements=["Enable webcam for body language analysis"],
            )

        total = len(snapshots)

        # Eye contact percentage
        eye_contact_count = sum(1 for s in snapshots if s.eye_contact)
        eye_contact_pct = (eye_contact_count / total) * 100

        # Emotion distribution
        emotion_counts: Counter = Counter()
        for s in snapshots:
            emotion_counts[s.dominant_emotion.value] += 1
        emotion_distribution = {
            emotion: round(count / total * 100, 1)
            for emotion, count in emotion_counts.most_common()
        }

        # Fidgeting score based on head movement variance
        head_pitches = [s.head_pitch for s in snapshots]
        head_yaws = [s.head_yaw for s in snapshots]

        import numpy as np

        pitch_var = float(np.std(head_pitches)) if head_pitches else 0.0
        yaw_var = float(np.std(head_yaws)) if head_yaws else 0.0
        # Normalize to 0-10 scale (lower variance = lower fidgeting = better)
        fidgeting_raw = (pitch_var + yaw_var) * 50
        fidgeting_score = min(10.0, round(fidgeting_raw, 1))

        # Compute overall score
        eye_score = min(10.0, eye_contact_pct / 10)
        confidence_pct = emotion_distribution.get("confident", 0) + emotion_distribution.get("happy", 0)
        nervous_pct = emotion_distribution.get("nervous", 0)
        emotion_score = min(10.0, max(0.0, 5.0 + (confidence_pct - nervous_pct) / 20))
        fidget_score_inv = max(0.0, 10.0 - fidgeting_score)

        overall = round((eye_score * 0.4 + emotion_score * 0.3 + fidget_score_inv * 0.3), 1)

        # Generate strengths and improvements
        strengths: list[str] = []
        improvements: list[str] = []

        if eye_contact_pct >= 70:
            strengths.append(f"Strong eye contact ({eye_contact_pct:.0f}% of the time)")
        elif eye_contact_pct < 50:
            improvements.append(
                f"Eye contact was low ({eye_contact_pct:.0f}%). Practice looking at the camera."
            )

        if confidence_pct > 40:
            strengths.append("Appeared confident and positive throughout")
        if nervous_pct > 30:
            improvements.append(
                "Appeared nervous for a significant portion. Practice deep breathing before interviews."
            )

        if fidgeting_score < 3:
            strengths.append("Minimal head movement -- appeared calm and composed")
        elif fidgeting_score > 6:
            improvements.append(
                "Significant head movement detected. Try to keep your head still and centered."
            )

        # Temporal trend analysis: compare first half vs second half
        if total >= 4:
            mid = total // 2
            first_half = snapshots[:mid]
            second_half = snapshots[mid:]

            first_eye = sum(1 for s in first_half if s.eye_contact) / len(first_half) * 100
            second_eye = sum(1 for s in second_half if s.eye_contact) / len(second_half) * 100
            eye_diff = second_eye - first_eye

            if eye_diff > 10:
                strengths.append(
                    "Eye contact improved over the course of the interview"
                )
            elif eye_diff < -10:
                improvements.append(
                    "Eye contact decreased toward the end. "
                    "Practice maintaining camera focus throughout longer sessions."
                )

            # Fidgeting trend
            first_pitches = [s.head_pitch for s in first_half]
            second_pitches = [s.head_pitch for s in second_half]
            first_yaws = [s.head_yaw for s in first_half]
            second_yaws = [s.head_yaw for s in second_half]

            first_fidget = (float(np.std(first_pitches)) + float(np.std(first_yaws))) * 50
            second_fidget = (float(np.std(second_pitches)) + float(np.std(second_yaws))) * 50

            if second_fidget > first_fidget * 1.5 and first_fidget > 1:
                improvements.append(
                    "Head movement increased in the second half, suggesting restlessness. "
                    "Practice staying composed during longer interviews."
                )
            elif first_fidget > second_fidget * 1.5 and second_fidget >= 0:
                strengths.append(
                    "You became noticeably calmer and more composed as the interview progressed"
                )

        return BodyLanguageScore(
            overall_score=overall,
            eye_contact_pct=round(eye_contact_pct, 1),
            emotion_distribution=emotion_distribution,
            fidgeting_score=fidgeting_score,
            strengths=strengths or ["Body language was adequate"],
            improvements=improvements or ["Continue practicing in front of a camera"],
        )
