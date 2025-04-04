import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
import logging
import asyncio
from handlers import start, game, button

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Добавляем обработчик ошибок для JobQueue
async def error_handler(context):
    logger.error(f"Произошла ошибка в задании: {context.error}", exc_info=True)

async def main():
    logger.info("Запуск бота...")
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN не задан!")
        return

    hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if not hostname:
        logger.error("RENDER_EXTERNAL_HOSTNAME не задан!")
        return

    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Используется порт: {port}")

    request = HTTPXRequest(read_timeout=60, connect_timeout=60)
    app = Application.builder().token(token).request(request).build()

    # Регистрируем обработчик ошибок для JobQueue
    app.job_queue.set_error_handler(error_handler)

    # Регистрируем обработчики команд и кнопок
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(["Игра"]), game))
    app.add_handler(CallbackQueryHandler(button))

    webhook_url = f"https://{hostname}/{token}"
    logger.info(f"Настройка вебхука: {webhook_url}")

    await app.initialize()
    logger.info("Приложение инициализировано")
    await app.start()
    logger.info("Приложение запущено")
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=token,
        webhook_url=webhook_url
    )
    logger.info(f"Вебхук запущен на порту {port}")

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
