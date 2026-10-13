"""
FinEasy AI - Google Gemini Client Wrapper
Uses the official google-genai SDK with client singleton and offline fallback support.
"""

import logging
from typing import Optional
from backend.config import settings

logger = logging.getLogger("fineasy.ai.gemini")

_gemini_client = None


def get_gemini_client():
    """
    Returns a singleton instance of the official google.genai Client.
    Returns None if GEMINI_API_KEY is not configured.
    """
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client

    import os
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key or "your-gemini" in api_key:
        logger.info("GEMINI_API_KEY not set or placeholder. Gemini client will run in fallback simulation mode.")
        return None

    try:
        from google import genai
        _gemini_client = genai.Client(api_key=api_key)
        logger.info("Google GenAI client initialized successfully.")
        return _gemini_client
    except Exception as e:
        logger.warning("Failed to initialize Google GenAI Client: %s", e)
        return None


def set_gemini_api_key(api_key: str, model: Optional[str] = None):
    """Dynamically sets or updates the Gemini API key at runtime."""
    global _gemini_client
    _gemini_client = None
    settings.GEMINI_API_KEY = api_key.strip()
    if model:
        settings.GEMINI_MODEL = model.strip()
    return get_gemini_client() is not None
