import aiosqlite
from datetime import date, datetime
from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.types import CallbackQuery, Message

from telegramtodobotreminder.database import reminders, users
from telegramtodobotreminder.database import notifications
from telegramtodobotreminder.keyboards import (
    delete_confirmation_keyboard,
    cancel_keyboard,
    date_picker_keyboard,
    language_keyboard,
    main_menu_keyboard,
    settings_keyboard,
    reminder_actions_keyboard,
    timezone_keyboard,
)
from telegramtodobotreminder.reminder_flow import (
    ReminderInputError,
    parse_reminder_datetime,
    validate_reminder_date,
)
from telegramtodobotreminder.states import ReminderCreation, ReminderEditing
from telegramtodobotreminder.scheduler import ReminderScheduler
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
        "Welcome back! Use /newreminder to create a reminder, "
        "or /reminders to view your reminders."
        if user["language"] == "en"
        else "С возвращением! Используйте /newreminder для создания "
        "напоминания или /reminders для просмотра списка."
    )
    await message.answer(
        greeting,
        reply_markup=main_menu_keyboard(user["language"]),
    )


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


@router.callback_query(lambda callback: callback.data == "settings:timezone")
async def settings_timezone_handler(
    callback: CallbackQuery, database: aiosqlite.Connection
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    user = await users.get_by_telegram_id(database, callback.from_user.id)
    language = user["language"] if user else "en"
    await callback.message.answer(
        "Choose your timezone:" if language == "en" else "Выберите часовой пояс:",
        reply_markup=timezone_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda callback: callback.data.startswith("settings:language:"))
async def settings_language_handler(
    callback: CallbackQuery, database: aiosqlite.Connection
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    language = callback.data.rsplit(":", maxsplit=1)[1]
    await users.update_language(database, callback.from_user.id, language)
    await callback.message.edit_text(
        "Language updated." if language == "en" else "Язык обновлён."
    )
    await callback.message.answer(
        "Choose an action:" if language == "en" else "Выберите действие:",
        reply_markup=main_menu_keyboard(language),
    )
    await callback.answer()


@router.callback_query(lambda callback: callback.data.startswith("settings:push:"))
async def settings_push_handler(
    callback: CallbackQuery,
    database: aiosqlite.Connection,
    reminder_scheduler: ReminderScheduler,
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    enabled = callback.data.endswith(":on")
    await users.update_push_notifications(database, callback.from_user.id, enabled)
    if not enabled:
        await notifications.cancel_pending_for_user(database, callback.from_user.id)
    else:
        await notifications.resume_for_user(database, callback.from_user.id)
        await reminder_scheduler.restore()
    user = await users.get_by_telegram_id(database, callback.from_user.id)
    language = user["language"] if user else "en"
    await callback.message.edit_text(
        "Notification settings updated."
        if language == "en"
        else "Настройки уведомлений обновлены.",
        reply_markup=settings_keyboard(language, enabled),
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
        f"Timezone saved: {timezone}.\n"
        "Use /newreminder to create a reminder or /reminders to view your list."
        if language == "en"
        else f"Часовой пояс сохранён: {timezone}.\n"
        "Используйте /newreminder для создания напоминания "
        "или /reminders для просмотра списка."
    )
    await callback.message.answer(
        "Choose an action:" if language == "en" else "Выберите действие:",
        reply_markup=main_menu_keyboard(language),
    )
    await callback.answer()


@router.message(F.text.in_({"Create reminder", "Создать напоминание"}))
async def create_reminder_button_handler(
    message: Message, state: FSMContext, database: aiosqlite.Connection
) -> None:
    await new_reminder_handler(message, state, database)


@router.message(F.text.in_({"My reminders", "Мои напоминания"}))
async def list_reminders_button_handler(
    message: Message, database: aiosqlite.Connection
) -> None:
    await reminders_list_handler(message, database)


@router.message(F.text.in_({"Settings", "Настройки"}))
async def settings_button_handler(
    message: Message, database: aiosqlite.Connection
) -> None:
    if message.from_user is None:
        return
    user = await users.get_by_telegram_id(database, message.from_user.id)
    if user is None:
        await message.answer("Please use /start first.")
        return
    language = user["language"]
    await message.answer(
        "Settings:" if language == "en" else "Настройки:",
        reply_markup=settings_keyboard(language, bool(user["push_notifications"])),
    )


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
    await state.update_data(language=user["language"], timezone=user["timezone"])
    user_language = user["language"]
    await message.answer(
        "Enter a reminder title:" if user_language == "en" else "Введите название напоминания:",
        reply_markup=cancel_keyboard(user_language),
    )


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("There is no active operation.")
        return
    data = await state.get_data()
    language = data.get("language", "en")
    await state.clear()
    await message.answer(
        "Reminder creation cancelled."
        if language == "en"
        else "Создание напоминания отменено.",
        reply_markup=main_menu_keyboard(language),
    )


@router.message(F.text.in_({"Cancel", "Отмена"}))
async def cancel_button_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    language = data.get("language", "en")
    await state.clear()
    await message.answer(
        "Reminder creation cancelled."
        if language == "en"
        else "Создание напоминания отменено.",
        reply_markup=main_menu_keyboard(language),
    )


@router.message(ReminderCreation.title)
async def reminder_title_handler(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("The title cannot be empty. Enter a title:")
        return
    await state.update_data(title=title)
    await state.set_state(ReminderCreation.date)
    await message.answer(
        "Choose the event date or enter it manually (YYYY-MM-DD):",
        reply_markup=date_picker_keyboard(
            date.today().year, date.today().month, "en"
        ),
    )


@router.callback_query(lambda callback: callback.data == "calendar:manual")
async def manual_date_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ReminderCreation.date)
    await callback.message.answer("Enter the event date (YYYY-MM-DD):")
    await callback.answer()


@router.callback_query(lambda callback: callback.data.startswith("calendar:date:"))
async def calendar_date_handler(
    callback: CallbackQuery, state: FSMContext, database: aiosqlite.Connection
) -> None:
    selected_date = callback.data.removeprefix("calendar:date:")
    data = await state.get_data()
    try:
        validate_reminder_date(selected_date, data.get("timezone", "UTC"))
    except ReminderInputError as error:
        await callback.answer(str(error), show_alert=True)
        return
    await state.update_data(date=selected_date)
    await state.set_state(ReminderCreation.time)
    await callback.message.edit_text(
        f"Selected date: {selected_date}\nEnter the event time (HH:MM):"
    )
    await callback.answer()


@router.callback_query(lambda callback: callback.data == "calendar:ignore")
async def calendar_ignore_handler(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message(ReminderCreation.date)
async def reminder_date_handler(message: Message, state: FSMContext) -> None:
    date_text = (message.text or "").strip()
    data = await state.get_data()
    try:
        validate_reminder_date(date_text, data.get("timezone", "UTC"))
    except ReminderInputError as error:
        await message.answer(str(error))
        return
    await state.update_data(date=date_text)
    await state.set_state(ReminderCreation.time)
    await message.answer("Enter the event time (HH:MM):")


@router.message(ReminderCreation.time)
async def reminder_time_handler(
    message: Message,
    state: FSMContext,
    database: aiosqlite.Connection,
    reminder_scheduler: ReminderScheduler,
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
    await reminder_scheduler.restore()
    await state.clear()
    await message.answer(
        f"Reminder #{reminder_id} created for {remind_at.isoformat()} UTC."
    )


@router.message(Command("reminders"))
async def reminders_list_handler(
    message: Message, database: aiosqlite.Connection
) -> None:
    if message.from_user is None:
        return
    items = await reminders.list_for_user(database, message.from_user.id)
    if not items:
        await message.answer("You have no reminders.")
        return

    for reminder in items:
        await message.answer(
            f"#{reminder['id']} — {reminder['title']}\n"
            f"Event: {reminder['remind_at']} UTC\n"
            f"Status: {reminder['status']}",
            reply_markup=reminder_actions_keyboard(reminder["id"]),
        )


@router.message(Command("reminder"))
async def reminder_details_handler(
    message: Message, command: CommandObject, database: aiosqlite.Connection
) -> None:
    reminder_id = _command_id(command.args)
    if reminder_id is None or message.from_user is None:
        await message.answer("Usage: /reminder <id>")
        return
    reminder = await reminders.get_for_user(
        database, message.from_user.id, reminder_id
    )
    if reminder is None:
        await message.answer("Reminder not found.")
        return
    await message.answer(
        f"#{reminder['id']} — {reminder['title']}\n"
        f"Event: {reminder['remind_at']} UTC\n"
        f"Status: {reminder['status']}",
        reply_markup=reminder_actions_keyboard(reminder["id"]),
    )


@router.message(Command("editreminder"))
async def edit_reminder_handler(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    database: aiosqlite.Connection,
) -> None:
    reminder_id = _command_id(command.args)
    if reminder_id is None or message.from_user is None:
        await message.answer("Usage: /editreminder <id>")
        return
    reminder = await reminders.get_for_user(
        database, message.from_user.id, reminder_id
    )
    if reminder is None:
        await message.answer("Reminder not found.")
        return
    await state.set_state(ReminderEditing.title)
    await state.update_data(reminder_id=reminder_id)
    await message.answer("Enter the new title, or /cancel to stop:")


@router.message(ReminderEditing.title)
async def edit_title_handler(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("The title cannot be empty. Enter a title:")
        return
    await state.update_data(title=title)
    await state.set_state(ReminderEditing.date)
    await message.answer("Enter the new event date (YYYY-MM-DD):")


@router.message(ReminderEditing.date)
async def edit_date_handler(
    message: Message, state: FSMContext, database: aiosqlite.Connection
) -> None:
    date_text = (message.text or "").strip()
    if message.from_user is None:
        return
    user = await users.get_by_telegram_id(database, message.from_user.id)
    timezone = user["timezone"] if user else "UTC"
    try:
        validate_reminder_date(date_text, timezone)
    except ReminderInputError as error:
        await message.answer(str(error))
        return
    await state.update_data(date=date_text)
    await state.set_state(ReminderEditing.time)
    await message.answer("Enter the new event time (HH:MM):")


@router.message(ReminderEditing.time)
async def edit_time_handler(
    message: Message,
    state: FSMContext,
    database: aiosqlite.Connection,
    reminder_scheduler: ReminderScheduler,
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
        updated = await reminders.update_for_user(
            database,
            message.from_user.id,
            data["reminder_id"],
            data["title"],
            remind_at,
        )
    except (KeyError, ReminderInputError) as error:
        await message.answer(f"{error}\nEnter the event time (HH:MM):")
        return
    await state.clear()
    if updated:
        await reminder_scheduler.restore()
    await message.answer("Reminder updated." if updated else "Reminder not found.")


@router.callback_query(lambda callback: callback.data.startswith("reminder:"))
async def reminder_action_handler(
    callback: CallbackQuery, database: aiosqlite.Connection
) -> None:
    if callback.from_user is None or callback.message is None:
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Invalid action.", show_alert=True)
        return
    action, reminder_id_text = parts[1:]
    try:
        reminder_id = int(reminder_id_text)
    except ValueError:
        await callback.answer("Invalid reminder.", show_alert=True)
        return

    reminder = await reminders.get_for_user(
        database, callback.from_user.id, reminder_id
    )
    if reminder is None:
        await callback.answer("Reminder not found.", show_alert=True)
        return
    if action == "delete":
        await callback.message.edit_reply_markup(
            reply_markup=delete_confirmation_keyboard(reminder_id)
        )
    elif action == "delete-confirm":
        await reminders.delete_for_user(database, callback.from_user.id, reminder_id)
        await callback.message.edit_text("Reminder deleted.")
    elif action == "delete-cancel":
        await callback.message.edit_reply_markup(
            reply_markup=reminder_actions_keyboard(reminder_id)
        )
    elif action == "edit":
        await callback.answer(
            "Use /editreminder <id> to edit this reminder.", show_alert=True
        )
        return
    await callback.answer()


def _command_id(args: str | None) -> int | None:
    if not args:
        return None
    try:
        return int(args.strip())
    except ValueError:
        return None
