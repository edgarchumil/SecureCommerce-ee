from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "SecureCommerce Advisor"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    secret_key: str = Field(default="development-only-secret-change-me-12345", min_length=32)
    database_url: str = (
        "postgresql+asyncpg://securecommerce:securecommerce_dev@localhost:5432/securecommerce"
    )
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:8080",
        "http://localhost:5173",
    ]
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    login_max_attempts: int = 5
    login_lock_minutes: int = 15
    cookie_secure: bool = False
    ai_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    ai_enabled: bool = False
    ai_max_tokens: int = Field(default=1000, ge=100, le=4000)
    ai_timeout_seconds: int = Field(default=30, ge=1, le=120)
    ai_monthly_budget_limit: float = Field(default=25, ge=0)
    ai_input_cost_per_million: float = Field(default=0, ge=0)
    ai_output_cost_per_million: float = Field(default=0, ge=0)
    report_storage_path: str = "storage/reports"
    report_execution_mode: Literal["celery", "background"] = "celery"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def use_async_postgres_driver(cls, value: object) -> object:
        """Adapt provider PostgreSQL URLs for SQLAlchemy's async engine."""
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if isinstance(value, str) and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
