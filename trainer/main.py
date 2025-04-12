import os
import logging
import asyncio
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
from telegram.request import HTTPXRequest
from handlers import start, game, button, setnick, handle_nick_reply
from database import init_db

# --- Глобальный логгер ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Получение и проверка переменных окружения ---
def get_env_variable(name: str, required: bool = True, default=None):
    value = os.getenv(name, default)
    if required and not value:
        logger.error(f"Переменная окружения '{name}' не задана!")
        raise EnvironmentError(f"{name} not set")
    return value

# --- Основная асинхронная точка запуска ---
async def main():
    logger.info("🚀 Запуск Telegram-бота...")

    # Получаем переменные окружения
    token = get_env_variable("TELEGRAM_TOKEN")
    hostname = get_env_variable("RENDER_EXTERNAL_HOSTNAME")
    port = int(os.getenv("PORT", "10000"))

    # Инициализация базы данных
    init_db()
    logger.info("🗄️ База данных SQLite инициализирована")

    # Настройка HTTP-запросов
    request = HTTPXRequest(read_timeout=60, connect_timeout=60)

    # Инициализация приложения
    app = Application.builder().token(token).request(request).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setnick", setnick))
    app.add_handler(MessageHandler(filters.REPLY & ~filters.COMMAND, handle_nick_reply))
    app.add_handler(MessageHandler(filters.Text(["Игра"]), game))
    app.add_handler(CallbackQueryHandler(button))

    # Настройка вебхука
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

    # Поддержка живого цикла
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Остановка бота...")
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

# --- Запуск ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"❌ Ошибка при запуске бота: {e}")
