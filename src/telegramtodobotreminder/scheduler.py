import logging
from datetime import UTC, datetime

import aiosqlite
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegramtodobotreminder.database import notifications

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(self, bot: Bot, database: aiosqlite.Connection) -> None:
        self.bot = bot
        self.database = database
        self.scheduler = AsyncIOScheduler(timezone=UTC)

    async def restore(self) -> None:
        for item in await notifications.pending_future(self.database):
            self.schedule(item["id"], datetime.fromisoformat(item["scheduled_at"]))

    def schedule(self, notification_id: int, scheduled_at: datetime) -> None:
        self.scheduler.add_job(
            self._send,
            "date",
            run_date=scheduled_at,
            args=(notification_id,),
            id=f"notification:{notification_id}",
            replace_existing=True,
        )

    async def _send(self, notification_id: int) -> None:
        item = await notifications.claim(self.database, notification_id)
        if item is None:
            return
        minutes = {"1d": "24 hours", "3h": "3 hours", "1h": "1 hour", "15m": "15 minutes"}
        text = (
            f"Reminder: {item['title']}\n"
            f"The event starts in {minutes[item['notification_type']]}.\n"
            f"Event time: {item['remind_at']} UTC"
        )
        try:
            await self.bot.send_message(item["telegram_id"], text)
        except (TelegramAPIError, OSError) as error:
            logger.exception("Notification %s failed", notification_id)
            await notifications.mark_failed(self.database, notification_id, str(error))
        else:
            await notifications.mark_sent(self.database, notification_id)

    def start(self) -> None:
        self.scheduler.start()

    async def shutdown(self) -> None:
        self.scheduler.shutdown(wait=False)
