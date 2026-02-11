"""
OpenAI LLM provider -- GPT-4o, GPT-4o-mini, etc.
Requires: OPENAI_API_KEY in .env
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI

from backend.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProvider):
    """LLM provider backed by OpenAI's chat completions API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI LLM provider")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        logger.info("OpenAILLMProvider initialized with model=%s", model)

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Send a chat completion request to OpenAI."""
        oai_messages: list[dict[str, str]] = []
        if system_prompt:
            oai_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            oai_messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=oai_messages,
                temperature=temperature,
                max_tokens=2048,
            )
            text = response.choices[0].message.content.strip()
            logger.debug("OpenAI response length: %d chars", len(text))
            return text
        except Exception:
            logger.exception("OpenAI chat request failed")
            raise

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Send a chat request expecting JSON output."""
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
            logger.error("Failed to parse OpenAI JSON response: %s", cleaned[:200])
            return {"error": "Failed to parse JSON", "raw": cleaned[:500]}
