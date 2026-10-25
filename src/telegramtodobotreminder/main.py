import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher

from telegramtodobotreminder.config import ConfigurationError, load_settings
from telegramtodobotreminder.database.connection import connect, initialize
from telegramtodobotreminder.handlers import router
from telegramtodobotreminder.scheduler import ReminderScheduler


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
    reminder_scheduler = ReminderScheduler(bot, database)
    await reminder_scheduler.restore()
    reminder_scheduler.start()

    try:
        logger.info("Starting Telegram bot")
        await dispatcher.start_polling(
            bot, database=database, reminder_scheduler=reminder_scheduler
        )
    finally:
        await reminder_scheduler.shutdown()
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
