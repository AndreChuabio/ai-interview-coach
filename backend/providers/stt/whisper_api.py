"""
OpenAI Whisper API STT provider -- cloud-based transcription.
Requires: OPENAI_API_KEY in .env
Cost: ~$0.006/minute of audio.
"""

from __future__ import annotations

import io
import logging

from openai import AsyncOpenAI

from backend.providers.base import STTProvider

logger = logging.getLogger(__name__)


class WhisperAPIProvider(STTProvider):
    """Speech-to-text using OpenAI's Whisper API (cloud)."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for Whisper API provider")
        self._client = AsyncOpenAI(api_key=api_key)
        logger.info("WhisperAPIProvider initialized")

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en",
    ) -> str:
        """Transcribe audio bytes using OpenAI Whisper API."""
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.webm"

        try:
            response = await self._client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="text",
            )
            text = response.strip() if isinstance(response, str) else str(response).strip()
            logger.debug("Whisper API transcription: %s", text[:120])
            return text
        except Exception:
            logger.exception("Whisper API transcription failed")
            raise
