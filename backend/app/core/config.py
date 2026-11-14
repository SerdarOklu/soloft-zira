"""Application settings, read from environment variables (see .env.example)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+psycopg://zira:zira@localhost:5432/zira"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me"
    power_base_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    config_dir: Path = REPO_ROOT / "config"


@lru_cache
def get_settings() -> Settings:
    return Settings()
