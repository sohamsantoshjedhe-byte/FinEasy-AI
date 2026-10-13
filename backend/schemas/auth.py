"""
FinEasy AI - Authentication Schemas
"""

from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    name: str = Field(..., min_length=2, max_length=100)
    user_type: Literal["individual", "ca", "admin"] = "individual"


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str
    user_type: str
