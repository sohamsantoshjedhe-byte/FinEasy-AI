"""
FinEasy AI - Security Utilities
Authentication token parsing and user identity verification.
"""

import logging
from typing import Optional, Dict, Any
from backend.database.supabase import get_supabase_client

logger = logging.getLogger("fineasy.security")


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """Extracts JWT token from Authorization header (Bearer <token>)."""
    if not authorization_header:
        return None
    parts = authorization_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def verify_auth_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies user token using Supabase Auth client.
    Returns user dictionary if valid, None otherwise.
    """
    if not token:
        return None

    client = get_supabase_client()
    try:
        auth_user_resp = client.auth.get_user(token)
        if auth_user_resp and hasattr(auth_user_resp, "user") and auth_user_resp.user:
            user = auth_user_resp.user
            return {
                "user_id": getattr(user, "id", None),
                "email": getattr(user, "email", ""),
                "user_metadata": getattr(user, "user_metadata", {}) or {},
            }
        return None
    except Exception as e:
        logger.warning("Token verification failed: %s", e)
        return None
