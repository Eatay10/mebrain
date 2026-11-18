"""Uygulama konfigürasyonu — sadece ortam değişkenlerinden (R-PY-07)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Yerel geliştirmede repo kökündeki .env okunur; konteynerde değerler ortamdan gelir.
_ENV_FILES = tuple(str(p / ".env") for p in Path(__file__).resolve().parents if (p / ".env").is_file())[:1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or None, env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = Field(alias="DATABASE_URL")
    migration_database_url: str | None = Field(default=None, alias="MIGRATION_DATABASE_URL")
    env: str = Field(default="development", alias="CTH_ENV")
    cookie_secure: bool = Field(default=True, alias="CTH_COOKIE_SECURE")
    cors_origins: str = Field(default="", alias="CTH_CORS_ORIGINS")
    session_hours: int = Field(default=8, alias="CTH_SESSION_HOURS")
    session_idle_minutes: int = Field(default=30, alias="CTH_SESSION_IDLE_MINUTES")
    public_base_url: str = Field(default="http://localhost:8080", alias="CTH_PUBLIC_BASE_URL")

    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    smtp_from: str = Field(default="cyber-task-hub@demo.local", alias="SMTP_FROM")

    seed_password: str | None = Field(default=None, alias="CTH_SEED_PASSWORD")

    max_body_bytes: int = Field(default=256 * 1024, alias="CTH_MAX_BODY_BYTES")
    rate_limit_anonymous_per_min: int = Field(default=30, alias="CTH_RATE_ANON")
    rate_limit_authenticated_per_min: int = Field(default=300, alias="CTH_RATE_AUTH")
    rate_limit_login_per_min: int = Field(default=10, alias="CTH_RATE_LOGIN")
    login_max_failures: int = 5
    login_lock_minutes: int = 15
    api_token_max_days: int = 90

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
