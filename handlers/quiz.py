import asyncio
import logging

import aiosqlite
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from db.repositories.answers import record_answer
from db.repositories.questions import get_question_by_id
from db.repositories.users import ensure_user, update_session_streak, get_longest_streak
from keyboards.callbacks import QuizAnswer, QuizControl, TaskStart
from keyboards.quiz import answer_keyboard, stop_keyboard, continue_keyboard
from keyboards.menu import main_menu_keyboard
from services.quiz_engine import get_next_question, build_options, check_answer
from states.quiz import QuizState
from utils.formatting import format_question_text, format_feedback_text, format_session_summary
from utils.safe_edit import safe_edit_text
from utils.constants import LONG_EXPLANATION_THRESHOLD

router = Router()
logger = logging.getLogger(__name__)

FEEDBACK_DELAY = 0.8  # seconds before auto-advancing on correct answer


async def send_question(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    """Fetch next question and display it."""
    data = await state.get_data()

    # Защита: если сессия очищена (пользователь нажал стоп), не показывать вопрос
    if "task_number" not in data:
        return

    try:
        task_number = data.get("task_number")
        subcategory = data.get("subcategory")
        task_numbers = data.get("task_numbers")  # multi-select mode
        streak = data.get("streak", 0)
        session_total = data.get("session_total", 0)
        best_streak = data.get("best_streak", 0)
        answered = data.get("answered_questions", [])

        question = await get_next_question(db, callback.from_user.id, task_number, subcategory, exclude_ids=answered, task_numbers=task_numbers)
        if not question:
            await safe_edit_text(
                callback,
                "В этой категории пока нет вопросов.",
                reply_markup=main_menu_keyboard(),
            )
            await state.clear()
            return

        options = build_options(question)

        await state.set_state(QuizState.answering)
        await state.update_data(
            current_question_id=question.id,
            options_order=options,
        )

        # In "all tasks" mode show the actual task number of the drawn question
        display_task_number = question.task_number if task_number is None else task_number

        text = format_question_text(
            task_number=display_task_number,
            subcategory=subcategory,
            word_display=question.word_display,
            streak=streak,
            session_total=session_total,
            best_streak=best_streak,
        )

        await safe_edit_text(
            callback,
            text=text,
            reply_markup=answer_keyboard(question.id, options),
        )
    except Exception:
        logger.exception("Error in send_question")
        await safe_edit_text(
            callback,
            "Что-то пошло не так. Попробуй /start",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()


@router.callback_query(QuizAnswer.filter(), QuizState.answering)
async def cb_answer(
    callback: CallbackQuery,
    callback_data: QuizAnswer,
    state: FSMContext,
    db: aiosqlite.Connection,
):
    data = await state.get_data()
    question_id = data.get("current_question_id")
    options_order = data.get("options_order", [])
    answered = data.get("answered_questions", [])

    if callback_data.qid != question_id:
        await callback.answer("Этот вопрос уже неактуален.")
        return

    if not options_order or callback_data.idx >= len(options_order):
        await callback.answer("Ошибка: неверный вариант ответа.")
        return

    question = await get_question_by_id(db, question_id)
    if not question:
        await callback.answer("Ошибка: вопрос не найден.")
        return

    try:
        selected_option = options_order[callback_data.idx]
        is_correct = check_answer(question, selected_option)

        session_total = data.get("session_total", 0) + 1
        session_correct = data.get("session_correct", 0)
        session_wrong = data.get("session_wrong", 0)
        streak = data.get("streak", 0)
        is_new_record = False

        if is_correct:
            streak += 1
            session_correct += 1
        else:
            # При ошибке: проверяем рекорд (один SQL, нет race condition)
            if streak > 0:
                is_new_record = await update_session_streak(db, callback.from_user.id, streak)
            streak = 0
            session_wrong += 1

        # Получаем актуальный рекорд одним запросом
        best_streak = await get_longest_streak(db, callback.from_user.id)

        await ensure_user(db, callback.from_user.id, callback.from_user.username)
        await record_answer(db, callback.from_user.id, question_id, is_correct)

        await state.update_data(
            session_total=session_total,
            session_correct=session_correct,
            session_wrong=session_wrong,
            streak=streak,
            best_streak=best_streak,
            answered_questions=list(set(answered + [question_id])),
        )

        text = format_feedback_text(
            is_correct=is_correct,
            word_display=question.word_display,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            streak=streak,
            session_total=session_total,
            best_streak=best_streak,
        )

        # Block double-tap during delay
        await state.set_state(QuizState.reviewing)

        # Определяем тип задания: если пояснение длинное — ручной переход
        has_long_explanation = question.explanation and len(question.explanation) > LONG_EXPLANATION_THRESHOLD

        if is_new_record:
            text += "\n\n🏆 <b>Новый рекорд!</b>"

        if has_long_explanation or not is_correct:
            # Длинное пояснение или ошибка — ждём нажатия "Продолжить"
            await safe_edit_text(callback, text=text, reply_markup=continue_keyboard())
        else:
            # Краткое правильное задание — авто-переход через FEEDBACK_DELAY
            await safe_edit_text(callback, text=text, reply_markup=stop_keyboard())
            await callback.answer()
            await asyncio.sleep(FEEDBACK_DELAY)
            # Проверяем что сессия всё ещё активна (пользователь мог нажать стоп)
            current_state = await state.get_state()
            if current_state == QuizState.reviewing:
                data = await state.get_data()
                if "task_number" in data:
                    await send_question(callback, state, db)
    except Exception:
        logger.exception("Error in cb_answer")
        await safe_edit_text(
            callback,
            "Что-то пошло не так. Попробуй /start",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
    await callback.answer()


@router.callback_query(QuizControl.filter(F.action == "continue"), QuizState.reviewing)
async def cb_continue(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
):
    data = await state.get_data()
    if "task_number" not in data:
        await callback.answer("Ошибка: данные сессии потеряны. Начни заново.")
        return
    await send_question(callback, state, db)
    await callback.answer()


@router.callback_query(QuizControl.filter(F.action == "restart"))
async def cb_restart(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
):
    """Restart the same task (or all-tasks mode) from scratch."""
    data = await state.get_data()
    # "task_number" key must exist; None = all-tasks mode, int = specific task
    if "task_number" not in data:
        from keyboards.category import tasks_keyboard
        await state.set_state(QuizState.choosing_category)
        await safe_edit_text(callback, "Выбери задание:", reply_markup=tasks_keyboard())
        await callback.answer()
        return

    # Получаем рекорд из БД
    best_streak = await get_longest_streak(db, callback.from_user.id)

    await state.update_data(
        subcategory=None,
        session_total=0,
        session_correct=0,
        session_wrong=0,
        streak=0,
        best_streak=best_streak,
    )
    await send_question(callback, state, db)
    await callback.answer()


@router.callback_query(QuizControl.filter(F.action == "stop"))
async def cb_stop_quiz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    best_streak = data.get("best_streak", 0)
    session_correct = data.get("session_correct", 0)
    session_wrong = data.get("session_wrong", 0)

    text = format_session_summary(best_streak, session_correct, session_wrong)
    await state.clear()
    await safe_edit_text(callback, text=text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(QuizControl.filter(F.action == "menu"))
async def cb_change_category(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit_text(
        callback,
        "Главное меню:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
