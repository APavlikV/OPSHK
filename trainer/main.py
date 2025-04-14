import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram import types
from dotenv import load_dotenv
from trainer.handlers import setup_handlers

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Добро пожаловать в OPSHK! 💪\nВведи уникальное имя своего бойца:"
    )

if __name__ == "__main__":
    setup_handlers(dp)
    dp.run_polling(bot)
