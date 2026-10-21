"""Configuration management using Pydantic v2 BaseSettings."""

import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable fallbacks."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Core
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Secure Heatwave Advisory Generator"
    API_V1_PREFIX: str = "/api/v1"

    # Security & Auth
    SECRET_KEY: str = "dev-secret-key-for-local-testing-purposes-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./heatwave.db"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "anthropic"

    # Provider Keys & Models
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Mock LLM Settings
    MOCK_LLM_FAILURE_MODE: str = "NONE"
    MOCK_LLM_LATENCY_MS: int = 0

    # Security Canary
    SYSTEM_CANARY_TOKEN: str = "CANARY-IMD-SEC-9981"

    # CORS
    ALLOWED_ORIGINS: list[str] | str = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.strip().startswith("[") and v.strip().endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]


settings = Settings()
