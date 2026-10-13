"""
FinEasy AI - Tax & Filing Data Validation Tests
"""

from backend.tax_engine.validator import validate_tax_data, validate_financial_year


def test_financial_year_format():
    assert validate_financial_year("2024-25") is True
    assert validate_financial_year("2025-26") is True
    assert validate_financial_year("2023-24") is True
    assert validate_financial_year("2024-2025") is False
    assert validate_financial_year("2024-26") is False  # Non-consecutive
    assert validate_financial_year("invalid-fy") is False
    assert validate_financial_year(None) is False


def test_tax_data_valid():
    result = validate_tax_data(
        gross_income=850000.0,
        deductions=150000.0,
        tds=35000.0,
        financial_year="2024-25",
    )
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_tax_data_negative_values():
    result = validate_tax_data(
        gross_income=-5000.0,
        deductions=10000.0,
        tds=0.0,
        financial_year="2024-25",
    )
    assert result["valid"] is False
    assert any("negative" in err.lower() for err in result["errors"])


def test_tax_data_invalid_fy():
    result = validate_tax_data(
        gross_income=500000.0,
        deductions=50000.0,
        tds=10000.0,
        financial_year="2024/2025",
    )
    assert result["valid"] is False
    assert any("financial year" in err.lower() for err in result["errors"])


def test_tax_data_warnings():
    # Deductions > Gross income should trigger a warning, not a hard crash
    result = validate_tax_data(
        gross_income=100000.0,
        deductions=150000.0,
        tds=None,
        financial_year="2024-25",
    )
    assert result["valid"] is True
    assert len(result["warnings"]) > 0
