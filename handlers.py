from telegram.ext import ContextTypes
from telegram import Update
from keyboards import start_keyboard, menu_keyboard, training_mode_keyboard, answer_keyboard
from game_logic import generate_fight_sequence, check_move, generate_short_log, generate_detailed_log, generate_final_stats
from data import MOVES, DEFENSE_MOVES
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /start")
    if context.user_data is None:
        context.user_data = {}
    await update.message.reply_text("🥋 Добро пожаловать в КАРАТЭ тренажер!\nСразитесь с <b>🥸 Bot Васей</b> и проверьте свои навыки!",
    parse_mode="HTML",
    reply_markup=start_keyboard())

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    if context.user_data is None:
        context.user_data = {}
    await update.message.reply_text("Приветствуем в нашем тотализаторе!\nВыберите режим:", reply_markup=menu_keyboard())

async def update_timer(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]
    remaining = job.data["remaining"] - 1
    job.data["remaining"] = remaining

    try:
        # Проверяем актуальность сообщения и шага
        last_message_id = job.data.get("last_message_id")
        step_completed = job.data.get("step_completed", False)
        if last_message_id != message_id or step_completed:
            logger.info(f"Message {message_id} is outdated or step completed, stopping timer")
            context.job_queue.remove_job(job.id)  # Мгновенная остановка
            return

        control, attack = job.data["current_move"]
        step = job.data["step"]
        text = (
            f"<code>⚔️ Шаг {step + 1} из {len(MOVES)}</code>\n\n"
            f"🎯 Контроль: <b>{control}</b>\n"
            f"💥 Атака: <b>{attack}</b>\n"
            f"Осталось: {remaining} сек"
        )

        if remaining > 0:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=answer_keyboard(), parse_mode="HTML")
        elif remaining <= 0:
            job.data["timer_end_time"] = datetime.utcnow()
            if "answer_time" not in job.data:
                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Время вышло! Вы проиграли.", parse_mode="HTML")
                job.data["timer_ended"] = True
            context.job_queue.remove_job(job.id)  # Мгновенная остановка
    except Exception as e:
        logger.error(f"Ошибка в update_timer: {e}", exc_info=True)
        context.job_queue.remove_job(job.id)  # Остановка в случае ошибки

