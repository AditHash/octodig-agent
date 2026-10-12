"""Environment-backed application configuration."""

from functools import lru_cache
from decimal import Decimal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://octodig:octodig@localhost:5432/octodig"
    environment: str = "development"
    jwt_secret: SecretStr = SecretStr("development-only-change-me")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(default=60, ge=5, le=1440)
    cors_origins: list[AnyHttpUrl] = Field(default_factory=lambda: ["http://localhost:5173"])
    run_lease_seconds: int = Field(default=300, ge=30, le=3600)
    run_max_attempts: int = Field(default=3, ge=1, le=10)
    worker_poll_seconds: float = Field(default=2.0, ge=0.2, le=60)
    openai_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    gpt_model: str = "openai:gpt-5-nano"
    gemini_model: str = "gemini-2.5-flash-lite"
    openai_input_usd_per_million: Decimal | None = None
    openai_output_usd_per_million: Decimal | None = None
    openai_search_call_usd: Decimal | None = None
    gemini_input_usd_per_million: Decimal | None = None
    gemini_output_usd_per_million: Decimal | None = None
    gemini_search_call_usd: Decimal | None = None
    research_max_input_tokens: int = Field(default=20_000, ge=1, le=1_000_000)
    research_max_output_tokens: int = Field(default=4_000, ge=1, le=100_000)
    research_max_search_calls: int = Field(default=3, ge=0, le=50)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if self.environment.lower() != "production":
            return self
        if self.jwt_secret.get_secret_value() == "development-only-change-me":
            raise ValueError("JWT_SECRET must be configured for production")
        if any(origin.host in {"localhost", "127.0.0.1"} for origin in self.cors_origins):
            raise ValueError("OCTODIG_CORS_ORIGINS must not include local origins in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
