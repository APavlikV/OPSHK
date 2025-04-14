import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
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

async def main():
    logger.info("🚀 Запуск Telegram-бота...")
    setup_handlers(dp)
    try:
        # Настройка вебхука
        webhook_path = "/webhook"
        hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
        port = int(os.getenv("PORT", "10000"))
        webhook_url = f"https://{hostname}{webhook_path}"

        logger.info(f"Setting webhook: {webhook_url}")
        await bot.set_webhook(webhook_url)

        # Настройка aiohttp-сервера
        app = web.Application()
        webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        webhook_handler.register(app, path=webhook_path)
        setup_application(app, dp, bot=bot)

        # Запуск сервера
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        logger.info(f"Starting webhook server on port {port}")
        await site.start()

        # Держим сервер запущенным
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"Webhook failed: {e}")
    finally:
        await bot.delete_webhook()
        await dp.storage.close()

if __name__ == "__main__":
    asyncio.run(main())
