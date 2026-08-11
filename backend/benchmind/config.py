from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BENCHMIND_", extra="ignore")

    environment: str = "development"
    model_provider: str = "mock"
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = "gpt-5.6-luna"
    data_dir: Path = Path(".benchmind")
    max_upload_bytes: int = 10 * 1024 * 1024
    max_files_per_case: int = 12
    cors_origins: str = "http://localhost:3000"
    request_timeout_seconds: float = 45.0
    max_parallel_agents: int = 4

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
