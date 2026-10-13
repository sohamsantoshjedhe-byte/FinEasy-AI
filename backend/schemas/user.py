"""
FinEasy AI - User Profile Schemas
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: EmailStr
    user_type: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    user_type: Optional[Literal["individual", "ca", "admin"]] = None
