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

# Соответствие защиты и контратаки
DEFENSE_MOVES = {
    "Аге уке": [("СС", "ДЗ")],
    "Учи уке": [("СС", "ТР"), ("СС", "СС"), ("СС", "ДЗ")],
    "Сото уке": [("ТР", "ТР"), ("ТР", "СС"), ("ТР", "ДЗ")],
    "Гедан барай": [("ДЗ", "ТР"), ("ДЗ", "СС"), ("ДЗ", "ГДН")]
}

# Фразы для логов
ATTACK_PHRASES = {
    "control_success": {
        "ГДН": "молниеносно провел контроль ниже пояса",
        "СС": "молниеносно провел контроль в солнечное сплетение",
        "ТР": "молниеносно провел контроль в трахею",
        "ДЗ": "молниеносно провел контроль в голову"
    },
    "control_fail": {
        "ГДН": "неуклюже попытался провести контроль ниже пояса",
        "СС": "неуклюже попытался провести контроль в солнечное сплетение",
        "ТР": "неуклюже попытался провести контроль в трахею",
        "ДЗ": "неуклюже попытался провести контроль в голову"
    },
    "attack_success": {
        "ГДН": "и не особо мешкая атаку ниже пояса",
        "СС": "и не особо мешкая атаку в солнечное сплетение",
        "ТР": "и не особо мешкая атаку в трахею",
        "ДЗ": "и не особо мешкая атаку в голову"
    },
    "attack_fail": {
        "ГДН": "и медленно нанёс атаку ниже пояса",
        "СС": "и медленно нанёс атаку в солнечное сплетение",
        "ТР": "и медленно нанёс атаку в трахею",
        "ДЗ": "и медленно нанёс атаку в голову"
    }
}

DEFENSE_PHRASES = {
    "defense_success": {
        "ГДН": "Вы не растерялись, закрывая область ниже пояса среагировали верно",
        "СС": "Вы не растерялись, закрывая солнечное сплетение среагировали верно",
        "ТР": "Вы не растерялись, закрывая трахею среагировали верно",
        "ДЗ": "Вы не растерялись, закрывая голову среагировали верно"
    },
    "defense_fail": {
        "ГДН": "Вы замешкались, закрывая область ниже пояса пропустили контроль",
        "СС": "Вы замешкались, закрывая солнечное сплетение пропустили контроль",
        "ТР": "Вы замешкались, закрывая трахею пропустили контроль",
        "ДЗ": "Вы замешкались, закрывая голову пропустили контроль"
    },
    "counter_success": {
        "Аге уке": "нанесли сокрушительный удар в голову, завершив контратаку сокрушительным Аге уке сломали атакующему руку",
        "Учи уке": "нанесли сокрушительный удар в трахею, завершив контратаку мощным Учи уке оглушив противника",
        "Сото уке": "нанесли сокрушительный удар в туловище, завершив контратаку точным Сото уке выбив дыхание",
        "Гедан барай": "нанесли сокрушительный удар ниже пояса, завершив контратаку резким Гедан барай повалив противника"
    },
    "counter_fail": {
        "Аге уке": "нанесли слабый удар в голову, завершив контратаку слабым Аге уке едва задев противника",
        "Учи уке": "нанесли слабый удар в трахею, завершив контратаку посредственным Учи уке не впечатлив противника",
        "Сото уке": "нанесли слабый удар в туловище, завершив контратаку слабым Сото уке слегка толкнув противника",
        "Гедан барай": "нанесли слабый удар ниже пояса, завершив контратаку посредственным Гедан барай повиснув на атакующей руке как шашлык"
    }
}

# Кастомная клавиатура
def start_keyboard():
    return ReplyKeyboardMarkup([["Игра"]], resize_keyboard=True)

def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Учебный бой", callback_data="training_fight")],
        [InlineKeyboardButton("Арена", callback_data="arena")],
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Памятка", callback_data="memo")]
    ])

def training_mode_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Простой бой", callback_data="simple_fight")],
        [InlineKeyboardButton("Бой на время", callback_data="timed_fight")]
    ])

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
    await update.message.reply_text("Добро пожаловать в КАРАТЭ тотализатор!", reply_markup=start_keyboard())

# Обработчик кнопки "Игра"
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    await update.message.reply_text("Приветствуем в нашем тотализаторе!\nВыберите режим:", 
                                    reply_markup=menu_keyboard())

