"""
FinEasy AI - Document Routes
Endpoints for uploading and viewing tax documents (Form 16 PDFs).
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from backend.schemas.document import DocumentUploadResponse, DocumentDetailResponse
from backend.dependencies import get_current_user
from backend.services import document_service
from backend.database import queries
from backend.utils.response import AppException

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED, summary="Upload Form 16 PDF")
async def upload_document(
    filing_id: str = Form(..., description="Target filing UUID"),
    document_type: str = Form("form_16", description="Document category (default: form_16)"),
    file: UploadFile = File(..., description="PDF Document"),
    current_user: dict = Depends(get_current_user),
):
    """
    Uploads a tax document PDF, verifies file integrity, extracts text via PyPDF,
    and updates filing status to 'document_uploaded'.
    """
    content = await file.read()
    return document_service.process_document_upload(
        user_id=current_user["user_id"],
        filing_id=filing_id,
        filename=file.filename or "form_16.pdf",
        content=content,
        document_type=document_type,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="Get document metadata and text")
def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieves document record, extracted text, and storage metadata."""
    doc = queries.get_document_by_id(document_id)
    if not doc:
        raise AppException(code="DOCUMENT_NOT_FOUND", message="Document not found.", status_code=status.HTTP_404_NOT_FOUND)

    if str(doc.get("user_id")) != str(current_user["user_id"]) and current_user.get("user_type") not in ["ca", "admin"]:
        raise AppException(code="UNAUTHORIZED", message="Unauthorized to view this document.", status_code=status.HTTP_403_FORBIDDEN)

    return doc
