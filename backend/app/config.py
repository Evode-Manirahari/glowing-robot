from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:localdev@localhost:5432/glowing_robot"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Storage
    upload_dir: str = "uploads"
    runs_dir: str = "runs"

    # Anthropic
    anthropic_api_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
