import random
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.ext import Updater, WebhookUpdate
import os

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
def main():
    # Токен бота из переменной окружения (для безопасности)
    token = os.getenv("TELEGRAM_TOKEN")
    app = Application.builder().token(token).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(["Игра"]), game))
    app.add_handler(CallbackQueryHandler(button))

    # Настройка вебхуков
    port = int(os.environ.get("PORT", 8443))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=token,
        webhook_url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{token}"
    )

if __name__ == "__main__":
    main()