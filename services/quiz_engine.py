import random

import aiosqlite

from db.models import Question
from db.repositories.questions import get_weighted_question, get_random_question, get_weighted_question_from_ids


async def get_next_question(
    db: aiosqlite.Connection,
    user_id: int,
    task_number: int | None,
    subcategory: str | None = None,
    exclude_ids: list[int] | None = None,
    task_numbers: list[int] | None = None,
    problem_ids: list[int] | None = None,
) -> Question | None:
    """Получить следующий вопрос, исключая уже отвеченные."""
    if problem_ids is not None:
        return await get_weighted_question_from_ids(db, user_id, problem_ids, exclude_ids)
    question = await get_weighted_question(db, user_id, task_number, subcategory, exclude_ids, task_numbers)
    if not question:
        question = await get_random_question(db, task_number, subcategory, task_numbers)
    return question


def build_options(question: Question) -> list[str]:
    """Shuffle correct + wrong options, return ordered list."""
    options = [question.correct_answer] + question.wrong_options
    random.shuffle(options)
    return options


def check_answer(question: Question, selected_option: str) -> bool:
    return selected_option == question.correct_answer
