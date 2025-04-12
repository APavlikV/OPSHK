import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
            f"Приветствуем в нашем КАРАТЭ тренажере!\n\n"
            f"🥋 {nickname}, выбери режим:",
            reply_markup=menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "Приветствуем в нашем КАРАТЭ тренажере!\n\n"
            "🥋 Укажи свой ник для игры.\n"
            "Ответь на это сообщение или выбери текущий Telegram-ник.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Использовать Telegram-ник", callback_data="use_telegram_nick")]
            ])
        )

async def setnick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        nickname = " ".join(context.args)
        set_nickname(update.effective_user.id, nickname)
        await update.message.reply_text(
            f"🥋 Ник '{nickname}' установлен!\n\n"
            "Выбери режим в КАРАТЭ тренажере:",
            reply_markup=menu_keyboard()
        )
    else:
        await update.message.reply_text("🥋 Укажи ник, например: /setnick Вася")

async def handle_nick_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    nickname = update.message.text.strip()
    set_nickname(user_id, nickname)
    await update.message.reply_text(
        f"🥋 Ник '{nickname}' установлен!\n\n"
        "Выбери режим в КАРАТЭ тренажере:",
        reply_markup=menu_keyboard()
    )

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    await update.message.reply_text(
        "🥋 КАРАТЭ тренажер: выбери режим!",
        reply_markup=menu_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "training_fight":
        logger.info("Переход в режим тренировки защиты")
        await query.edit_message_text(
            "🥋 Тренировка защиты: выбери действие!",
            reply_markup=training_fight_keyboard()
        )

    elif query.data == "training_rules":
        rules_text = (
            "📜 ПРАВИЛА ТРЕНИРОВКИ ЗАЩИТЫ\n\n"
            "🥸 Bot Вася атакует, твоя задача — выбрать правильную защиту.\n"
            "1. У тебя 4 варианта: Аге уке, Учи уке, Сото уке, Гедан барай.\n"
            "2. Каждая защита блокирует определённые атаки:\n"
            "   - Аге уке: защищает от ДЗ.\n"
            "   - Учи уке: защищает от СС, ТР, ДЗ.\n"
            "   - Сото уке: защищает от СС, ТР, ДЗ.\n"
            "   - Гедан барай: защищает от СС, ТР, ГДН.\n"
            "3. В простом бою — время не ограничено.\n"
            "4. В бою на время — 10 секунд на ход.\n\n"
            "Выбери действие:"
        )
        await query.edit_message_text(
            rules_text,
            reply_markup=training_rules_keyboard()
        )

    elif query.data == "training_memo":
        memo_text = (
            "📝 ПАМЯТКА ПО ЗАЩИТЕ\n\n"
            "Используй для выбора защиты:\n"
            "- Аге уке: против атак в голову (ДЗ).\n"
            "- Учи уке: универсальная защита для СС, ТР, ДЗ.\n"
            "- Сото уке: блокирует СС, ТР, ДЗ.\n"
            "- Гедан барай: защищает от атак ниже пояса (ГДН), СС, ТР.\n\n"
            "💡 В бою можно запросить подсказку!\n\n"
            "Выбери действие:"
        )
        await query.edit_message_text(
            memo_text,
            reply_markup=training_memo_keyboard()
        )

    elif query.data == "simple_fight":
        context.user_data["mode"] = "simple_fight"
        context.user_data["control"], context.user_data["attack"] = random.choice([("СС", "ДЗ"), ("СС", "ТР"), ("ТР", "СС"), ("ДЗ", "ТР")])
        control, attack = context.user_data["control"], context.user_data["attack"]
        control_phrase = random.choice(ATTACK_PHRASES["control_success"][control])
        attack_phrase = random.choice(ATTACK_PHRASES["attack_success"][attack])
        await query.edit_message_text(
            f"🥊 БОЙ НАЧИНАЕТСЯ!\n\n"
            f"🥸 Bot Вася: {control_phrase} {attack_phrase}\n\n"
            f"🛡️ Выбери защиту:",
            reply_markup=answer_keyboard(True)
        )

    elif query.data == "timed_fight":
        context.user_data["mode"] = "timed_fight"
        context.user_data["control"], context.user_data["attack"] = random.choice([("СС", "ДЗ"), ("СС", "ТР"), ("ТР", "СС"), ("ДЗ", "ТР")])
        control, attack = context.user_data["control"], context.user_data["attack"]
        control_phrase = random.choice(ATTACK_PHRASES["control_success"][control])
        attack_phrase = random.choice(ATTACK_PHRASES["attack_success"][attack])
        await query.edit_message_text(
            f"🥊 БОЙ НА ВРЕМЯ!\n\n"
            f"🥸 Bot Вася: {control_phrase} {attack_phrase}\n\n"
            f"🛡️ Выбери защиту (10 сек):",
            reply_markup=answer_keyboard(True)
        )

    elif query.data in DEFENSE_MOVES:
        defense = query.data
        control = context.user_data.get("control")
        attack = context.user_data.get("attack")
        if not control or not attack:
            await query.message.reply_text("🥋 Ошибка: атака не выбрана. Начни бой заново!", reply_markup=menu_keyboard())
            return
        result = check_round(control, attack, defense)
        control_phrase = random.choice(ATTACK_PHRASES["control_success"][control])
        attack_phrase = random.choice(ATTACK_PHRASES["attack_success"][attack])
        defense_phrase = random.choice(DEFENSE_PHRASES["defense_success" if result["defense_attack_success"] else "defense_fail"][attack])
        counter_phrase = random.choice(DEFENSE_PHRASES["counter_success" if result["counter_success"] else "counter_fail"][defense])
        await query.edit_message_text(
            f"🥊 РЕЗУЛЬТАТ:\n\n"
            f"🥸 Bot Вася: {control_phrase} {attack_phrase}\n"
            f"Ты: {defense_phrase}\n"
            f"{counter_phrase if result['counter_success'] else ''}\n\n"
            f"🏆 {'УСПЕХ' if result['defense_attack_success'] else 'ПОРАЖЕНИЕ'}"
        )
        context.user_data["control"] = None
        context.user_data["attack"] = None
        await query.message.reply_text(
            "🥋 Выбери действие:",
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
                "🥋 Подсказка недоступна: атака не выбрана!",
                reply_markup=answer_keyboard()
            )

    elif query.data == "pvp_bot":
        logger.info("Переход в режим PvP: использование меню")
        await query.edit_message_text(
            "🥊 СПОРТИВНЫЙ БОЙ: выбери действие!",
            reply_markup=pvp_bot_keyboard()
        )

    elif query.data == "pvp_rules":
        rules_text = (
            "ПРАВИЛА СПОРТИВНОГО ПОЕДИНКА\n"
            "➖\n"
            "Вы сражаетесь с 🥸 Bot Васей на счёт.\n\n"
            "Схватка:\n"
            "- Выбираете уровни 🎯 Контроля и 💥 Атаки (СС, ТР, ДЗ).\n"
            "- Выбираете 🛡️ Защиту (Аге уке, Сото уке, Учи уке, Гедан барай).\n\n"
            "Начисление баллов:\n"
            "Тори:\n"
            "- 🎯 Контроль: +1.\n"
            "- 💥 Атака: +2 (если Контроль успешен ✅) или +1.\n"
            "Уке:\n"
            "- ➡️ Контратака: +1 (если защита от контроля удалась ✅).\n"
            "- 🔥 Добивание: +2 (если защита от Контроля и Защита от атаки успешны ✅).\n"
            "- 🛑 Защита от атаки: +1 (если защита от Контроля не удалась ❌, но Защита от атаки успешна ✅).\n\n"
            "🏆 Победа:\n"
            "- Победа за тем, кто за 5 схваток наберёт большее количество очков."
        )
        await query.edit_message_text(
            rules_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Начать бой", callback_data="pvp_start")]
            ])
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
            f"⚔️ Схватка {context.user_data['step']}\n\n"
            f"🎯 Начните боевое действие!\n"
            f"1. Выберите уровень контроля",
            reply_markup=pvp_attack_keyboard("control")
        )

    elif query.data.startswith("attack_control_"):
        control = query.data.split("_")[2]
        logger.info(f"Выбран контроль: {control}")
        context.user_data["player_control"] = control
        try:
            await query.edit_message_text(
                f"⚔️ Схватка {context.user_data['step']}\n\n"
                f"🎯 Контроль: {control}\n"
                f"💥 Выбери атаку:"
            )
        except Exception as e:
            logger.error(f"Ошибка при выборе контроля: {e}", exc_info=True)
            await query.message.reply_text("🥋 Ошибка! Попробуй снова.", reply_markup=menu_keyboard())

    elif query.data.startswith("attack_hit_"):
        if not context.user_data.get("player_control"):
            logger.warning("Попытка выбрать атаку без контроля")
            current_text = query.message.text or ""
            new_text = (
                f"⚔️ Схватка {context.user_data['step']}\n\n"
                f"🎯 Сначала выбери уровень контроля!"
            )
            if current_text.strip() != new_text.strip():
                await query.edit_message_text(
                    new_text,
                    reply_markup=pvp_attack_keyboard("control")
                )
            return
        attack = query.data.split("_")[2]
        logger.info(f"Выбрана атака: {attack}")
        context.user_data["player_attack"] = attack
        step = context.user_data["step"]
        try:
            await query.edit_message_text(
                f"⚔️ Схватка {step}\n\n"
                f"Твоя атака: 🎯 {context.user_data['player_control']} 💥 {context.user_data['player_attack']}\n"
                f"🛡️ Выбери защиту:"
            )
        except Exception as e:
            logger.error(f"Ошибка при выборе атаки: {e}", exc_info=True)
            await query.message.reply_text("🥋 Ошибка! Попробуй снова.", reply_markup=menu_keyboard())

    elif query.data in DEFENSE_MOVES:
        context.user_data["player_defense"] = query.data
        logger.info(f"Выбрана защита: {query.data}")
        try:
            await query.edit_message_text(
                f"⚔️ Схватка {context.user_data['step']}\n\n"
                f"Твой ход:\n"
                f"🎯 {context.user_data['player_control']} 💥 {context.user_data['player_attack']}\n"
                f"🛡️ {context.user_data['player_defense']}\n\n"
                f"Подтверди:"
            )
        except Exception as e:
            logger.error(f"Ошибка при выборе защиты: {e}", exc_info=True)
            await query.message.reply_text("🥋 Ошибка! Попробуй снова.", reply_markup=menu_keyboard())

    elif query.data == "pvp_move":
        logger.info("Подтверждение хода в PvP")
        player_control = context.user_data.get("player_control")
        player_attack = context.user_data.get("player_attack")
        player_defense = context.user_data.get("player_defense")
        bot_control, bot_attack = random.choice([("СС", "ДЗ"), ("СС", "ТР"), ("ТР", "СС"), ("ДЗ", "ТР")])
        bot_defense = random.choice(list(DEFENSE_MOVES.keys()))

        if not all([player_control, player_attack, player_defense]):
            logger.error(
                f"Неполные данные хода: контроль={player_control}, атака={player_attack}, защита={player_defense}"
            )
            await query.message.reply_text("🥋 Ошибка в ходе! Попробуй снова.", reply_markup=menu_keyboard())
            return

        player_result = check_round(bot_control, bot_attack, player_defense)
        bot_result = check_round(player_control, player_attack, bot_defense)

        player_score = (
            (1 if bot_result["control_success"] else 0) +
            (2 if bot_result["attack_success"] and bot_result["control_success"] else 1 if bot_result["attack_success"] else 0) +
            (1 if player_result["defense_control_success"] else 0) +
            (1 if player_result["counter_success"] else 0) +
            (2 if player_result["defense_control_success"] and player_result["defense_attack_success"] else 1 if player_result["defense_attack_success"] else 0)
        )
        bot_score = (
            (1 if player_result["control_success"] else 0) +
            (2 if player_result["attack_success"] and player_result["control_success"] else 1 if player_result["attack_success"] else 0) +
            (1 if bot_result["defense_control_success"] else 0) +
            (1 if bot_result["counter_success"] else 0) +
            (2 if bot_result["defense_control_success"] and bot_result["defense_attack_success"] else 1 if bot_result["defense_attack_success"] else 0)
        )

        context.user_data["player_score"] += player_score
        context.user_data["bot_score"] += bot_score

        log_message = (
            f"⚔️ Схватка {context.user_data['step']}\n\n"
            f"🥋 Тори (Ты):\n"
            f"🎯 Контроль {player_control} {'✅' if bot_result['control_success'] else '❌'} (+{1 if bot_result['control_success'] else 0})\n"
            f"💥 Атака {player_attack} {'✅' if bot_result['attack_success'] else '❌'} (+{2 if bot_result['attack_success'] and bot_result['control_success'] else 1 if bot_result['attack_success'] else 0})\n\n"
            f"🥸 Уке (Bot Вася):\n"
            f"🛡️ Защита {bot_defense}\n"
            f"🛑 Защита контроля: {'✅' if bot_result['defense_control_success'] else '❌'} (+{1 if bot_result['defense_control_success'] else 0})\n"
            f"➡️ Контратака: {'✅' if bot_result['counter_success'] else '❌'} (+{1 if bot_result['counter_success'] else 0})\n"
            f"🔥 Добивание: {'✅' if bot_result['defense_control_success'] and bot_result['defense_attack_success'] else '❌'} (+{2 if bot_result['defense_control_success'] and bot_result['defense_attack_success'] else 1 if bot_result['defense_attack_success'] else 0})\n\n"
            f"--------\n\n"
            f"🥸 Тори (Bot Вася):\n"
            f"🎯 Контроль {bot_control} {'✅' if player_result['control_success'] else '❌'} (+{1 if player_result['control_success'] else 0})\n"
            f"💥 Атака {bot_attack} {'✅' if player_result['attack_success'] else '❌'} (+{2 if player_result['attack_success'] and player_result['control_success'] else 1 if player_result['attack_success'] else 0})\n\n"
            f"🥋 Уке (Ты):\n"
            f"🛡️ Защита {player_defense}\n"
            f"🛑 Защита контроля: {'✅' if player_result['defense_control_success'] else '❌'} (+{1 if player_result['defense_control_success'] else 0})\n"
            f"➡️ Контратака: {'✅' if player_result['counter_success'] else '❌'} (+{1 if player_result['counter_success'] else 0})\n"
            f"🔥 Добивание: {'✅' if player_result['defense_control_success'] and player_result['defense_attack_success'] else '❌'} (+{2 if player_result['defense_control_success'] and player_result['defense_attack_success'] else 1 if player_result['defense_attack_success'] else 0})\n\n"
            f"🏆 Счёт: Ты {context.user_data['player_score']} - Bot Вася {context.user_data['bot_score']}"
        )
        context.user_data["log"].append(log_message)

        await query.message.delete()
        await query.message.reply_text(
            log_message
        )

        context.user_data["step"] += 1
        context.user_data["player_control"] = None
        context.user_data["player_attack"] = None
        context.user_data["player_defense"] = None

        if context.user_data["step"] <= 5:
            await query.message.reply_text(
                f"⚔️ Схватка {context.user_data['step']}\n\n"
                f"🎯 Начните боевое действие!\n"
                f"1. Выберите уровень контроля",
                reply_markup=pvp_attack_keyboard("control")
            )
        else:
            user_id = update.effective_user.id
            nickname = get_nickname(user_id) or "Каратэка"
            winner = nickname if context.user_data["player_score"] > context.user_data["bot_score"] else \
                "Bot Вася" if context.user_data["bot_score"] > context.user_data["player_score"] else "Ничья"
            final_message = (
                f"🏆 БОЙ ЗАВЕРШЁН!\n\n"
                f"Со счётом {context.user_data['player_score']} - {context.user_data['bot_score']} "
                f"победил {winner}!\n\n"
                f"📜 Лог боя:\n"
                f"{'-' * 20}\n"
                f"\n{'-' * 20}\n".join(context.user_data["log"])
            )
            await query.message.reply_text(
                final_message,
                reply_markup=menu_keyboard()
            )
