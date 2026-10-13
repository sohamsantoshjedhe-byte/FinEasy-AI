"""
Mock Government API - Filing Submission Simulation
Simulates Income Tax Department ITR submission and acknowledgement receipt generation.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter(prefix="/mock", tags=["Mock Government Submission"])

# Simulated in-memory database of submissions
_mock_submissions = {}


class MockSubmitRequest(BaseModel):
    filing_id: str
    user_id: Optional[str] = "demo-user"
    financial_year: Optional[str] = "2024-25"
    taxable_income: Optional[float] = 0.0
    total_tax: Optional[float] = 0.0
    tds: Optional[float] = 0.0


@router.post("/submit", summary="Simulate Final ITR Government Submission")
def mock_submit(payload: MockSubmitRequest):
    """
    Simulates final return upload to Income Tax Department server.
    Generates a synthetic ITR-V acknowledgement number.
    """
    ack_number = f"FINDEMO-2026-{uuid.uuid4().hex[:8].upper()}"
    submitted_at = datetime.now(timezone.utc).isoformat()

    receipt = {
        "success": True,
        "status": "submitted",
        "filing_id": payload.filing_id,
        "acknowledgement_number": ack_number,
        "submitted_at": submitted_at,
        "form_type": "ITR-1 (SAHAJ) - SIMULATED",
        "message": "SIMULATED GOVERNMENT SUBMISSION",
        "notice": "DEMO EDUCATIONAL PROTOTYPE — NOT AN ACTUAL TAX RETURN SUBMISSION TO ITD",
    }

    _mock_submissions[payload.filing_id] = receipt
    return receipt


@router.get("/acknowledgement/{filing_id}", summary="Get ITR-V Acknowledgement Receipt")
def get_acknowledgement(filing_id: str):
    """Fetches previously issued mock ITR-V acknowledgement details."""
    receipt = _mock_submissions.get(filing_id)
    if not receipt:
        ack_number = f"FINDEMO-2026-{filing_id[:8].upper()}"
        return {
            "success": True,
            "filing_id": filing_id,
            "acknowledgement_number": ack_number,
            "status": "submitted",
            "message": "SIMULATED GOVERNMENT ACKNOWLEDGEMENT (GENERATED)",
        }
    return receipt
