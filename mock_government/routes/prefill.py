"""
Mock Government API - Prefill Simulation
Simulates fetching Form 26AS & Annual Information Statement (AIS) data.
"""

import json
import os
from fastapi import APIRouter

router = APIRouter(prefix="/mock/prefill", tags=["Mock Government Prefill"])

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "demo_taxpayer.json")


@router.get("/{user_id}", summary="Get prefill tax data for taxpayer")
def get_prefill(user_id: str):
    """Returns simulated prefill financial data."""
    taxpayer_data = {}
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r") as f:
                all_data = json.load(f)
                taxpayer_data = all_data.get(user_id) or all_data.get("default", {})
        except Exception:
            pass

    salary = taxpayer_data.get("form_26as", {}).get("salary_income", 850000.0)
    tds = taxpayer_data.get("form_26as", {}).get("tds_salary", 42000.0)
    interest = taxpayer_data.get("ais", {}).get("savings_interest", 12000.0)

    return {
        "success": True,
        "user_id": user_id,
        "data": {
            "gross_salary": salary,
            "tds": tds,
            "interest_income": interest,
            "pan": taxpayer_data.get("pan", "DEMOP9999Z"),
            "taxpayer_name": taxpayer_data.get("name", "Demo Taxpayer"),
        },
        "source": "MOCK_GOVERNMENT_API",
        "notice": "SIMULATED PREFILL DATA — FOR EDUCATIONAL DEMO ONLY",
    }
