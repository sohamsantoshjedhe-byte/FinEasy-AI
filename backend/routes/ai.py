"""
FinEasy AI - AI Routes
Endpoints for AI document extraction and natural language tax explanations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from backend.schemas.ai import AIAnalysisResponse, AIExplainResponse, GeminiKeyRequest
from backend.dependencies import get_current_user
from backend.services import ai_service
from backend.ai.gemini_client import set_gemini_api_key

router = APIRouter(prefix="/api/ai", tags=["AI Engine"])


@router.post("/analyse/{filing_id}", response_model=AIAnalysisResponse, summary="Extract data from Form 16 using Gemini AI")
def analyse_document(filing_id: str, current_user: dict = Depends(get_current_user)):
    """
    Extracts employer name, employee name, PAN, gross salary, deductions, taxable income, TDS,
    and financial year from the uploaded document text.
    Validates output with Pydantic, stores analysis, and computes tax.
    """
    return ai_service.process_filing_ai_analysis(filing_id=filing_id, user_id=current_user["user_id"])


@router.get("/analysis/{filing_id}", response_model=Optional[AIAnalysisResponse], summary="Get latest Form 16 AI analysis")
def get_analysis_endpoint(filing_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves the most recent AI Form 16 extraction and summary for a filing."""
    record = ai_service.get_filing_ai_analysis(filing_id=filing_id, user_id=current_user["user_id"])
    return record


@router.post("/set-key", summary="Configure Gemini API Key")
def configure_gemini_key(payload: GeminiKeyRequest, current_user: dict = Depends(get_current_user)):
    """
    Saves and initializes the Google Gemini API key at runtime.
    Enables direct Gemini 2.5 Flash / 1.5 Flash extraction and explanations.
    """
    success = set_gemini_api_key(payload.api_key, payload.model)
    return {
        "success": True,
        "message": "Gemini AI client connected successfully." if success else "Key stored; testing connection on next request.",
        "model": payload.model,
    }


@router.post("/explain/{filing_id}", response_model=AIExplainResponse, summary="Explain tax calculation in plain language")
def explain_calculation(filing_id: str, current_user: dict = Depends(get_current_user)):
    """
    Provides an AI-generated educational explanation of the computed tax liability or refund.
    Strictly reads deterministic calculation outputs and does not alter figures.
    """
    return ai_service.generate_tax_explanation(filing_id=filing_id, user_id=current_user["user_id"])
