import calendar
from datetime import date

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from telegramtodobotreminder.timezones import COMMON_TIMEZONES


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский", callback_data="language:ru"),
                InlineKeyboardButton(text="English", callback_data="language:en"),
            ]
        ]
    )


def timezone_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label, callback_data=f"timezone:{identifier}"
                )
            ]
            for identifier, label in COMMON_TIMEZONES
        ]
    )


def reminder_actions_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Edit", callback_data=f"reminder:edit:{reminder_id}"
                ),
                InlineKeyboardButton(
                    text="Delete", callback_data=f"reminder:delete:{reminder_id}"
                ),
            ]
        ]
    )


def delete_confirmation_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Confirm deletion",
                    callback_data=f"reminder:delete-confirm:{reminder_id}",
                ),
                InlineKeyboardButton(
                    text="Cancel", callback_data=f"reminder:delete-cancel:{reminder_id}"
                ),
            ]
        ]
    )


def main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    labels = (
        ("Create reminder", "My reminders", "Settings")
        if language == "en"
        else ("Создать напоминание", "Мои напоминания", "Настройки")
    )
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label) for label in labels]],
        resize_keyboard=True,
    )


def cancel_keyboard(language: str) -> ReplyKeyboardMarkup:
    label = "Cancel" if language == "en" else "Отмена"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def date_picker_keyboard(year: int, month: int, language: str) -> InlineKeyboardMarkup:
    month_name = calendar.month_name[month]
    weekdays = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
    rows = [[InlineKeyboardButton(text=day, callback_data="calendar:ignore") for day in weekdays]]
    for week in calendar.monthcalendar(year, month):
        rows.append(
            [
                InlineKeyboardButton(
                    text=str(day) if day else " ",
                    callback_data=(
                        f"calendar:date:{year:04d}-{month:02d}-{day:02d}"
                        if day
                        else "calendar:ignore"
                    ),
                )
                for day in week
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=f"{month_name} {year}", callback_data="calendar:ignore"
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="Enter date manually" if language == "en" else "Ввести дату вручную",
                callback_data="calendar:manual",
            ),
            InlineKeyboardButton(
                text="Cancel" if language == "en" else "Отмена",
                callback_data="creation:cancel",
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
