"""
FinEasy AI - Filing Service
Lifecycle management, state transitions, and audit logging for ITR filings.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import status

from backend.database import queries
from backend.tax_engine.validator import validate_financial_year
from backend.utils.response import AppException

logger = logging.getLogger("fineasy.services.filing")

# Finite State Machine valid transitions
ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    "draft": ["document_uploaded", "analysing", "calculation_complete"],
    "document_uploaded": ["analysing", "calculation_complete", "draft"],
    "analysing": ["analysed", "draft"],
    "analysed": ["calculation_complete", "draft"],
    "calculation_complete": ["validation_pending", "ca_review", "draft"],
    "validation_pending": ["ca_review", "calculation_complete", "draft"],
    "ca_review": ["approved", "rejected", "changes_requested"],
    "changes_requested": ["draft", "document_uploaded"],
    "approved": ["submitted"],
    "submitted": [],  # Terminal state
    "rejected": ["draft"],
}


def transition_status(filing_id: str, new_status: str, actor_id: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates and executes a filing status transition according to the state machine.
    """
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message=f"Filing with ID '{filing_id}' does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    current_status = filing.get("status", "draft")
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])

    if new_status not in allowed:
        raise AppException(
            code="INVALID_STATUS_TRANSITION",
            message=f"Cannot transition filing status from '{current_status}' to '{new_status}'. Allowed: {allowed}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    updated = queries.update_filing(filing_id, {"status": new_status})

    queries.create_audit_log(
        action=f"status_transition_{new_status}",
        filing_id=filing_id,
        user_id=actor_id or filing.get("user_id"),
        details={"previous_status": current_status, "new_status": new_status, "notes": notes},
    )

    return updated or filing


def create_new_filing(user_id: str, financial_year: str, filing_type: str = "ITR") -> Dict[str, Any]:
    """Creates a new tax filing for the authenticated user."""
    if not validate_financial_year(financial_year):
        raise AppException(
            code="INVALID_FINANCIAL_YEAR",
            message=f"Financial year '{financial_year}' is invalid. Please use 'YYYY-YY' format (e.g., '2024-25').",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    filing = queries.create_filing(user_id=user_id, financial_year=financial_year, filing_type=filing_type)

    queries.create_audit_log(
        action="filing_created",
        filing_id=filing["id"],
        user_id=user_id,
        details={"financial_year": financial_year, "filing_type": filing_type},
    )

    return filing


def get_filing(filing_id: str, user_id: str, user_type: str = "individual") -> Dict[str, Any]:
    """Fetches complete details of a filing if user is authorized."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="The requested filing was not found.", status_code=status.HTTP_404_NOT_FOUND)

    # Authorization check
    if user_type == "individual" and str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="You do not have permission to access this filing.", status_code=status.HTTP_403_FORBIDDEN)

    # Fetch related records
    documents = queries.list_documents_by_filing(filing_id)
    ai_analysis = queries.get_ai_analysis_by_filing(filing_id)
    latest_calc = queries.get_latest_tax_calculation(filing_id)
    reviews = queries.get_reviews_by_filing(filing_id)
    audit_logs = queries.list_audit_logs_by_filing(filing_id)

    return {
        "filing": filing,
        "documents": documents,
        "ai_analysis": ai_analysis,
        "latest_calculation": latest_calc,
        "reviews": reviews,
        "audit_logs": audit_logs,
    }


def list_filings(user_id: str, user_type: str = "individual") -> List[Dict[str, Any]]:
    """Lists filings belonging to an individual or reviewable filings for a CA."""
    if user_type in ["ca", "admin"]:
        return queries.list_filings_for_ca()
    return queries.list_filings_by_user(user_id)


def update_filing_income_data(filing_id: str, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Updates editable filing financial fields."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="The requested filing was not found.", status_code=status.HTTP_404_NOT_FOUND)

    if str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="You are not authorized to modify this filing.", status_code=status.HTTP_403_FORBIDDEN)

    clean_updates = {k: v for k, v in updates.items() if v is not None}
    updated = queries.update_filing(filing_id, clean_updates)
    return updated or filing


def delete_filing(filing_id: str, user_id: str) -> bool:
    """Deletes a filing only if it is still in draft status."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="The requested filing was not found.", status_code=status.HTTP_404_NOT_FOUND)

    if str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="Unauthorized to delete this filing.", status_code=status.HTTP_403_FORBIDDEN)

    if filing.get("status") != "draft":
        raise AppException(
            code="CANNOT_DELETE",
            message=f"Filing in '{filing.get('status')}' status cannot be deleted. Only 'draft' filings may be removed.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return queries.delete_filing(filing_id)
