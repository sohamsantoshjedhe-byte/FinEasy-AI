"""
FinEasy AI - File Utilities
Secure file handling, sanitization, validation, and PDF inspection.
"""

import os
import re
import uuid
from typing import Tuple

from backend.config import settings

# Dangerous extensions explicitly prohibited
FORBIDDEN_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".js", ".vbs", ".py", ".msi", ".dll", ".bin"}


def sanitize_filename(filename: str) -> str:
    """Strips path traversal and normalizes filename to safe characters."""
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r"[^\w\.-]", "_", clean_name)
    return clean_name


def validate_file_safety(filename: str, content: bytes) -> Tuple[bool, str]:
    """
    Validates file extension, magic bytes, and size.
    Returns (is_valid, error_message).
    """
    _, ext = os.path.splitext(filename.lower())

    # 1. Extension validation
    if ext in FORBIDDEN_EXTENSIONS:
        return False, f"Prohibited file type: '{ext}'. Executables and scripts are strictly rejected."

    if ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type: '{ext}'. Only PDF documents are allowed in V1."

    # 2. File size validation (Max 10 MB)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        return False, f"File size ({len(content) / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB."

    # 3. PDF Magic Bytes inspection (%PDF-)
    if not content.startswith(b"%PDF-"):
        return False, "Invalid PDF format: Missing %PDF- header magic bytes."

    return True, ""


def save_upload_file(content: bytes, original_filename: str) -> Tuple[str, str]:
    """
    Saves uploaded file into configured uploads directory with unique prefix.
    Returns (stored_relative_path, safe_file_name).
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    clean_original = sanitize_filename(original_filename)
    unique_prefix = uuid.uuid4().hex[:8]
    safe_name = f"{unique_prefix}_{clean_original}"
    dest_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    with open(dest_path, "wb") as f:
        f.write(content)

    return dest_path, safe_name
