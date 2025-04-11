from telegram.ext import ContextTypes
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import menu_keyboard, training_mode_keyboard, answer_keyboard, pvp_bot_keyboard, pvp_attack_keyboard, pvp_move_keyboard
from game_logic import generate_fight_sequence, check_move, generate_short_log, generate_detailed_log, generate_final_stats
from data import MOVES, DEFENSE_MOVES
import logging
from datetime import datetime, timedelta
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
    await update.message.reply_text(
        "🥋 Добро пожаловать в КАРАТЭ тренажер!\nСразитесь с <b>🥸 Bot Васей</b> и проверьте свои навыки!",
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

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"Нажата кнопка: {query.data}")
    if context.user_data is None:
        context.user_data = {}

    if query.data == "training_fight":
        await query.edit_message_text("Выберите режим боя:", reply_markup=training_mode_keyboard())
    elif query.data in ["simple_fight", "timed_fight"]:
        # Оставляем старую логику
        context.user_data["fight_sequence"] = generate_fight_sequence()
        context.user_data["current_step"] = 0
        context.user_data["correct_count"] = 0
        context.user_data["control_count"] = 0
        context.user_data["hint_count"] = 0
        context.user_data["mode"] = query.data
        context.user_data["timer_ended"] = False
        await show_next_move(context, query.message.chat_id, query.data, context.user_data["fight_sequence"], 0)
        await query.delete_message()
    elif query.data == "pvp_bot":
        await query.edit_message_text("Бой с ботом: выберите действие:", reply_markup=pvp_bot_keyboard())
    elif query.data == "pvp_rules":
        await query.edit_message_text(
            "<b>ПРАВИЛА СПОРТИВНОГО ПОЕДИНКА</b>\n➖\n"
            "Вы сражаетесь с <b>Bot Васей</b> за очки.\n\n"
            "<u>Схватка:</u>\n"
            "- Выбираете <b>Контроль</b> и <b>Атаку</b> (СС, ТР, ДЗ).\n"
            "- Выбираете <b>Защиту</b> (Аге уке, Сото уке, Учи уке, Гедан барай).\n\n"
            "<u>Очки:</u>\n"
            "- Контроль: +1.\n"
            "- Атака: +2 (если контроль успешен) или +1.\n"
            "- Контратака: +1 (если защита от контроля).\n"
            "- Добивание: +2 (если контратака и защита от атаки).\n\n"
            "<u>Победа:</u>\n"
            "- Разрыв в 8 очков или 5 минут.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Начать бой", callback_data="pvp_start")]]),
            parse_mode="HTML"
        )
    elif query.data == "pvp_start":
        context.user_data["pvp_mode"] = "sport"  # Спортивный поединок
        context.user_data["player_score"] = 0
        context.user_data["bot_score"] = 0
        context.user_data["step"] = 0
        context.user_data["player_control"] = None
        context.user_data["player_attack"] = None
        context.user_data["player_defense"] = None
        context.user_data["bot_control"] = random.choice(["СС", "ТР", "ДЗ"])
        context.user_data["bot_attack"] = random.choice(["СС", "ТР", "ДЗ"])
        await query.edit_message_text(
            "Выберите контроль и атаку:\n1. Контроль (верхняя строка)\n2. Атака (нижняя строка)",
            reply_markup=pvp_attack_keyboard()
        )
    elif query.data.startswith("attack_control_"):
        context.user_data["player_control"] = query.data.split("_")[2]
        if context.user_data["player_attack"]:
            await query.edit_message_text(
                f"Ваш ход: Контроль {context.user_data['player_control']}, Атака {context.user_data['player_attack']}\nВыберите защиту:",
                reply_markup=answer_keyboard()
            )
        else:
            await query.edit_message_text("Теперь выберите атаку (нижняя строка):", reply_markup=pvp_attack_keyboard())
    elif query.data.startswith("attack_hit_"):
        context.user_data["player_attack"] = query.data.split("_")[2]
        if context.user_data["player_control"]:
            await query.edit_message_text(
                f"Ваш ход: Контроль {context.user_data['player_control']}, Атака {context.user_data['player_attack']}\nВыберите защиту:",
                reply_markup=answer_keyboard()
            )
        else:
            await query.edit_message_text("Сначала выберите контроль (верхняя строка):", reply_markup=pvp_attack_keyboard())
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"] and "pvp_mode" in context.user_data:
        context.user_data["player_defense"] = query.data
        await query.edit_message_text(
            f"Ваш ход: Контроль {context.user_data['player_control']}, Атака {context.user_data['player_attack']}, Защита {context.user_data['player_defense']}\nПодтвердите:",
            reply_markup=pvp_move_keyboard()
        )
    elif query.data == "pvp_move":
        # Базовая логика боя
        player_control = context.user_data["player_control"]
        player_attack = context.user_data["player_attack"]
        player_defense = context.user_data["player_defense"]
        bot_control = context.user_data["bot_control"]
        bot_attack = context.user_data["bot_attack"]
        bot_defense = random.choice(["Аге уке", "Сото уке", "Учи уке", "Гедан барай"])

        # Игрок атакует, бот защищается
        player_control_success = bot_defense != DEFENSE_MOVES[bot_defense]["control"] != bot_control
        player_attack_success = player_attack not in DEFENSE_MOVES[bot_defense]["attack_defense"]
        bot_counter_success = not player_control_success
        bot_dobivanie_success = bot_counter_success and player_attack not in DEFENSE_MOVES[bot_defense]["counter"]

        if player_control_success:
            context.user_data["player_score"] += 1
            if player_attack_success:
                context.user_data["player_score"] += 2
        elif player_attack_success:
            context.user_data["player_score"] += 1
        if bot_counter_success:
            context.user_data["bot_score"] += 1
            if bot_dobivanie_success:
                context.user_data["bot_score"] += 2

        # Бот атакует, игрок защищается
        bot_control_success = player_defense != DEFENSE_MOVES[player_defense]["control"] != bot_control
        bot_attack_success = bot_attack not in DEFENSE_MOVES[player_defense]["attack_defense"]
        player_counter_success = not bot_control_success
        player_dobivanie_success = player_counter_success and bot_attack not in DEFENSE_MOVES[player_defense]["counter"]

        if bot_control_success:
            context.user_data["bot_score"] += 1
            if bot_attack_success:
                context.user_data["bot_score"] += 2
        elif bot_attack_success:
            context.user_data["bot_score"] += 1
        if player_counter_success:
            context.user_data["player_score"] += 1
            if player_dobivanie_success:
                context.user_data["player_score"] += 2

        step = context.user_data["step"] + 1
        context.user_data["step"] = step
        log = (
            f"Схватка {step}:\n"
            f"Вы: Контроль {player_control} {'успех' if player_control_success else 'неуспех'}, "
            f"Атака {player_attack} {'успех' if player_attack_success else 'неуспех'}\n"
            f"Бот: Контроль {bot_control} {'успех' if bot_control_success else 'неуспех'}, "
            f"Атака {bot_attack} {'успех' if bot_attack_success else 'неуспех'}\n"
            f"Счёт: Вы {context.user_data['player_score']} - Бот {context.user_data['bot_score']}"
        )
        await query.edit_message_text(log)
        if abs(context.user_data["player_score"] - context.user_data["bot_score"]) >= 8 or step >= 5:  # 5 схваток для теста
            winner = "Вы" if context.user_data["player_score"] > context.user_data["bot_score"] else "Бот" if context.user_data["bot_score"] > context.user_data["player_score"] else "Ничья"
            await query.message.reply_text(f"Бой завершён! Победитель: {winner}", reply_markup=get_start_keyboard())
            context.user_data.clear()
        else:
            context.user_data["player_control"] = None
            context.user_data["player_attack"] = None
            context.user_data["player_defense"] = None
            context.user_data["bot_control"] = random.choice(["СС", "ТР", "ДЗ"])
            context.user_data["bot_attack"] = random.choice(["СС", "ТР", "ДЗ"])
            await query.message.reply_text(
                "Выберите контроль и атаку для следующей схватки:",
                reply_markup=pvp_attack_keyboard()
            )
