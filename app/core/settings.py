from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "RouteLM"

    APP_VERSION: str = "1.0.0"

    DEBUG: bool = False

    LOG_LEVEL: str = "INFO"

    HOST: str = "0.0.0.0"

    PORT: int = 8000

    DATABASE_URL: str

    REDIS_HOST: str

    REDIS_PORT: int


    REQUEST_TIMEOUT: int = 120

    MAX_RETRIES: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()