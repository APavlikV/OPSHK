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
    "Аге уке": {"defense": "СС", "counter": ["ДЗ", "ТР"]},
    "Учи уке": {"defense": "СС", "counter": ["ДЗ", "ТР"]},
    "Сото уке": {"defense": "ТР", "counter": ["ДЗ", "СС"]},
    "Гедан барай": {"defense": "ДЗ", "counter": ["ТР", "СС", "ГДН"]}
}

# Фразы для логов (5-10 вариантов)
ATTACK_PHRASES = {
    "control_success": {
        "ГДН": ["молниеносно провел контроль ниже пояса ⚡", "стремительно захватил область ниже пояса ⚡", "точно зафиксировал ноги ⚡", "быстро сковал нижнюю часть ⚡", "уверенно перехватил пояс ⚡"],
        "СС": ["молниеносно провел контроль в солнечное сплетение ⚡", "точно нацелился в центр тела ⚡", "быстро сжал солнечное сплетение ⚡", "уверенно захватил середину ⚡", "стремительно перекрыл дыхание ⚡"],
        "ТР": ["молниеносно провел контроль в трахею ⚡", "резко сжал шею ⚡", "точно перехватил горло ⚡", "быстро зафиксировал дыхание ⚡", "уверенно сковал трахею ⚡"],
        "ДЗ": ["молниеносно провел контроль в голову ⚡", "стремительно захватил голову ⚡", "точно сжал виски ⚡", "быстро перехватил череп ⚡", "уверенно зафиксировал лицо ⚡"]
    },
    "control_fail": {
        "ГДН": ["неуклюже попытался провести контроль ниже пояса", "неловко потянулся к ногам", "медленно двинулся к поясу", "сбивчиво попробовал захватить низ", "неуверенно дернулся к нижней части"],
        "СС": ["неуклюже попытался провести контроль в солнечное сплетение", "неловко ткнул в центр", "медленно потянулся к середине", "сбивчиво махнул в живот", "неуверенно дернулся к груди"],
        "ТР": ["неуклюже попытался провести контроль в трахею", "неловко потянулся к шее", "медленно двинулся к горлу", "сбивчиво ткнул в трахею", "неуверенно дернулся к шее"],
        "ДЗ": ["неуклюже попытался провести контроль в голову", "неловко потянулся к лицу", "медленно махнул по голове", "сбивчиво дернулся к черепу", "неуверенно ткнул в висок"]
    },
    "attack_success": {
        "ГДН": ["и не особо мешкая атаку ниже пояса 💥", "и резко ударил под пояс 💥", "и стремительно врезал в ноги 💥", "и мощно атаковал низ 💥", "и точно пробил ниже пояса 💥"],
        "СС": ["и не особо мешкая атаку в солнечное сплетение 💥", "и мощно врезал в центр 💥", "и резко ударил в живот 💥", "и точно пробил грудь 💥", "и стремительно атаковал середину 💥"],
        "ТР": ["и не особо мешкая атаку в трахею 💥", "и резко сжал горло 💥", "и мощно ударил в шею 💥", "и точно врезал в трахею 💥", "и стремительно атаковал гортань 💥"],
        "ДЗ": ["и не особо мешкая атаку в голову 💥", "и мощно ударил в лицо 💥", "и резко врезал в череп 💥", "и точно пробил висок 💥", "и стремительно атаковал голову 💥"]
    },
    "attack_fail": {
        "ГДН": ["и медленно нанёс атаку ниже пояса", "и вяло ткнул под пояс", "и неуверенно махнул по ногам", "и слабо ударил в низ", "и неловко дернулся к поясу"],
        "СС": ["и медленно нанёс атаку в солнечное сплетение", "и вяло ткнул в живот", "и неуверенно махнул по центру", "и слабо ударил в грудь", "и неловко дернулся к середине"],
        "ТР": ["и медленно нанёс атаку в трахею", "и вяло ткнул в шею", "и неуверенно махнул по горлу", "и слабо ударил в трахею", "и неловко дернулся к гортани"],
        "ДЗ": ["и медленно нанёс атаку в голову", "и вяло ткнул в лицо", "и неуверенно махнул по голове", "и слабо ударил в висок", "и неловко дернулся к черепу"]
    }
}

