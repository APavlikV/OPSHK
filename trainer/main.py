import os
import sys
import logging
import asyncio
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from telegram.request import HTTPXRequest

# Добавляем корень проекта в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trainer.handlers import start, game, button, setnick, handle_nick_reply

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_env_variable(name: str, required: bool = True, default=None):
    value = os.getenv(name, default)
    if required and not value:
        logger.error(f"Переменная окружения '{name}' не задана!")
        raise EnvironmentError(f"{name} not set")
    return value

async def main():
    logger.info("🚀 Запуск Telegram-бота...")

    token = get_env_variable("TELEGRAM_TOKEN")
    hostname = get_env_variable("RENDER_EXTERNAL_HOSTNAME")
    port = int(os.getenv("PORT", "10000"))

    request = HTTPXRequest(read_timeout=60, connect_timeout=60)

    app = Application.builder().token(token).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setnick", setnick))
    app.add_handler(MessageHandler(filters.REPLY, handle_nick_reply))
    app.add_handler(MessageHandler(filters.Text(["Игра"]), game))
    app.add_handler(CallbackQueryHandler(button))

    webhook_url = f"https://{hostname}/{token}"
    logger.info(f"🌐 Установка webhook: {webhook_url}")

    await app.initialize()
    await app.start()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=token,
        webhook_url=webhook_url
    )

    logger.info(f"✅ Вебхук активен на порту {port}")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Остановка бота...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"❌ Ошибка при запуске бота: {e}")
