"""
Mock Government API - Authentication Simulation
"""

from fastapi import APIRouter

router = APIRouter(prefix="/mock/auth", tags=["Mock Government Auth"])


@router.get("/login", summary="Simulate Government e-Filing Login")
def mock_login():
    """Simulates authentication with the Income Tax Department e-Filing portal."""
    return {
        "success": True,
        "authenticated": True,
        "token": "MOCK-GOV-SESSION-987654",
        "portal": "Income Tax Department e-Filing Portal (SIMULATED DEMO)",
        "message": "SIMULATED AUTHENTICATION — NOT CONNECTED TO REAL GOVERNMENT SYSTEMS",
    }
