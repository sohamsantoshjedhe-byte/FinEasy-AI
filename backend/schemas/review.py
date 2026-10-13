"""
FinEasy AI - Review Schemas
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class ReviewActionRequest(BaseModel):
    comments: Optional[str] = Field(None, max_length=1000, description="Notes from CA or reviewer")


class ReviewResponse(BaseModel):
    id: str
    filing_id: str
    reviewer_id: Optional[str] = None
    status: Literal["pending", "approved", "rejected", "changes_requested"]
    comments: Optional[str] = None
    reviewed_at: Optional[str] = None
