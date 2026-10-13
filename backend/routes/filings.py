"""
FinEasy AI - Filing Routes
Endpoints for creating, listing, viewing, updating, and deleting tax filings.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from backend.schemas.filing import FilingCreate, FilingUpdate, FilingResponse, FilingDetailResponse
from backend.dependencies import get_current_user
from backend.services import filing_service

router = APIRouter(prefix="/api/filings", tags=["Filings"])


@router.post("", response_model=FilingResponse, status_code=status.HTTP_201_CREATED, summary="Create a new ITR filing")
def create_filing(payload: FilingCreate, current_user: dict = Depends(get_current_user)):
    """Creates a new tax filing in 'draft' status for the authenticated user."""
    return filing_service.create_new_filing(
        user_id=current_user["user_id"],
        financial_year=payload.financial_year,
        filing_type=payload.filing_type,
    )


@router.get("", response_model=List[FilingResponse], summary="List user filings")
def list_filings(current_user: dict = Depends(get_current_user)):
    """Returns all filings belonging to the authenticated individual (or pending review filings if CA)."""
    return filing_service.list_filings(
        user_id=current_user["user_id"],
        user_type=current_user.get("user_type", "individual"),
    )


@router.get("/{filing_id}", response_model=FilingDetailResponse, summary="Get full filing details")
def get_filing(filing_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves full details including attached documents, AI analysis, calculations, and reviews."""
    return filing_service.get_filing(
        filing_id=filing_id,
        user_id=current_user["user_id"],
        user_type=current_user.get("user_type", "individual"),
    )


@router.put("/{filing_id}", response_model=FilingResponse, summary="Update filing income data")
def update_filing(filing_id: str, payload: FilingUpdate, current_user: dict = Depends(get_current_user)):
    """Updates editable income, deduction, or TDS values for a filing."""
    return filing_service.update_filing_income_data(
        filing_id=filing_id,
        user_id=current_user["user_id"],
        updates=payload.model_dump(exclude_unset=True),
    )


@router.delete("/{filing_id}", summary="Delete a draft filing")
def delete_filing(filing_id: str, current_user: dict = Depends(get_current_user)):
    """Deletes a filing. Allowed only while filing is in 'draft' status."""
    deleted = filing_service.delete_filing(filing_id=filing_id, user_id=current_user["user_id"])
    return {"success": deleted, "message": "Filing deleted successfully."}
