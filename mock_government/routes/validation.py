"""
Mock Government API - Filing Validation Simulation
Validates taxpayer return schema before final submission.
"""

from typing import Dict, Any, List
import uuid
from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter(prefix="/mock", tags=["Mock Government Validation"])


class MockValidateRequest(BaseModel):
    filing_id: str
    taxable_income: float = Field(..., description="Computed taxable income")
    tax_amount: float = Field(..., description="Computed tax amount")


@router.post("/validate", summary="Simulate Government e-Filing Rule Validation")
def mock_validate(payload: MockValidateRequest):
    """
    Simulates Centralized Processing Center (CPC) pre-submission XML/JSON validation rules.
    """
    errors: List[str] = []

    # Check negative figures
    if payload.taxable_income < 0:
        errors.append("RULE_ERR_01: Taxable income cannot be negative.")
    if payload.tax_amount < 0:
        errors.append("RULE_ERR_02: Tax amount cannot be negative.")

    # Check extreme outliers for demo error demonstration
    if payload.taxable_income > 100000000:
        errors.append("RULE_ERR_03: Taxable income exceeds single-form schema ceiling for ITR-1.")

    ref_id = f"DEMO-VAL-{uuid.uuid4().hex[:8].upper()}"

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "reference_id": ref_id,
        "disclaimer": "SIMULATED GOVERNMENT VALIDATION (DEMO)",
    }
