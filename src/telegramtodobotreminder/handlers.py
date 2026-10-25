import aiosqlite
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from telegramtodobotreminder.database import users
from telegramtodobotreminder.keyboards import language_keyboard


router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(message: Message, database: aiosqlite.Connection) -> None:
    if message.from_user is None:
        return

    user = await users.get_by_telegram_id(database, message.from_user.id)
    if user is None:
        await message.answer(
            "Welcome! Please choose your language:",
            reply_markup=language_keyboard(),
        )
        return

    greeting = (
        "Welcome back! Reminder management will be available soon."
        if user["language"] == "en"
        else "С возвращением! Управление напоминаниями скоро будет доступно."
    )
    await message.answer(greeting)


@router.callback_query(lambda callback: callback.data in {"language:ru", "language:en"})
async def language_handler(
    callback: CallbackQuery, database: aiosqlite.Connection
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    language = callback.data.rsplit(":", maxsplit=1)[1]
    existing_user = await users.get_by_telegram_id(database, callback.from_user.id)
    if existing_user is None:
        await users.create(database, callback.from_user.id, language)
    else:
        await users.update_language(database, callback.from_user.id, language)

    await callback.message.edit_text(
        "Language saved. Reminder management will be available soon."
        if language == "en"
        else "Язык сохранён. Управление напоминаниями скоро будет доступно."
    )
    await callback.answer()
