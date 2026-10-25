from aiogram.fsm.state import State, StatesGroup


class ReminderCreation(StatesGroup):
    title = State()
    date = State()
    time = State()
