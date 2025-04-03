import random
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import logging
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Все возможные атаки
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

# Обновлённое главное меню (без "Бой на время")
def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Учебный бой", callback_data="training_fight")],
        [InlineKeyboardButton("Арена", callback_data="arena")],
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Памятка", callback_data="memo")]
    ])

# Подменю для "Учебного боя"
def training_mode_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Простой бой", callback_data="simple_fight")],
        [InlineKeyboardButton("Бой на время", callback_data="timed_fight")]
    ])

# Инлайн-клавиатура для ответов
def answer_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Аге уке", callback_data="Аге уке")],
        [InlineKeyboardButton("Сото уке", callback_data="Сото уке")],
        [InlineKeyboardButton("Учи уке", callback_data="Учи уке")],
        [InlineKeyboardButton("Гедан барай", callback_data="Гедан барай")]
    ])

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /start")
    await update.message.reply_text("Добро пожаловать!", reply_markup=start_keyboard())

# Обработчик кнопки "Игра"
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    await update.message.reply_text("Приветствуем в нашем тотализаторе!\nВыберите режим:", 
                                    reply_markup=menu_keyboard())

# Обработчик callback’ов
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"Нажата кнопка: {query.data}")

    if query.data == "rules":
        await query.edit_message_text("Правила игры: Выбери правильный блок для атаки соперника!")
    elif query.data == "memo":
        await query.edit_message_text("Памятка: СС - солнечное сплетение, ТР - трахея, ДЗ - голова, ГДН - ниже пояса.")
    elif query.data == "arena":
        await query.edit_message_text("Арена: Пока в разработке!")
    elif query.data == "training_fight":
        await query.edit_message_text("Выберите режим боя:", reply_markup=training_mode_keyboard())
    elif query.data in ["simple_fight", "timed_fight"]:
        # Создаём случайную последовательность всех атак
        fight_sequence = MOVES.copy()
        random.shuffle(fight_sequence)
        context.user_data["fight_sequence"] = fight_sequence
        context.user_data["current_step"] = 0
        context.user_data["correct_count"] = 0
        context.user_data["mode"] = query.data  # Запоминаем режим

        # Показываем первый удар
        control, attack = fight_sequence[0]
        text = f"Бой начался!\nШаг 1 из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}"
        if query.data == "timed_fight":
            text += "\nУ вас 5 секунд на ответ!"
            # Запускаем таймер
            context.job_queue.run_once(timeout_callback, 5, data=query.id, context=context)
        
        await query.edit_message_text(text, reply_markup=answer_keyboard())
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"]:
        sequence = context.user_data.get("fight_sequence")
        step = context.user_data.get("current_step")
        mode = context.user_data.get("mode")
        
        if sequence and step is not None:
            current_move = sequence[step]
            correct = query.data in CORRECT_ANSWERS.get(current_move, [])
            if correct:
                context.user_data["correct_count"] += 1
            
            # Переходим к следующему шагу
            step += 1
            context.user_data["current_step"] = step
            
            if step < len(sequence):
                # Показываем следующий удар
                control, attack = sequence[step]
                text = f"Шаг {step + 1} из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}"
                if mode == "timed_fight":
                    text += "\nУ вас 5 секунд на ответ!"
                    context.job_queue.run_once(timeout_callback, 5, data=query.id, context=context)
                await query.edit_message_text(text, reply_markup=answer_keyboard())
            else:
                # Бой завершён
                correct_count = context.user_data["correct_count"]
                total = len(MOVES)
                result = f"Бой завершён!\nПравильных блоков: {correct_count} из {total}"
                await query.edit_message_text(result)

# Callback для таймера
async def timeout_callback(context: ContextTypes.DEFAULT_TYPE):
    query_id = context.job.data
    sequence = context.user_data.get("fight_sequence")
    step = context.user_data.get("current_step")
    
    if sequence and step is not None and step < len(sequence):
        # Переходим к следующему шагу при тайм-ауте
        step += 1
        context.user_data["current_step"] = step
        
        if step < len(sequence):
            control, attack = sequence[step]
            text = f"Время вышло!\nШаг {step + 1} из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}\nУ вас 5 секунд на ответ!"
            await context.bot.edit_message_text(
                chat_id=context.job.context.chat_id,
                message_id=context.job.context.message_id,
                text=text,
                reply_markup=answer_keyboard()
            )
            context.job_queue.run_once(timeout_callback, 5, data=query_id, context=context)
        else:
            correct_count = context.user_data["correct_count"]
            total = len(MOVES)
            result = f"Бой завершён!\nПравильных блоков: {correct_count} из {total}"
            await context.bot.edit_message_text(
                chat_id=context.job.context.chat_id,
                message_id=context.job.context.message_id,
                text=result
            )

# Главная функция
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

    # Регистрация обработчиков
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
