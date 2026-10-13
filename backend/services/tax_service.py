"""
FinEasy AI - Tax Service
Executes deterministic tax calculations and persists history in the database.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import status

from backend.database import queries
from backend.tax_engine.calculator import calculate_tax
from backend.services.filing_service import transition_status
from backend.utils.response import AppException

logger = logging.getLogger("fineasy.services.tax")


def run_tax_calculation(
    filing_id: str,
    user_id: str,
    gross_income_override: Optional[float] = None,
    deductions_override: Optional[float] = None,
    tds_override: Optional[float] = None
) -> Dict[str, Any]:
    """
    Runs deterministic tax calculations for a filing using either saved figures or overrides.
    """
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    if str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="Unauthorized to calculate tax for this filing.", status_code=status.HTTP_403_FORBIDDEN)

    # Determine input values: override -> filing record -> 0.0
    gross = gross_income_override if gross_income_override is not None else float(filing.get("gross_income", 0.0))
    deductions = deductions_override if deductions_override is not None else float(filing.get("deductions", 0.0))
    tds = tds_override if tds_override is not None else float(filing.get("tds_amount", 0.0))

    # Deterministic calculation
    result = calculate_tax(gross_income=gross, deductions=deductions, tds=tds)

    # Persist in tax_calculations table
    calc_record = queries.save_tax_calculation(
        filing_id=filing_id,
        gross_income=result["gross_income"],
        deductions=result["deductions"],
        taxable_income=result["taxable_income"],
        tax_amount=result["tax_amount"],
        cess=result["cess"],
        total_tax=result["total_tax"],
        tds=result["tds"],
        refund_or_payable=result["refund_or_payable"],
        calculation_version=result["calculation_version"],
    )

    # Update filing table aggregates
    queries.update_filing(filing_id, {
        "gross_income": result["gross_income"],
        "deductions": result["deductions"],
        "taxable_income": result["taxable_income"],
        "tax_amount": result["total_tax"],
        "tds_amount": result["tds"],
        "refund_amount": abs(result["refund_or_payable"]) if result["refund_or_payable"] < 0 else 0.0,
    })

    # Transition state to calculation_complete
    try:
        transition_status(filing_id, "calculation_complete", actor_id=user_id)
    except Exception as e:
        logger.info("Transition to calculation_complete skipped or already done: %s", e)

    # Audit log
    queries.create_audit_log(
        action="tax_calculated",
        filing_id=filing_id,
        user_id=user_id,
        details={
            "calculation_version": result["calculation_version"],
            "taxable_income": result["taxable_income"],
            "total_tax": result["total_tax"],
            "refund_or_payable": result["refund_or_payable"],
        },
    )

    return result


def get_filing_tax_calculation(filing_id: str, user_id: str, user_type: str = "individual") -> Dict[str, Any]:
    """Retrieves the most recent tax calculation for a filing."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    if user_type == "individual" and str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="Unauthorized to view this calculation.", status_code=status.HTTP_403_FORBIDDEN)

    calc = queries.get_latest_tax_calculation(filing_id)
    if not calc:
        raise AppException(code="CALCULATION_NOT_FOUND", message="No calculation has been generated for this filing yet.", status_code=status.HTTP_404_NOT_FOUND)

    calc["disclaimer"] = "EDUCATIONAL DEMO RULES — NOT FOR ACTUAL TAX FILING"
    return calc
