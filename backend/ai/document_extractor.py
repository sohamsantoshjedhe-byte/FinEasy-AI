"""
FinEasy AI - AI Document Extractor
Performs AI-assisted extraction from Form 16 text using Google Gemini with regex fallbacks.
"""

import json
import re
import logging
from typing import Dict, Any, Optional

from backend.ai.gemini_client import get_gemini_client
from backend.ai.prompts import (
    FORM16_EXTRACTION_SYSTEM_PROMPT,
    FORM16_EXTRACTION_USER_PROMPT,
)
from backend.schemas.ai import Form16ExtractionResult

logger = logging.getLogger("fineasy.ai.extractor")


def _clean_json_string(text: str) -> str:
    """Removes Markdown code blocks and extra whitespace from LLM output."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _regex_heuristic_fallback(document_text: str) -> Form16ExtractionResult:
    """
    Deterministic rule/regex-based extraction used when Gemini API is offline or unconfigured.
    Accurately parses both TRACES standard Form 16 Part B certificates and generic formats.
    """
    warnings = ["Extracted via deterministic heuristic fallback (Gemini API standby)."]
    employer_name = None
    employee_name = None
    pan_number = None
    financial_year = "2024-25"
    gross_salary = None
    deductions = 0.0
    taxable_income = None
    tds = None

    # 1. Search for Employer Name (TRACES & generic)
    emp_match = re.search(r"Name\s+and\s+address\s+of\s+the\s+Employer[^\n]*\n+([A-Za-z0-9\s,\.\(\)&]+)", document_text, re.IGNORECASE)
    if not emp_match:
        emp_match = re.search(r"(?:Employer|Deductor|Company)\s*(?:Name)?[:\-]\s*([A-Za-z0-9\s,\.\(\)&]+)", document_text, re.IGNORECASE)
    if emp_match:
        employer_name = emp_match.group(1).split("\n")[0].strip()

    # 2. Search for Employee Name
    ee_match = re.search(r"Name\s+and\s+address\s+of\s+the\s+Employee[^\n]*\n+([A-Za-z0-9\s,\.\(\)&]+)", document_text, re.IGNORECASE)
    if not ee_match:
        ee_match = re.search(r"(?:Employee|Taxpayer)\s*(?:Name)?[:\-]\s*([A-Za-z0-9\s,\.\(\)&]+)", document_text, re.IGNORECASE)
    if ee_match:
        employee_name = ee_match.group(1).split("\n")[0].strip()

    # 3. Search for Employee PAN
    pan_match = re.search(r"PAN\s+(?:of\s+the\s+Employee|of\s+Employee)[^\n]*[:\s\n]+([A-Z]{5}[0-9]{4}[A-Z])", document_text, re.IGNORECASE)
    if not pan_match:
        pan_match = re.search(r"(?:Employee\s+PAN|PAN)[:\s]+([A-Z]{5}[0-9]{4}[A-Z])", document_text, re.IGNORECASE)
    if pan_match:
        pan_number = pan_match.group(1).strip()

    # 4. Search for Financial Year
    fy_match = re.search(r"(?:Financial\s*Year|F\.?\s*Y\.?|Assessment\s*Year|A\.?\s*Y\.?)[:\s\-]*(\d{4}[-\/]\d{2,4})", document_text, re.IGNORECASE)
    if fy_match:
        fy_raw = fy_match.group(1).replace("/", "-")
        if len(fy_raw) == 9:  # 2024-2025 -> 2024-25
            financial_year = f"{fy_raw[:5]}{fy_raw[7:]}"
        else:
            financial_year = fy_raw

    # 5. Search for Gross Salary
    gross_match = re.search(r"section\s*17\(1\)[^\n]*?\s+([\d,]+(?:\.\d{2})?)", document_text, re.IGNORECASE)
    if not gross_match:
        gross_match = re.search(r"([\d,]+(?:\.\d{2})?)\s*(?:\d\.\s*)?Total\s+amount\s+of\s+salary\s+received", document_text, re.IGNORECASE)
    if not gross_match:
        gross_match = re.search(
            r"(?:Total\s*Gross\s*Salary|Total\s*Salary|Gross\s*Salary|Salary\s*as\s*per\s*provisions[^\n]*?)[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)",
            document_text,
            re.IGNORECASE,
        )
    if gross_match:
        try:
            gross_salary = float(gross_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # 6. Search for Taxable Income
    taxable_match = re.search(r"([\d,]+(?:\.\d{2})?)\s*Total\s+taxable\s+income", document_text, re.IGNORECASE)
    if not taxable_match:
        taxable_match = re.search(r"Total\s+taxable\s+income[^\n]*?[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)", document_text, re.IGNORECASE)
    if taxable_match:
        try:
            taxable_income = float(taxable_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # 7. Deductions calculation
    via_match = re.search(r"([\d,]+(?:\.\d{2})?)\s*11\.\s*\n", document_text)
    if not via_match:
        via_match = re.search(r"Aggregate\s+of\s+deductible\s+amount\s+under\s+Chapter\s+VI-A[^\n]*?\n[^\n]*?([\d,]+(?:\.\d{2})?)", document_text, re.IGNORECASE)
    ded_via = float(via_match.group(1).replace(",", "")) if via_match else 0.0

    if gross_salary is not None and taxable_income is not None and gross_salary > taxable_income:
        deductions = round(gross_salary - taxable_income, 2)
    elif ded_via > 0:
        deductions = ded_via + 50000.0
    else:
        ded_match = re.search(r"(?:Total\s*Deductions|Deductions\s*under\s*Chapter\s*VI-A)[^\n]*?[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)", document_text, re.IGNORECASE)
        deductions = float(ded_match.group(1).replace(",", "")) if ded_match else 50000.0

    # 8. Search for TDS / Net Tax Payable
    tds_match = re.search(
        r"Total\s+Tax\s+Deducted\s+and\s+Deposited[^\n]*?[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)",
        document_text,
        re.IGNORECASE,
    )
    if not tds_match:
        tds_match = re.search(r"Net\s+tax\s+payable[^\n\d]*\(\d+-\d+\)\d*\.\s*([\d,]+(?:\.\d{2})?)", document_text, re.IGNORECASE)
    if not tds_match:
        tds_match = re.search(
            r"(?:Total\s*Tax\s*Deducted|Net\s*Tax\s*Deposited)[^\n]*?[:\-]?\s*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d{2})?)",
            document_text,
            re.IGNORECASE,
        )
    if tds_match:
        try:
            tds = float(tds_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # 9. Generate AI-style executive summary
    ee_display = employee_name or "Taxpayer"
    emp_display = f" at {employer_name}" if employer_name else ""
    pan_display = f" (PAN: {pan_number})" if pan_number else ""
    gross_disp = f"₹{gross_salary:,.2f}" if gross_salary is not None else "N/A"
    ded_disp = f"₹{deductions:,.2f}" if deductions else "₹0.00"
    tax_disp = f"₹{taxable_income:,.2f}" if taxable_income is not None else (f"₹{(gross_salary - deductions):,.2f}" if gross_salary else "N/A")
    tds_disp = f"₹{tds:,.2f}" if tds is not None else "₹0.00"

    summary = (
        f"Form 16 analyzed for {ee_display}{pan_display}{emp_display}. "
        f"Total Gross Salary reported is {gross_disp} with claimed deductions of {ded_disp}, "
        f"leaving a net Taxable Income base of {tax_disp}. "
        f"Total TDS deducted and credited is {tds_disp} for AY {financial_year}."
    )

    confidence = 0.90 if (gross_salary is not None and tds is not None) else 0.50

    return Form16ExtractionResult(
        employer_name=employer_name,
        employee_name=employee_name,
        pan_number=pan_number,
        gross_salary=gross_salary,
        deductions=deductions,
        taxable_income=taxable_income,
        tds=tds,
        financial_year=financial_year,
        summary=summary,
        warnings=warnings,
        confidence_score=confidence,
    )


def analyse_form16(document_text: str) -> Form16ExtractionResult:
    """
    Extracts structured taxpayer information from Form 16 text.
    Uses official google-genai SDK when configured; falls back gracefully if offline.
    """
    if not document_text or not document_text.strip():
        return Form16ExtractionResult(
            employer_name=None,
            employee_name=None,
            pan_number=None,
            gross_salary=None,
            deductions=None,
            taxable_income=None,
            tds=None,
            financial_year=None,
            summary="Empty document: No readable text found in upload.",
            warnings=["Document is empty or contains no readable text."],
            confidence_score=0.0,
        )

    client = get_gemini_client()
    if not client:
        return _regex_heuristic_fallback(document_text)

    try:
        from backend.config import settings
        prompt = FORM16_EXTRACTION_USER_PROMPT.format(document_text=document_text[:8000])

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[FORM16_EXTRACTION_SYSTEM_PROMPT, prompt],
        )

        response_text = response.text if hasattr(response, "text") else str(response)
        cleaned_json = _clean_json_string(response_text)
        data = json.loads(cleaned_json)

        # Fallback to regex if Gemini returned null for gross_salary
        fallback = _regex_heuristic_fallback(document_text)

        employer_name = data.get("employer_name") or fallback.employer_name
        employee_name = data.get("employee_name") or fallback.employee_name
        pan_number = data.get("pan_number") or fallback.pan_number
        gross_salary = float(data["gross_salary"]) if data.get("gross_salary") is not None else fallback.gross_salary
        deductions = float(data["deductions"]) if data.get("deductions") is not None else fallback.deductions
        taxable_income = float(data["taxable_income"]) if data.get("taxable_income") is not None else fallback.taxable_income
        tds = float(data["tds"]) if data.get("tds") is not None else fallback.tds
        financial_year = data.get("financial_year") or fallback.financial_year
        summary = data.get("summary") or fallback.summary

        return Form16ExtractionResult(
            employer_name=employer_name,
            employee_name=employee_name,
            pan_number=pan_number,
            gross_salary=gross_salary,
            deductions=deductions,
            taxable_income=taxable_income,
            tds=tds,
            financial_year=financial_year,
            summary=summary,
            warnings=data.get("warnings", []),
            confidence_score=float(data.get("confidence_score", 0.95)),
        )

    except Exception as e:
        logger.warning("Gemini AI extraction encountered error: %s. Reverting to heuristic fallback.", e)
        fallback_result = _regex_heuristic_fallback(document_text)
        fallback_result.warnings.append(f"AI service note: {str(e)}")
        return fallback_result
