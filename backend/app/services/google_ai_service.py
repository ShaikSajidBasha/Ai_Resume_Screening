"""
Centralized Google Generative AI (Google AI Studio) client.

All agents call through this module rather than hitting the SDK directly, so that
timeout/retry/logging/JSON-validation behaviour lives in exactly one place.

The API key is read only from the environment (via app.core.config) and is never
sent to, or exposed in, the frontend.
"""
import json
import logging
import time
from typing import Optional

import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger("google_ai_service")

_configured = False


class AIServiceError(Exception):
    """Raised when the AI backend is unavailable or returns unusable output."""
    pass


def _ensure_configured():
    global _configured
    if not _configured:
        if not settings.GOOGLE_API_KEY:
            logger.warning("GOOGLE_API_KEY is not set. AI agents will use fallback logic.")
        else:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        _configured = True


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.replace("json\n", "", 1) if text.lower().startswith("json") else text
    return text.strip()


def generate_json(system_prompt: str, user_prompt: str, retries: Optional[int] = None) -> dict:
    """
    Calls the Google AI model, instructing it to return ONLY JSON, and safely
    parses the response. Raises AIServiceError on repeated failure so callers
    can fall back to deterministic/rule-based behaviour instead of crashing.
    """
    _ensure_configured()

    if not settings.GOOGLE_API_KEY:
        raise AIServiceError("GOOGLE_API_KEY not configured.")

    retries = settings.AI_MAX_RETRIES if retries is None else retries
    model = genai.GenerativeModel(
        model_name=settings.GOOGLE_MODEL,
        system_instruction=system_prompt,
        generation_config={"response_mime_type": "application/json"},
    )

    last_error = None
    for attempt in range(retries + 1):
        try:
            response = model.generate_content(
                user_prompt,
                request_options={"timeout": settings.AI_TIMEOUT_SECONDS},
            )
            raw_text = response.text
            cleaned = _strip_json_fences(raw_text)
            parsed = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError as exc:
            last_error = exc
            logger.warning("AI response was not valid JSON (attempt %s): %s", attempt + 1, exc)
        except Exception as exc:  # noqa: BLE001 - broad by design, we always fall back
            last_error = exc
            logger.warning("Google AI call failed (attempt %s): %s", attempt + 1, exc)
            time.sleep(1.5 * (attempt + 1))

    raise AIServiceError(f"AI analysis is temporarily unavailable: {last_error}")
