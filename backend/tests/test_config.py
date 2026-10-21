"""Unit tests for configuration loading and validation."""

from app.core.config import Settings


def test_default_settings():
    """Verify default settings initialization."""
    cfg = Settings()
    assert cfg.ENVIRONMENT in ["development", "testing", "production"]
    assert cfg.LLM_PROVIDER in ["mock", "openai", "anthropic"]
    assert cfg.SYSTEM_CANARY_TOKEN != ""
    assert isinstance(cfg.ALLOWED_ORIGINS, list)


def test_cors_origins_parsing():
    """Verify CORS parsing from JSON list and comma-separated string."""
    cfg1 = Settings(ALLOWED_ORIGINS='["http://localhost:5173", "http://example.com"]')
    assert cfg1.ALLOWED_ORIGINS == ["http://localhost:5173", "http://example.com"]

    cfg2 = Settings(ALLOWED_ORIGINS="http://localhost:3000, http://localhost:8000")
    assert cfg2.ALLOWED_ORIGINS == ["http://localhost:3000", "http://localhost:8000"]
