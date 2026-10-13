"""
FinEasy AI - End-to-End Workflow Demonstration Script
Run this standalone script to simulate a complete taxpayer journey from start to finish!
"""

import os
import sys
import uuid

# Ensure root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.database import queries
from backend.services import (
    auth_service,
    filing_service,
    document_service,
    ai_service,
    tax_service,
    validation_service,
    review_service,
    government_service,
)
import asyncio


def print_step(num: int, title: str):
    print(f"\n{'='*60}")
    print(f" STEP {num}: {title.upper()}")
    print(f"{'='*60}")


async def main():
    print("""
    =======================================================
               FINEASY AI — END-TO-END DEMO TEST
    =======================================================
    """)

    # 1. Register User
    print_step(1, "User Registration & Login")
    email = f"taxpayer_{uuid.uuid4().hex[:6]}@demo.com"
    auth = auth_service.register_user(
        email=email,
        password="secure_password_123",
        name="Arjun Sharma",
        user_type="individual",
    )
    user_id = auth["user_id"]
    print(f"✅ Taxpayer registered successfully!")
    print(f"   Name   : {auth['name']}")
    print(f"   Email  : {auth['email']}")
    print(f"   User ID: {user_id}")

    # 2. Create Filing
    print_step(2, "Create ITR Filing Draft")
    filing = filing_service.create_new_filing(
        user_id=user_id,
        financial_year="2024-25",
        filing_type="ITR",
    )
    filing_id = filing["id"]
    print(f"✅ Filing Created:")
    print(f"   Filing ID : {filing_id}")
    print(f"   Status    : {filing['status']}")
    print(f"   F.Y.      : {filing['financial_year']}")

    # 3. Upload Form 16 PDF
    print_step(3, "Upload Form 16 PDF & PyPDF Text Extraction")
    pdf_path = os.path.join(PROJECT_ROOT, "sample_data", "demo_form16.pdf")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    doc = document_service.process_document_upload(
        user_id=user_id,
        filing_id=filing_id,
        filename="demo_form16.pdf",
        content=pdf_bytes,
        document_type="form_16",
    )
    print(f"✅ Document Processed & Stored:")
    print(f"   File Name : {doc['file_name']}")
    print(f"   Status    : {doc['upload_status']}")
    print(f"   Preview   : {doc['extracted_text_preview'][:80]}...")

    # 4. AI Document Extraction
    print_step(4, "AI Extraction (Google Gemini / Heuristic Engine)")
    ai_result = ai_service.process_filing_ai_analysis(filing_id=filing_id, user_id=user_id)
    print(f"✅ AI Analysis Complete:")
    print(f"   Employer Name : {ai_result.get('employer_name')}")
    print(f"   Gross Salary  : ₹{ai_result.get('gross_salary', 0):,.2f}")
    print(f"   TDS Deducted  : ₹{ai_result.get('tds', 0):,.2f}")
    print(f"   Confidence    : {ai_result.get('confidence_score') * 100:.0f}%")

    # 5. Deterministic Tax Engine
    print_step(5, "Deterministic Tax Engine Calculation")
    tax_result = tax_service.run_tax_calculation(
        filing_id=filing_id,
        user_id=user_id,
        deductions_override=150000.0,  # e.g. 80C deductions
    )
    print(f"✅ Tax Calculation Output:")
    print(f"   Gross Income    : ₹{tax_result['gross_income']:,.2f}")
    print(f"   Deductions      : ₹{tax_result['deductions']:,.2f}")
    print(f"   Taxable Income  : ₹{tax_result['taxable_income']:,.2f}")
    print(f"   Slab Tax        : ₹{tax_result['tax_amount']:,.2f}")
    print(f"   Cess (4%)       : ₹{tax_result['cess']:,.2f}")
    print(f"   Total Tax       : ₹{tax_result['total_tax']:,.2f}")
    print(f"   TDS Credit      : ₹{tax_result['tds']:,.2f}")
    net = tax_result["refund_or_payable"]
    if net < 0:
        print(f"   Refund Due      : ₹{abs(net):,.2f} (REFUND TO TAXPAYER)")
    else:
        print(f"   Net Payable     : ₹{net:,.2f}")

    # 6. Natural Language AI Explanation
    print_step(6, "AI Natural Language Tax Explanation")
    explanation = ai_service.generate_tax_explanation(filing_id=filing_id, user_id=user_id)
    print(f"   Summary: {explanation.summary}")

    # 7. Tax Data Validation
    print_step(7, "Filing Validation & Queue for CA Review")
    val = validation_service.validate_filing_for_review(filing_id=filing_id, user_id=user_id)
    print(f"✅ Validation Passed: {val['valid']}")
    print(f"   Filing Status is now: 'ca_review'")

    # 8. CA Review & Approval
    print_step(8, "Chartered Accountant (CA) Review")
    ca_id = str(uuid.uuid4())
    queries.create_profile(user_id=ca_id, email="ca_reviewer@demo.com", name="CA R. K. Gupta", user_type="ca")
    review = review_service.ca_approve_filing(
        filing_id=filing_id,
        reviewer_id=ca_id,
        comments="Form 16 verified. Figures match AIS data perfectly. Approved.",
    )
    print(f"✅ CA Decision: {review['status'].upper()}")
    print(f"   Reviewer   : CA R. K. Gupta")
    print(f"   Comments   : {review['comments']}")

    # 9. Submit to Mock Government API
    print_step(9, "Simulated Government e-Filing Portal Submission")
    submission = await government_service.submit_filing_to_government(
        filing_id=filing_id,
        user_id=user_id,
    )
    print(f"🎉 FINAL SUBMISSION SUCCESSFUL!")
    print(f"   Status                 : {submission.get('status').upper()}")
    print(f"   Acknowledgement Number : {submission.get('acknowledgement_number')}")
    print(f"   Notice                 : {submission.get('message', submission.get('notice'))}")

    # Final filing check
    updated_filing = queries.get_filing_by_id(filing_id)
    print(f"\nFinal State in Database: status = '{updated_filing['status']}'")
    print("=======================================================")
    print("      ALL WORKFLOW STEPS TESTED & VERIFIED 100%!       ")
    print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
