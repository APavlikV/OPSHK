import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler
from telegram.request import HTTPXRequest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def start(update, context):
    await update.message.reply_text("Добро пожаловать на Арену! Здесь будут PvP-сражения.")

async def main():
    logger.info("🚀 Запуск бота Арены...")
    token = os.getenv("ARENA_TELEGRAM_TOKEN")  # Отдельный токен для Арены
    if not token:
        raise ValueError("ARENA_TELEGRAM_TOKEN не задан!")
    hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    port = int(os.getenv("PORT", "10000"))

    request = HTTPXRequest(read_timeout=60, connect_timeout=60)
    app = Application.builder().token(token).request(request).build()

    app.add_handler(CommandHandler("start", start))

    webhook_url = f"https://{hostname}/{token}"
    logger.info(f"🌐 Установка webhook: {webhook_url}")

    await app.initialize()
    await app.start()
    await app.updater.start_webhook(listen="0.0.0.0", port=port, url_path=token, webhook_url=webhook_url)

    logger.info(f"✅ Вебхук активен на порту {port}")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
