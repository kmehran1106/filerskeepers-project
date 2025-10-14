from functools import lru_cache
from typing import Literal

from pydantic import MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = "TrulyRandomSecretKey"

    # Application settings
    DEBUG: bool = False
    ENVIRONMENT: Literal["dev", "stage", "prod"] = "dev"

    # MongoDB settings
    MONGODB_URL: MongoDsn = "mongodb://filerskeepers:filerskeepers@localhost:27017/filerskeepers?authSource=admin"
    MONGODB_DATABASE: str = "filerskeepers"

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"

    # ARQ settings (for background tasks)
    ARQ_HOST: str = "localhost"
    ARQ_PORT: int = 6379
    ARQ_DB: int = 2

    # Rate limiting
    RATE_LIMIT_PER_HOUR: int = 100

    # Crawler settings
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_RETRIES: int = 3
    CRAWLER_RETRY_DELAY: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="FILERSKEEPERS_",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
