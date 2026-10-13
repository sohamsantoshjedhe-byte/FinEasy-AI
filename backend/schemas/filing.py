"""
FinEasy AI - Filing Schemas
"""

from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class FilingStatusEnum(str, Enum):
    DRAFT = "draft"
    DOCUMENT_UPLOADED = "document_uploaded"
    ANALYSING = "analysing"
    ANALYSED = "analysed"
    CALCULATION_COMPLETE = "calculation_complete"
    VALIDATION_PENDING = "validation_pending"
    CA_REVIEW = "ca_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    SUBMITTED = "submitted"
    REJECTED = "rejected"


class FilingCreate(BaseModel):
    financial_year: str = Field(..., json_schema_extra={"example": "2024-25"}, description="Financial Year in YYYY-YY format")
    filing_type: str = Field(default="ITR", json_schema_extra={"example": "ITR"}, description="Type of filing (V1: ITR)")


class FilingUpdate(BaseModel):
    gross_income: Optional[float] = Field(None, ge=0.0)
    deductions: Optional[float] = Field(None, ge=0.0)
    tds_amount: Optional[float] = Field(None, ge=0.0)


class FilingResponse(BaseModel):
    id: str
    user_id: str
    financial_year: str
    filing_type: str
    status: FilingStatusEnum
    gross_income: float = 0.0
    deductions: float = 0.0
    taxable_income: float = 0.0
    tax_amount: float = 0.0
    tds_amount: float = 0.0
    refund_amount: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FilingDetailResponse(BaseModel):
    filing: FilingResponse
    documents: List[Dict[str, Any]] = []
    ai_analysis: Optional[Dict[str, Any]] = None
    latest_calculation: Optional[Dict[str, Any]] = None
    reviews: List[Dict[str, Any]] = []
    audit_logs: List[Dict[str, Any]] = []
