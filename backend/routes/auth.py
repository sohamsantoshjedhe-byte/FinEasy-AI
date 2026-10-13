"""
FinEasy AI - Authentication Routes
Endpoints for user registration, authentication, and session retrieval.
"""

from fastapi import APIRouter, Depends
from backend.schemas.auth import UserRegister, UserLogin, TokenResponse
from backend.schemas.user import UserProfileResponse
from backend.services import auth_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, summary="Register a new taxpayer or CA account")
def register(payload: UserRegister):
    """Creates a new user profile and returns access tokens."""
    return auth_service.register_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
        user_type=payload.user_type,
    )


@router.post("/login", response_model=TokenResponse, summary="Login with email and password")
def login(payload: UserLogin):
    """Authenticates credentials and returns access token."""
    return auth_service.login_user(email=payload.email, password=payload.password)


@router.get("/me", response_model=UserProfileResponse, summary="Retrieve current authenticated user")
def me(current_user: dict = Depends(get_current_user)):
    """Returns profile information for the authenticated user."""
    return current_user
