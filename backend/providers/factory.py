"""
Provider factory -- reads .env config and returns the correct provider implementation.
Swap providers by changing LLM_PROVIDER, STT_PROVIDER, TTS_PROVIDER in .env.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from backend.config import settings
from backend.providers.base import LLMProvider, STTProvider, TTSProvider

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider instance."""
    provider = settings.llm_provider.lower()
    model = settings.llm_model
    logger.info("Initializing LLM provider: %s (model=%s)", provider, model)

    match provider:
        case "gemini":
            from backend.providers.llm.gemini import GeminiProvider
            return GeminiProvider(api_key=settings.google_api_key, model=model)

        case "openai":
            from backend.providers.llm.openai_llm import OpenAILLMProvider
            return OpenAILLMProvider(api_key=settings.openai_api_key, model=model)

        case "anthropic":
            from backend.providers.llm.anthropic_llm import AnthropicProvider
            return AnthropicProvider(api_key=settings.anthropic_api_key, model=model)

        case "ollama":
            from backend.providers.llm.ollama import OllamaProvider
            return OllamaProvider(base_url=settings.ollama_url, model=model)

        case _:
            raise ValueError(f"Unknown LLM provider: {provider}")


@lru_cache(maxsize=1)
def get_stt_provider() -> STTProvider:
    """Return the configured STT provider instance."""
    provider = settings.stt_provider.lower()
    logger.info("Initializing STT provider: %s", provider)

    match provider:
        case "local_whisper":
            from backend.providers.stt.whisper_local import WhisperLocalProvider
            return WhisperLocalProvider(model_size=settings.stt_model)

        case "whisper_api":
            from backend.providers.stt.whisper_api import WhisperAPIProvider
            return WhisperAPIProvider(api_key=settings.openai_api_key)

        case "deepgram":
            from backend.providers.stt.deepgram_stt import DeepgramProvider
            return DeepgramProvider(api_key=settings.deepgram_api_key)

        case "google_stt":
            from backend.providers.stt.google_stt import GoogleSTTProvider
            return GoogleSTTProvider(api_key=settings.google_api_key)

        case _:
            raise ValueError(f"Unknown STT provider: {provider}")


@lru_cache(maxsize=1)
def get_tts_provider() -> TTSProvider:
    """Return the configured TTS provider instance."""
    provider = settings.tts_provider.lower()
    voice = settings.tts_voice
    logger.info("Initializing TTS provider: %s (voice=%s)", provider, voice)

    match provider:
        case "edge_tts":
            from backend.providers.tts.edge import EdgeTTSProvider
            return EdgeTTSProvider(voice=voice)

        case "openai_tts":
            from backend.providers.tts.openai_tts import OpenAITTSProvider
            return OpenAITTSProvider(api_key=settings.openai_api_key, voice=voice)

        case "elevenlabs":
            from backend.providers.tts.elevenlabs_tts import ElevenLabsTTSProvider
            return ElevenLabsTTSProvider(api_key=settings.elevenlabs_api_key, voice=voice)

        case "google_tts":
            from backend.providers.tts.google_tts import GoogleTTSProvider
            return GoogleTTSProvider(api_key=settings.google_api_key, voice=voice)

        case _:
            raise ValueError(f"Unknown TTS provider: {provider}")
