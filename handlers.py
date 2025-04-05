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
    await update.message.reply_text("🥋 Добро пожаловать в КАРАТЭ тренажер!\nСразитесь с <b>🥸 Bot Васей</b> и проверьте свои навыки!",
    parse_mode="HTML",
    reply_markup=start_keyboard())

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    await update.message.reply_text("Приветствуем в нашем тотализаторе!\nВыберите режим:", reply_markup=menu_keyboard())

async def update_timer(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]
    remaining = job.data["remaining"] - 1
    job.data["remaining"] = remaining

    if not job.data.get("is_step_active", False):
        return  # Выходим, если шаг неактивен

    # Дополнительная проверка: если таймер должен быть остановлен, выходим сразу
    if "current_timer" not in context.user_data or context.user_data["current_timer"] != job:
        logger.info(f"Job {job.id} is outdated, skipping execution")
        return

    try:
        control, attack = job.data["current_move"]
        text = (
            f"<code>⚔️ Шаг {job.data['step']} из {len(MOVES)}</code>\n\n"
            f"🎯 Контроль: <b>{control}</b>\n"
            f"💥 Атака: <b>{attack}</b>\n"
            f"Осталось: {remaining} сек"
        )

        timer_end_time = job.data.get("timer_end_time")
        answer_time = job.data.get("answer_time")
        current_time = datetime.utcnow()

        if remaining > 0 and (not answer_time or answer_time > timer_end_time):
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=answer_keyboard(), parse_mode="HTML")
        elif remaining <= 0 and (not answer_time or timer_end_time < answer_time):
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Время вышло! Вы проиграли.", parse_mode="HTML")
            job.data["is_step_active"] = False
            job.schedule_removal()
            job.data["timer_ended"] = True
            context.user_data["timer_ended"] = True
    except Exception as e:
        logger.error(f"Ошибка в update_timer: {e}", exc_info=True)

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
            "Добро пожаловать в <b>КАРАТЭ</b> тотализатор! Здесь вы найдёте пояснения к зонам, используемым в бою:\n\n"
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
            "Используйте эти знания, чтобы выбрать правильный блок и победить!\n\n"
            "<b>P.S.</b> Нужно учитывать некоторые особенности, а именно:\n"
            "<b>Во-первых</b>: Все технические элементы (аге, сото, учи и гедан) можно условно разделить на три части.\n"
            "<b>1)</b> защита от контроля\n"
            "<b>2)</b> контратака\n"
            "<b>3)</b> завершающий элемент (это может быть как добивание, так и вынужденная защита от атаки после контроля)\n\n"
            "<b>Например</b>: Аге уке\n"
            "<b>1)</b> Защита области солнечного сплетения (СС)\n"
            "<b>2)</b> Контратака тут может быть как в грудь, так и в голову (в зависимости от ситуации, соответственно, ДЗ или ТР)\n"
            "<b>3)</b> Последний элемент Аге уке — это добивание в голову или защита головы (ТР или ДЗ)\n\n"
            "Другие варианты контратак также многовариантны, и полезно понимание того, что последний элемент Аге уке не обязательно в ДЗ: возможен и уровень ТР.\n\n"
            "Это тренажёр на воображение и открытие для себя понимания, что изучаемая техника далеко не однозначна и может использоваться вариабельно в зависимости от реальной ситуации.\n\n"
            "Чтобы правильно ответить, необходимо представить весь процесс боевых действий и в своей голове воспроизвести каждый этап.\n\n"
            "<b>Во-вторых</b>: как уже понятно, в представленном выше описании нет третьей части этих техник, поэтому это может вызвать некоторое недопонимание.\n"
            "<b>Ещё раз</b> ☝🏻 Каждое техническое действие (аге, сото, учи и гедан) состоит из трёх частей:\n"
            "<b>1)</b> защита от контроля\n"
            "<b>2)</b> контратака\n"
            "<b>3)</b> завершающий элемент (это может быть как добивание, так и вынужденная защита от атаки после контроля)\n\n",
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
        context.user_data["last_message_id"] = None
        context.user_data["step_processed"] = False
        context.user_data["timer_ended"] = False
        if "current_timer" in context.user_data:
            del context.user_data["current_timer"]

        control, attack = context.user_data["fight_sequence"][0]
        text = (
            f"<code>⚔️ Шаг 1 из {len(MOVES)}</code>\n\n"
            f"🎯 Контроль: <b>{control}</b>\n"
            f"💥 Атака: <b>{attack}</b>"
        )
        if query.data == "timed_fight":
            text += "\nОсталось: 5 сек"
            msg = await query.message.reply_text(text, reply_markup=answer_keyboard(), parse_mode="HTML")
            start_time = datetime.utcnow()
            timer_end_time = start_time + timedelta(seconds=5)
            job = context.job_queue.run_repeating(
                update_timer,
                interval=1,
                first=0,
                data={
                    "chat_id": query.message.chat_id,
                    "message_id": msg.message_id,
                    "remaining": 5,
                    "current_move": (control, attack),
                    "step": 1,
                    "is_step_active": True,
                    "timer_end_time": timer_end_time,
                    "answer_time": None,
                    "timer_ended": False
                }
            )
            context.user_data["current_timer"] = job
        else:
            msg = await query.message.reply_text(text, reply_markup=answer_keyboard(send_hint=True), parse_mode="HTML")
        context.user_data["last_message_id"] = msg.message_id
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
            if context.user_data.get("step_processed", False):
                logger.info(f"Повторный клик на шаге {step}, игнорируем")
                return
            
            context.user_data["step_processed"] = True
            answer_time = datetime.utcnow()  # Фиксируем время ответа
            
            # Проверяем, не завершился ли таймер раньше
            if mode == "timed_fight" and context.user_data.get("timer_ended", False):
                await query.message.reply_text("Время вышло! Вы проиграли.", parse_mode="HTML")
                try:
                    await query.delete_message()
                except Exception as e:
                    logger.error(f"Ошибка удаления сообщения при истечении времени: {e}")
                return
            
            # Мгновенная обратная связь
            processing_msg = await query.message.reply_text("⏳ Обработка вашего хода...", parse_mode="HTML")
            
            # Останавливаем таймер до удаления сообщения
            if mode == "timed_fight" and "current_timer" in context.user_data:
                current_job = context.user_data["current_timer"]
                if current_job in context.job_queue.jobs():
                    current_job.data["is_step_active"] = False
                    current_job.data["answer_time"] = answer_time
                    current_job.schedule_removal()  # Удаляем задачу
                    logger.info(f"Removed job {current_job.id} before processing next step")
                del context.user_data["current_timer"]
            
            # Удаляем текущее сообщение
            try:
                await query.delete_message()
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения при переходе на шаг {step + 1}: {e}")
            
            # Проверяем текущий шаг до инкремента
            if step >= len(sequence) - 1:  # Последний шаг уже обработан
                await query.message.reply_text("<b>Бой завершён!</b>", parse_mode="HTML")
                final_stats = generate_final_stats(
                    context.user_data["correct_count"],
                    context.user_data["control_count"],
                    context.user_data.get("hint_count", 0),
                    len(MOVES)
                )
                await query.message.reply_text(final_stats, parse_mode="HTML")
                logger.info("Бой успешно завершён")
                context.user_data["step_processed"] = False
            else:
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
                
                control, attack = sequence[step]
                text = (
                    f"<code>⚔️ Шаг {step + 1} из {len(MOVES)}</code>\n\n"
                    f"🎯 Контроль: <b>{control}</b>\n"
                    f"💥 Атака: <b>{attack}</b>"
                )
                
                if mode == "timed_fight":
                    text += "\nОсталось: 5 сек"
                    msg = await query.message.reply_text(text, reply_markup=answer_keyboard(), parse_mode="HTML")
                    start_time = datetime.utcnow()
                    timer_end_time = start_time + timedelta(seconds=5)
                    job = context.job_queue.run_repeating(
                        update_timer,
                        interval=1,
                        first=0,
                        data={
                            "chat_id": query.message.chat_id,
                            "message_id": msg.message_id,
                            "remaining": 5,
                            "current_move": (control, attack),
                            "step": step + 1,
                            "is_step_active": True,
                            "timer_end_time": timer_end_time,
                            "answer_time": None,
                            "timer_ended": False
                        }
                    )
                    context.user_data["current_timer"] = job
                else:
                    msg = await query.message.reply_text(text, reply_markup=answer_keyboard(send_hint=True), parse_mode="HTML")
                context.user_data["last_message_id"] = msg.message_id
                context.user_data["step_processed"] = False
            
            try:
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=processing_msg.message_id)
            except Exception as e:
                logger.error(f"Ошибка удаления сообщения 'Обработка...': {e}")
        else:
            logger.info(f"Клик не соответствует текущему шагу {step} или сообщению {current_message_id}, игнорируем")
