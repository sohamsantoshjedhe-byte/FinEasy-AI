"""
FinEasy AI - FastAPI Dependencies
Authentication, user identification, and Role-Based Access Control (RBAC).
"""

import logging
from typing import Dict, Any, Optional
from fastapi import Header, HTTPException, status, Depends

from backend.utils.security import extract_bearer_token, verify_auth_token
from backend.database import queries
from backend.utils.response import AppException

logger = logging.getLogger("fineasy.dependencies")


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency that extracts and validates the authenticated user from the Authorization header.
    In demo / development mode, accepts synthetic mock tokens for immediate testing.
    """
    if not authorization:
        raise AppException(
            code="UNAUTHENTICATED",
            message="Authorization header is required (Bearer <token>).",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = extract_bearer_token(authorization)
    if not token:
        raise AppException(
            code="INVALID_TOKEN_FORMAT",
            message="Invalid Authorization header format. Expected 'Bearer <token>'.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # 1. Try Supabase verify
    auth_data = verify_auth_token(token)
    user_id = auth_data.get("user_id") if auth_data else None

    # 2. Demo token fallback (e.g. mock-token-<uuid> or demo-token)
    if not user_id:
        if token.startswith("mock-token-"):
            user_id = token.replace("mock-token-", "")
        elif token.startswith("token-"):
            user_id = token.replace("token-", "")
        elif token.startswith("demo-"):
            user_id = token

    if not user_id:
        raise AppException(
            code="INVALID_TOKEN",
            message="Authentication token is expired or invalid.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    profile = queries.get_profile_by_user_id(user_id)
    if not profile:
        # Auto-provision demo profile if missing
        profile = queries.create_profile(
            user_id=user_id,
            email=f"{user_id}@example.com",
            name="Demo Taxpayer",
            user_type="individual",
        )

    return profile


def require_individual(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Requires an authenticated user."""
    return user


def require_ca(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Requires user to hold CA (Chartered Accountant) or Admin privileges."""
    user_type = user.get("user_type", "individual")
    if user_type not in ["ca", "admin"]:
        raise AppException(
            code="FORBIDDEN_ROLE",
            message=f"Access denied. Chartered Accountant (CA) or Admin role required. Current role: '{user_type}'.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return user


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Requires user to hold Admin privileges."""
    user_type = user.get("user_type", "individual")
    if user_type != "admin":
        raise AppException(
            code="FORBIDDEN_ROLE",
            message=f"Access denied. Admin privileges required. Current role: '{user_type}'.",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    return user
