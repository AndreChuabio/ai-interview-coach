"""
OpenAI TTS provider -- high-quality text-to-speech.
Requires: OPENAI_API_KEY in .env
Cost: $15/1M characters (tts-1), $30/1M characters (tts-1-hd).
"""

from __future__ import annotations

import logging

from openai import AsyncOpenAI

from backend.providers.base import TTSProvider

logger = logging.getLogger(__name__)

# Available OpenAI TTS voices
VALID_VOICES = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}


class OpenAITTSProvider(TTSProvider):
    """Text-to-speech using OpenAI's TTS API."""

    def __init__(
        self,
        api_key: str,
        voice: str = "nova",
        model: str = "tts-1",
    ):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI TTS provider")
        self._client = AsyncOpenAI(api_key=api_key)
        self._voice = voice if voice in VALID_VOICES else "nova"
        self._model = model
        logger.info("OpenAITTSProvider initialized (voice=%s, model=%s)", self._voice, model)

    async def synthesize(
        self,
        text: str,
        voice: str = "default",
    ) -> bytes:
        """Convert text to speech using OpenAI TTS API. Returns mp3 bytes."""
        use_voice = voice if voice in VALID_VOICES else self._voice

        try:
            response = await self._client.audio.speech.create(
                model=self._model,
                voice=use_voice,
                input=text,
                response_format="mp3",
            )
            audio_bytes = response.content
            logger.debug("OpenAI TTS synthesized %d bytes", len(audio_bytes))
            return audio_bytes
        except Exception:
            logger.exception("OpenAI TTS synthesis failed")
            raise
