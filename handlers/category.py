import logging

import aiosqlite
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from db.repositories.questions import get_subcategories
from db.repositories.users import get_longest_streak
from keyboards.callbacks import MenuAction, TaskToggle, MultiTaskStart, TaskStart, SubcategorySelect
from keyboards.category import tasks_keyboard, task_info_keyboard
from keyboards.menu import subcategory_keyboard
from states.quiz import QuizState
from handlers.quiz import send_question
from utils.safe_edit import safe_edit_text

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(MenuAction.filter(F.action == "tasks"))
async def cb_show_tasks(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QuizState.choosing_category)
    await state.update_data(selected_tasks=[])
    await safe_edit_text(
        callback,
        "Выбери задания для тренировки:",
        reply_markup=tasks_keyboard(selected=set()),
    )
    await callback.answer()


@router.callback_query(TaskToggle.filter(), QuizState.choosing_category)
async def cb_toggle_task(
    callback: CallbackQuery,
    callback_data: TaskToggle,
    state: FSMContext,
):
    data = await state.get_data()
    selected = set(data.get("selected_tasks", []))
    task = callback_data.task
    if task in selected:
        selected.discard(task)
    else:
        selected.add(task)
    await state.update_data(selected_tasks=list(selected))
    await safe_edit_text(
        callback,
        "Выбери задания для тренировки:",
        reply_markup=tasks_keyboard(selected=selected),
    )
    await callback.answer()


@router.callback_query(MultiTaskStart.filter(), QuizState.choosing_category)
async def cb_multi_start(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
):
    data = await state.get_data()
    selected = list(data.get("selected_tasks", []))
    if not selected:
        await callback.answer("Выбери хотя бы одно задание.", show_alert=True)
        return

    best_streak = await get_longest_streak(db, callback.from_user.id)
    await state.update_data(
        task_number=None,
        task_numbers=selected,
        subcategory=None,
        session_total=0,
        session_correct=0,
        session_wrong=0,
        streak=0,
        best_streak=best_streak,
    )
    await send_question(callback, state, db)
    await callback.answer()


@router.callback_query(TaskStart.filter())
async def cb_start_task(
    callback: CallbackQuery,
    callback_data: TaskStart,
    state: FSMContext,
    db: aiosqlite.Connection,
):
    task_number = callback_data.task
    subcats = await get_subcategories(db, task_number)

    # Если несколько подкатегорий — показываем экран выбора
    if len(subcats) > 1:
        await state.update_data(task_number=task_number)
        from utils.constants import TASK_NAMES
        name = TASK_NAMES.get(task_number, f"Задание {task_number}")
        await safe_edit_text(
            callback,
            f"📂 <b>Задание {task_number}: {name}</b>\n\nВыбери раздел:",
            reply_markup=subcategory_keyboard(task_number, subcats),
        )
        await callback.answer()
        return

    # Одна подкатегория — стартуем сразу
    best_streak = await get_longest_streak(db, callback.from_user.id)
    await state.update_data(
        task_number=task_number,
        task_numbers=None,
        subcategory=subcats[0] if subcats else None,
        session_total=0,
        session_correct=0,
        session_wrong=0,
        streak=0,
        best_streak=best_streak,
    )
    await send_question(callback, state, db)
    await callback.answer()


@router.callback_query(SubcategorySelect.filter())
async def cb_select_subcategory(
    callback: CallbackQuery,
    callback_data: SubcategorySelect,
    state: FSMContext,
    db: aiosqlite.Connection,
):
    best_streak = await get_longest_streak(db, callback.from_user.id)
    subcategory = callback_data.subcat if callback_data.subcat else None

    await state.update_data(
        task_number=callback_data.task,
        task_numbers=None,
        subcategory=subcategory,
        session_total=0,
        session_correct=0,
        session_wrong=0,
        streak=0,
        best_streak=best_streak,
    )
    await send_question(callback, state, db)
    await callback.answer()
