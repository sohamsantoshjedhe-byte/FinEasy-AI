"""
FinEasy AI - Tax Schemas
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class TaxCalculationRequest(BaseModel):
    gross_income: Optional[float] = Field(None, ge=0.0, description="Override gross income")
    deductions: Optional[float] = Field(None, ge=0.0, description="Override deductions (80C, 80D, etc.)")
    tds: Optional[float] = Field(None, ge=0.0, description="Override TDS credit")


class TaxCalculationResponse(BaseModel):
    gross_income: float
    deductions: float
    taxable_income: float
    tax_amount: float
    cess: float
    total_tax: float
    tds: float
    refund_or_payable: float
    calculation_version: str = "demo-v1"
    disclaimer: str = "EDUCATIONAL DEMO RULES — NOT FOR ACTUAL TAX FILING"


class TaxValidationResponse(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
