"""
Deepgram STT provider -- fast cloud-based transcription.
Requires: DEEPGRAM_API_KEY in .env
Cost: ~$0.0043/minute. Free $200 credits on signup.
"""

from __future__ import annotations

import logging

import httpx

from backend.providers.base import STTProvider

logger = logging.getLogger(__name__)

DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"


class DeepgramProvider(STTProvider):
    """Speech-to-text using Deepgram's Nova-2 model."""

    def __init__(self, api_key: str, model: str = "nova-2"):
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY is required for Deepgram provider")
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(timeout=30.0)
        logger.info("DeepgramProvider initialized with model=%s", model)

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en",
    ) -> str:
        """Transcribe audio bytes using Deepgram API."""
        headers = {
            "Authorization": f"Token {self._api_key}",
            "Content-Type": "audio/webm",
        }
        params = {
            "model": self._model,
            "language": language,
            "smart_format": "true",
            "punctuate": "true",
        }

        try:
            response = await self._client.post(
                DEEPGRAM_API_URL,
                headers=headers,
                params=params,
                content=audio_bytes,
            )
            response.raise_for_status()
            data = response.json()

            # Extract transcript from Deepgram response
            transcript = (
                data.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])[0]
                .get("transcript", "")
            )
            text = transcript.strip()
            logger.debug("Deepgram transcription: %s", text[:120])
            return text

        except httpx.HTTPStatusError as exc:
            logger.error("Deepgram API error: %s %s", exc.response.status_code, exc.response.text[:200])
            raise
        except Exception:
            logger.exception("Deepgram transcription failed")
            raise
