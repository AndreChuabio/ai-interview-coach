"""
ElevenLabs TTS provider -- most natural-sounding voices.
Requires: ELEVENLABS_API_KEY in .env
Free tier: 10,000 characters/month. Paid plans start at $5/month.
"""

from __future__ import annotations

import logging

import httpx

from backend.providers.base import TTSProvider

logger = logging.getLogger(__name__)

ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Default voice IDs (ElevenLabs pre-made voices)
DEFAULT_VOICES = {
    "rachel": "21m00Tcm4TlvDq8ikWAM",
    "adam": "pNInz6obpgDQGcFmaJgB",
    "josh": "TxGEqnHWrfWFTfGW9XjX",
    "bella": "EXAVITQu4vr4xnSDxMaL",
    "default": "21m00Tcm4TlvDq8ikWAM",  # Rachel
}


class ElevenLabsTTSProvider(TTSProvider):
    """Text-to-speech using ElevenLabs API."""

    def __init__(
        self,
        api_key: str,
        voice: str = "rachel",
        model_id: str = "eleven_monolingual_v1",
    ):
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is required for ElevenLabs TTS provider")
        self._api_key = api_key
        self._voice_id = DEFAULT_VOICES.get(voice.lower(), voice)
        self._model_id = model_id
        self._client = httpx.AsyncClient(timeout=30.0)
        logger.info(
            "ElevenLabsTTSProvider initialized (voice=%s, voice_id=%s)",
            voice, self._voice_id,
        )

    async def synthesize(
        self,
        text: str,
        voice: str = "default",
    ) -> bytes:
        """Convert text to speech using ElevenLabs API. Returns mp3 bytes."""
        voice_id = DEFAULT_VOICES.get(voice.lower(), self._voice_id) if voice != "default" else self._voice_id

        url = f"{ELEVENLABS_API_URL}/{voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self._model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        try:
            response = await self._client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            audio_bytes = response.content
            logger.debug("ElevenLabs TTS synthesized %d bytes", len(audio_bytes))
            return audio_bytes
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ElevenLabs API error: %s %s",
                exc.response.status_code,
                exc.response.text[:200],
            )
            raise
        except Exception:
            logger.exception("ElevenLabs TTS synthesis failed")
            raise
