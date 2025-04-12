from telegram.ext import ContextTypes
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from keyboards import menu_keyboard, training_fight_keyboard, training_rules_keyboard, training_memo_keyboard, answer_keyboard, pvp_bot_keyboard, pvp_attack_keyboard, pvp_move_keyboard
from game_logic import generate_fight_sequence, check_move, generate_short_log, generate_detailed_log, generate_final_stats
from data import MOVES, DEFENSE_MOVES
from database import get_nickname, set_nickname
import logging
from telegram.error import BadRequest
import random

logger = logging.getLogger(__name__)

def get_start_keyboard():
    keyboard = [["Игра"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /start")
    if context.user_data is None:
        context.user_data = {}
    
    user_id = update.effective_user.id
    saved_nickname = get_nickname(user_id)
    
    if saved_nickname:
        context.user_data["nickname"] = saved_nickname
        await update.message.reply_text(
            f"<b>🥋 Добро пожаловать обратно, {saved_nickname}!</b>\n"
            f"Готовы сразиться с <b>🥸 Bot Васей</b>?",
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )
    else:
        telegram_username = update.effective_user.username or update.effective_user.first_name
        if telegram_username:
            keyboard = [
                [InlineKeyboardButton("Использовать Telegram", callback_data="use_telegram_nick")],
                [InlineKeyboardButton("Выбрать свой", callback_data="choose_own_nick")]
            ]
            await update.message.reply_text(
                f"<b>🥋 Добро пожаловать в КАРАТЭ тренажер!</b>\n"
                f"Использовать ваш <b>ник Telegram ({telegram_username})</b> или <b>выбрать свой?</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                "<b>🥋 Добро пожаловать в КАРАТЭ тренажер!</b>\n"
                "Введите ваш ник:",
                parse_mode="HTML",
                reply_markup=ForceReply(selective=True)
            )

async def setnick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /setnick")
    await update.message.reply_text(
        "Введите ваш новый ник:",
        reply_markup=ForceReply(selective=True)
    )

async def handle_nick_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    nick = update.message.text.strip()
    user_id = update.effective_user.id
    if len(nick) > 20:
        await update.message.reply_text(
            "Ник слишком длинный! Максимум 20 символов.",
            reply_markup=get_start_keyboard()
        )
    elif nick:
        context.user_data["nickname"] = nick
        set_nickname(user_id, nick)
        await update.message.reply_text(
            f"Ник установлен: <b>{nick}</b>\n"
            "Готовы сразиться с <b>🥸 Bot Васей</b>?",
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )
    else:
        nick = "Вы"
        context.user_data["nickname"] = nick
        set_nickname(user_id, nick)
        await update.message.reply_text(
            "Ник не указан, используем <b>Вы</b>.\n"
            "Готовы сразиться с <b>🥸 Bot Васей</b>?",
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    if context.user_data is None:
        context.user_data = {}
    await update.message.reply_text(
        "Приветствуем в нашем КАРАТЭ тренажере!\nВыберите режим:",
        reply_markup=menu_keyboard()
    )

async def update_timer(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    if not job.data.get("active", True):
        return
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]
    remaining = job.data["remaining"] - 1
    job.data["remaining"] = remaining
    try:
        control, attack = job.data["current_move"]
        step = job.data["step"]
        text = (
            f"<u>⚔️ Схватка {step + 1} из {len(MOVES)}</u>\n\n"
            f"🎯 <i>Контроль:</i> <b>{control}</b>\n"
            f"💥 <i>Атака:</i> <b>{attack}</b>\n"
            f"Осталось: {remaining} сек"
        )
        if remaining > 0:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=message_id, text=text, reply_markup=answer_keyboard(), parse_mode="HTML"
                )
            except BadRequest as e:
                if "Message to edit not found" in str(e):
                    logger.info(f"Сообщение {message_id} уже удалено, пропускаем редактирование")
                    job.data["active"] = False
                    return
                raise
        else:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=message_id, text="Время вышло! Вы проиграли.", parse_mode="HTML"
                )
            except BadRequest as e:
                if "Message to edit not found" in str(e):
                    logger.info(f"Сообщение {message_id} уже удалено, пропускаем редактирование")
                else:
                    raise
            job.data["timer_ended"] = True
            job.data["active"] = False
    except Exception as e:
        logger.error(f"Ошибка в update_timer: {e}", exc_info=True)
        job.data["active"] = False
    finally:
        if not job.data.get("active", True):
            try:
                job.schedule_removal()
            except Exception as e:
                logger.warning(f"Не удалось удалить задачу в update_timer: {e}")

async def show_next_move(context, chat_id, mode, sequence, step):
    control, attack = sequence[step]
    if mode == "timed_fight":
        text = (
            f"<u>⚔️ Схватка {step + 1} из {len(MOVES)}</u>\n\n"
            f"🎯 <i>Контроль:</i> <b>{control}</b>\n"
            f"💥 <i>Атака:</i> <b>{attack}</b>\n"
            f"Осталось: 5 сек"
        )
    else:  # simple_fight
        text = (
            f"<u>⚔️ Схватка {step + 1} из {len(MOVES)}</u>\n\n"
            f"🎯 <i>Контроль:</i> <b>{control}</b>\n"
            f"💥 <i>Атака:</i> <b>{attack}</b>"
        )
    reply_markup = answer_keyboard(send_hint=(mode == "simple_fight"))
    msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
    context.user_data["last_message_id"] = msg.message_id
    if mode == "timed_fight":
        job = context.job_queue.run_repeating(
            update_timer, interval=1, first=0,
            data={
                "chat_id": chat_id,
                "message_id": msg.message_id,
                "remaining": 5,
                "current_move": (control, attack),
                "step": step,
                "timer_ended": False,
                "active": True
            }
        )
        context.user_data["current_timer"] = job
    return msg

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"Нажата кнопка: {query.data}")
    if context.user_data is None:
        context.user_data = {}

    if query.data == "use_telegram_nick":
        telegram_username = update.effective_user.username or update.effective_user.first_name
        user_id = update.effective_user.id
        context.user_data["nickname"] = telegram_username
        set_nickname(user_id, telegram_username)
        await query.message.reply_text(
            f"Ник установлен: <b>{telegram_username}</b>\n"
            "Готовы сразиться с <b>🥸 Bot Васей</b>?",
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )
        try:
            await query.message.delete()
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
    elif query.data == "choose_own_nick":
        await query.message.reply_text(
            "Введите ваш ник:",
            reply_markup=ForceReply(selective=True)
        )
        try:
            await query.message.delete()
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
    elif query.data == "training_fight":
        await query.edit_message_text(
            "🥊 Учебный бой: выберите действие:",
            reply_markup=training_fight_keyboard(),
            parse_mode="HTML"
        )
    elif query.data == "training_rules":
        await query.edit_message_text(
            "<b>ПРАВИЛА ИГРЫ</b>\n"
            "➖\n"
            "Добро пожаловать в КАРАТЭ тренажер! Здесь вы сражаетесь с виртуальным противником <b>🥸 Bot Васей</b>. Ваша задача — правильно защищаться от его атак и контратаковать.\n\n"
            "<b>Как устроен поединок:</b>\n"
            "1. <i>Шаг боя:</i> Противник выбирает уровни 🎯 <b>Контроля</b> (по сути это тот же удар или захват) и 💥 <b>Атаки</b> (куда нанесёт основной удар).\n"
            "2. <i>Ваш ход:</i> Вы выбираете один из видов защиты: 🛡️ <b>Аге уке</b>, <b>Учи уке</b>, <b>Сото уке</b> или <b>Гедан барай</b>.\n"
            "3. <i>Результат:</i>\n"
            "   - ✅ <b>УСПЕХ:</b> если защита отражает контроль и атаку.\n"
            "   - ⚠️ <b>ЧАСТИЧНЫЙ УСПЕХ:</b> если контроль не отбит, но атака заблокирована или наоборот.\n"
            "   - ❌ <b>ПОРАЖЕНИЕ:</b> если контроль или атака достигли цели.\n"
            "4. <i>Лог боя:</i> После хода — краткий и подробный результат Схватки.\n\n"
            "<b>Режимы:</b>\n"
            "- <i>Простой бой:</i> Без таймера, с подсказками.\n"
            "- <i>Бой на время:</i> 5 секунд на ход.\n\n"
            "<b>Цель:</b>\n"
            "Пройти 9 шагов, набрав максимум побед в Схватках.",
            parse_mode="HTML",
            reply_markup=training_rules_keyboard()
        )
    elif query.data == "training_memo":
        await query.edit_message_text(
            "<b>🧠 ПАМЯТКА</b>\n"
            "➖\n"
            "👊🏻 <i>Зоны контроля и атаки:</i>\n"
            "• <b>СС</b> — Чудан (солнечное сплетение)\n"
            "• <b>ТР</b> — Чудан (трахея)\n"
            "• <b>ДЗ</b> — Дзедан (голова)\n"
            "• <b>ГДН</b> — Годан (ниже пояса)\n\n"
            "🛡️ <i>Типы защиты:</i>\n"
            "▫️ <b>Аге уке</b>\n"
            "   • <i>Защита:</i> <b>СС</b>\n"
            "   • <i>Контратака:</i> <b>ДЗ</b> / <b>ТР</b>\n"
            "   • <i>Добивание:</i> <b>ДЗ</b>\n"
            "▫️ <b>Учи уке</b>\n"
            "   • <i>Защита:</i> <b>СС</b>\n"
            "   • <i>Контратака:</i> <b>ДЗ</b> / <b>ТР</b>\n"
            "   • <i>Добивание:</i> <b>ДЗ</b> / <b>ТР</b> / <b>СС</b>\n"
            "▫️ <b>Сото уке</b>\n"
            "   • <i>Защита:</i> <b>ТР</b>\n"
            "   • <i>Контратака:</i> <b>ДЗ</b> / <b>СС</b>\n"
            "   • <i>Добивание:</i> <b>ДЗ</b> / <b>ТР</b> / <b>СС</b>\n"
            "▫️ <b>Гедан барай</b>\n"
            "   • <i>Защита:</i> <b>ДЗ</b>\n"
            "   • <i>Контратака:</i> <b>ТР</b> / <b>СС</b>\n"
            "   • <i>Добивание:</i> <b>ТР</b> / <b>СС</b> / <b>ГДН</b>",
            parse_mode="HTML",
            reply_markup=training_memo_keyboard()
        )
    elif query.data in ["simple_fight", "timed_fight"]:
        context.user_data["fight_sequence"] = generate_fight_sequence()
        context.user_data["current_step"] = 0
        context.user_data["correct_count"] = 0
        context.user_data["control_count"] = 0
        context.user_data["hint_count"] = 0
        context.user_data["mode"] = query.data
        context.user_data["timer_ended"] = False
        await show_next_move(context, query.message.chat_id, query.data, context.user_data["fight_sequence"], 0)
        await query.delete_message()
    elif query.data == "hint":
        sequence = context.user_data.get("fight_sequence")
        step = context.user_data.get("current_step")
        mode = context.user_data.get("mode")
        current_message_id = context.user_data.get("last_message_id")
        if mode == "simple_fight" and sequence and step is not None and query.message.message_id == current_message_id:
            control, attack = sequence[step]
            is_success, partial_success, correct_answer = check_move(control, attack, "Аге уке")
            text = (
                f"<u>⚔️ Схватка {step + 1} из {len(MOVES)}</u>\n\n"
                f"🎯 <i>Контроль:</i> <b>{control}</b>\n"
                f"💥 <i>Атака:</i> <b>{attack}</b>\n\n"
                f"💡 <i>Правильно:</i> 🛡 <b>{correct_answer}</b>"
            )
            await query.edit_message_text(text, reply_markup=answer_keyboard(send_hint=True), parse_mode="HTML")
            context.user_data["hint_count"] = context.user_data.get("hint_count", 0) + 1
    elif query.data == "pvp_bot":
        logger.info("Переход в режим PvP: отображение меню")
        if "current_timer" in context.user_data:
            job = context.user_data["current_timer"]
            if job and job.data.get("active", False):
                job.data["active"] = False
                try:
                    job.schedule_removal()
                    logger.info("Остановлен активный таймер перед входом в PvP")
                except Exception as e:
                    logger.warning(f"Не удалось удалить таймер: {e}")
            del context.user_data["current_timer"]
        try:
            await query.edit_message_text(
                "🥊 Бой с ботом: выберите действие:",
                reply_markup=pvp_bot_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения в pvp_bot: {e}", exc_info=True)
            await query.message.reply_text("Произошла ошибка. Попробуйте снова.", reply_markup=get_start_keyboard())
    elif query.data == "pvp_rules":
        await query.edit_message_text(
            "<b>ПРАВИЛА СПОРТИВНОГО ПОЕДИНКА</b>\n"
            "➖\n"
            "Вы сражаетесь с <b>🥸 Bot Васей</b> на счёт.\n\n"
            "<b>Схватка:</b>\n"
            "- Выбираете уровни 🎯 <b>Контроля</b> и 💥 <b>Атаки</b> (<b>СС</b>, <b>ТР</b>, <b>ДЗ</b>).\n"
            "- Выбираете 🛡️ <b>Защиту</b> (<b>Аге уке</b>, <b>Сото уке</b>, <b>Учи уке</b>, <b>Гедан барай</b>).\n\n"
            "<b>Начисление баллов:</b>\n"
            "<b>Тори:</b>\n"
            "- 🎯 <b>Контроль:</b> +1 (если Контроль достиг цели ✅).\n"
            "- 💥 <b>Атака:</b> +2 (если Атака достигла цели при успешном Контроле ✅) или +1 (если Атака достигла цели, но при неуспешном Контроле ❌).\n"
            "<b>Уке:</b>\n"
            "- ➡️ <b>Контратака:</b> +1 (если защита от контроля удалась ✅).\n"
            "- 🔥 <b>Добивание:</b> +2 (если защита от Контроля и Защита от атаки успешны ✅).\n"
            "- 🛑 <b>Защита от атаки:</b> +1 (если защита от Контроля не удалась ❌, но Защита от атаки успешна ✅).\n\n"
            "<b>🏆 Победа:</b>\n"
            "- Победа за тем, кто за 5 схваток наберёт большее количество баллов.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Начать бой", callback_data="pvp_start")]])
        )
    elif query.data == "pvp_start":
        logger.info("Начало PvP боя")
        context.user_data["pvp_mode"] = "sport"
        context.user_data["player_score"] = 0
        context.user_data["bot_score"] = 0
        context.user_data["step"] = 0
        context.user_data["player_control"] = None
        context.user_data["player_attack"] = None
        context.user_data["player_defense"] = None
        context.user_data["bot_control"] = random.choice(["СС", "ТР", "ДЗ"])
        context.user_data["bot_attack"] = random.choice(["СС", "ТР", "ДЗ"])
        await query.edit_message_text(
            f"<u>⚔️ Схватка 1</u>\n\n🎯 <i>Начните боевое действие!</i>\n<b>1. Выберите уровень контроля</b>",
            reply_markup=pvp_attack_keyboard("control"),
            parse_mode="HTML"
        )
    elif query.data.startswith("attack_control_"):
        control = query.data.split("_")[2]
        logger.info(f"Выбран контроль: {control}")
        context.user_data["player_control"] = control
        step = context.user_data["step"] + 1
        try:
            await query.edit_message_text(
                f"<u>⚔️ Схватка {step}</u>\n\n💥 <i>Завершите боевое действие!</i>\n<b>2. Выберите уровень атаки</b>",
                reply_markup=pvp_attack_keyboard("attack"),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при выборе контроля: {e}", exc_info=True)
            await query.message.reply_text("Произошла ошибка. Попробуйте снова.", reply_markup=get_start_keyboard())
    elif query.data.startswith("attack_hit_"):
        attack = query.data.split("_")[2]
        logger.info(f"Выбрана атака: {attack}")
        context.user_data["player_attack"] = attack
        step = context.user_data["step"] + 1
        try:
            await query.edit_message_text(
                f"<u>⚔️ Схватка {step}</u>\n\n"
                f"Ваша атака: <i>Контроль</i> <b>{context.user_data['player_control']}</b>, <i>Атака</i> <b>{context.user_data['player_attack']}</b>\n"
                f"<b>🛡️ Выберите защиту:</b>",
                reply_markup=answer_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при выборе атаки: {e}", exc_info=True)
            await query.message.reply_text("Произошла ошибка. Попробуйте снова.", reply_markup=get_start_keyboard())
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"] and "pvp_mode" in context.user_data:
        logger.info(f"Выбрана защита: {query.data}")
        context.user_data["player_defense"] = query.data
        try:
            await query.edit_message_text(
                f"Ваш ход\n"
                f"👊🏻<i>Атака:</i>\n"
                f"<i>Контроль</i> <b>{context.user_data['player_control']}</b>,\n"
                f"<i>Атака</i> <b>{context.user_data['player_attack']}</b>\n"
                f"<i>Защита:</i> <b>{context.user_data['player_defense']}</b>\n"
                f"<i>Подтвердите:</i>",
                reply_markup=pvp_move_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при выборе защиты: {e}", exc_info=True)
            await query.message.reply_text("Произошла ошибка. Попробуйте снова.", reply_markup=get_start_keyboard())
    elif query.data == "pvp_move":
        logger.info("Подтверждение хода в PvP")
        player_control = context.user_data.get("player_control")
        player_attack = context.user_data.get("player_attack")
        player_defense = context.user_data.get("player_defense")
        bot_control = context.user_data.get("bot_control")
        bot_attack = context.user_data.get("bot_attack")
        if not all([player_control, player_attack, player_defense, bot_control, bot_attack]):
            logger.error(f"Неполные данные хода: control={player_control}, attack={player_attack}, defense={player_defense}, bot_control={bot_control}, bot_attack={bot_attack}")
            await query.message.reply_text("Произошла ошибка в ходе. Попробуйте снова.", reply_markup=get_start_keyboard())
            return

        bot_defense = random.choice(["Аге уке", "Сото уке", "Учи уке", "Гедан барай"])
        player_name = context.user_data.get("nickname", "Вы")

        # Игрок атакует, бот защищается
        player_control_success = DEFENSE_MOVES[bot_defense]["control"] != player_control
        player_attack_success = player_attack not in DEFENSE_MOVES[bot_defense]["attack_defense"]
        bot_control_defense_success = not player_control_success
        bot_counter_success = bot_control_defense_success
        bot_attack_defense_success = player_attack not in DEFENSE_MOVES[bot_defense]["attack_defense"]
        bot_dobivanie = player_control_success and bot_attack_defense_success
        bot_attack_defense = not player_control_success and bot_attack_defense_success

        if player_control_success:
            context.user_data["player_score"] += 1
        if player_attack_success:
            context.user_data["player_score"] += (2 if player_control_success else 1)
        if bot_counter_success:
            context.user_data["bot_score"] += 1

        # Бот атакует, игрок защищается
        bot_control_success = DEFENSE_MOVES[player_defense]["control"] != bot_control
        bot_attack_success = bot_attack not in DEFENSE_MOVES[player_defense]["attack_defense"]
        player_control_defense_success = not bot_control_success
        player_counter_success = player_control_defense_success
        player_attack_defense_success = bot_attack not in DEFENSE_MOVES[player_defense]["attack_defense"]
        player_dobivanie = bot_control_success and player_attack_defense_success
        player_attack_defense = not bot_control_success and player_attack_defense_success

        if bot_control_success:
            context.user_data["bot_score"] += 1
        if bot_attack_success:
            context.user_data["bot_score"] += (2 if bot_control_success else 1)
        if player_counter_success:
            context.user_data["player_score"] += 1
        if player_dobivanie:
            context.user_data["player_score"] += 2
        elif player_attack_defense:
            context.user_data["player_score"] += 1

        step = context.user_data["step"] + 1
        context.user_data["step"] = step
        log = (
            f"<u>⚔️ Схватка {step}</u>\n\n"
            f"<u>Тори</u> <b>{player_name}</b>:\n"
            f"🎯 <i>Контроль</i> <b>{player_control}</b> {'✅' if player_control_success else '❌'} <b>(+{1 if player_control_success else 0})</b>\n"
            f"💥 <i>Атака</i> <b>{player_attack}</b> {'✅' if player_attack_success else '❌'} <b>(+{2 if player_control_success and player_attack_success else 1 if player_attack_success else 0})</b>\n\n"
            f"<u>Уке</u> <b>Бот</b>:\n"
            f"🛡️ <i>Защита</i> <b>{bot_defense}</b>\n"
            f"🛑 <i>Защита контроля:</i> {'✅' if bot_control_defense_success else '❌'} <b>(+{1 if bot_control_defense_success else 0})</b>\n"
            f"➡️ <i>Контратака:</i> {'✅' if bot_counter_success else '❌'} <b>(+{1 if bot_counter_success else 0})</b>\n"
            f"🔥 <i>{'Добивание' if bot_dobivanie else 'Защита от атаки'}:</i> {'✅' if bot_dobivanie or bot_attack_defense else '❌'} <b>(+{2 if bot_dobivanie else 0})</b>\n\n"
            f"--------\n\n"
            f"<u>Тори</u> <b>Бот</b>:\n"
            f"🎯 <i>Контроль</i> <b>{bot_control}</b> {'✅' if bot_control_success else '❌'} <b>(+{1 if bot_control_success else 0})</b>\n"
            f"💥 <i>Атака</i> <b>{bot_attack}</b> {'✅' if bot_attack_success else '❌'} <b>(+{2 if bot_control_success and bot_attack_success else 1 if bot_attack_success else 0})</b>\n\n"
            f"<u>Уке</u> <b>{player_name}</b>:\n"
            f"🛡️ <i>Защита</i> <b>{player_defense}</b>\n"
            f"🛑 <i>Защита контроля:</i> {'✅' if player_control_defense_success else '❌'} <b>(+{1 if player_control_defense_success else 0})</b>\n"
            f"➡️ <i>Контратака:</i> {'✅' if player_counter_success else '❌'} <b>(+{1 if player_counter_success else 0})</b>\n"
            f"🔥 <i>{'Добивание' if player_dobivanie else 'Защита от атаки'}:</i> {'✅' if player_dobivanie or player_attack_defense else '❌'} <b>(+{2 if player_dobivanie else 1 if player_attack_defense else 0})</b>\n\n"
            f"🥊 <i>Счёт:</i> <b>{player_name}</b> {context.user_data['player_score']} - <b>Бот</b> {context.user_data['bot_score']}"
        )
        await query.message.reply_text(log, parse_mode="HTML")
        try:
            await query.message.delete()
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
        if step >= 5:
            winner = player_name if context.user_data["player_score"] > context.user_data["bot_score"] else "Бот" if context.user_data["bot_score"] > context.user_data["player_score"] else "Ничья"
            winner_text = f"<b>🏆 {winner}</b>" if winner != "Ничья" else "<b>🏆 Ничья</b>"
            await query.message.reply_text(
                f"<b>Бой завершён!</b>\n\n"
                f"<u>Со счётом {context.user_data['player_score']} - {context.user_data['bot_score']} одержал победу</u>\n\n"
                f"{winner_text}",
                reply_markup=get_start_keyboard(),
                parse_mode="HTML"
            )
            context.user_data.clear()
        else:
            context.user_data["player_control"] = None
            context.user_data["player_attack"] = None
            context.user_data["player_defense"] = None
            context.user_data["bot_control"] = random.choice(["СС", "ТР", "ДЗ"])
            context.user_data["bot_attack"] = random.choice(["СС", "ТР", "ДЗ"])
            await query.message.reply_text(
                f"<u>⚔️ Схватка {step + 1}</u>\n\n🎯 <i>Начните боевое действие!</i>\n<b>1. Выберите уровень контроля</b>",
                reply_markup=pvp_attack_keyboard("control"),
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
                job.data["active"] = False
                try:
                    job.schedule_removal()
                except Exception as e:
                    logger.warning(f"Не удалось удалить таймер: {e}")
                timer_ended = job.data.get("timer_ended", False)
                del context.user_data["current_timer"]
                if timer_ended:
                    await query.edit_message_text("Время вышло! Вы проиграли.", parse_mode="HTML")
                    return
            await query.delete_message()
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
            if step >= len(sequence) - 1:
                await query.message.reply_text("<b>Бой завершён!</b>", parse_mode="HTML")
                final_stats = generate_final_stats(
                    context.user_data["correct_count"],
                    context.user_data["control_count"],
                    context.user_data.get("hint_count", 0),
                    len(MOVES)
                )
                await query.message.reply_text(final_stats, parse_mode="HTML", reply_markup=get_start_keyboard())
                context.user_data.clear()
            else:
                context.user_data["current_step"] += 1
                await show_next_move(context, query.message.chat_id, mode, sequence, context.user_data["current_step"])
