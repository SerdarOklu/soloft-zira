"""Application settings, read from environment variables (see .env.example)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]

INSECURE_SECRET = "change-me"
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://zira:zira@localhost:5432/zira"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = INSECURE_SECRET
    access_token_ttl_minutes: int = 720
    power_base_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    # Green API (WhatsApp gateway). Leave empty and approved messages wait instead of sending.
    green_api_url: str = "https://api.green-api.com"
    green_api_instance_id: str = ""
    green_api_token: str = ""
    config_dir: Path = REPO_ROOT / "config"
    # Run Celery tasks inline instead of sending them to the worker (tests, quick checks).
    celery_task_always_eager: bool = False

    @property
    def whatsapp_configured(self) -> bool:
        return bool(self.green_api_instance_id and self.green_api_token)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def check(self) -> None:
        """Refuse to run in production with the placeholder or a short secret."""
        if not self.is_production:
            return
        if self.secret_key == INSECURE_SECRET or len(self.secret_key) < MIN_SECRET_LENGTH:
            raise RuntimeError(
                f"SECRET_KEY must be a random value of at least {MIN_SECRET_LENGTH} characters "
                "in production"
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.check()
    return settings
