import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from handlers import (
    start,
    setnick,
    handle_nick_reply,
    game,
    button,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def shutdown(application):
    logger.info("Завершение работы приложения")
    await application.stop()
    await application.updater.stop()

def main():
    try:
        logger.info("Запуск приложения")
        application = Application.builder().token("7027562944:AAHhp7ajrp28z7E8mlVkKth0P2BbP79v2LM").build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("setnick", setnick))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex("Игра"), game))
        application.add_handler(MessageHandler(filters.REPLY & ~filters.COMMAND, handle_nick_reply))
        application.add_handler(CallbackQueryHandler(button))

        logger.info("Настройка polling")
        application.run_polling(allowed_updates=["message", "callback_query"], drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
        raise
    finally:
        logger.info("Инициируется завершение работы")
        import asyncio
        asyncio.run(shutdown(application))

if __name__ == "__main__":
    main()
