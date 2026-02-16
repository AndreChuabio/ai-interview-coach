"""
Audio tone analyzer using librosa.

Extracts speaking pace, filler words, pitch (average, variation, range,
intonation patterns), energy, silence, and voice quality metrics (jitter,
shimmer). Runs entirely locally -- no API cost.
"""

from __future__ import annotations

import logging
import re
import tempfile

import numpy as np

from backend.models.schemas import ToneSnapshot

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Filler word detection
# ---------------------------------------------------------------------------
# Single-word fillers matched with word boundaries.
SINGLE_WORD_FILLERS = {
    "um", "uh", "uhm", "hmm", "basically", "actually",
    "literally", "right", "well",
}

# Multi-word fillers matched as literal phrases with word boundaries.
MULTI_WORD_FILLERS = {
    "you know", "i mean", "kind of", "sort of",
}

# Context-dependent fillers: negative lookahead excludes common non-filler
# usages (e.g. "I would like to", "so that we can").
CONTEXT_FILLER_PATTERNS: dict[str, re.Pattern[str]] = {
    "like": re.compile(
        r"\blike\b(?!\s+(?:to|a|the|that|this|it|an|my|his|her|their|our|your)\b)",
        re.IGNORECASE,
    ),
    "so": re.compile(
        r"\bso\b(?!\s+(?:that|much|many|far|long|few)\b)",
        re.IGNORECASE,
    ),
}

# Pitch coefficient of variation threshold below which delivery is "monotone"
_MONOTONE_CV_THRESHOLD = 0.08


def _count_fillers(transcript: str) -> tuple[int, list[str]]:
    """Return (total_count, list_of_detected_fillers) using word-boundary matching.

    Args:
        transcript: Transcribed candidate speech.

    Returns:
        Tuple of total filler count and a flat list of each detected filler.
    """
    if not transcript:
        return 0, []

    total = 0
    found: list[str] = []

    # Single-word fillers
    for filler in SINGLE_WORD_FILLERS:
        pattern = re.compile(rf"\b{re.escape(filler)}\b", re.IGNORECASE)
        matches = pattern.findall(transcript)
        if matches:
            total += len(matches)
            found.extend([filler] * len(matches))

    # Multi-word fillers
    for filler in MULTI_WORD_FILLERS:
        pattern = re.compile(rf"\b{re.escape(filler)}\b", re.IGNORECASE)
        matches = pattern.findall(transcript)
        if matches:
            total += len(matches)
            found.extend([filler] * len(matches))

    # Context-aware fillers
    for label, pattern in CONTEXT_FILLER_PATTERNS.items():
        matches = pattern.findall(transcript)
        if matches:
            total += len(matches)
            found.extend([label] * len(matches))

    return total, found


# ---------------------------------------------------------------------------
# Voice quality helpers
# ---------------------------------------------------------------------------

def _compute_jitter(pitch_values: list[float]) -> float:
    """Relative jitter: average absolute pitch-to-pitch difference divided by mean pitch.

    A higher value indicates more vocal instability (often associated with nervousness).

    Args:
        pitch_values: Sequential fundamental frequency values in Hz.

    Returns:
        Relative jitter (dimensionless, 0-1 typical range).
    """
    if len(pitch_values) < 2:
        return 0.0
    mean_pitch = sum(pitch_values) / len(pitch_values)
    if mean_pitch == 0:
        return 0.0
    diffs = [abs(pitch_values[i + 1] - pitch_values[i]) for i in range(len(pitch_values) - 1)]
    return sum(diffs) / len(diffs) / mean_pitch


def _compute_shimmer(rms_values: np.ndarray) -> float:
    """Relative shimmer: average absolute amplitude-to-amplitude difference divided by mean.

    Similar to jitter but for amplitude. High shimmer can indicate breathy or
    strained vocal quality.

    Args:
        rms_values: Sequential RMS energy values.

    Returns:
        Relative shimmer (dimensionless).
    """
    if len(rms_values) < 2:
        return 0.0
    mean_rms = float(np.mean(rms_values))
    if mean_rms == 0:
        return 0.0
    diffs = np.abs(np.diff(rms_values))
    return float(np.mean(diffs) / mean_rms)