DEFENSE_PHRASES = {
    "defense_success": {
        "ГДН": ["**Вы** не растерялись, закрывая область ниже пояса среагировали верно 🛡️", "**Вы** стремительно защитили низ 🛡️", "**Вы** точно перекрыли пояс 🛡️", "**Вы** уверенно встали в защиту ног 🛡️", "**Вы** быстро закрыли нижнюю часть 🛡️"],
        "СС": ["**Вы** не растерялись, закрывая солнечное сплетение среагировали верно 🛡️", "**Вы** быстро прикрыли центр 🛡️", "**Вы** точно защитили живот 🛡️", "**Вы** уверенно перекрыли грудь 🛡️", "**Вы** стремительно закрыли середину 🛡️"],
        "ТР": ["**Вы** не растерялись, закрывая трахею среагировали верно 🛡️", "**Вы** быстро прикрыли шею 🛡️", "**Вы** точно защитили горло 🛡️", "**Вы** уверенно перекрыли трахею 🛡️", "**Вы** стремительно закрыли гортань 🛡️"],
        "ДЗ": ["**Вы** не растерялись, закрывая голову среагировали верно 🛡️", "**Вы** быстро прикрыли лицо 🛡️", "**Вы** точно защитили голову 🛡️", "**Вы** уверенно перекрыли череп 🛡️", "**Вы** стремительно закрыли висок 🛡️"]
    },
    "defense_fail": {
        "ГДН": ["**Вы** замешкались, закрывая область ниже пояса пропустили контроль", "**Вы** неловко прикрыли низ и промахнулись", "**Вы** медленно среагировали на пояс", "**Вы** неуверенно защитили ноги", "**Вы** сбились, пропустив низ"],
        "СС": ["**Вы** замешкались, закрывая солнечное сплетение пропустили контроль", "**Вы** неловко прикрыли центр и промахнулись", "**Вы** медленно среагировали на живот", "**Вы** неуверенно защитили грудь", "**Вы** сбились, пропустив середину"],
        "ТР": ["**Вы** замешкались, закрывая трахею пропустили контроль", "**Вы** неловко прикрыли шею и промахнулись", "**Вы** медленно среагировали на горло", "**Вы** неуверенно защитили трахею", "**Вы** сбились, пропустив шею"],
        "ДЗ": ["**Вы** замешкались, закрывая голову пропустили контроль", "**Вы** неловко прикрыли лицо и промахнулись", "**Вы** медленно среагировали на голову", "**Вы** неуверенно защитили череп", "**Вы** сбились, пропустив висок"]
    },
    "counter_success": {
        "Аге уке": ["нанесли сокрушительный удар в голову, завершив контратаку мощным Аге уке сломали атакующему руку 💥", "резко контратаковали в висок Аге уке, выбив противника из равновесия 💥", "точно ударили в голову Аге уке, оглушив врага 💥", "уверенно завершили Аге уке в череп, сбив с ног 💥", "стремительно врезали Аге уке в лицо, сломав нос 💥"],
        "Учи уке": ["нанесли сокрушительный удар в трахею, завершив контратаку точным Учи уке оглушив противника 💥", "мощно контратаковали в шею Учи уке, перекрыв дыхание 💥", "резко ударили Учи уке в горло, заставив задохнуться 💥", "точно врезали Учи уке в трахею, сбив ритм 💥", "уверенно завершили Учи уке в шею, выведя из строя 💥"],
        "Сото уке": ["нанесли сокрушительный удар в туловище, завершив контратаку резким Сото уке выбив дыхание 💥", "мощно контратаковали в живот Сото уке, согнув врага пополам 💥", "точно ударили Сото уке в грудь, выбив воздух 💥", "уверенно врезали Сото уке в центр, сбив с ног 💥", "резко завершили Сото уке в тело, заставив отступить 💥"],
        "Гедан барай": ["нанесли сокрушительный удар ниже пояса, завершив контратаку стремительным Гедан барай повалив противника 💥", "мощно контратаковали в ноги Гедан барай, сбив с ног 💥", "точно ударили Гедан барай под пояс, заставив упасть 💥", "уверенно врезали Гедан барай в низ, выведя из строя 💥", "резко завершили Гедан барай в пояс, повалив врага 💥"]
    },
    "counter_fail": {
        "Аге уке": ["нанесли слабый удар в голову, завершив контратаку слабым Аге уке едва задев противника", "неловко махнули Аге уке по голове, промахнувшись", "слабо ткнули Аге уке в висок, не впечатлив врага", "неуверенно завершили Аге уке в лицо, слегка задев", "поскользнулись, пытаясь контратаковать Аге уке в голову"],
        "Учи уке": ["нанесли слабый удар в трахею, завершив контратаку посредственным Учи уке не впечатлив противника", "неловко ткнули Учи уке в шею, промахнувшись", "слабо махнули Учи уке по горлу, едва задев", "неуверенно завершили Учи уке в трахею, слегка толкнув", "поскользнулись, пытаясь ударить Учи уке в шею"],
        "Сото уке": ["нанесли слабый удар в туловище, завершив контратаку слабым Сото уке слегка толкнув противника", "неловко махнули Сото уке по груди, промахнувшись", "слабо ткнули Сото уке в живот, не впечатлив", "неуверенно завершили Сото уке в центр, едва задев", "поскользнулись, пытаясь контратаковать Сото уке в тело"],
        "Гедан барай": ["нанесли слабый удар ниже пояса, завершив контратаку посредственным Гедан барай повиснув на атакующей руке как шашлык", "неловко ткнули Гедан барай в ноги, промахнувшись", "слабо махнули Гедан барай под пояс, слегка задев", "неуверенно завершили Гедан барай в низ, едва тронув", "поскользнулись, пытаясь ударить Гедан барай в пояс"]
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

def answer_keyboard(show_hint=False):
    buttons = [
        [InlineKeyboardButton("Аге уке", callback_data="Аге уке")],
        [InlineKeyboardButton("Сото уке", callback_data="Сото уке")],
        [InlineKeyboardButton("Учи уке", callback_data="Учи уке")],
        [InlineKeyboardButton("Гедан барай", callback_data="Гедан барай")]
    ]
    if not show_hint:
        buttons.append([InlineKeyboardButton("Подсказка", callback_data="hint")])
    return InlineKeyboardMarkup(buttons)

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
            reply_markup=answer_keyboard(show_hint=True)  # Без подсказки в "Бое на время"
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
        context.user_data["control_count"] = 0
        context.user_data["hint_count"] = 0
        context.user_data["mode"] = query.data
        context.user_data["fight_log"] = []

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
        await query.edit_message_text(text, reply_markup=answer_keyboard(show_hint=(query.data == "timed_fight")))
    elif query.data == "hint" and context.user_data.get("mode") == "simple_fight":
        sequence = context.user_data.get("fight_sequence")
        step = context.user_data.get("current_step")
        if sequence and step is not None:
            control, attack = sequence[step]
            correct_answer = next((move for move, data in DEFENSE_MOVES.items() if control == data["defense"] and attack in data["counter"]), None)
            await query.edit_message_text(
                f"Шаг {step + 1} из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}\nПодсказка: {correct_answer}",
                reply_markup=answer_keyboard(show_hint=True)
            )
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"]:
        sequence = context.user_data.get("fight_sequence")
        step = context.user_data.get("current_step")
        mode = context.user_data.get("mode")
        
        if sequence and step is not None:
            current_move = sequence[step]
            control, attack = current_move
            chosen_defense = query.data
            defense_data = DEFENSE_MOVES.get(chosen_defense, {})
            is_success = control == defense_data.get("defense") and attack in defense_data.get("counter", [])
            control_success = control == defense_data.get("defense")
            
            # Находим правильный ответ для подсказки
            correct_answer = next((move for move, data in DEFENSE_MOVES.items() if control == data["defense"] and attack in data["counter"]), None)
            
            # Формируем короткий лог для текущего хода
            short_log = f"Атака {step + 1}\nКонтроль: {control}\nАтака: {attack}\nЗащита и контратака: {chosen_defense}\n" \
                        f"**{'УСПЕХ' if is_success else 'ПОРАЖЕНИЕ'}**" + (f" (правильно: {correct_answer})" if not is_success and correct_answer else "")
            await query.message.reply_text(short_log, parse_mode="Markdown")
            
            # Формируем развёрнутый лог
            attacker_control_success = random.choice([True, False])
            attacker_attack_success = random.choice([True, False])
            counter_zone = random.choice(defense_data.get("counter", ["ДЗ"])) if is_success else random.choice(["ГДН", "СС", "ТР", "ДЗ"])
            
            attacker_name = "**ОПШКА Вася**"
            attack_text = f"{attacker_name} {'яростно атаковал' if attacker_attack_success else 'недолго думая ринулся в атаку'}: " \
                          f"{random.choice(ATTACK_PHRASES['control_success' if attacker_control_success else 'control_fail'][control])} " \
                          f"{random.choice(ATTACK_PHRASES['attack_success' if attacker_attack_success else 'attack_fail'][attack])} ⚔️ "
            defense_text = f"{DEFENSE_PHRASES['defense_success' if control_success else 'defense_fail'][control if control_success else random.choice(list(DEFENSE_PHRASES['defense_fail'].keys()))]} " \
                           f"{random.choice(DEFENSE_PHRASES['counter_success' if is_success else 'counter_fail'][chosen_defense])}"
            detailed_log = f"Атака {step + 1}\n{attack_text}{defense_text}"
            context.user_data["fight_log"].append(detailed_log)
            
            if is_success:
                context.user_data["correct_count"] += 1
            if control_success:
                context.user_data["control_count"] += 1
            
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
                await query.edit_message_text(text, reply_markup=answer_keyboard(show_hint=(mode == "timed_fight")))
            else:
                if mode == "timed_fight" and context.job_queue.jobs():
                    for job in context.job_queue.jobs():
                        job.schedule_removal()
                
                correct_count = context.user_data["correct_count"]
                control_count = context.user_data["control_count"]
                hint_count = context.user_data.get("hint_count", 0)
                total = len(MOVES)
                full_log = "ЛОГ БОЯ\n" + "\n\n".join(context.user_data["fight_log"]) + \
                           f"\n\nСтатистика боя:\nПравильных: {correct_count}, с подсказкой: {hint_count}, из {total}\n" \
                           f"Отбито {control_count} из {total} контролей\nПропущено {total - correct_count} атак"
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
