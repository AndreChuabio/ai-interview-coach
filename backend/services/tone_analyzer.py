"""
Audio tone analyzer using librosa.
Extracts speaking pace, filler words, pitch, energy, and silence patterns.
Runs entirely locally -- no API cost.
"""

from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path

import numpy as np

from backend.models.schemas import ToneSnapshot

logger = logging.getLogger(__name__)

# Common filler words to detect in transcribed text
FILLER_WORDS = {
    "um", "uh", "uhm", "hmm", "like", "you know", "basically",
    "actually", "literally", "right", "so", "well", "I mean",
    "kind of", "sort of",
}


class ToneAnalyzer:
    """Analyze audio characteristics for communication feedback."""

    def analyze(self, audio_bytes: bytes, transcript: str = "") -> ToneSnapshot:
        """
        Analyze audio bytes and return a ToneSnapshot.

        Args:
            audio_bytes: Raw audio data.
            transcript: Optional transcript text for filler word counting.

        Returns:
            ToneSnapshot with pace, pitch, energy, filler, and silence metrics.
        """
        try:
            import librosa

            # Write to temp file for librosa to load
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                tmp.write(audio_bytes)
                tmp.flush()
                y, sr = librosa.load(tmp.name, sr=None)

            duration_sec = len(y) / sr if sr > 0 else 0.0

            # Pitch analysis (fundamental frequency)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)

            avg_pitch = float(np.mean(pitch_values)) if pitch_values else 0.0
            pitch_var = float(np.std(pitch_values)) if pitch_values else 0.0

            # Energy analysis (RMS)
            rms = librosa.feature.rms(y=y)[0]
            avg_energy = float(np.mean(rms))
            # Normalize energy to 0-1 range (approximate)
            normalized_energy = min(1.0, avg_energy / 0.1) if avg_energy > 0 else 0.0

            # Silence detection
            intervals = librosa.effects.split(y, top_db=30)
            if len(intervals) > 0:
                speech_frames = sum(end - start for start, end in intervals)
                silence_ratio = 1.0 - (speech_frames / len(y)) if len(y) > 0 else 0.0
            else:
                silence_ratio = 1.0

            # Filler word analysis (requires transcript)
            filler_count = 0
            filler_list: list[str] = []
            if transcript:
                lower_text = transcript.lower()
                for filler in FILLER_WORDS:
                    count = lower_text.count(filler)
                    if count > 0:
                        filler_count += count
                        filler_list.extend([filler] * count)

            # Speaking pace (words per minute) from transcript
            word_count = len(transcript.split()) if transcript else 0
            wpm = (word_count / duration_sec * 60) if duration_sec > 0 else 0.0

            return ToneSnapshot(
                speaking_pace_wpm=round(wpm, 1),
                filler_word_count=filler_count,
                filler_words=filler_list,
                avg_pitch_hz=round(avg_pitch, 1),
                pitch_variation=round(pitch_var, 1),
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
