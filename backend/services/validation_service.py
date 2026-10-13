"""
FinEasy AI - Validation Service
Validates complete filing data before submission to CA review.
"""

import logging
from typing import Dict, Any
from fastapi import status

from backend.database import queries
from backend.tax_engine.validator import validate_tax_data
from backend.services.filing_service import transition_status
from backend.utils.response import AppException

logger = logging.getLogger("fineasy.services.validation")


def validate_filing_for_review(filing_id: str, user_id: str) -> Dict[str, Any]:
    """
    Validates filing completeness, runs tax data sanity checks, and
    transitions filing status to 'ca_review' if validation passes.
    """
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    if str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="Unauthorized to validate this filing.", status_code=status.HTTP_403_FORBIDDEN)

    # Fetch latest calculation if available
    calc = queries.get_latest_tax_calculation(filing_id)

    gross = calc.get("gross_income") if calc else filing.get("gross_income")
    deductions = calc.get("deductions") if calc else filing.get("deductions")
    tds = calc.get("tds") if calc else filing.get("tds_amount")
    fy = filing.get("financial_year")

    # Run tax data validation
    validation_result = validate_tax_data(
        gross_income=gross,
        deductions=deductions,
        tds=tds,
        financial_year=fy,
    )

    # Document check
    docs = queries.list_documents_by_filing(filing_id)
    if not docs:
        validation_result["warnings"].append("No documents attached to this filing.")

    # Status transition if valid
    if validation_result["valid"]:
        try:
            transition_status(filing_id, "ca_review", actor_id=user_id, notes="Validation passed; queued for CA review.")
        except Exception as e:
            logger.info("Transition to ca_review note: %s", e)

    # Create audit log
    queries.create_audit_log(
        action="validation_completed",
        filing_id=filing_id,
        user_id=user_id,
        details={"valid": validation_result["valid"], "errors_count": len(validation_result["errors"]), "warnings_count": len(validation_result["warnings"])},
    )

    return validation_result
