"""
FinEasy AI - AI Schemas
Models for document extraction results, AI analysis responses, and tax explanations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Form16ExtractionResult(BaseModel):
    employer_name: Optional[str] = Field(None, description="Extracted employer / company name")
    employee_name: Optional[str] = Field(None, description="Extracted employee / taxpayer name")
    pan_number: Optional[str] = Field(None, description="Extracted PAN number of employee")
    gross_salary: Optional[float] = Field(None, description="Gross salary or income from salary")
    deductions: Optional[float] = Field(None, description="Total allowable deductions")
    taxable_income: Optional[float] = Field(None, description="Total taxable income")
    tds: Optional[float] = Field(None, description="Tax deducted at source (TDS)")
    financial_year: Optional[str] = Field(None, description="Financial Year (e.g. 2024-25)")
    summary: Optional[str] = Field(None, description="AI-generated executive summary of Form 16")
    warnings: List[str] = Field(default_factory=list, description="Ambiguities or extraction flags")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence rating between 0 and 1")


class AIAnalysisResponse(BaseModel):
    id: str
    filing_id: str
    employer_name: Optional[str] = None
    employee_name: Optional[str] = None
    pan_number: Optional[str] = None
    gross_salary: Optional[float] = 0.0
    deductions: Optional[float] = 0.0
    taxable_income: Optional[float] = 0.0
    tds: Optional[float] = 0.0
    financial_year: Optional[str] = None
    summary: Optional[str] = None
    extracted_data: Dict[str, Any] = {}
    confidence_score: float = 0.0
    warnings: List[str] = []
    created_at: Optional[str] = None


class GeminiKeyRequest(BaseModel):
    api_key: str = Field(..., description="Google Gemini API Key")
    model: Optional[str] = Field("gemini-2.5-flash", description="Gemini model to use")


class AIExplainResponse(BaseModel):
    summary: str
    income_explanation: str
    tax_explanation: str
    warnings: List[str] = []
    disclaimer: str = "DEMO / EDUCATIONAL TAX EXPLANATION ONLY — NOT OFFICIAL LEGAL OR TAX ADVICE"
