"""
Configuration management using environment variables.
All secrets are loaded from the environment — never hardcoded.
"""

import secrets
from functools import lru_cache

# 引入 Pydantic v2 專屬的 SettingsConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── GitHub OAuth2 ──────────────────────────────────────────────────────────
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str

    # Must match the "Authorization callback URL" set on the GitHub OAuth App
    GITHUB_REDIRECT_URI: str = "http://127.0.0.1:8000/auth/callback"

    # ── Session ────────────────────────────────────────────────────────────────
    # Generate a strong random key: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = secrets.token_hex(32)  # Override in production via env var
    SESSION_MAX_AGE: int = 3600              # 1 hour in seconds
    SESSION_HTTPS_ONLY: bool = False         # Set True in production (HTTPS only)

    # ── Notion ────────────────────────────────────────────────────────────────
    # 新增這兩個欄位，Pydantic 會自動去 .env 對應名稱的設定並載入
    NOTION_API_KEY: str
    NOTION_DATABASE_ID: str

    # ── App ────────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"

    # Pydantic v2 的新寫法，用來取代舊版的 class Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 忽略環境變數或 .env 中多餘的欄位，避免非預期報錯
    )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — reads .env once."""
    return Settings()


settings = get_settings()