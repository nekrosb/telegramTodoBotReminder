from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message


router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! Я бот для управления напоминаниями. "
        "Функции напоминаний скоро будут доступны."
    )
