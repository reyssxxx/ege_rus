import asyncio

import aiosqlite
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from db.repositories.answers import record_answer
from db.repositories.questions import get_question_by_id
from db.repositories.users import ensure_user, update_streak
from keyboards.callbacks import QuizAnswer, QuizControl, TaskStart
from keyboards.quiz import answer_keyboard, stop_keyboard, paused_keyboard, wrong_answer_keyboard
from keyboards.menu import main_menu_keyboard
from services.quiz_engine import get_next_question, build_options, check_answer
from states.quiz import QuizState
from utils.formatting import format_question_text, format_feedback_text, format_session_summary

router = Router()

FEEDBACK_DELAY = 0.8  # seconds before auto-advancing on correct answer


async def send_question(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection):
    """Fetch next question and display it."""
    data = await state.get_data()
    task_number = data["task_number"]
    subcategory = data.get("subcategory")
    streak = data.get("streak", 0)
    session_total = data.get("session_total", 0)

    question = await get_next_question(db, callback.from_user.id, task_number, subcategory)
    if not question:
        await callback.message.edit_text(
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
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=answer_keyboard(question.id, options),
    )


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

    if callback_data.qid != question_id:
        await callback.answer("Этот вопрос уже неактуален.")
        return

    question = await get_question_by_id(db, question_id)
    if not question:
        await callback.answer("Ошибка: вопрос не найден.")
        return

    selected_option = options_order[callback_data.idx]
    is_correct = check_answer(question, selected_option)

    session_total = data.get("session_total", 0) + 1
    streak = data.get("streak", 0)
    if is_correct:
        streak += 1
    else:
        streak = 0

    await ensure_user(db, callback.from_user.id, callback.from_user.username)
    await record_answer(db, callback.from_user.id, question_id, is_correct)
    await update_streak(db, callback.from_user.id)

    await state.update_data(
        session_total=session_total,
        streak=streak,
    )

    text = format_feedback_text(
        is_correct=is_correct,
        word_display=question.word_display,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        streak=streak,
        session_total=session_total,
    )

    # Block double-tap during delay
    await state.set_state(QuizState.reviewing)

    if is_correct:
        # Auto-advance to next question after brief feedback
        await callback.message.edit_text(text=text, reply_markup=stop_keyboard())
        await callback.answer()
        await asyncio.sleep(FEEDBACK_DELAY)
        current_state = await state.get_state()
        if current_state == QuizState.reviewing:
            await send_question(callback, state, db)
    else:
        # Wrong answer — session stops, offer restart
        await callback.message.edit_text(text=text, reply_markup=wrong_answer_keyboard())
        await callback.answer()


@router.callback_query(QuizControl.filter(F.action == "pause"), QuizState.reviewing)
async def cb_pause(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QuizState.paused)
    await callback.message.edit_reply_markup(reply_markup=paused_keyboard())
    await callback.answer()


@router.callback_query(QuizControl.filter(F.action == "continue"), QuizState.paused)
async def cb_continue(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
):
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
        await callback.message.edit_text("Выбери задание:", reply_markup=tasks_keyboard())
        await callback.answer()
        return

    await state.update_data(
        subcategory=None,
        session_correct=0,
        session_total=0,
        streak=0,
    )
    await send_question(callback, state, db)
    await callback.answer()


@router.callback_query(QuizControl.filter(F.action == "stop"))
async def cb_stop_quiz(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    streak = data.get("streak", 0)
    session_total = data.get("session_total", 0)

    text = format_session_summary(streak, session_total)
    await state.clear()
    await callback.message.edit_text(text=text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(QuizControl.filter(F.action == "menu"))
async def cb_change_category(callback: CallbackQuery, state: FSMContext):
    from keyboards.category import tasks_keyboard

    await state.clear()
    await state.set_state(QuizState.choosing_category)
    await callback.message.edit_text(
        "Выбери задание:",
        reply_markup=tasks_keyboard(),
    )
    await callback.answer()
