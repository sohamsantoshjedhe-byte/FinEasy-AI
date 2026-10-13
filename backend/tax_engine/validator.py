"""
FinEasy AI - Tax Data Validator
Validates financial and tax details for consistency, bounds, and required attributes.
"""

import re
from typing import Any, Dict, List, Optional


def validate_financial_year(fy: Optional[str]) -> bool:
    """Validates financial year format (e.g., '2024-25' or '2025-26')."""
    if not fy or not isinstance(fy, str):
        return False
    match = re.match(r"^(\d{4})-(\d{2})$", fy.strip())
    if not match:
        return False
    start_year = int(match.group(1))
    end_suffix = int(match.group(2))
    expected_suffix = (start_year + 1) % 100
    return end_suffix == expected_suffix


def validate_tax_data(
    gross_income: Any,
    deductions: Any,
    tds: Any,
    financial_year: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates tax inputs against business constraints and sanity checks.
    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Missing values check
    if gross_income is None:
        errors.append("Gross income is required.")
    if deductions is None:
        warnings.append("Deductions value was not specified; defaulting to 0.00.")
    if tds is None:
        warnings.append("TDS value was not specified; assuming zero TDS credit.")

    # 2. Financial year check
    if financial_year is not None:
        if not validate_financial_year(financial_year):
            errors.append(
                f"Invalid financial year format '{financial_year}'. Expected YYYY-YY (e.g. '2024-25')."
            )

    # Convert to floats if possible
    gross_val = 0.0
    deduct_val = 0.0
    tds_val = 0.0

    if gross_income is not None:
        try:
            gross_val = float(gross_income)
            if gross_val < 0:
                errors.append("Gross income cannot be negative.")
            elif gross_val == 0:
                warnings.append("Gross income is reported as zero. Verify if filing is required.")
        except (ValueError, TypeError):
            errors.append("Gross income must be a valid number.")

    if deductions is not None:
        try:
            deduct_val = float(deductions)
            if deduct_val < 0:
                errors.append("Deductions cannot be negative.")
        except (ValueError, TypeError):
            errors.append("Deductions must be a valid number.")

    if tds is not None:
        try:
            tds_val = float(tds)
            if tds_val < 0:
                errors.append("TDS cannot be negative.")
        except (ValueError, TypeError):
            errors.append("TDS must be a valid number.")

    # 3. Inconsistent values check
    if gross_val > 0 and deduct_val > gross_val:
        warnings.append(
            f"Deductions (₹{deduct_val:,.2f}) exceed gross income (₹{gross_val:,.2f}). Taxable income will be capped at ₹0.00."
        )

    if tds_val > gross_val and gross_val > 0:
        warnings.append(
            f"TDS (₹{tds_val:,.2f}) is unusually higher than gross income (₹{gross_val:,.2f}). Please verify Form 16."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
