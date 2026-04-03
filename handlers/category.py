import aiosqlite
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from db.repositories.questions import get_task_answer_stats
from keyboards.callbacks import MenuAction, TaskSelect, TaskStart
from keyboards.category import tasks_keyboard, task_info_keyboard
from states.quiz import QuizState
from handlers.quiz import send_question
from utils.formatting import format_task_info

router = Router()


@router.callback_query(MenuAction.filter(F.action == "tasks"))
async def cb_show_tasks(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QuizState.choosing_category)
    await callback.message.edit_text("Выбери задание:", reply_markup=tasks_keyboard())
    await callback.answer()


@router.callback_query(TaskSelect.filter())
async def cb_show_task_info(
    callback: CallbackQuery,
    callback_data: TaskSelect,
    state: FSMContext,
    db: aiosqlite.Connection,
):
    task_number = callback_data.task
    total, accuracy = await get_task_answer_stats(db, callback.from_user.id, task_number)

    await state.set_state(QuizState.choosing_category)
    await state.update_data(task_number=task_number)

    text = format_task_info(task_number, total, accuracy)
    await callback.message.edit_text(text, reply_markup=task_info_keyboard(task_number))
    await callback.answer()


@router.callback_query(TaskStart.filter())
async def cb_start_task(
    callback: CallbackQuery,
    callback_data: TaskStart,
    state: FSMContext,
    db: aiosqlite.Connection,
):
    await state.update_data(
        task_number=callback_data.task,
        subcategory=None,
        session_correct=0,
        session_total=0,
        streak=0,
    )
    await send_question(callback, state, db)
    await callback.answer()
