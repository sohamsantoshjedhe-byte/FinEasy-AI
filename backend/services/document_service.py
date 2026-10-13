"""
FinEasy AI - Document Processing Service
Handles PDF validation, storage, PyPDF text extraction, and filing attachment.
"""

import io
import logging
from typing import Dict, Any, Tuple
from pypdf import PdfReader
from fastapi import status

from backend.database import queries
from backend.utils.file_utils import validate_file_safety, save_upload_file
from backend.utils.response import AppException
from backend.services.filing_service import transition_status

logger = logging.getLogger("fineasy.services.document")


def extract_text_from_pdf(content: bytes) -> str:
    """
    Extracts text from PDF binary content using PyPDF.
    Gracefully handles encrypted, corrupted, or scanned PDFs.
    """
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise AppException(
                    code="PDF_ENCRYPTED",
                    message="The uploaded PDF is password protected. Please provide an unencrypted PDF.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        extracted_pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text)

        full_text = "\n".join(extracted_pages).strip()
        if not full_text:
            logger.warning("PDF uploaded contains no extractable text layer (possible scanned image).")
            return ""

        return full_text

    except AppException:
        raise
    except Exception as e:
        logger.error("PyPDF text extraction error: %s", e)
        raise AppException(
            code="PDF_EXTRACTION_ERROR",
            message=f"Failed to read PDF text: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def process_document_upload(
    user_id: str,
    filing_id: str,
    filename: str,
    content: bytes,
    document_type: str = "form_16"
) -> Dict[str, Any]:
    """
    Validates, stores, and extracts text from an uploaded tax document.
    """
    # 1. Verify filing exists and belongs to user
    filing = queries.get_filing_by_id(filing_id)
    if not filing:
        raise AppException(code="FILING_NOT_FOUND", message="The specified filing does not exist.", status_code=status.HTTP_404_NOT_FOUND)

    if str(filing.get("user_id")) != str(user_id):
        raise AppException(code="UNAUTHORIZED", message="Unauthorized to attach documents to this filing.", status_code=status.HTTP_403_FORBIDDEN)

    # 2. Validate safety and format
    is_safe, error_msg = validate_file_safety(filename, content)
    if not is_safe:
        raise AppException(code="INVALID_FILE", message=error_msg, status_code=status.HTTP_400_BAD_REQUEST)

    # 3. Store file securely
    stored_path, safe_name = save_upload_file(content, filename)

    # 4. Extract text
    extracted_text = extract_text_from_pdf(content)
    upload_status = "extracted" if extracted_text else "uploaded"

    # 5. Save database record
    doc_record = queries.create_document(
        user_id=user_id,
        filing_id=filing_id,
        file_name=safe_name,
        document_type=document_type,
        storage_path=stored_path,
        extracted_text=extracted_text,
        upload_status=upload_status,
    )

    # 6. Update filing status transition to document_uploaded
    try:
        transition_status(filing_id, "document_uploaded", actor_id=user_id, notes=f"Attached {document_type} ({safe_name})")
    except Exception as e:
        logger.info("Filing status transition to document_uploaded omitted: %s", e)

    # 7. Audit log
    queries.create_audit_log(
        action="document_uploaded",
        filing_id=filing_id,
        user_id=user_id,
        details={"file_name": safe_name, "document_type": document_type, "has_text": bool(extracted_text)},
    )

    preview = (extracted_text[:200] + "...") if extracted_text else "No text extracted."

    return {
        "id": doc_record["id"],
        "filing_id": filing_id,
        "file_name": safe_name,
        "document_type": document_type,
        "upload_status": upload_status,
        "extracted_text_preview": preview,
        "created_at": doc_record.get("created_at"),
    }
