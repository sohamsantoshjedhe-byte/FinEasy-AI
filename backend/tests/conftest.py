"""
FinEasy AI - Pytest Configuration & Test Fixtures
"""

import sys
import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set test environment flags
os.environ["ENVIRONMENT"] = "test"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["MOCK_GOVERNMENT_URL"] = "http://127.0.0.1:8001"

from backend.main import app as backend_app
from mock_government.main import app as gov_app
from backend.database.supabase import reset_mock_db


@pytest.fixture(autouse=True)
def clean_database():
    """Resets mock database state before each test."""
    reset_mock_db()
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """TestClient fixture for FinEasy AI FastAPI Backend."""
    with TestClient(backend_app) as c:
        yield c


@pytest.fixture
def gov_client() -> Generator[TestClient, None, None]:
    """TestClient fixture for Mock Government API."""
    with TestClient(gov_app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict:
    """Provides a synthetic authentication header for testing."""
    return {"Authorization": "Bearer mock-token-test-user-123"}


@pytest.fixture
def ca_auth_headers() -> dict:
    """Provides a synthetic CA authentication header for testing."""
    from backend.database import queries
    queries.create_profile(user_id="ca-reviewer-999", email="ca@example.com", name="CA Ramesh", user_type="ca")
    return {"Authorization": "Bearer mock-token-ca-reviewer-999"}
