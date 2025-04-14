from aiogram import Dispatcher, types
from aiogram.filters import Command
from trainer.keyboards import get_fight_keyboard
from trainer.texts import FIGHT_TEXT, PROFILE_TEXT

def setup_handlers(dp: Dispatcher):
    @dp.message(Command("profile"))
    async def cmd_profile(message: types.Message):
        await message.answer(PROFILE_TEXT)

    @dp.message(Command("fight"))
    async def cmd_fight(message: types.Message):
        keyboard = get_fight_keyboard()
        await message.answer(FIGHT_TEXT, reply_markup=keyboard)
