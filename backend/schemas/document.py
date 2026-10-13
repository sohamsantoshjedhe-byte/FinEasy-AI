"""
FinEasy AI - Document Schemas
"""

from typing import Optional
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: str
    filing_id: str
    file_name: str
    document_type: str
    upload_status: str
    extracted_text_preview: Optional[str] = None
    created_at: Optional[str] = None


class DocumentDetailResponse(BaseModel):
    id: str
    user_id: str
    filing_id: str
    file_name: str
    document_type: str
    storage_path: str
    extracted_text: Optional[str] = None
    upload_status: str
    created_at: Optional[str] = None
