"""
Abstract base classes for all external API providers.
Every external service (LLM, STT, TTS) is accessed through these interfaces.
Swap implementations by changing a single env var -- zero code changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Interface for large language model providers (conversation + feedback)."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """
        Send a chat completion request and return the assistant's text response.

        Args:
            messages: Conversation history as [{"role": "user"|"assistant", "content": "..."}].
            system_prompt: Optional system-level instruction prepended to the conversation.
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).

        Returns:
            The model's text response.
        """
        ...

    @abstractmethod
    async def chat_json(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """
        Send a chat request expecting a JSON-parseable response.

        Args:
            messages: Conversation history.
            system_prompt: System instruction that should request JSON output.
            temperature: Lower temperature recommended for structured output.

        Returns:
            Parsed JSON dict from the model's response.
        """
        ...


class STTProvider(ABC):
    """Interface for speech-to-text providers."""

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "en",
    ) -> str:
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data (wav, mp3, webm, etc.).
            language: ISO 639-1 language code.

        Returns:
            Transcribed text string.
        """
        ...


class TTSProvider(ABC):
    """Interface for text-to-speech providers."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = "default",
    ) -> bytes:
        """
        Convert text to speech audio.

        Args:
            text: The text to speak.
            voice: Voice identifier (provider-specific).

        Returns:
            Audio bytes (mp3 format preferred for web playback).
        """
        ...
