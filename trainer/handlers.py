import logging
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from trainer.keyboards import get_fight_keyboard, get_nickname_keyboard
from trainer.texts import FIGHT_TEXT, PROFILE_TEXT
from trainer.state import FightState
from trainer.data import save_fighter

logger = logging.getLogger(__name__)

def setup_handlers(dp: Dispatcher):
    @dp.message(Command("profile"))
    async def cmd_profile(message: types.Message):
        await message.answer(PROFILE_TEXT)

    @dp.message(Command("fight"))
    async def cmd_fight(message: types.Message):
        keyboard = get_fight_keyboard()
        await message.answer(FIGHT_TEXT, reply_markup=keyboard)

    @dp.callback_query()
    async def debug_callback(callback: CallbackQuery):
        logger.info(f"Received callback: {callback.data} from {callback.from_user.id}")
        await callback.answer()

    @dp.callback_query(F.data == "use_telegram_nick")
    async def use_telegram_nick(callback: CallbackQuery, state: FSMContext):
        logger.info(f"Button use_telegram_nick pressed by {callback.from_user.id}")
        username = callback.from_user.username or f"User{callback.from_user.id}"
        user_id = callback.from_user.id
        try:
            save_fighter(user_id, username)
            await callback.message.edit_text(f"Ник сохранён: {username}! Готов к бою? 💪")
            await state.clear()
        except Exception as e:
            await callback.message.edit_text(f"Ошибка сохранения: {e}")
        await callback.answer()

    @dp.callback_query(F.data == "custom_nick")
    async def custom_nick(callback: CallbackQuery, state: FSMContext):
        logger.info(f"Button custom_nick pressed by {callback.from_user.id}")
        await callback.message.edit_text("Введи свой уникальный ник:")
        await state.set_state(FightState.waiting_for_name)
        await callback.answer()

    @dp.message(FightState.waiting_for_name)
    async def process_custom_nick(message: Message, state: FSMContext):
        nickname = message.text.strip()
        user_id = message.from_user.id
        try:
            save_fighter(user_id, nickname)
            await message.answer(f"Ник сохранён: {nickname}! Готов к бою? 💪")
            await state.clear()
        except Exception as e:
            await message.answer(f"Ошибка сохранения: {e}")
