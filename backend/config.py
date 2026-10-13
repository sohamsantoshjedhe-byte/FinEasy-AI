"""
FinEasy AI - Configuration Module
Educational Prototype Configuration & Environment Settings
"""

import os
from typing import List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "FinEasy AI Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Supabase Credentials
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Google Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Mock Government API URL
    MOCK_GOVERNMENT_URL: str = os.getenv("MOCK_GOVERNMENT_URL", "http://127.0.0.1:8001")

    # Document Upload Settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "backend/uploads")
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]

    # CORS Settings
    CORS_ORIGINS: Any = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def get_cors_origins(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            import json
            if self.CORS_ORIGINS.strip().startswith("["):
                try:
                    return json.loads(self.CORS_ORIGINS)
                except Exception:
                    pass
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return list(self.CORS_ORIGINS)


settings = Settings()

