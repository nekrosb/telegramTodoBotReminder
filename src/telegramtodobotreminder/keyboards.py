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
