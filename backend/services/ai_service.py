"""
FinEasy AI - AI Coordination Service
Coordinates AI document analysis with Google Gemini and natural language tax explanations.
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import status

from backend.database import queries
from backend.ai.document_extractor import analyse_form16, _clean_json_string
from backend.ai.gemini_client import get_gemini_client
from backend.ai.prompts import TAX_EXPLANATION_SYSTEM_PROMPT
from backend.services.filing_service import transition_status
from backend.utils.response import AppException
from backend.schemas.ai import AIExplainResponse

logger = logging.getLogger("fineasy.services.ai")


def process_filing_ai_analysis(filing_id: str, user_id: str) -> Dict[str, Any]:
    """
    Finds the Form 16 document for the filing, runs AI extraction, validates with Pydantic,
    updates the filing with initial income figures, and transitions state to 'analysed'.
    """
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    if str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="Unauthorized to run AI analysis on this filing.", status_code=status.HTTP_403_FORBIDDEN)

    docs = queries.list_documents_by_filing(filing_id)
    form16_doc = next((d for d in docs if d.get("document_type") == "form_16" and d.get("extracted_text")), None)

    if not form16_doc:
        # Check if there is any document with text
        form16_doc = next((d for d in docs if d.get("extracted_text")), None)

    if not form16_doc or not form16_doc.get("extracted_text"):
        raise AppException(
            code="NO_DOCUMENT_TEXT",
            message="No document with readable text was found. Please upload a legible Form 16 PDF first.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 1. State transition to analysing
    try:
        transition_status(filing_id, "analysing", actor_id=user_id)
    except Exception as e:
        logger.info("Transition to analysing bypassed: %s", e)

    # 2. Run AI extraction
    extracted = analyse_form16(form16_doc["extracted_text"])

    # 3. Store AI analysis
    raw_data = {
        "employer_name": extracted.employer_name,
        "employee_name": extracted.employee_name,
        "pan_number": extracted.pan_number,
        "gross_salary": extracted.gross_salary,
        "deductions": extracted.deductions or 0.0,
        "taxable_income": extracted.taxable_income,
        "tds": extracted.tds,
        "financial_year": extracted.financial_year,
        "summary": extracted.summary,
    }

    ai_record = queries.save_ai_analysis(
        filing_id=filing_id,
        employer_name=extracted.employer_name,
        gross_salary=extracted.gross_salary or 0.0,
        tds=extracted.tds or 0.0,
        financial_year=extracted.financial_year or filing.get("financial_year", "2024-25"),
        extracted_data=raw_data,
        confidence_score=extracted.confidence_score,
        warnings=extracted.warnings,
    )

    # Attach rich fields for AIAnalysisResponse
    ai_record["employee_name"] = extracted.employee_name
    ai_record["pan_number"] = extracted.pan_number
    ai_record["deductions"] = extracted.deductions or 0.0
    ai_record["taxable_income"] = extracted.taxable_income or 0.0
    ai_record["summary"] = extracted.summary

    # 4. Synchronize extracted numbers into filing draft
    filing_updates: Dict[str, Any] = {}
    if extracted.gross_salary is not None:
        filing_updates["gross_income"] = extracted.gross_salary
    if extracted.deductions is not None:
        filing_updates["deductions"] = extracted.deductions
    if extracted.tds is not None:
        filing_updates["tds_amount"] = extracted.tds

    if filing_updates:
        queries.update_filing(filing_id, filing_updates)

    # 5. Automatically compute deterministic tax with freshly extracted figures
    try:
        from backend.services import tax_service
        tax_service.run_tax_calculation(
            filing_id=filing_id,
            user_id=user_id,
            gross_income_override=extracted.gross_salary,
            deductions_override=extracted.deductions,
            tds_override=extracted.tds,
        )
    except Exception as e:
        logger.warning("Automatic tax calculation after AI analysis failed: %s", e)

    # 6. State transition to analysed
    transition_status(filing_id, "analysed", actor_id=user_id)

    # 7. Audit log
    queries.create_audit_log(
        action="document_analysed",
        filing_id=filing_id,
        user_id=user_id,
        details={
            "employer_name": extracted.employer_name,
            "employee_name": extracted.employee_name,
            "gross_salary": extracted.gross_salary,
            "deductions": extracted.deductions,
            "taxable_income": extracted.taxable_income,
            "tds": extracted.tds,
            "confidence_score": extracted.confidence_score,
        },
    )

    return ai_record


def generate_tax_explanation(filing_id: str, user_id: str) -> AIExplainResponse:
    """
    Generates a clear natural language explanation of the calculated tax result.
    Strictly reads deterministic calculation outputs and does NOT alter them.
    """
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    calc = queries.get_latest_tax_calculation(filing_id)
    if not calc:
        raise AppException(code="NO_CALCULATION", message="Tax calculation has not been executed yet for this filing.", status_code=status.HTTP_400_BAD_REQUEST)

    gross = calc.get("gross_income", 0.0)
    deductions = calc.get("deductions", 0.0)
    taxable = calc.get("taxable_income", 0.0)
    total_tax = calc.get("total_tax", 0.0)
    tds = calc.get("tds", 0.0)
    net = calc.get("refund_or_payable", 0.0)

    # Deterministic base summary template
    if net < 0:
        net_text = f"You are eligible for an estimated demo refund of ₹{abs(net):,.2f} because your TDS credit (₹{tds:,.2f}) exceeds total tax (₹{total_tax:,.2f})."
    elif net > 0:
        net_text = f"You have an estimated net demo tax liability of ₹{net:,.2f} remaining to be paid after accounting for ₹{tds:,.2f} TDS credit."
    else:
        net_text = "Your total tax liability matches your TDS credit exactly. No additional tax or refund is due."

    default_summary = (
        f"For Assessment Year based on gross income of ₹{gross:,.2f} and deductions of ₹{deductions:,.2f}, "
        f"taxable income is ₹{taxable:,.2f}. {net_text}"
    )

    default_income_exp = (
        f"Gross Income (₹{gross:,.2f}) minus Deductions (₹{deductions:,.2f}) results in a net Taxable Income of ₹{taxable:,.2f}."
    )

    default_tax_exp = (
        f"Calculated progressive slab tax is ₹{calc.get('tax_amount', 0.0):,.2f} plus 4% Health & Education Cess (₹{calc.get('cess', 0.0):,.2f}), "
        f"giving a total tax of ₹{total_tax:,.2f}."
    )

    client = get_gemini_client()
    if not client:
        return AIExplainResponse(
            summary=default_summary,
            income_explanation=default_income_exp,
            tax_explanation=default_tax_exp,
            warnings=["Explanation generated via local deterministic template (Gemini API offline)."],
        )

    try:
        from backend.config import settings
        prompt_content = f"""Structured Calculation Data:
