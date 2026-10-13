"""
FinEasy AI - Deterministic Tax Engine Tests
"""

from backend.tax_engine.calculator import (
    calculate_taxable_income,
    calculate_tax_slab,
    calculate_cess,
    calculate_total_tax,
    calculate_refund_or_payable,
    calculate_tax,
)


def test_taxable_income_calculation():
    assert calculate_taxable_income(1000000, 150000) == 850000.0
    # Negative gross or excessive deductions should floor at 0
    assert calculate_taxable_income(50000, 100000) == 0.0


def test_demo_rebate_under_7_lakhs():
    # Taxable income <= 7,00,000 gets full demo rebate
    assert calculate_tax_slab(600000) == 0.0
    assert calculate_tax_slab(700000) == 0.0


def test_progressive_tax_slab_above_7_lakhs():
    # For taxable income = 8,00,000:
    # 0 to 3L: 0
    # 3L to 6L (3L * 5%): 15,000
    # 6L to 8L (2L * 10%): 20,000
    # Total slab tax: 35,000
    slab_tax = calculate_tax_slab(800000)
    assert slab_tax == 35000.0


def test_cess_calculation():
    tax_amt = 35000.0
    cess = calculate_cess(tax_amt)
    assert cess == 1400.0  # 4% of 35000


def test_total_tax_and_refund_or_payable():
    tax_amt = 35000.0
    cess = 1400.0
    total = calculate_total_tax(tax_amt, cess)
    assert total == 36400.0

    # Case A: TDS was 40,000 -> Refund of 3,600 (-3600)
    refund = calculate_refund_or_payable(total, 40000.0)
    assert refund == -3600.0

    # Case B: TDS was 30,000 -> Net payable of 6,400 (+6400)
    payable = calculate_refund_or_payable(total, 30000.0)
    assert payable == 6400.0


def test_full_calculate_tax_pipeline():
    result = calculate_tax(gross_income=950000.0, deductions=150000.0, tds=40000.0)
    assert result["gross_income"] == 950000.0
    assert result["deductions"] == 150000.0
    assert result["taxable_income"] == 800000.0
    assert result["tax_amount"] == 35000.0
    assert result["cess"] == 1400.0
    assert result["total_tax"] == 36400.0
    assert result["tds"] == 40000.0
    assert result["refund_or_payable"] == -3600.0
    assert "EDUCATIONAL DEMO RULES" in result["disclaimer"]
