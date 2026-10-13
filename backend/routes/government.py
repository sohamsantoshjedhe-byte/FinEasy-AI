"""
FinEasy AI - Government Integration Routes
Endpoints for retrieving simulated prefill data and submitting approved filings to Mock Government API.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from backend.dependencies import get_current_user
from backend.services import government_service
from backend.database import queries
from backend.utils.response import AppException

router = APIRouter(prefix="/api/government", tags=["Government Integration (Mock)"])


@router.get("/prefill/{user_id}", summary="Get prefill tax data from Mock Government API")
async def get_prefill(user_id: str, current_user: dict = Depends(get_current_user)):
    """Fetches simulated prefilled Form 26AS/AIS financial data for a taxpayer."""
    return await government_service.get_mock_prefill_data(user_id)


@router.post("/validate/{filing_id}", summary="Validate filing against Mock Government API")
async def validate_with_government(filing_id: str, current_user: dict = Depends(get_current_user)):
    """Performs schema and rule validation against the Mock Government API."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.")

    calc = queries.get_latest_tax_calculation(filing_id) or {}
    taxable = calc.get("taxable_income", filing.get("taxable_income", 0.0))
    tax_amt = calc.get("total_tax", filing.get("tax_amount", 0.0))

    return await government_service.validate_with_government_mock(
        filing_id=filing_id,
        taxable_income=taxable,
        tax_amount=tax_amt,
    )


@router.post("/submit/{filing_id}", summary="Submit approved filing to Mock Government API")
async def submit_filing(filing_id: str, current_user: dict = Depends(get_current_user)):
    """
    Submits an approved filing to the simulated Income Tax portal.
    Generates an official demo acknowledgement number and transitions filing to 'submitted'.
    """
    return await government_service.submit_filing_to_government(
        filing_id=filing_id,
        user_id=current_user["user_id"],
    )
