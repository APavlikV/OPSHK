import random
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# Ходы бота
MOVES = [
    ("СС", "ДЗ"), ("СС", "ТР"), ("СС", "СС"),
    ("ТР", "ТР"), ("ТР", "СС"), ("ТР", "ДЗ"),
    ("ДЗ", "ТР"), ("ДЗ", "СС"), ("ДЗ", "ГДН")
]

# Соответствие правильных ответов
CORRECT_ANSWERS = {
    ("СС", "ДЗ"): ["Аге уке", "Учи уке"],
    ("СС", "ТР"): ["Учи уке"],
    ("СС", "СС"): ["Учи уке"],
    ("ТР", "ТР"): ["Сото уке"],
    ("ТР", "СС"): ["Сото уке"],
    ("ТР", "ДЗ"): ["Сото уке"],
    ("ДЗ", "ТР"): ["Гедан барай"],
    ("ДЗ", "СС"): ["Гедан барай"],
    ("ДЗ", "ГДН"): ["Гедан барай"]
}

# Кастомная клавиатура
def start_keyboard():
    return ReplyKeyboardMarkup([["Игра"]], resize_keyboard=True)

# Инлайн-клавиатура меню
def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("В бой", callback_data="fight")],
        [InlineKeyboardButton("Памятка", callback_data="memo")]
    ])

# Инлайн-клавиатура ответа
def answer_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Аге уке", callback_data="Аге уке")],
        [InlineKeyboardButton("Сото уке", callback_data="Сото уке")],
        [InlineKeyboardButton("Учи уке", callback_data="Учи уке")],
        [InlineKeyboardButton("Гедан барай", callback_data="Гедан барай")]
    ])

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать!", reply_markup=start_keyboard())

# Обработчик кнопки "Игра"
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Приветствуем в нашем тотализаторе!\nВыберите нужный вам вариант.", 
                                    reply_markup=menu_keyboard())

# Обработчик callback’ов
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "rules":
        await query.edit_message_text("Правила игры: Выбери правильный блок для атаки соперника!")
    elif query.data == "memo":
        await query.edit_message_text("Памятка: СС - солнечное сплетение, ТР - трахея, ДЗ - голова, ГДН - ниже пояса.")
    elif query.data == "fight":
        move = random.choice(MOVES)
        control, attack = move
        text = f"Контроль: {control}\nАтака: {attack}"
        context.user_data["current_move"] = move
        await query.edit_message_text(text, reply_markup=answer_keyboard())
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"]:
        move = context.user_data.get("current_move")
        if move:
            correct = query.data in CORRECT_ANSWERS.get(move, [])
            result = "Правильно!" if correct else "Неправильно!"
            await query.edit_message_text(f"Вы выбрали: {query.data}\n{result}")

# Главная функция для вебхуков
async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Ошибка: TELEGRAM_TOKEN не задан!")
        return

    hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if not hostname:
        print("Ошибка: RENDER_EXTERNAL_HOSTNAME не задан!")
        return

    # Увеличиваем таймаут
    request = HTTPXRequest(connection_pool_size=8, read_timeout=60, connect_timeout=60)
    app = Application.builder().token(token).http_client(request).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(["Игра"]), game))
    app.add_handler(CallbackQueryHandler(button))

    # Порт от Render
    port = int(os.environ.get("PORT", 10000))  # Render обычно использует 10000

    try:
        await app.initialize()
        await app.start()
        webhook_url = f"https://{hostname}/{token}"
        await app.updater.start_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=token,
            webhook_url=webhook_url
        )
        print(f"Бот запущен на порту {port} с вебхуком {webhook_url}")
        await app.updater.run_forever()
    except Exception as e:
        print(f"Ошибка при запуске: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
