"""
FinEasy AI - Chartered Accountant (CA) Review Service
Manages professional review workflows, approvals, rejections, and feedback.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import status

from backend.database import queries
from backend.services.filing_service import transition_status
from backend.utils.response import AppException

logger = logging.getLogger("fineasy.services.review")


def list_pending_ca_reviews() -> List[Dict[str, Any]]:
    """Lists all filings currently in 'ca_review' status awaiting review."""
    return queries.list_filings_for_ca()


def ca_approve_filing(filing_id: str, reviewer_id: str, comments: Optional[str] = None) -> Dict[str, Any]:
    """Approves a filing for simulated government submission."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    # 1. State transition to approved
    transition_status(filing_id, "approved", actor_id=reviewer_id, notes=comments or "Approved by CA")

    # 2. Record review record
    review = queries.create_review(
        filing_id=filing_id,
        reviewer_id=reviewer_id,
        status="approved",
        comments=comments,
    )

    # 3. Audit log
    queries.create_audit_log(
        action="ca_approved",
        filing_id=filing_id,
        user_id=reviewer_id,
        details={"comments": comments},
    )

    return review


def ca_reject_filing(filing_id: str, reviewer_id: str, comments: Optional[str] = None) -> Dict[str, Any]:
    """Rejects a filing."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    transition_status(filing_id, "rejected", actor_id=reviewer_id, notes=comments or "Rejected by CA")

    review = queries.create_review(
        filing_id=filing_id,
        reviewer_id=reviewer_id,
        status="rejected",
        comments=comments,
    )

    queries.create_audit_log(
        action="ca_rejected",
        filing_id=filing_id,
        user_id=reviewer_id,
        details={"comments": comments},
    )

    return review


def ca_request_changes(filing_id: str, reviewer_id: str, comments: Optional[str] = None) -> Dict[str, Any]:
    """Sends filing back to taxpayer requesting revisions."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    transition_status(filing_id, "changes_requested", actor_id=reviewer_id, notes=comments or "Changes requested by CA")

    review = queries.create_review(
        filing_id=filing_id,
        reviewer_id=reviewer_id,
        status="changes_requested",
        comments=comments,
    )

    queries.create_audit_log(
        action="ca_changes_requested",
        filing_id=filing_id,
        user_id=reviewer_id,
        details={"comments": comments},
    )

    return review


def get_filing_reviews(filing_id: str) -> List[Dict[str, Any]]:
    """Returns review history for a filing."""
    return queries.get_reviews_by_filing(filing_id)
