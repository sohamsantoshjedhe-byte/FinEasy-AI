"""
FinEasy AI - Database Query Operations
Database helper functions abstracting queries across Supabase tables.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from backend.database.supabase import get_supabase_client

logger = logging.getLogger("fineasy.queries")


# ------------------------------------------------------------------------------
# PROFILES
# ------------------------------------------------------------------------------
def get_profile_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("profiles").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None


def get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("profiles").select("*").eq("id", profile_id).execute()
    return res.data[0] if res.data else None


def create_profile(user_id: str, email: str, name: str, user_type: str = "individual") -> Dict[str, Any]:
    client = get_supabase_client()
    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "user_type": user_type,
    }
    res = client.table("profiles").insert(payload).execute()
    return res.data[0] if res.data else payload


def update_profile(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("profiles").update(updates).eq("user_id", user_id).execute()
    return res.data[0] if res.data else None


# ------------------------------------------------------------------------------
# FILINGS
# ------------------------------------------------------------------------------
def create_filing(user_id: str, financial_year: str, filing_type: str = "ITR") -> Dict[str, Any]:
    client = get_supabase_client()
    payload = {
        "user_id": user_id,
        "financial_year": financial_year,
        "filing_type": filing_type,
        "status": "draft",
        "gross_income": 0.0,
        "deductions": 0.0,
        "taxable_income": 0.0,
        "tax_amount": 0.0,
        "tds_amount": 0.0,
        "refund_amount": 0.0,
    }
    res = client.table("filings").insert(payload).execute()
    return res.data[0] if res.data else payload


def get_filing_by_id(filing_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("filings").select("*").eq("id", filing_id).execute()
    return res.data[0] if res.data else None


def list_filings_by_user(user_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("filings").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data or []


def list_filings_for_ca() -> List[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("filings").select("*").eq("status", "ca_review").order("created_at", desc=True).execute()
    return res.data or []


def update_filing(filing_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("filings").update(updates).eq("id", filing_id).execute()
    return res.data[0] if res.data else None


def delete_filing(filing_id: str) -> bool:
    client = get_supabase_client()
    res = client.table("filings").delete().eq("id", filing_id).execute()
    return bool(res.data)


# ------------------------------------------------------------------------------
# DOCUMENTS
# ------------------------------------------------------------------------------
def create_document(
    user_id: str,
    filing_id: str,
    file_name: str,
    document_type: str,
    storage_path: str,
    extracted_text: Optional[str] = None,
    upload_status: str = "uploaded"
) -> Dict[str, Any]:
    client = get_supabase_client()
    payload = {
        "user_id": user_id,
        "filing_id": filing_id,
        "file_name": file_name,
        "document_type": document_type,
        "storage_path": storage_path,
        "extracted_text": extracted_text,
        "upload_status": upload_status,
    }
    res = client.table("documents").insert(payload).execute()
    return res.data[0] if res.data else payload


def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("documents").select("*").eq("id", document_id).execute()
    return res.data[0] if res.data else None


def list_documents_by_filing(filing_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("documents").select("*").eq("filing_id", filing_id).order("created_at", desc=True).execute()
    return res.data or []


def update_document(document_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("documents").update(updates).eq("id", document_id).execute()
    return res.data[0] if res.data else None


# ------------------------------------------------------------------------------
# AI ANALYSIS
# ------------------------------------------------------------------------------
def save_ai_analysis(
    filing_id: str,
    employer_name: Optional[str],
    gross_salary: float,
    tds: float,
    financial_year: str,
    extracted_data: Dict[str, Any],
    confidence_score: float,
    warnings: List[str]
) -> Dict[str, Any]:
    client = get_supabase_client()
    payload = {
        "filing_id": filing_id,
        "employer_name": employer_name,
        "gross_salary": gross_salary,
        "tds": tds,
        "financial_year": financial_year,
        "extracted_data": extracted_data,
        "confidence_score": confidence_score,
        "warnings": warnings,
    }
    res = client.table("ai_analysis").insert(payload).execute()
    return res.data[0] if res.data else payload


def get_ai_analysis_by_filing(filing_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("ai_analysis").select("*").eq("filing_id", filing_id).order("created_at", desc=True).execute()
    return res.data[0] if res.data else None


# ------------------------------------------------------------------------------
# TAX CALCULATIONS
# ------------------------------------------------------------------------------
def save_tax_calculation(
    filing_id: str,
    gross_income: float,
    deductions: float,
    taxable_income: float,
    tax_amount: float,
    cess: float,
    total_tax: float,
    tds: float,
    refund_or_payable: float,
    calculation_version: str = "demo-v1"
) -> Dict[str, Any]:
    client = get_supabase_client()
    payload = {
        "filing_id": filing_id,
        "gross_income": gross_income,
        "deductions": deductions,
        "taxable_income": taxable_income,
        "tax_amount": tax_amount,
        "cess": cess,
        "total_tax": total_tax,
        "tds": tds,
        "refund_or_payable": refund_or_payable,
        "calculation_version": calculation_version,
    }
    res = client.table("tax_calculations").insert(payload).execute()
    return res.data[0] if res.data else payload


def get_latest_tax_calculation(filing_id: str) -> Optional[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("tax_calculations").select("*").eq("filing_id", filing_id).order("created_at", desc=True).execute()
    return res.data[0] if res.data else None


# ------------------------------------------------------------------------------
# REVIEWS
# ------------------------------------------------------------------------------
def create_review(
    filing_id: str,
    reviewer_id: Optional[str],
    status: str,
    comments: Optional[str]
) -> Dict[str, Any]:
    client = get_supabase_client()
    payload = {
        "filing_id": filing_id,
        "reviewer_id": reviewer_id,
        "status": status,
        "comments": comments,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }
    res = client.table("reviews").insert(payload).execute()
    return res.data[0] if res.data else payload


def get_reviews_by_filing(filing_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("reviews").select("*").eq("filing_id", filing_id).order("created_at", desc=True).execute()
    return res.data or []


# ------------------------------------------------------------------------------
# AUDIT LOGS
# ------------------------------------------------------------------------------
def create_audit_log(
    action: str,
    filing_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    client = get_supabase_client()
    # Filter out sensitive keys from details
    safe_details = {}
    if details:
        sensitive_keys = {"password", "token", "secret", "key", "api_key", "authorization"}
        safe_details = {k: v for k, v in details.items() if k.lower() not in sensitive_keys}

    payload = {
        "action": action,
        "filing_id": filing_id,
        "user_id": user_id,
        "details": safe_details,
    }
    res = client.table("audit_logs").insert(payload).execute()
    return res.data[0] if res.data else payload


def list_audit_logs_by_filing(filing_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    res = client.table("audit_logs").select("*").eq("filing_id", filing_id).order("created_at", desc=True).execute()
    return res.data or []
