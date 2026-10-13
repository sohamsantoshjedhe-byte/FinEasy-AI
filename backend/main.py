"""
FinEasy AI - Main Application Entrypoint
FastAPI backend for an educational prototype of an AI-assisted Indian tax-compliance platform.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.utils.response import AppException, create_error_response
from backend.routes import (
    auth,
    users,
    filings,
    documents,
    ai,
    tax,
    review,
    government,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fineasy.main")

# Initialize FastAPI application
app = FastAPI(
    title="FinEasy AI Backend",
    description="Educational prototype of an AI-assisted Indian tax-compliance platform (Individual ITR V1).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# GLOBAL EXCEPTION HANDLERS
# ------------------------------------------------------------------------------
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Custom application exception with structured error format."""
    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic request validation errors."""
    error_details = exc.errors()
    first_error = error_details[0] if error_details else {}
    msg = f"{first_error.get('loc', ['field'])[-1]}: {first_error.get('msg', 'Invalid input')}"
    return create_error_response(
        code="VALIDATION_ERROR",
        message=msg,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": str(error_details)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unhandled exceptions (avoids leaking stack traces)."""
    logger.exception("Unhandled server error on %s %s: %s", request.method, request.url.path, exc)
    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ------------------------------------------------------------------------------
# HEALTH & ROOT ENDPOINTS
# ------------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    """Root status endpoint."""
    return {
        "status": "ok",
        "service": "FinEasy AI Backend",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "FinEasy AI Backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


# ------------------------------------------------------------------------------
# REGISTER ROUTERS
# ------------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(filings.router)
app.include_router(documents.router)
app.include_router(ai.router)
app.include_router(tax.router)
app.include_router(review.router)
app.include_router(government.router)

# ------------------------------------------------------------------------------
# SERVE FRONTEND STATIC FILES (Optional convenience for single-service hosting)
# ------------------------------------------------------------------------------
import os
from fastapi.staticfiles import StaticFiles

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
