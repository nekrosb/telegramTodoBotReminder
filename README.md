# Telegram Todo Bot Reminder

A Telegram bot for managing reminders. The project currently includes
configuration loading, the `/start` command, basic logging, user registration,
language selection, and SQLite persistence.
Users can also select and update an IANA timezone, with DST-aware local time
conversion utilities.

## Running locally

Python 3.12 or newer is required.

1. Install the dependencies:

   ```bash
   python -m pip install -e .
   ```

   If you use `uv`, run `uv sync` instead.

2. Create a `.env` file in the project root:

   ```dotenv
   BOT_TOKEN=your_telegram_bot_token
   ```

   You can get a token from [@BotFather](https://t.me/BotFather). The `.env`
   file is intentionally excluded from Git.

3. Start the bot:

   ```bash
   python -m telegramtodobotreminder.main
   ```

   The installed console command is also available:

   ```bash
   telegramtodobotreminder
   ```

If `BOT_TOKEN` is missing or empty, the application exits with a clear error
before opening a connection to Telegram.

## Development

Run the test suite with:

```bash
uv run --with pytest --with pytest-asyncio pytest -q
```

The SQLite database is stored in `data/bot.sqlite3` and is created
automatically when the application starts.
