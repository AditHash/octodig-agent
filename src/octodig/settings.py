"""Environment-backed application configuration."""

from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://octodig:octodig@localhost:5432/octodig"
    jwt_secret: SecretStr = SecretStr("development-only-change-me")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(default=60, ge=5, le=1440)
    cors_origins: list[AnyHttpUrl] = Field(default_factory=lambda: ["http://localhost:5173"])
    run_lease_seconds: int = Field(default=300, ge=30, le=3600)
    worker_poll_seconds: float = Field(default=2.0, ge=0.2, le=60)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
