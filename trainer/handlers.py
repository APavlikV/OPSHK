import logging
import random
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from keyboards import (
    menu_keyboard, training_fight_keyboard, training_rules_keyboard,
    training_memo_keyboard, answer_keyboard, pvp_bot_keyboard,
    pvp_attack_keyboard, pvp_move_keyboard
)
from database import get_nickname, set_nickname
from data import DEFENSE_MOVES, ATTACK_PHRASES, DEFENSE_PHRASES
from game_logic import check_round, get_hint

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nickname = get_nickname(user_id)
    if nickname:
        await update.message.reply_text(
            f"Добро пожаловать обратно, {nickname}!\n\n"
            "Выберите режим игры:",
            reply_markup=menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "Добро пожаловать! Укажите ваш ник для игры.\n"
            "Ответьте на это сообщение с вашим ником или выберите текущий Telegram-ник.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Использовать Telegram-ник", callback_data="use_telegram_nick")]
            ])
        )

async def setnick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        nickname = " ".join(context.args)
        set_nickname(update.effective_user.id, nickname)
        await update.message.reply_text(
            f"Ник '{nickname}' установлен!\n\n"
            "Выберите режим игры:",
            reply_markup=menu_keyboard()
        )
    else:
        await update.message.reply_text("Пожалуйста, укажите ник после команды, например: /setnick Вася")

