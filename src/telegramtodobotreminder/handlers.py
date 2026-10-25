import aiosqlite
from datetime import datetime
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from telegramtodobotreminder.database import reminders, users
from telegramtodobotreminder.keyboards import language_keyboard, timezone_keyboard
from telegramtodobotreminder.reminder_flow import ReminderInputError, parse_reminder_datetime
from telegramtodobotreminder.states import ReminderCreation
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


@router.message(Command("newreminder"))
async def new_reminder_handler(
    message: Message, state: FSMContext, database: aiosqlite.Connection
) -> None:
    if message.from_user is None:
        return
    user = await users.get_by_telegram_id(database, message.from_user.id)
    if user is None:
        await message.answer("Please use /start first.")
        return

    await state.set_state(ReminderCreation.title)
    await message.answer("Enter a reminder title, or /cancel to stop:")


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("There is no active operation.")
        return
    await state.clear()
    await message.answer("Reminder creation cancelled.")


@router.message(ReminderCreation.title)
async def reminder_title_handler(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("The title cannot be empty. Enter a title:")
        return
    await state.update_data(title=title)
    await state.set_state(ReminderCreation.date)
    await message.answer("Enter the event date (YYYY-MM-DD):")


@router.message(ReminderCreation.date)
async def reminder_date_handler(message: Message, state: FSMContext) -> None:
    date_text = (message.text or "").strip()
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        await message.answer("Use the date format YYYY-MM-DD:")
        return
    await state.update_data(date=date_text)
    await state.set_state(ReminderCreation.time)
    await message.answer("Enter the event time (HH:MM):")


@router.message(ReminderCreation.time)
async def reminder_time_handler(
    message: Message, state: FSMContext, database: aiosqlite.Connection
) -> None:
    if message.from_user is None:
        return
    data = await state.get_data()
    user = await users.get_by_telegram_id(database, message.from_user.id)
    if user is None:
        await state.clear()
        await message.answer("Please use /start first.")
        return

    try:
        remind_at = parse_reminder_datetime(
            data["date"], (message.text or "").strip(), user["timezone"]
        )
    except (KeyError, ReminderInputError) as error:
        await message.answer(f"{error}\nEnter the event time (HH:MM):")
        return

    reminder_id = await reminders.create(
        database, message.from_user.id, data["title"], remind_at
    )
    await state.clear()
    await message.answer(
        f"Reminder #{reminder_id} created for {remind_at.isoformat()} UTC."
    )
