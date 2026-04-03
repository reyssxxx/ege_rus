from aiogram.fsm.state import State, StatesGroup


class QuizState(StatesGroup):
    choosing_category = State()
    choosing_subcategory = State()
    answering = State()
    reviewing = State()
    paused = State()
