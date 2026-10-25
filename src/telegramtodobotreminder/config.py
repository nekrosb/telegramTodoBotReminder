from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str


def load_settings(dotenv_path: str | Path | None = None) -> Settings:
    """Load application settings from environment variables and a .env file."""
    load_dotenv(dotenv_path=dotenv_path)
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise ConfigurationError(
            "BOT_TOKEN is not set. Add it to the .env file in the project root."
        )
    return Settings(bot_token=token)
