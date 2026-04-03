from aiogram.fsm.state import State, StatesGroup


class QuizState(StatesGroup):
    choosing_category = State()
    answering = State()
    reviewing = State()
