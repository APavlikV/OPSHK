import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
from trainer.handlers import setup_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"User {message.from_user.id} started bot")
    await message.answer(
        "Добро пожаловать в OPSHK! 💪\nВведи уникальное имя своего бойца:"
    )

if __name__ == "__main__":
    logger.info("Starting bot polling")
    setup_handlers(dp)
    try:
        dp.run_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Polling failed: {e}")
