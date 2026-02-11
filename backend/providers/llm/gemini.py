"""
Google Gemini LLM provider.
Free tier: 15 RPM, ~1M tokens/day on gemini-2.0-flash.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai

from backend.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """LLM provider backed by Google Gemini (free tier available)."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini provider")
        self._client = genai.Client(api_key=api_key)
        self._model = model
        logger.info("GeminiProvider initialized with model=%s", model)

    def _build_contents(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
    ) -> str:
        """
        Build a single prompt string from messages and system prompt.
        Gemini's generate_content works with a flat string or structured Content objects.
        We use a simple string concatenation approach for compatibility.
        """
        parts: list[str] = []
        if system_prompt:
            parts.append(f"System: {system_prompt}\n")
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                parts.append(f"Assistant: {content}")
            else:
                parts.append(f"User: {content}")
        return "\n\n".join(parts)

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Send a chat request to Gemini and return the text response."""
        prompt = self._build_contents(messages, system_prompt)
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": 2048,
                },
            )
            text = response.text.strip() if response.text else ""
            logger.debug("Gemini response length: %d chars", len(text))
            return text
        except Exception:
            logger.exception("Gemini chat request failed")
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
            logger.error("Failed to parse Gemini JSON response: %s", cleaned[:200])
            return {"error": "Failed to parse JSON", "raw": cleaned[:500]}
