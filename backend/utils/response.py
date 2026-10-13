"""
FinEasy AI - API Response Utilities
Standardized error formatting and envelope structures.
"""

from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse
from fastapi import HTTPException, status


def create_error_response(
    code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Returns a standardized error response body."""
    error_payload = {
        "code": code,
        "message": message,
    }
    if details:
        error_payload["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error_payload,
        }
    )


def create_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """Returns a standardized success envelope."""
    payload = {
        "success": True,
        "data": data,
    }
    if message:
        payload["message"] = message
    return payload


class AppException(HTTPException):
    """Custom Application Exception with structured error code and status."""
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
        self.code = code
        self.message = message
