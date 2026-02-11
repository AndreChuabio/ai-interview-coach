"""
Local Whisper STT provider.
Runs the openai-whisper Python package locally -- fully offline, zero cost.
Requires: pip install openai-whisper
"""

from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path

from backend.providers.base import STTProvider

logger = logging.getLogger(__name__)


class WhisperLocalProvider(STTProvider):
    """Speech-to-text using local Whisper model (no API key needed)."""

    def __init__(self, model_size: str = "base"):
        """
        Args:
            model_size: Whisper model size -- tiny, base, small, medium, large.
                        'base' is a good balance of speed and accuracy for development.
        """
        self._model_size = model_size
        self._model = None  # Lazy-loaded on first transcription
        logger.info("WhisperLocalProvider initialized (model_size=%s, lazy load)", model_size)

    def _load_model(self):
        """Load the Whisper model on first use to avoid slow startup."""
        if self._model is None:
            import whisper

            logger.info("Loading Whisper model: %s", self._model_size)
            self._model = whisper.load_model(self._model_size)
            logger.info("Whisper model loaded")

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en",
    ) -> str:
        """Transcribe audio bytes using local Whisper."""
        self._load_model()

        # Whisper expects a file path, so write to a temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            tmp_path = tmp.name

            result = self._model.transcribe(
                tmp_path,
                language=language,
                fp16=False,  # CPU-safe
            )

        text = result.get("text", "").strip()
        logger.debug("Whisper transcription (%d bytes audio): %s", len(audio_bytes), text[:120])
        return text
