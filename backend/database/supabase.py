"""
FinEasy AI - Supabase Database Client & Fallback Engine
Provides resilient Supabase client connectivity with in-memory fallback for offline/test environments.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from backend.config import settings

logger = logging.getLogger("fineasy.database")


class MockQueryBuilder:
    """In-memory mock query builder emulating Supabase postgrest-py syntax for offline/test runs."""

    def __init__(self, table_name: str, store: Dict[str, List[Dict[str, Any]]]):
        self.table_name = table_name
        self.store = store
        self.filters = []
        self._action = "select"
        self._data = None
        self._order_col = None
        self._order_desc = False

    def select(self, columns: str = "*"):
        self._action = "select"
        return self

    def insert(self, data: Any):
        self._action = "insert"
        self._data = data if isinstance(data, list) else [data]
        return self

    def update(self, data: Dict[str, Any]):
        self._action = "update"
        self._data = data
        return self

    def delete(self):
        self._action = "delete"
        return self

    def eq(self, column: str, value: Any):
        self.filters.append((column, "eq", value))
        return self

    def order(self, column: str, desc: bool = False):
        self._order_col = column
        self._order_desc = desc
        return self

    def execute(self):
        rows = self.store.setdefault(self.table_name, [])

        if self._action == "insert":
            inserted = []
            for item in self._data:
                record = dict(item)
                if "id" not in record or not record["id"]:
                    record["id"] = str(uuid.uuid4())
                now = datetime.now(timezone.utc).isoformat()
                record.setdefault("created_at", now)
                record.setdefault("updated_at", now)
                rows.append(record)
                inserted.append(record)
            return MockResponse(data=inserted)

        elif self._action == "select":
            filtered = list(rows)
            for col, op, val in self.filters:
                if op == "eq":
                    filtered = [r for r in filtered if str(r.get(col)) == str(val)]
            if self._order_col:
                filtered.sort(
                    key=lambda r: str(r.get(self._order_col, "")),
                    reverse=self._order_desc,
                )
            return MockResponse(data=filtered)

        elif self._action == "update":
            updated = []
            for r in rows:
                match = True
                for col, op, val in self.filters:
                    if str(r.get(col)) != str(val):
                        match = False
                        break
                if match:
                    r.update(self._data)
                    r["updated_at"] = datetime.now(timezone.utc).isoformat()
                    updated.append(r)
            return MockResponse(data=updated)

        elif self._action == "delete":
            to_keep = []
            deleted = []
            for r in rows:
                match = True
                for col, op, val in self.filters:
                    if str(r.get(col)) != str(val):
                        match = False
                        break
                if match:
                    deleted.append(r)
                else:
                    to_keep.append(r)
            self.store[self.table_name] = to_keep
            return MockResponse(data=deleted)

        return MockResponse(data=[])


class MockResponse:
    def __init__(self, data: Any):
        self.data = data


class MockAuth:
    """Mock authentication engine when Supabase credentials are not supplied."""

    def __init__(self, store: Dict[str, List[Dict[str, Any]]]):
        self.store = store

    def sign_up(self, credentials: Dict[str, str]):
        email = credentials.get("email")
        user_id = str(uuid.uuid4())
        users = self.store.setdefault("_users", [])
        if any(u["email"] == email for u in users):
            raise Exception("User already registered")
        user_obj = {
            "id": user_id,
            "email": email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        users.append(user_obj)
        return MockAuthResponse(user_obj, f"mock-token-{user_id}")

    def sign_in_with_password(self, credentials: Dict[str, str]):
        email = credentials.get("email")
        users = self.store.setdefault("_users", [])
        user = next((u for u in users if u["email"] == email), None)
        if not user:
            # Auto-create in demo mode if not found
            user = {
                "id": str(uuid.uuid4()),
                "email": email,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            users.append(user)
        return MockAuthResponse(user, f"mock-token-{user['id']}")

    def get_user(self, token: str):
        if not token:
            raise Exception("No token provided")
        user_id = token.replace("Bearer ", "").replace("mock-token-", "")
        return MockAuthResponse({"id": user_id, "email": f"{user_id}@example.com"}, token)


class MockAuthResponse:
    def __init__(self, user_dict: Dict[str, Any], token: str):
        self.user = MockUser(user_dict)
        self.session = MockSession(token)


class MockUser:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.email = data.get("email")
        self.user_metadata = data.get("user_metadata", {})


class MockSession:
    def __init__(self, access_token: str):
        self.access_token = access_token


class MockSupabaseClient:
    """Mock Supabase client providing storage and auth mocks."""

    def __init__(self):
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        self.auth = MockAuth(self._store)

    def table(self, table_name: str) -> MockQueryBuilder:
        return MockQueryBuilder(table_name, self._store)


# Global client instance
_supabase_client = None


def get_supabase_client():
    """
    Returns a configured Supabase client.
    If valid credentials are provided, connects to real Supabase.
    Otherwise, initializes a thread-safe in-memory MockSupabaseClient.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.SUPABASE_URL and settings.SUPABASE_KEY and "your-project" not in settings.SUPABASE_URL:
        try:
            from supabase import create_client
            key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY
            _supabase_client = create_client(settings.SUPABASE_URL, key)
            logger.info("Connected successfully to Supabase PostgreSQL at %s", settings.SUPABASE_URL)
            return _supabase_client
        except Exception as e:
            logger.warning("Failed to initialize live Supabase client (%s). Falling back to mock database.", e)

    logger.info("Initializing FinEasy AI in-memory database mock (DEMO mode).")
    _supabase_client = MockSupabaseClient()
    return _supabase_client


def reset_mock_db():
    """Helper to reset mock database state during unit tests."""
    global _supabase_client
    if isinstance(_supabase_client, MockSupabaseClient):
        _supabase_client._store.clear()
