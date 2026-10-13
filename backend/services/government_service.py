"""
FinEasy AI - Government API Client Service
Handles communication with the Mock Government API for prefill, validation, and demo filing submission.
"""

import logging
from typing import Dict, Any
import httpx
from fastapi import status

from backend.config import settings
from backend.database import queries
from backend.services.filing_service import transition_status
from backend.utils.response import AppException

logger = logging.getLogger("fineasy.services.government")


async def get_mock_prefill_data(user_id: str) -> Dict[str, Any]:
    """Fetches simulated prefilled Form 26AS/AIS data from Mock Government API."""
    url = f"{settings.MOCK_GOVERNMENT_URL}/mock/prefill/{user_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning("Mock Government API unavailable at %s (%s). Using built-in fallback demo prefill.", url, e)

    # Built-in educational fallback if mock server is not currently running
    return {
        "success": True,
        "user_id": user_id,
        "data": {
            "gross_salary": 850000.0,
            "tds": 42000.0,
            "interest_income": 12000.0,
        },
        "source": "MOCK_GOVERNMENT_API_FALLBACK",
        "notice": "DEMO DATA — NOT REAL TAXPAYER DATA",
    }


async def validate_with_government_mock(filing_id: str, taxable_income: float, tax_amount: float) -> Dict[str, Any]:
    """Calls Mock Government API validation endpoint."""
    url = f"{settings.MOCK_GOVERNMENT_URL}/mock/validate"
    payload = {
        "filing_id": filing_id,
        "taxable_income": taxable_income,
        "tax_amount": tax_amount,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning("Mock Government API validate unreachable (%s). Using fallback validation.", e)

    # Built-in fallback
    return {
        "valid": True,
        "errors": [],
        "reference_id": f"DEMO-VAL-{filing_id[:8].upper()}",
        "disclaimer": "SIMULATED GOVERNMENT VALIDATION (DEMO)",
    }


async def submit_filing_to_government(filing_id: str, user_id: str) -> Dict[str, Any]:
    """
    Submits an approved filing to the Mock Government API, generates acknowledgement,
    transitions status to 'submitted', and logs audit entry.
    """
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    if str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="Unauthorized to submit this filing.", status_code=status.HTTP_403_FORBIDDEN)

    if filing.get("status") != "approved":
        raise AppException(
            code="NOT_APPROVED",
            message=f"Filing cannot be submitted in '{filing.get('status')}' status. CA approval is required first.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    calc = queries.get_latest_tax_calculation(filing_id) or {}
    submission_payload = {
        "filing_id": filing_id,
        "user_id": user_id,
        "financial_year": filing.get("financial_year"),
        "taxable_income": calc.get("taxable_income", filing.get("taxable_income", 0.0)),
        "total_tax": calc.get("total_tax", filing.get("tax_amount", 0.0)),
        "tds": calc.get("tds", filing.get("tds_amount", 0.0)),
    }

    url = f"{settings.MOCK_GOVERNMENT_URL}/mock/submit"
    result = None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=submission_payload)
            if resp.status_code == 200:
                result = resp.json()
    except Exception as e:
        logger.warning("Mock Government API submit unreachable (%s). Using local fallback response.", e)

    if not result:
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ack = f"FINDEMO-2026-{filing_id[:8].upper()}"
        result = {
            "success": True,
            "status": "submitted",
            "acknowledgement_number": ack,
            "submitted_at": now,
            "message": "SIMULATED GOVERNMENT SUBMISSION (FALLBACK)",
        }

    # Transition state to submitted
    transition_status(filing_id, "submitted", actor_id=user_id, notes=f"Acknowledged: {result.get('acknowledgement_number')}")

    # Audit log
    queries.create_audit_log(
        action="filing_submitted",
        filing_id=filing_id,
        user_id=user_id,
        details={
            "acknowledgement_number": result.get("acknowledgement_number"),
            "status": "submitted",
            "simulated": True,
        },
    )

    return result
