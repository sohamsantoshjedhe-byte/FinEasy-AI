"""
FinEasy AI - Tax Calculation & Validation Routes
Endpoints for computing tax liabilities, retrieving calculations, and validating filing data.
"""

from fastapi import APIRouter, Depends
from backend.schemas.tax import TaxCalculationRequest, TaxCalculationResponse, TaxValidationResponse
from backend.dependencies import get_current_user
from backend.services import tax_service, validation_service

router = APIRouter(prefix="/api/tax", tags=["Tax Engine"])


@router.post("/calculate/{filing_id}", response_model=TaxCalculationResponse, summary="Compute tax for a filing")
def calculate_tax_endpoint(
    filing_id: str,
    payload: TaxCalculationRequest = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Executes deterministic tax calculation for the specified filing.
    Optionally accepts overrides for gross income, deductions, or TDS.
    """
    gross = payload.gross_income if payload else None
    deductions = payload.deductions if payload else None
    tds = payload.tds if payload else None

    return tax_service.run_tax_calculation(
        filing_id=filing_id,
        user_id=current_user["user_id"],
        gross_income_override=gross,
        deductions_override=deductions,
        tds_override=tds,
    )


@router.get("/{filing_id}", response_model=TaxCalculationResponse, summary="Get latest tax calculation")
def get_tax_calculation(filing_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves the most recent tax calculation for a filing."""
    return tax_service.get_filing_tax_calculation(
        filing_id=filing_id,
        user_id=current_user["user_id"],
        user_type=current_user.get("user_type", "individual"),
    )


@router.post("/validate/{filing_id}", response_model=TaxValidationResponse, summary="Validate filing data")
def validate_filing_endpoint(filing_id: str, current_user: dict = Depends(get_current_user)):
    """
    Validates filing completeness, checks for negative values, inconsistencies,
    and transitions status to 'ca_review' if valid.
    """
    return validation_service.validate_filing_for_review(filing_id=filing_id, user_id=current_user["user_id"])
