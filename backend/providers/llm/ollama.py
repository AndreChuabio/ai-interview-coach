"""
Ollama LLM provider -- fully local, zero cost, no API key needed.
Requires Ollama running locally: https://ollama.com
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.providers.base import LLMProvider

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120.0  # seconds -- local models can be slow on first load


class OllamaProvider(LLMProvider):
    """LLM provider backed by a local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma2:2b"):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=DEFAULT_TIMEOUT)
        logger.info("OllamaProvider initialized with model=%s at %s", model, base_url)

    def _build_messages(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> list[dict[str, str]]:
        """Build Ollama-compatible message list with optional system prompt."""
        result: list[dict[str, str]] = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        for msg in messages:
            result.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        return result

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Send a chat request to the local Ollama instance."""
        ollama_messages = self._build_messages(messages, system_prompt)

        try:
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self._model,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": 2048,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            text = data.get("message", {}).get("content", "").strip()
            logger.debug("Ollama response length: %d chars", len(text))
            return text

        except httpx.ConnectError:
            logger.error("Cannot connect to Ollama at %s. Is it running?", self._base_url)
            raise RuntimeError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Start it with: ollama serve"
            )
        except Exception:
            logger.exception("Ollama chat request failed")
            raise

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Send a chat request expecting JSON output, parse and return as dict."""
        json_instruction = (
            "\n\nRespond with valid JSON only. No markdown, no code fences, no explanation."
        )
        full_system = (system_prompt + json_instruction) if system_prompt else json_instruction

        raw = await self.chat(messages, system_prompt=full_system, temperature=temperature)

        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):].strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[len("```"):].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error("Failed to parse Ollama JSON response: %s", cleaned[:200])
            return {"error": "Failed to parse JSON", "raw": cleaned[:500]}