async def show_next_move(context, chat_id, mode, sequence, step):
    control, attack = sequence[step]
    text = (
        f"<code>⚔️ Шаг {step + 1} из {len(MOVES)}</code>\n\n"
        f"🎯 Контроль: <b>{control}</b>\n"
        f"💥 Атака: <b>{attack}</b>"
    )
    if mode == "timed_fight":
        text += "\nОсталось: 5 сек"
        msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=answer_keyboard(), parse_mode="HTML")
        start_time = datetime.utcnow()
        timer_end_time = start_time + timedelta(seconds=5)
        job = context.job_queue.run_repeating(
            update_timer,
            interval=1,
            first=0,
            data={
                "chat_id": chat_id,
                "message_id": msg.message_id,
                "remaining": 5,
                "current_move": (control, attack),
                "step": step,
                "timer_end_time": timer_end_time,
                "answer_time": None,
                "last_message_id": msg.message_id,
                "timer_ended": False,
                "step_completed": False
            }
        )
        context.user_data["current_timer"] = job
    else:
        msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=answer_keyboard(send_hint=True), parse_mode="HTML")
    context.user_data["last_message_id"] = msg.message_id
    return msg

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"Нажата кнопка: {query.data}")
    if context.user_data is None:
        context.user_data = {}

    if query.data == "rules":
        await query.edit_message_text(
            "<b>ПРАВИЛА ИГРЫ</b>\n➖\n"
            "Добро пожаловать в КАРАТЭ тотализатор! Здесь вы сражаетесь с виртуальным противником <b>Bot Васей</b>. "
            "Ваша задача — правильно блокировать его атаки и контратаковать.\n\n"
            "<u>Как устроен поединок:</u>\n"
            "1. <b>Шаг боя</b>: Противник выбирает <i>Контроль</i> (где он вас держит) и <i>Атаку</i> (куда бьёт).\n"
            "2. <b>Ваш ход</b>: Вы выбираете один из блоков: Аге уке, Учи уке, Сото уке или Гедан барай.\n"
            "3. <b>Результат</b>:\n"
            "   - 🟢 <b>УСПЕХ</b>: если блок отражает контроль и атаку.\n"
            "   - 🟠 <b>ЧАСТИЧНЫЙ УСПЕХ</b>: если контроль не отбит, но атака заблокирована или наоборот.\n"
            "   - 🔴 <b>ПОРАЖЕНИЕ</b>: если контроль или атака достигли цели.\n"
            "4. <b>Лог боя</b>: После хода — краткий и подробный результат.\n\n"
            "<u>Режимы:</u>\n"
            "- <b>Простой бой</b>: Без таймера, с подсказками.\n"
            "- <b>Бой на время</b>: 5 секунд на ход.\n\n"
            "<u>Цель:</u>\n"
            "Пройти 9 шагов, набрав максимум очков.",
            parse_mode="HTML"
        )
    elif query.data == "memo":
        await query.edit_message_text(
            "<b>🧠 ПАМЯТКА</b>\n➖\n"
            "<u>👊🏻 Зоны контроля и атаки:</u>\n"
            "• <b>СС</b> — Чудан (солнечное сплетение)\n"
            "• <b>ТР</b> — Чудан (трахея)\n"
            "• <b>ДЗ</b> — Дзедан (голова)\n"
            "• <b>ГДН</b> — Годан (ниже пояса)\n\n"
            "<u>🛡️ Блоки:</u>\n"
            "▫️ <b>Аге уке</b>\n"
            "   • Защита: СС\n"
            "   • Контратака: ДЗ / ТР\n"
            "   • Добивание: ДЗ\n\n"
            "▫️ <b>Учи уке</b>\n"
            "   • Защита: СС\n"
            "   • Контратака: ДЗ / ТР\n"
            "   • Добивание: ДЗ / ТР / СС\n\n"
            "▫️ <b>Сото уке</b>\n"
            "   • Защита: ТР\n"
            "   • Контратака: ДЗ / СС\n"
            "   • Добивание: ДЗ / ТР / СС\n\n"
            "▫️ <b>Гедан барай</b>\n"
            "   • Защита: ДЗ\n"
            "   • Контратака: ТР / СС\n"
            "   • Добивание: ТР / СС / ГДН",
            parse_mode="HTML"
        )
    elif query.data == "karate_arena":
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
        context.user_data["timer_ended"] = False
        await show_next_move(context, query.message.chat_id, query.data, context.user_data["fight_sequence"], 0)
        try:
            await query.delete_message()
        except Exception as e:
            logger.error(f"Ошибка удаления сообщения при старте: {e}")
    elif query.data == "hint" and context.user_data.get("mode") == "simple_fight":
        sequence = context.user_data.get("fight_sequence")
        step = context.user_data.get("current_step")
        if sequence and step is not None:
            control, attack = sequence[step]
            _, _, correct_answer = check_move(control, attack, "")
            context.user_data["hint_count"] += 1
            await query.edit_message_text(
                f"<code>⚔️ Шаг {step + 1} из {len(MOVES)}</code>\n\n"
                f"🎯 Контроль: <b>{control}</b>\n"
                f"💥 Атака: <b>{attack}</b>\n"
                f"<b><i>🛡️ Правильный блок: {correct_answer}</i></b>",
                reply_markup=answer_keyboard(send_hint=True),
                parse_mode="HTML"
            )
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"]:
        sequence = context.user_data.get("fight_sequence")
        step = context.user_data.get("current_step")
        mode = context.user_data.get("mode")
        current_message_id = context.user_data.get("last_message_id")

        if sequence and step is not None and query.message.message_id == current_message_id:
            if mode == "timed_fight" and "current_timer" in context.user_data:
                job = context.user_data["current_timer"]
                job.data["answer_time"] = datetime.utcnow()  # Фиксируем время ответа
                
                # Ждём завершения таймера, если он ещё не готов
                if "timer_end_time" not in job.data:
                    logger.info(f"Waiting for timer to end for step {step}")
                    return
                
                timer_end_time = job.data["timer_end_time"]
                answer_time = job.data["answer_time"]

                # Помечаем шаг как завершённый и мгновенно останавливаем таймер
                job.data["step_completed"] = True
                context.job_queue.remove_job(job.id)  # Мгновенная остановка
                del context.user_data["current_timer"]

                # Проверяем время
                if answer_time >= timer_end_time or job.data.get("timer_ended", False):
                    await query.edit_message_text("Время вышло! Вы проиграли.", parse_mode="HTML")
                    context.user_data["timer_ended"] = True
                    return

            # Удаляем сообщение после остановки таймера
            try:
                await query.delete_message()
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения: {e}")

            # Обрабатываем шаг
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

            # Проверяем, закончен ли бой
            if step >= len(sequence) - 1:
                await query.message.reply_text("<b>Бой завершён!</b>", parse_mode="HTML")
                final_stats = generate_final_stats(
                    context.user_data["correct_count"],
                    context.user_data["control_count"],
                    context.user_data.get("hint_count", 0),
                    len(MOVES)
                )
                await query.message.reply_text(final_stats, parse_mode="HTML")
                logger.info("Бой успешно завершён")
            else:
                context.user_data["current_step"] += 1
                await show_next_move(context, query.message.chat_id, mode, sequence, context.user_data["current_step"])
        else:
            logger.info(f"Клик не соответствует текущему шагу {step} или сообщению {current_message_id}, игнорируем")
