"""
FinEasy AI - Deterministic Tax Calculator
Pure mathematical calculation functions executing independently of AI/LLM models.
"""

from typing import Any, Dict
from backend.tax_engine.rules import (
    DEMO_TAX_SLABS,
    DEMO_CESS_RATE,
    DEMO_REBATE_87A_THRESHOLD,
    RULES_VERSION,
    DISCLAIMER,
)


def calculate_taxable_income(gross_income: float, deductions: float) -> float:
    """Calculates taxable income as max(0, gross_income - deductions)."""
    return max(0.0, round(float(gross_income) - float(deductions), 2))


def calculate_tax_slab(taxable_income: float) -> float:
    """
    Calculates tax amount based on demo progressive slabs.
    Applies educational demo 87A rebate if taxable income is within the rebate threshold.
    """
    taxable_income = float(taxable_income)
    if taxable_income <= 0:
        return 0.0

    tax_amount = 0.0
    for lower, upper, rate in DEMO_TAX_SLABS:
        if taxable_income > lower:
            slab_limit = min(taxable_income, upper) if upper is not None else taxable_income
            taxable_chunk = slab_limit - lower
            tax_amount += taxable_chunk * rate
        else:
            break

    # Apply demo 87A rebate
    if taxable_income <= DEMO_REBATE_87A_THRESHOLD:
        tax_amount = 0.0

    return round(tax_amount, 2)


def calculate_cess(tax_amount: float) -> float:
    """Calculates health and education cess on tax amount."""
    return round(float(tax_amount) * DEMO_CESS_RATE, 2)


def calculate_total_tax(tax_amount: float, cess: float) -> float:
    """Calculates total tax including cess."""
    return round(float(tax_amount) + float(cess), 2)


def calculate_refund_or_payable(total_tax: float, tds: float) -> float:
    """
    Calculates net refund or tax payable.
    Positive value: Tax is payable to the government.
    Negative value: Taxpayer is eligible for a refund from the government.
    """
    return round(float(total_tax) - float(tds), 2)


def calculate_tax(gross_income: float, deductions: float = 0.0, tds: float = 0.0) -> Dict[str, Any]:
    """
    Complete deterministic tax calculation pipeline.
    """
    gross = max(0.0, round(float(gross_income), 2))
    deduct = max(0.0, round(float(deductions), 2))
    tax_deducted = max(0.0, round(float(tds), 2))

    taxable = calculate_taxable_income(gross, deduct)
    tax_amt = calculate_tax_slab(taxable)
    cess_amt = calculate_cess(tax_amt)
    total_tax = calculate_total_tax(tax_amt, cess_amt)
    net_payable_or_refund = calculate_refund_or_payable(total_tax, tax_deducted)

    return {
        "gross_income": gross,
        "deductions": deduct,
        "taxable_income": taxable,
        "tax_amount": tax_amt,
        "cess": cess_amt,
        "total_tax": total_tax,
        "tds": tax_deducted,
        "refund_or_payable": net_payable_or_refund,
        "calculation_version": RULES_VERSION,
        "disclaimer": DISCLAIMER,
    }
