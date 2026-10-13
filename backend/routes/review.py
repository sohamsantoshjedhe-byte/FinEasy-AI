"""
FinEasy AI - Chartered Accountant Review Routes
Endpoints for CA filing reviews, approvals, rejections, and revision requests.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from backend.schemas.review import ReviewActionRequest, ReviewResponse
from backend.schemas.filing import FilingResponse
from backend.dependencies import get_current_user, require_ca
from backend.services import review_service

router = APIRouter(prefix="/api/reviews", tags=["CA Review"])


@router.get("/pending", response_model=List[FilingResponse], summary="List filings awaiting CA review")
def get_pending_reviews(current_user: dict = Depends(require_ca)):
    """Returns all filings in 'ca_review' status. Accessible only to CAs and Admins."""
    return review_service.list_pending_ca_reviews()


@router.post("/{filing_id}/approve", response_model=ReviewResponse, summary="Approve filing for submission")
def approve_filing(
    filing_id: str,
    payload: ReviewActionRequest = None,
    current_user: dict = Depends(require_ca),
):
    """Marks filing as 'approved'. Accessible to CAs and Admins."""
    comments = payload.comments if payload else "Approved by CA."
    return review_service.ca_approve_filing(
        filing_id=filing_id,
        reviewer_id=current_user["user_id"],
        comments=comments,
    )


@router.post("/{filing_id}/reject", response_model=ReviewResponse, summary="Reject filing")
def reject_filing(
    filing_id: str,
    payload: ReviewActionRequest = None,
    current_user: dict = Depends(require_ca),
):
    """Marks filing as 'rejected'. Accessible to CAs and Admins."""
    comments = payload.comments if payload else "Rejected by CA."
    return review_service.ca_reject_filing(
        filing_id=filing_id,
        reviewer_id=current_user["user_id"],
        comments=comments,
    )


@router.post("/{filing_id}/request-changes", response_model=ReviewResponse, summary="Request filing revisions")
def request_changes(
    filing_id: str,
    payload: ReviewActionRequest = None,
    current_user: dict = Depends(require_ca),
):
    """Sends filing back to taxpayer with 'changes_requested' status."""
    comments = payload.comments if payload else "Changes requested by CA."
    return review_service.ca_request_changes(
        filing_id=filing_id,
        reviewer_id=current_user["user_id"],
        comments=comments,
    )


@router.get("/{filing_id}", response_model=List[Dict[str, Any]], summary="Get review history for filing")
def get_reviews(filing_id: str, current_user: dict = Depends(get_current_user)):
    """Returns all review decisions and comments for a specific filing."""
    return review_service.get_filing_reviews(filing_id)
