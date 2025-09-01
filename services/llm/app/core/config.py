from typing import List
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Environment
    ENV: str = os.getenv("ENV", "development")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://tonebridge:tonebridge123@localhost:5432/tonebridge_db"
    )

    # Redis
    REDIS_ADDR: str = os.getenv("REDIS_ADDR", "localhost:6379")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://gateway:8080",
    ]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

    # Cache TTL (in seconds)
    CACHE_TTL: int = 86400  # 24 hours

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
