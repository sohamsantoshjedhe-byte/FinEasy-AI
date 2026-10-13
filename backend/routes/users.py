"""
FinEasy AI - User Profile Routes
Endpoints for fetching and updating user profiles.
"""

from fastapi import APIRouter, Depends
from backend.schemas.user import UserProfileResponse, UserProfileUpdate
from backend.dependencies import get_current_user
from backend.services import auth_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
def get_me(current_user: dict = Depends(get_current_user)):
    """Returns the authenticated user's profile information."""
    return auth_service.get_current_user_profile(current_user["user_id"])


@router.put("/me", response_model=UserProfileResponse, summary="Update user profile")
def update_me(payload: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Allows updating user profile information such as name and role."""
    updates = payload.model_dump(exclude_unset=True)
    return auth_service.update_user_profile(current_user["user_id"], updates)