async def handle_nick_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nickname = update.message.text.strip()
    set_nickname(user_id, nickname)
    await update.message.reply_text(
        f"Ник '{nickname}' установлен!\n\n"
        "Выберите режим игры:",
        reply_markup=menu_keyboard()
    )

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    await update.message.reply_text(
        "Выберите режим игры:",
        reply_markup=menu_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "training_fight":
        logger.info("Переход в режим тренировки защиты")
        await query.edit_message_text(
            "🥋 Тренировка защиты: выберите действие:",
            reply_markup=training_fight_keyboard()
        )

    elif query.data == "training_rules":
        rules_text = (
            "📜 <b>Правила тренировки защиты:</b>\n\n"
            "1. Бот атакует, ваша задача — выбрать правильную защиту.\n"
            "2. У вас есть 4 варианта: Аге уке, Учи уке, Сото уке, Гедан барай.\n"
            "3. Каждая защита блокирует определённые атаки:\n"
            "   - <b>Аге уке</b>: защищает от ДЗ.\n"
            "   - <b>Учи уке</b>: защищает от СС, ТР, ДЗ.\n"
            "   - <b>Сото уке</b>: защищает от СС, ТР, ДЗ.\n"
            "   - <b>Гедан барай</b>: защищает от СС, ТР, ГДН.\n"
            "4. В простом бою у вас неограниченное время.\n"
            "5. В бою на время — 10 секунд на ход.\n\n"
            "Выберите действие:"
        )
        await query.edit_message_text(
            rules_text,
            reply_markup=training_rules_keyboard(),
            parse_mode="HTML"
        )

    elif query.data == "training_memo":
        memo_text = (
            "📝 <b>Памятка по защите:</b>\n\n"
            "Используйте эту памятку для выбора защиты:\n"
            "- <b>Аге уке</b>: эффективно против атак в голову (ДЗ).\n"
            "- <b>Учи уке</b>: универсальная защита для СС, ТР, ДЗ.\n"
            "- <b>Сото уке</b>: надёжно блокирует СС, ТР, ДЗ.\n"
            "- <b>Гедан барай</b>: защищает от атак ниже пояса (ГДН) и СС, ТР.\n\n"
            "Подсказка: в бою можно запросить 💡 Подсказку, чтобы узнать, какая защита лучше.\n\n"
            "Выберите действие:"
        )
        await query.edit_message_text(
            memo_text,
            reply_markup=training_memo_keyboard(),
            parse_mode="HTML"
        )

    elif query.data == "simple_fight":
        context.user_data["mode"] = "simple_fight"
        context.user_data["control"], context.user_data["attack"] = random.choice([("СС", "ДЗ"), ("СС", "ТР"), ("ТР", "СС"), ("ДЗ", "ТР")])
        control, attack = context.user_data["control"], context.user_data["attack"]
        control_phrase = random.choice(ATTACK_PHRASES["control_success"][control])
        attack_phrase = random.choice(ATTACK_PHRASES["attack_success"][attack])
        await query.edit_message_text(
            f"<b>🥊 Бот атакует!</b>\n\n"
            f"Бот {control_phrase} {attack_phrase}\n\n"
            f"<b>🛡️ Выберите защиту:</b>",
            reply_markup=answer_keyboard(True),
            parse_mode="HTML"
        )

    elif query.data == "timed_fight":
        context.user_data["mode"] = "timed_fight"
        context.user_data["control"], context.user_data["attack"] = random.choice([("СС", "ДЗ"), ("СС", "ТР"), ("ТР", "СС"), ("ДЗ", "ТР")])
        control, attack = context.user_data["control"], context.user_data["attack"]
        control_phrase = random.choice(ATTACK_PHRASES["control_success"][control])
        attack_phrase = random.choice(ATTACK_PHRASES["attack_success"][attack])
        await query.edit_message_text(
            f"<b>🥊 Бот атакует!</b>\n\n"
            f"Бот {control_phrase} {attack_phrase}\n\n"
            f"<b>🛡️ Выберите защиту (10 сек):</b>",
            reply_markup=answer_keyboard(True),
            parse_mode="HTML"
        )

    elif query.data in DEFENSE_MOVES:
        defense = query.data
        control = context.user_data.get("control")
        attack = context.user_data.get("attack")
        if not control or not attack:
            await query.message.reply_text("Ошибка: атака не выбрана. Начните бой заново.", reply_markup=menu_keyboard())
            return
        result = check_round(control, attack, defense)
        control_phrase = random.choice(ATTACK_PHRASES["control_success"][control])
        attack_phrase = random.choice(ATTACK_PHRASES["attack_success"][attack])
        defense_phrase = random.choice(DEFENSE_PHRASES["defense_success" if result["defense_success"] else "defense_fail"][attack])
        counter_phrase = random.choice(DEFENSE_PHRASES["counter_success" if result["counter_success"] else "counter_fail"][defense])
        await query.edit_message_text(
            f"<b>🥊 Результат:</b>\n\n"
            f"Бот: {control_phrase} {attack_phrase}\n"
            f"Вы: {defense_phrase}\n"
            f"{counter_phrase if result['counter_success'] else ''}\n\n"
            f"<b>Счёт:</b> {'Успешно' if result['defense_success'] else 'Провал'}",
            parse_mode="HTML"
        )
        context.user_data["control"] = None
        context.user_data["attack"] = None
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=training_fight_keyboard()
        )

    elif query.data == "hint":
        control = context.user_data.get("control")
        attack = context.user_data.get("attack")
        if control and attack:
            hint = get_hint(control, attack)
            await query.message.reply_text(
                f"💡 Подсказка: {hint}",
                reply_markup=answer_keyboard(True)
            )
        else:
            await query.message.reply_text(
                "Подсказка недоступна: атака не выбрана.",
                reply_markup=answer_keyboard()
            )

    elif query.data == "pvp_bot":
        logger.info("Переход в режим PvP: использование меню")
        await query.edit_message_text(
            "🥊 Бой с ботом: выберите действие:",
            reply_markup=pvp_bot_keyboard()
        )

    elif query.data == "pvp_rules":
        rules_text = (
            "📜 <b>Правила спортивного боя:</b>\n\n"
            "1. Бой состоит из 5 схваток.\n"
            "2. Вы и бот поочерёдно атакуете и защищаетесь.\n"
            "3. Атака состоит из:\n"
            "   - <b>Контроль</b> (СС, ТР).\n"
            "   - <b>Атака</b> (СС, ТР, ДЗ).\n"
            "4. Защита выбирается из: Аге уке, Учи уке, Сото уке, Гедан барай.\n"
            "5. Очки начисляются:\n"
            "   - 🎯 Успешный контроль: +1\n"
            "   - 💥 Успешная атака: +1\n"
            "   - 🛑 Успешная защита от контроля: +1\n"
            "   - ➡️ Успешная контратака: +1\n"
            "   - 🔥 Успешная защита от атаки: +1\n"
            "6. Побеждает набравший больше очков.\n\n"
            "Выберите действие:"
        )
        await query.edit_message_text(
            rules_text,
            reply_markup=pvp_bot_keyboard(),
            parse_mode="HTML"
        )

    elif query.data == "pvp_start":
        logger.info("Начало PvP боя")
        context.user_data["step"] = 1
        context.user_data["player_score"] = 0
        context.user_data["bot_score"] = 0
        context.user_data["player_control"] = None
        context.user_data["player_attack"] = None
        context.user_data["player_defense"] = None
        context.user_data["log"] = []
        await query.edit_message_text(
            f"<u>⚔️ Схватка 1</u>\n\n"
            f"<b>👊 Атака:</b> Выберите контроль:",
            reply_markup=pvp_attack_keyboard("control"),
            parse_mode="HTML"
        )

    elif query.data.startswith("attack_control_"):
        control = query.data.split("_")[2]
        logger.info(f"Выбран контроль: {control}")
        context.user_data["player_control"] = control
        try:
            await query.edit_message_text(
                f"<u>⚔️ Схватка {context.user_data['step']}</u>\n\n"
                f"Ваш контроль: <b>{control}</b>\n"
                f"<b>👊 Выберите атаку:</b>",
                reply_markup=pvp_attack_keyboard("attack"),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при выборе контроля: {e}", exc_info=True)
            await query.message.reply_text("Произошла ошибка. Попробуйте снова.", reply_markup=menu_keyboard())

    elif query.data.startswith("attack_hit_"):
        if not context.user_data.get("player_control"):
            logger.warning("Попытка выбрать атаку без контроля")
            await query.edit_message_text(
                f"<u>⚔️ Схватка {context.user_data['step']}</u>\n\n"
                f"<b>👊 Атака:</b> Сначала выберите контроль:",
                reply_markup=pvp_attack_keyboard("control"),
                parse_mode="HTML"
            )
            return
        attack = query.data.split("_")[2]
        logger.info(f"Выбрана атака: {attack}")
        context.user_data["player_attack"] = attack
        step = context.user_data["step"]
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
            await query.message.reply_text("Произошла ошибка. Попробуйте снова.", reply_markup=menu_keyboard())

    elif query.data in DEFENSE_MOVES:
        context.user_data["player_defense"] = query.data
        logger.info(f"Выбрана защита: {query.data}")
        try:
            await query.edit_message_text(
                f"<u>⚔️ Схватка {context.user_data['step']}</u>\n\n"
                f"Ваш ход\n"
                f"👊 Атака: <i>Контроль</i> <b>{context.user_data['player_control']}</b>, <i>Атака</i> <b>{context.user_data['player_attack']}</b>\n"
                f"🛡️ Защита: <b>{context.user_data['player_defense']}</b>\n\n"
                f"<b>Подтвердите:</b>",
                reply_markup=pvp_move_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при выборе защиты: {e}", exc_info=True)
            await query.message.reply_text("Произошла ошибка. Попробуйте снова.", reply_markup=menu_keyboard())

    elif query.data == "pvp_move":
        logger.info("Подтверждение хода в PvP")
        player_control = context.user_data.get("player_control")
        player_attack = context.user_data.get("player_attack")
        player_defense = context.user_data.get("player_defense")
        bot_control, bot_attack = random.choice([("СС", "ДЗ"), ("СС", "ТР"), ("ТР", "СС"), ("ДЗ", "ТР")])
        bot_defense = random.choice(list(DEFENSE_MOVES.keys()))

        if not all([player_control, player_attack, player_defense]):
            logger.error(
                f"Неполные данные хода: контроль={player_control}, атака={player_attack}, защита={player_defense}, "
                f"bot_control={bot_control}, bot_attack={bot_attack}"
            )
            await query.message.reply_text("Произошла ошибка в ходе. Попробуйте снова.", reply_markup=menu_keyboard())
            return

        player_result = check_round(bot_control, bot_attack, player_defense)
        bot_result = check_round(player_control, player_attack, bot_defense)

        player_score = (
            (1 if bot_result["control_success"] else 0) +
            (1 if bot_result["attack_success"] else 0) +
            (1 if player_result["defense_control_success"] else 0) +
            (1 if player_result["counter_success"] else 0) +
            (1 if player_result["defense_attack_success"] else 0)
        )
        bot_score = (
            (1 if player_result["control_success"] else 0) +
            (1 if player_result["attack_success"] else 0) +
            (1 if bot_result["defense_control_success"] else 0) +
            (1 if bot_result["counter_success"] else 0) +
            (1 if bot_result["defense_attack_success"] else 0)
        )

        context.user_data["player_score"] += player_score
        context.user_data["bot_score"] += bot_score

        log_message = (
            f"<u>⚔️ Схватка {context.user_data['step']}</u>\n\n"
            f"<b>Тори Вы:</b>\n"
            f"🎯 Контроль {player_control} {'✅' if bot_result['control_success'] else '❌'} (+{1 if bot_result['control_success'] else 0})\n"
            f"💥 Атака {player_attack} {'✅' if bot_result['attack_success'] else '❌'} (+{1 if bot_result['attack_success'] else 0})\n\n"
            f"<b>Уке Бот:</b>\n"
            f"🛡️ Защита {bot_defense}\n"
            f"🛑 Защита контроля: {'✅' if bot_result['defense_control_success'] else '❌'} (+{1 if bot_result['defense_control_success'] else 0})\n"
            f"➡️ Контратака: {'✅' if bot_result['counter_success'] else '❌'} (+{1 if bot_result['counter_success'] else 0})\n"
            f"🔥 Защита от атаки: {'✅' if bot_result['defense_attack_success'] else '❌'} (+{1 if bot_result['defense_attack_success'] else 0})\n\n"
            f"--------\n\n"
            f"<b>Тори Бот:</b>\n"
            f"🎯 Контроль {bot_control} {'✅' if player_result['control_success'] else '❌'} (+{1 if player_result['control_success'] else 0})\n"
            f"💥 Атака {bot_attack} {'✅' if player_result['attack_success'] else '❌'} (+{1 if player_result['attack_success'] else 0})\n\n"
            f"<b>Уке Вы:</b>\n"
            f"🛡️ Защита {player_defense}\n"
            f"🛑 Защита контроля: {'✅' if player_result['defense_control_success'] else '❌'} (+{1 if player_result['defense_control_success'] else 0})\n"
            f"➡️ Контратака: {'✅' if player_result['counter_success'] else '❌'} (+{1 if player_result['counter_success'] else 0})\n"
            f"🔥 Защита от атаки: {'✅' if player_result['defense_attack_success'] else '❌'} (+{1 if player_result['defense_attack_success'] else 0})\n\n"
            f"<b>🥊 Счёт: Вы {context.user_data['player_score']} - Бот {context.user_data['bot_score']}</b>"
        )
        context.user_data["log"].append(log_message)

        await query.message.delete()
        await query.message.reply_text(
            log_message,
            parse_mode="HTML"
        )

        context.user_data["step"] += 1
        context.user_data["player_control"] = None
        context.user_data["player_attack"] = None
        context.user_data["player_defense"] = None

        if context.user_data["step"] <= 5:
            await query.message.reply_text(
                f"<u>⚔️ Схватка {context.user_data['step']}</u>\n\n"
                f"<b>👊 Атака:</b> Выберите контроль:",
                reply_markup=pvp_attack_keyboard("control"),
                parse_mode="HTML"
            )
        else:
            user_id = update.effective_user.id
            nickname = get_nickname(user_id) or "Игрок"
            winner = nickname if context.user_data["player_score"] > context.user_data["bot_score"] else \
                "Бот" if context.user_data["bot_score"] > context.user_data["player_score"] else "Ничья"
            final_message = (
                f"<b>🏆 Бой завершён!</b>\n\n"
                f"<u>Со счётом {context.user_data['player_score']} - {context.user_data['bot_score']} "
                f"одержал победу</u>\n"
                f"<b>🏆 {winner}</b>\n\n"
                f"<i>Лог боя:</i>\n"
                f"{'-' * 20}\n"
                f"\n{'-' * 20}\n".join(context.user_data["log"])
            )
            await query.message.reply_text(
                final_message,
                parse_mode="HTML",
                reply_markup=menu_keyboard()
            )
