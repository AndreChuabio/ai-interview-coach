"""
Microsoft Edge TTS provider.
Completely free, no API key needed. Uses edge-tts Python package.
Requires: pip install edge-tts
"""

from __future__ import annotations

import io
import logging
import tempfile

import edge_tts

from backend.providers.base import TTSProvider

logger = logging.getLogger(__name__)

# Good default voices for interview scenarios
EDGE_VOICES = {
    "male_us": "en-US-GuyNeural",
    "female_us": "en-US-JennyNeural",
    "male_uk": "en-GB-RyanNeural",
    "female_uk": "en-GB-SoniaNeural",
    "default": "en-US-GuyNeural",
}


class EdgeTTSProvider(TTSProvider):
    """Text-to-speech using Microsoft Edge TTS (free, no API key)."""

    def __init__(self, voice: str = "en-US-GuyNeural"):
        self._voice = voice if voice != "default" else EDGE_VOICES["default"]
        logger.info("EdgeTTSProvider initialized (voice=%s)", self._voice)

    async def synthesize(
        self,
        text: str,
        voice: str = "default",
    ) -> bytes:
        """Convert text to speech using Edge TTS. Returns mp3 bytes."""
        selected_voice = voice if voice != "default" else self._voice

        communicate = edge_tts.Communicate(text, selected_voice)

        # Collect audio bytes from the streaming response
        audio_chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        audio_bytes = b"".join(audio_chunks)
        logger.debug(
            "Edge TTS synthesized %d chars -> %d bytes audio",
            len(text),
            len(audio_bytes),
        )
        return audio_bytes
