"""
FinEasy AI - Authentication Service
Handles registration, login, and user profile management via Supabase Auth & PostgreSQL.
"""

import logging
from typing import Dict, Any, Optional
from backend.database.supabase import get_supabase_client
from backend.database import queries
from backend.utils.response import AppException
from fastapi import status

logger = logging.getLogger("fineasy.services.auth")


def register_user(email: str, password: str, name: str, user_type: str = "individual") -> Dict[str, Any]:
    """Registers a new user and creates their profile."""
    client = get_supabase_client()
    try:
        auth_resp = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"name": name, "user_type": user_type}},
        })
    except Exception as e:
        logger.error("Supabase sign_up error: %s", e)
        raise AppException(code="REGISTRATION_FAILED", message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    user_id = getattr(auth_resp.user, "id", None) if hasattr(auth_resp, "user") else None
    if not user_id:
        raise AppException(code="REGISTRATION_FAILED", message="Failed to obtain user identity from auth provider.")

    # Create profile in PostgreSQL
    profile = queries.create_profile(user_id=user_id, email=email, name=name, user_type=user_type)

    # Audit log
    queries.create_audit_log(
        action="user_registered",
        user_id=user_id,
        details={"email": email, "user_type": user_type}
    )

    access_token = getattr(auth_resp.session, "access_token", f"token-{user_id}") if hasattr(auth_resp, "session") and auth_resp.session else f"token-{user_id}"

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "email": email,
        "name": name,
        "user_type": user_type,
    }


def login_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticates user credentials and returns session tokens."""
    client = get_supabase_client()
    try:
        auth_resp = client.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        logger.error("Supabase login error: %s", e)
        raise AppException(code="INVALID_CREDENTIALS", message="Invalid email or password.", status_code=status.HTTP_401_UNAUTHORIZED)

    user = getattr(auth_resp, "user", None)
    user_id = getattr(user, "id", None) if user else None
    if not user_id:
        raise AppException(code="AUTH_FAILED", message="Unable to verify user session.", status_code=status.HTTP_401_UNAUTHORIZED)

    profile = queries.get_profile_by_user_id(user_id)
    if not profile:
        profile = queries.create_profile(
            user_id=user_id,
            email=email,
            name=user.user_metadata.get("name", email.split("@")[0]),
            user_type=user.user_metadata.get("user_type", "individual"),
        )

    # Audit log
    queries.create_audit_log(
        action="login",
        user_id=user_id,
        details={"email": email}
    )

    access_token = getattr(auth_resp.session, "access_token", f"token-{user_id}") if hasattr(auth_resp, "session") and auth_resp.session else f"token-{user_id}"

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "email": profile.get("email", email),
        "name": profile.get("name", "User"),
        "user_type": profile.get("user_type", "individual"),
    }


def get_current_user_profile(user_id: str) -> Dict[str, Any]:
    """Fetches user profile details."""
    profile = queries.get_profile_by_user_id(user_id)
    if not profile:
        raise AppException(code="PROFILE_NOT_FOUND", message="User profile does not exist.", status_code=status.HTTP_404_NOT_FOUND)
    return profile


def update_user_profile(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Updates user profile information."""
    updated = queries.update_profile(user_id, updates)
    if not updated:
        raise AppException(code="UPDATE_FAILED", message="Failed to update user profile.", status_code=status.HTTP_400_BAD_REQUEST)
    return updated
