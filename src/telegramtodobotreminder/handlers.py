import aiosqlite
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from telegramtodobotreminder.database import users
from telegramtodobotreminder.keyboards import language_keyboard, timezone_keyboard
from telegramtodobotreminder.timezones import get_timezone


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


@router.message(Command("timezone"))
async def timezone_command_handler(
    message: Message, database: aiosqlite.Connection
) -> None:
    if message.from_user is None:
        return

    user = await users.get_by_telegram_id(database, message.from_user.id)
    language = user["language"] if user is not None else "en"
    prompt = (
        "Choose your timezone:" if language == "en" else "Выберите часовой пояс:"
    )
    await message.answer(prompt, reply_markup=timezone_keyboard())


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
        "Language saved. Now choose your timezone:"
        if language == "en"
        else "Язык сохранён. Теперь выберите часовой пояс:",
        reply_markup=timezone_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda callback: callback.data.startswith("timezone:"))
async def timezone_handler(
    callback: CallbackQuery, database: aiosqlite.Connection
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return

    timezone = callback.data.removeprefix("timezone:")
    try:
        get_timezone(timezone)
    except ValueError:
        await callback.answer("Invalid timezone.", show_alert=True)
        return

    user = await users.get_by_telegram_id(database, callback.from_user.id)
    if user is None:
        await callback.answer("Please use /start first.", show_alert=True)
        return

    await users.update_timezone(database, callback.from_user.id, timezone)
    language = user["language"]
    await callback.message.edit_text(
        f"Timezone saved: {timezone}. Reminder management will be available soon."
        if language == "en"
        else f"Часовой пояс сохранён: {timezone}. "
        "Управление напоминаниями скоро будет доступно."
    )
    await callback.answer()