def _analyze_prosody(
    pitch_values: list[float],
    speech_intervals: np.ndarray,
    pitches_matrix: np.ndarray,
    magnitudes_matrix: np.ndarray,
    sr: int,
    hop_length: int,
) -> tuple[float, float, bool]:
    """Analyze intonation patterns from pitch contour.

    Args:
        pitch_values: Flat list of all non-zero pitch values for summary stats.
        speech_intervals: Array of (start_sample, end_sample) from librosa.effects.split.
        pitches_matrix: Pitch matrix from librosa.piptrack.
        magnitudes_matrix: Magnitude matrix from librosa.piptrack.
        sr: Sample rate.
        hop_length: Hop length used by piptrack (default 512).

    Returns:
        Tuple of (pitch_range_hz, rising_intonation_ratio, monotone_flag).
    """
    if len(pitch_values) < 2:
        return 0.0, 0.0, False

    pitch_range_hz = float(max(pitch_values) - min(pitch_values))
    mean_pitch = float(np.mean(pitch_values))
    cv = float(np.std(pitch_values)) / mean_pitch if mean_pitch > 0 else 0.0
    monotone_flag = cv < _MONOTONE_CV_THRESHOLD

    # Rising intonation: for each speech segment, compare pitch in the
    # last quarter vs the first quarter. If pitch rises, count it.
    rising_count = 0
    total_segments = 0

    for start_sample, end_sample in speech_intervals:
        start_frame = start_sample // hop_length
        end_frame = end_sample // hop_length
        if end_frame - start_frame < 4:
            continue

        total_segments += 1
        quarter = max(1, (end_frame - start_frame) // 4)

        def _segment_avg_pitch(f_start: int, f_end: int) -> float:
            vals = []
            for t in range(max(0, f_start), min(pitches_matrix.shape[1], f_end)):
                idx = magnitudes_matrix[:, t].argmax()
                p = pitches_matrix[idx, t]
                if p > 0:
                    vals.append(float(p))
            return sum(vals) / len(vals) if vals else 0.0

        first_q = _segment_avg_pitch(start_frame, start_frame + quarter)
        last_q = _segment_avg_pitch(end_frame - quarter, end_frame)

        if first_q > 0 and last_q > first_q * 1.05:
            rising_count += 1

    rising_ratio = rising_count / total_segments if total_segments > 0 else 0.0

    return pitch_range_hz, rising_ratio, monotone_flag


# ---------------------------------------------------------------------------
# Main analyzer
# ---------------------------------------------------------------------------

class ToneAnalyzer:
    """Analyze audio characteristics for communication feedback."""

    def analyze(self, audio_bytes: bytes, transcript: str = "") -> ToneSnapshot:
        """Analyze audio bytes and return a ToneSnapshot.

        Args:
            audio_bytes: Raw audio data (WAV or compatible format).
            transcript: Optional transcript text for filler word counting.

        Returns:
            ToneSnapshot with pace, pitch, energy, filler, prosody,
            and voice quality metrics.
        """
        try:
            import librosa

            # Write to temp file for librosa to load
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                y, sr = librosa.load(tmp.name, sr=None)

            duration_sec = len(y) / sr if sr > 0 else 0.0
            hop_length = 512

            # ---------------------------------------------------------------
            # Pitch analysis (fundamental frequency)
            # ---------------------------------------------------------------
            pitches, magnitudes = librosa.piptrack(
                y=y, sr=sr, hop_length=hop_length,
            )
            pitch_values: list[float] = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(float(pitch))

            avg_pitch = float(np.mean(pitch_values)) if pitch_values else 0.0
            pitch_var = float(np.std(pitch_values)) if pitch_values else 0.0

            # ---------------------------------------------------------------
            # Energy analysis (RMS) with adaptive normalization
            # ---------------------------------------------------------------
            rms = librosa.feature.rms(y=y)[0]
            avg_energy = float(np.mean(rms))
            # Use the 95th percentile of RMS as normalization reference
            # so the metric adapts to different mics and environments.
            p95 = float(np.percentile(rms, 95)) if len(rms) > 0 else 0.1
            normalized_energy = (
                min(1.0, avg_energy / max(p95, 0.001)) if avg_energy > 0 else 0.0
            )

            # ---------------------------------------------------------------
            # Silence detection
            # ---------------------------------------------------------------
            intervals = librosa.effects.split(y, top_db=30)
            if len(intervals) > 0:
                speech_frames = sum(end - start for start, end in intervals)
                silence_ratio = 1.0 - (speech_frames / len(y)) if len(y) > 0 else 0.0
            else:
                silence_ratio = 1.0

            # ---------------------------------------------------------------
            # Prosody analysis (intonation patterns)
            # ---------------------------------------------------------------
            pitch_range_hz, rising_intonation_ratio, monotone_flag = (
                _analyze_prosody(
                    pitch_values, intervals, pitches, magnitudes, sr, hop_length,
                )
            )

            # ---------------------------------------------------------------
            # Voice quality metrics
            # ---------------------------------------------------------------
            jitter = _compute_jitter(pitch_values)
            shimmer = _compute_shimmer(rms)

            # ---------------------------------------------------------------
            # Filler word analysis (word-boundary aware)
            # ---------------------------------------------------------------
            filler_count, filler_list = _count_fillers(transcript)

            # ---------------------------------------------------------------
            # Speaking pace (words per minute)
            # ---------------------------------------------------------------
            word_count = len(transcript.split()) if transcript else 0
            wpm = (word_count / duration_sec * 60) if duration_sec > 0 else 0.0

            return ToneSnapshot(
                speaking_pace_wpm=round(wpm, 1),
                filler_word_count=filler_count,
                filler_words=filler_list,
                avg_pitch_hz=round(avg_pitch, 1),
                pitch_variation=round(pitch_var, 1),
                pitch_range_hz=round(pitch_range_hz, 1),
                rising_intonation_ratio=round(rising_intonation_ratio, 3),
                monotone_flag=monotone_flag,
                jitter=round(jitter, 4),
                shimmer=round(shimmer, 4),
                energy_level=round(normalized_energy, 3),
                silence_ratio=round(max(0.0, silence_ratio), 3),
                duration_sec=round(duration_sec, 2),
            )

        except ImportError:
            logger.warning("librosa not installed -- returning empty ToneSnapshot")
            return ToneSnapshot()
        except Exception:
            logger.exception("Tone analysis failed")
            return ToneSnapshot()