- Gross Income: ₹{gross}
- Deductions: ₹{deductions}
- Taxable Income: ₹{taxable}
- Base Tax Amount: ₹{calc.get('tax_amount')}
- Cess (4%): ₹{calc.get('cess')}
- Total Tax: ₹{total_tax}
- TDS Credit: ₹{tds}
- Refund/Payable: ₹{net}

Please explain this calculation following the required JSON schema."""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[TAX_EXPLANATION_SYSTEM_PROMPT, prompt_content],
        )

        response_text = response.text if hasattr(response, "text") else str(response)
        cleaned = _clean_json_string(response_text)
        data = json.loads(cleaned)

        return AIExplainResponse(
            summary=data.get("summary", default_summary),
            income_explanation=data.get("income_explanation", default_income_exp),
            tax_explanation=data.get("tax_explanation", default_tax_exp),
            warnings=data.get("warnings", []),
        )

    except Exception as e:
        logger.warning("Gemini explanation generation failed: %s. Using default deterministic explanation.", e)
        return AIExplainResponse(
            summary=default_summary,
            income_explanation=default_income_exp,
            tax_explanation=default_tax_exp,
            warnings=[f"AI explanation service note: {str(e)}"],
        )


def get_filing_ai_analysis(filing_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the latest stored AI analysis record for a filing."""
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="Filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    record = queries.get_ai_analysis_by_filing(filing_id)
    if not record:
        return None

    extracted_data = record.get("extracted_data") or {}
    record["employee_name"] = extracted_data.get("employee_name")
    record["pan_number"] = extracted_data.get("pan_number")
    record["deductions"] = extracted_data.get("deductions") or float(filing.get("deductions", 0.0))
    record["taxable_income"] = extracted_data.get("taxable_income") or float(filing.get("taxable_income", 0.0))
    record["summary"] = extracted_data.get("summary")
    return record
