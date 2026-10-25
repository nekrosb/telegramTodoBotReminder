from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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
