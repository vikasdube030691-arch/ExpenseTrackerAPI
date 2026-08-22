from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ExpenseTrackerAPI"
    environment: str = "development"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "expensedb"
    mongodb_min_pool_size: int = 1
    mongodb_max_pool_size: int = 20

    refresh_token_expire_days: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
