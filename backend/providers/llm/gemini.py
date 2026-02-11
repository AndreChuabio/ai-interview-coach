"""
Google Gemini LLM provider.
Free tier: 15 RPM, ~1M tokens/day on gemini-2.0-flash.
Includes retry logic for rate limit (429) errors.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from google import genai
from google.genai import errors as genai_errors

from backend.providers.base import LLMProvider

logger = logging.getLogger(__name__)

# Retry config for rate-limited requests
MAX_RETRIES = 3
BASE_DELAY_SEC = 5


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

    def _extract_retry_delay(self, error: Exception) -> float:
        """Extract retry delay from Gemini 429 error message, or use default."""
        error_str = str(error)
        match = re.search(r"retry in ([\d.]+)s", error_str)
        if match:
            return float(match.group(1)) + 1.0
        return BASE_DELAY_SEC

    async def chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Send a chat request to Gemini with retry on rate limit errors."""
        prompt = self._build_contents(messages, system_prompt)

        for attempt in range(MAX_RETRIES + 1):
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

            except genai_errors.ClientError as exc:
                if "429" in str(exc) and attempt < MAX_RETRIES:
                    delay = self._extract_retry_delay(exc)
                    logger.warning(
                        "Gemini rate limited (attempt %d/%d). Retrying in %.1fs...",
                        attempt + 1,
                        MAX_RETRIES,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.exception("Gemini request failed after retries")
                raise

            except Exception:
                logger.exception("Gemini chat request failed")
                raise

        raise RuntimeError("Gemini request failed: max retries exceeded")

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
