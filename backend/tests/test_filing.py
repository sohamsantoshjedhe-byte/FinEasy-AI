"""
FinEasy AI - Filing Workflow & Mock Government Integration Tests
"""

import pytest
from backend.services.filing_service import transition_status, ALLOWED_TRANSITIONS
from backend.tax_engine.calculator import calculate_tax
from backend.ai.document_extractor import analyse_form16, _clean_json_string
from backend.utils.response import AppException


def test_create_filing_success(client, auth_headers):
    payload = {
        "financial_year": "2024-25",
        "filing_type": "ITR",
    }
    response = client.post("/api/filings", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["financial_year"] == "2024-25"
    assert data["status"] == "draft"


def test_invalid_filing_id_not_found(client, auth_headers):
    response = client.get("/api/filings/non-existent-uuid-12345", headers=auth_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FILING_NOT_FOUND"


def test_state_machine_transitions(client, auth_headers):
    # 1. Create filing
    resp = client.post("/api/filings", json={"financial_year": "2024-25", "filing_type": "ITR"}, headers=auth_headers)
    filing_id = resp.json()["id"]

    # 2. Transition draft -> document_uploaded
    t1 = transition_status(filing_id, "document_uploaded")
    assert t1["status"] == "document_uploaded"

    # 3. Transition document_uploaded -> analysing
    t2 = transition_status(filing_id, "analysing")
    assert t2["status"] == "analysing"

    # 4. Transition analysing -> analysed
    t3 = transition_status(filing_id, "analysed")
    assert t3["status"] == "analysed"

    # 5. Transition analysed -> calculation_complete
    t4 = transition_status(filing_id, "calculation_complete")
    assert t4["status"] == "calculation_complete"

    # 6. Invalid transition: cannot jump from calculation_complete directly to submitted
    with pytest.raises(AppException) as exc_info:
        transition_status(filing_id, "submitted")
    assert exc_info.value.code == "INVALID_STATUS_TRANSITION"


def test_malformed_ai_handling():
    # Empty string should not crash
    result = analyse_form16("")
    assert result.confidence_score == 0.0
    assert len(result.warnings) > 0
    assert result.employer_name is None

    # JSON markdown wrapper cleaner
    raw_markdown = "```json\n{\"test\": 123}\n```"
    cleaned = _clean_json_string(raw_markdown)
    assert cleaned == "{\"test\": 123}"


def test_mock_government_validation_endpoint(gov_client):
    # Valid payload
    payload = {
        "filing_id": "demo-filing-001",
        "taxable_income": 750000.0,
        "tax_amount": 32500.0,
    }
    response = gov_client.post("/mock/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "reference_id" in data
    assert "SIMULATED" in data["disclaimer"]

    # Negative value validation failure
    invalid_payload = {
        "filing_id": "demo-filing-002",
        "taxable_income": -1000.0,
        "tax_amount": 500.0,
    }
    invalid_resp = gov_client.post("/mock/validate", json=invalid_payload)
    assert invalid_resp.status_code == 200
    invalid_data = invalid_resp.json()
    assert invalid_data["valid"] is False
    assert len(invalid_data["errors"]) > 0


def test_mock_government_submission_endpoint(gov_client):
    payload = {
        "filing_id": "demo-filing-999",
        "user_id": "taxpayer-123",
        "financial_year": "2024-25",
        "taxable_income": 800000.0,
        "total_tax": 36400.0,
        "tds": 40000.0,
    }
    response = gov_client.post("/mock/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "submitted"
    assert "FINDEMO-2026-" in data["acknowledgement_number"]
    assert "SIMULATED" in data["message"]


def test_ca_review_workflow_and_submission(client, auth_headers, ca_auth_headers):
    # 1. User creates filing
    resp = client.post("/api/filings", json={"financial_year": "2024-25", "filing_type": "ITR"}, headers=auth_headers)
    filing_id = resp.json()["id"]

    # 2. Run tax calculation
    calc_resp = client.post(
        f"/api/tax/calculate/{filing_id}",
        json={"gross_income": 950000.0, "deductions": 150000.0, "tds": 45000.0},
        headers=auth_headers,
    )
    assert calc_resp.status_code == 200
    assert calc_resp.json()["taxable_income"] == 800000.0

    # 3. Validate filing -> advances to ca_review
    val_resp = client.post(f"/api/tax/validate/{filing_id}", headers=auth_headers)
    assert val_resp.status_code == 200
    assert val_resp.json()["valid"] is True

    # 4. CA lists pending reviews
    pending_resp = client.get("/api/reviews/pending", headers=ca_auth_headers)
    assert pending_resp.status_code == 200
    pending_list = pending_resp.json()
    assert any(f["id"] == filing_id for f in pending_list)

    # 5. CA approves filing
    approve_resp = client.post(
        f"/api/reviews/{filing_id}/approve",
        json={"comments": "Verified against 26AS. Form 16 figures match perfectly."},
        headers=ca_auth_headers,
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    # 6. User submits approved filing
    submit_resp = client.post(f"/api/government/submit/{filing_id}", headers=auth_headers)
    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    assert submit_data["status"] == "submitted"
    assert "acknowledgement_number" in submit_data


def test_document_upload_and_ai_extraction_pipeline(client, auth_headers):
    import os
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "demo_form16.pdf")
    assert os.path.exists(pdf_path), "Sample Form 16 PDF must exist"

    # 1. Create a draft filing
    create_resp = client.post("/api/filings", json={"financial_year": "2024-25", "filing_type": "ITR"}, headers=auth_headers)
    assert create_resp.status_code == 201
    filing_id = create_resp.json()["id"]

    # 2. Upload the PDF
    with open(pdf_path, "rb") as f:
        upload_resp = client.post(
            "/api/documents/upload",
            data={"filing_id": filing_id, "document_type": "form_16"},
            files={"file": ("demo_form16.pdf", f, "application/pdf")},
            headers=auth_headers,
        )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert upload_data["upload_status"] == "extracted"
    assert "FORM NO. 16" in upload_data["extracted_text_preview"]

    # 3. Trigger AI analysis
    ai_resp = client.post(f"/api/ai/analyse/{filing_id}", headers=auth_headers)
    assert ai_resp.status_code == 200
    ai_data = ai_resp.json()
    assert ai_data["employer_name"] is not None
    assert "Infosys" in ai_data["employer_name"]
    assert ai_data["gross_salary"] == 950000.0
    assert ai_data["tds"] == 52000.0

    # 4. Verify filing updated with extracted numbers
    filing_resp = client.get(f"/api/filings/{filing_id}", headers=auth_headers)
    assert filing_resp.status_code == 200
    filing_data = filing_resp.json()["filing"]
    assert filing_data["gross_income"] == 950000.0
    assert filing_data["tds_amount"] == 52000.0
    assert filing_data["status"] == "analysed"

    # 5. Run tax calculation on extracted numbers
    calc_resp = client.post(f"/api/tax/calculate/{filing_id}", headers=auth_headers)
    assert calc_resp.status_code == 200
    calc_data = calc_resp.json()
    assert calc_data["gross_income"] == 950000.0
    assert calc_data["tds"] == 52000.0

    # 6. Test AI explanation endpoint
    explain_resp = client.post(f"/api/ai/explain/{filing_id}", headers=auth_headers)
    assert explain_resp.status_code == 200
    explain_data = explain_resp.json()
    assert "summary" in explain_data
    assert "income_explanation" in explain_data
    assert "tax_explanation" in explain_data
    assert "DEMO" in explain_data["disclaimer"]