# Обновление таймера
async def update_timer(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]
    remaining = job.data["remaining"] - 1
    job.data["remaining"] = remaining

    control, attack = job.data["current_move"]
    text = f"Шаг {job.data['step']} из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}\nОсталось: {remaining} сек"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=answer_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка обновления таймера: {e}")

    if remaining <= 0:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Время вышло! Вы проиграли."
            )
            if job in context.job_queue.jobs():
                job.schedule_removal()
        except Exception as e:
            logger.error(f"Ошибка при завершении таймера: {e}")

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
        fight_sequence = MOVES.copy()
        random.shuffle(fight_sequence)
        context.user_data["fight_sequence"] = fight_sequence
        context.user_data["current_step"] = 0
        context.user_data["correct_count"] = 0
        context.user_data["mode"] = query.data
        context.user_data["fight_log"] = []  # Лог боя

        control, attack = fight_sequence[0]
        text = f"Шаг 1 из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}"
        if query.data == "timed_fight":
            text += "\nОсталось: 5 сек"
            context.job_queue.run_repeating(
                update_timer,
                interval=1,
                first=0,
                data={
                    "chat_id": query.message.chat_id,
                    "message_id": query.message.message_id,
                    "remaining": 5,
                    "current_move": (control, attack),
                    "step": 1
                }
            )
        await query.edit_message_text(text, reply_markup=answer_keyboard())
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"]:
        sequence = context.user_data.get("fight_sequence")
        step = context.user_data.get("current_step")
        mode = context.user_data.get("mode")
        
        if sequence and step is not None:
            current_move = sequence[step]
            control, attack = current_move
            chosen_defense = query.data
            valid_defenses = DEFENSE_MOVES.get(chosen_defense, [])
            is_success = current_move in valid_defenses
            
            # Формируем короткий лог для текущего хода
            short_log = f"Атака {step + 1}\nКонтроль: {control}\nАтака: {attack}\nЗащита и контратака: {chosen_defense}\n{'УСПЕХ' if is_success else 'ПОРАЖЕНИЕ'}"
            await query.message.reply_text(short_log)
            
            # Формируем развёрнутый лог
            control_success = random.choice([True, False])  # Случайный успех контроля атакующего
            attack_success = random.choice([True, False])   # Случайный успех атаки
            defense_success = is_success and control in [move[0] for move in valid_defenses]
            counter_success = is_success
            
            attacker_name = "ОПШКА Вася"
            defender_name = "Вы"
            attack_text = f"{attacker_name} {'яростно атаковал' if attack_success else 'недолго думая ринулся в атаку'}: " \
                          f"{ATTACK_PHRASES['control_success' if control_success else 'control_fail'][control]} " \
                          f"{ATTACK_PHRASES['attack_success' if attack_success else 'attack_fail'][attack]} ⚔️ "
            defense_text = f"{defender_name} " \
                           f"{DEFENSE_PHRASES['defense_success' if defense_success else 'defense_fail'][control if defense_success else random.choice(list(DEFENSE_PHRASES['defense_fail'].keys()))]} " \
                           f"{DEFENSE_PHRASES['counter_success' if counter_success else 'counter_fail'][chosen_defense]}"
            detailed_log = f"Атака {step + 1}\n{attack_text}{defense_text}"
            context.user_data["fight_log"].append(detailed_log)
            
            if is_success:
                context.user_data["correct_count"] += 1
            
            step += 1
            context.user_data["current_step"] = step
            
            if step < len(sequence):
                if mode == "timed_fight" and context.job_queue.jobs():
                    for job in context.job_queue.jobs():
                        job.schedule_removal()
                
                control, attack = sequence[step]
                text = f"Шаг {step + 1} из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}"
                if mode == "timed_fight":
                    text += "\nОсталось: 5 сек"
                    context.job_queue.run_repeating(
                        update_timer,
                        interval=1,
                        first=0,
                        data={
                            "chat_id": query.message.chat_id,
                            "message_id": query.message.message_id,
                            "remaining": 5,
                            "current_move": (control, attack),
                            "step": step + 1
                        }
                    )
                await query.edit_message_text(text, reply_markup=answer_keyboard())
            else:
                if mode == "timed_fight" and context.job_queue.jobs():
                    for job in context.job_queue.jobs():
                        job.schedule_removal()
                
                correct_count = context.user_data["correct_count"]
                total = len(MOVES)
                full_log = "ЛОГ БОЯ\n" + "\n\n".join(context.user_data["fight_log"]) + \
                           f"\n\nСтатистика боя: {correct_count} из {total} удача"
                await query.message.reply_text(full_log)
                await query.edit_message_text("Бой завершён!")

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
