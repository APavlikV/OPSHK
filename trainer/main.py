import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from handlers import start, setnick, game, button, handle_nick_reply

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    application = Application.builder().token("7027562944:AAHhp7ajrp28z7E8mlVkKth0P2BbP79v2LM").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setnick", setnick))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(Игра)$"), game))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.REPLY & ~filters.COMMAND, handle_nick_reply))

    logger.info("Бот запущен")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
