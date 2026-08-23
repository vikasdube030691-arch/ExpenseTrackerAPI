from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ExpenseTrackerAPI"
    environment: str = "development"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "expensedb"
    mongodb_min_pool_size: int = 1
    mongodb_max_pool_size: int = 20

    # JWT access tokens are short-lived and stateless; refresh tokens are opaque,
    # stored (hashed) in MongoDB, and are the only thing that can be revoked.
    jwt_secret_key: str = "change-me-in-production-use-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    login_rate_limit: str = "5/minute"

    cors_origins: list[str] = ["http://localhost:4200"]

    # The LangChain/LangGraph agent layer (app/agents, app/tools) is only active
    # when a key is configured; otherwise ChatService falls back to the
    # placeholder in app/services/ai/chat_completion.py so local dev and the
    # test suite never need a live Anthropic account.
    anthropic_api_key: str | None = None
    ai_model: str = "claude-sonnet-5"
    ai_max_tool_iterations: int = 6
    ai_history_message_limit: int = 20

    # Browsers special-case `localhost` as a secure context, so Secure cookies work
    # fine there even over http. Default True; only flip to false via env if you're
    # deliberately testing over plain http on a non-localhost host.
    cookie_secure: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
