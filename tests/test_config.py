import pytest

from telegramtodobotreminder.config import ConfigurationError, load_settings


def test_load_settings_reads_bot_token_from_dotenv(tmp_path):
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("BOT_TOKEN=test-token\n", encoding="utf-8")

    settings = load_settings(dotenv_file)

    assert settings.bot_token == "test-token"


def test_load_settings_rejects_missing_bot_token(tmp_path, monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    with pytest.raises(ConfigurationError, match="BOT_TOKEN is not set"):
        load_settings(tmp_path / ".env")
