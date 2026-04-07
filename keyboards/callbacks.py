from aiogram.filters.callback_data import CallbackData


class MenuAction(CallbackData, prefix="menu"):
    action: str  # "tasks", "stats", "problems", "back"


class TaskSelect(CallbackData, prefix="task"):
    task: int  # 4, 5, 9, 10, 11, 12, 14, 15


class TaskStart(CallbackData, prefix="tstart"):
    task: int  # start quiz for this task (no subcategory filter)


class QuizAnswer(CallbackData, prefix="ans"):
    qid: int  # question_id
    idx: int  # answer index in shuffled options


class QuizControl(CallbackData, prefix="qctl"):
    action: str  # "stop", "menu", "restart", "continue"


class StatsView(CallbackData, prefix="stats"):
    view: str  # "general", "tasks", "refresh"


class ReminderToggle(CallbackData, prefix="rem"):
    pass
