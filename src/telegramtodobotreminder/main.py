import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher

from telegramtodobotreminder.config import ConfigurationError, load_settings
from telegramtodobotreminder.database.connection import connect, initialize
from telegramtodobotreminder.handlers import router


logger = logging.getLogger(__name__)
DATABASE_PATH = Path("data") / "bot.sqlite3"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def run() -> None:
    settings = load_settings()
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    database = await connect(DATABASE_PATH)
    await initialize(database)

    try:
        logger.info("Starting Telegram bot")
        await dispatcher.start_polling(bot, database=database)
    finally:
        await database.close()
        await bot.session.close()
        logger.info("Telegram bot stopped")


def main() -> None:
    configure_logging()
    try:
        asyncio.run(run())
    except ConfigurationError as error:
        logger.error("%s", error)
        raise SystemExit(1) from error
    except KeyboardInterrupt:
        logger.info("Shutdown requested")


if __name__ == "__main__":
    main()
