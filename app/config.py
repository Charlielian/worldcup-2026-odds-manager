"""Pydantic Settings 配置。"""
import json
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_odds_providers_config() -> dict:
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "config", "odds_providers.json"
    )
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load odds providers config: {e}")
        return {
            "providers": {
                "mock": {
                    "enabled": True,
                    "class": "MockOddsProvider",
                    "priority": 99,
                }
            }
        }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "worldcup.db")
    PORT: int = int(os.environ.get("PORT", 6000))
    CORS_ORIGINS: str = os.environ.get(
        "CORS_ORIGINS", f"http://localhost:6000,http://127.0.0.1:6000,http://localhost:6018,http://127.0.0.1:6018"
    )
    ADMIN_TOKEN: str = os.environ.get("ADMIN_TOKEN", "wc2026-admin-token")
    DEBUG: bool = os.environ.get("FLASK_ENV", "development") == "development"

    ODDS_PROVIDERS: dict = _load_odds_providers_config()

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
