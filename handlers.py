from telegram.ext import ContextTypes
from telegram import Update
from keyboards import start_keyboard, menu_keyboard, training_mode_keyboard, answer_keyboard
from game_logic import generate_fight_sequence, check_move, generate_short_log, generate_detailed_log, generate_final_stats
from data import MOVES  # Добавляем импорт MOVES
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /start")
    await update.message.reply_text("🥋 Добро пожаловать в КАРАТЭ тотализатор! Сразитесь с Bot Васей и проверьте свои навыки!", reply_markup=start_keyboard())

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    await update.message.reply_text("Приветствуем в нашем тотализаторе!\nВыберите режим:", reply_markup=menu_keyboard())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]
    remaining = job.data["remaining"] - 1
    job.data["remaining"] = remaining

    control, attack = job.data["current_move"]
    text = f"Шаг {job.data['step']} из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}\nОсталось: {remaining} сек"
    
    try:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=answer_keyboard(show_hint=True))
    except Exception as e:
        logger.error(f"Ошибка обновления таймера: {e}")

    if remaining <= 0:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Время вышло! Вы проиграли.")
            if job in context.job_queue.jobs():
                job.schedule_removal()
        except Exception as e:
            logger.error(f"Ошибка при завершении таймера: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"Нажата кнопка: {query.data}")

    if query.data == "rules":
        await query.edit_message_text(
            "<b>ПРАВИЛА ИГРЫ</b>\n➖\n"
            "Добро пожаловать в КАРАТЭ тотализатор! Здесь вы сражаетесь с виртуальным противником <b>Bot Васей</b>. "
            "Ваша задача — правильно блокировать его атаки и контратаковать.\n\n"
            "<u>Как устроен поединок:</u>\n"
            "1. <b>Шаг боя</b>: Противник выбирает <i>Контроль</i> (где он вас держит) и <i>Атаку</i> (куда бьёт). Например: Контроль: СС, Атака: ДЗ.\n"
            "2. <b>Ваш ход</b>: Вы выбираете один из блоков: Аге уке, Учи уке, Сото уке или Гедан барай.\n"
            "3. <b>Результат</b>:\n"
            "   - 🟢 <b>УСПЕХ</b>: если ваш блок защищает зону контроля и блокирует атаку (см. Памятку).\n"
            "   - 🟠 <b>ПОРАЖЕНИЕ</b>: если контроль не отбит, но атака заблокирована — вы устояли, но не контратаковали.\n"
            "   - 🔴 <b>ПОРАЖЕНИЕ</b>: если контроль или атака не заблокированы полностью.\n"
            "4. <b>Лог боя</b>: После каждого хода вы видите короткий результат и развёрнутый рассказ о бое.\n\n"
            "<u>Режимы игры:</u>\n"
            "- <b>Простой бой</b>: Отбивайте атаки без спешки, можно взять подсказку.\n"
            "- <b>Бой на время</b>: У вас 5 секунд на ход — успейте выбрать блок!\n\n"
            "<u>Цель:</u>\n"
            "Пройдите все шаги (9 атак) и наберите максимум очков. Статистика покажет, сколько контролей вы отбили и атак пропустили.\n\n"
            "Удачи в бою, каратист!",
            parse_mode="HTML"
        )
    elif query.data == "memo":
        await query.edit_message_text(
            "<b>ПАМЯТКА</b>\n➖\n"
            "Добро пожаловать в КАРАТЭ тотализатор! Здесь вы найдёте пояснения к зонам, используемым в бою:\n\n"
            "<u>Зоны контроля и атаки:</u>\n"
            "- <b>СС</b> — <i>Солнечное сплетение</i>: центр тела, уязвимая точка для ударов в живот или грудь.\n"
            "- <b>ТР</b> — <i>Трахея</i>: область шеи и горла, удары сюда нарушают дыхание.\n"
            "- <b>ДЗ</b> — <i>Данто (голова)</i>: зона головы, включая лицо и виски.\n"
            "- <b>ГДН</b> — <i>Гедан (ниже пояса)</i>: нижняя часть тела, ноги или область под поясом.\n\n"
            "<u>Защита и контратака:</u>\n"
            "- <b>Аге уке</b>: защищает СС, контратакует в ДЗ или ТР.\n"
            "- <b>Учи уке</b>: защищает СС, контратакует в ДЗ или ТР.\n"
            "- <b>Сото уке</b>: защищает ТР, контратакует в ДЗ или СС.\n"
            "- <b>Гедан барай</b>: защищает ДЗ, контратакует в ТР или СС.\n\n"
            "Используйте эти знания, чтобы выбрать правильный блок и победить!",
            parse_mode="HTML"
        )
    elif query.data == "arena":
        await query.edit_message_text("Арена: Пока в разработке!")
    elif query.data == "training_fight":
        await query.edit_message_text("Выберите режим боя:", reply_markup=training_mode_keyboard())
    elif query.data in ["simple_fight", "timed_fight"]:
        context.user_data["fight_sequence"] = generate_fight_sequence()
        context.user_data["current_step"] = 0
        context.user_data["correct_count"] = 0
        context.user_data["control_count"] = 0
        context.user_data["hint_count"] = 0
        context.user_data["mode"] = query.data
        context.user_data["last_message_id"] = None

        control, attack = context.user_data["fight_sequence"][0]
        text = f"Шаг 1 из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}"
        if query.data == "timed_fight":
            text += "\nОсталось: 5 сек"
            msg = await query.message.reply_text(text, reply_markup=answer_keyboard(show_hint=True))
            context.job_queue.run_repeating(
                update_timer,
                interval=1,
                first=0,
                data={
                    "chat_id": query.message.chat_id,
                    "message_id": msg.message_id,
                    "remaining": 5,
                    "current_move": (control, attack),
                    "step": 1
                }
            )
        else:
            msg = await query.message.reply_text(text, reply_markup=answer_keyboard())
        context.user_data["last_message_id"] = msg.message_id
        await query.delete_message()
   elif query.data == "hint" and context.user_data.get("mode") == "simple_fight":
    sequence = context.user_data.get("fight_sequence")
    step = context.user_data.get("current_step")
    if sequence and step is not None:
        control, attack = sequence[step]
        _, _, correct_answer = check_move(control, attack, "")
        context.user_data["hint_count"] += 1
        await query.edit_message_text(
            f"Шаг {step + 1} из {len(MOVES)}\nКонтроль: {control}\nАтака: {attack}\n<b><i>🛡️ Правильный блок: {correct_answer}</i></b>",
            reply_markup=answer_keyboard(show_hint=True),
            parse_mode="HTML"
        )
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"]:
        sequence = context.user_data.get("fight_sequence")
        step = context.user_data.get("current_step")
        mode = context.user_data.get("mode")
        
        if sequence and step is not None:
            control, attack = sequence[step]
            chosen_defense = query.data
            is_success, partial_success, correct_answer = check_move(control, attack, chosen_defense)
            
            short_log = generate_short_log(step, control, attack, chosen_defense, is_success, partial_success, correct_answer)
            short_msg = await query.message.reply_text(short_log, parse_mode="HTML")
            
            detailed_log = generate_detailed_log(control, attack, chosen_defense, is_success)
            await query.message.reply_text(detailed_log, parse_mode="HTML", reply_to_message_id=short_msg.message_id)
            
            if is_success:
                context.user_data["correct_count"] += 1
            if control == DEFENSE_MOVES[chosen_defense]["control"]:
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
                    msg = await query.message.reply_text(text, reply_markup=answer_keyboard(show_hint=True))
                    context.job_queue.run_repeating(
                        update_timer,
                        interval=1,
                        first=0,
                        data={
                            "chat_id": query.message.chat_id,
                            "message_id": msg.message_id,
                            "remaining": 5,
                            "current_move": (control, attack),
                            "step": step + 1
                        }
                    )
                else:
                    msg = await query.message.reply_text(text, reply_markup=answer_keyboard())
                context.user_data["last_message_id"] = msg.message_id
                await query.delete_message()
            else:
                if mode == "timed_fight" and context.job_queue.jobs():
                    for job in context.job_queue.jobs():
                        job.schedule_removal()
                
                final_stats = generate_final_stats(
                    context.user_data["correct_count"],
                    context.user_data["control_count"],
                    context.user_data.get("hint_count", 0),
                    len(MOVES)
                )
                await query.message.reply_text(final_stats, parse_mode="HTML")
                await query.edit_message_text("Бой завершён!")
                logger.info("Бой успешно завершён")
