import random
import logging
from telegram import Update
from telegram.ext import CallbackContext
from trainer.game_logic import check_move, generate_detailed_log
from trainer.keyboards import pvp_attack_keyboard, end_fight_keyboard

logger = logging.getLogger(__name__)

MOVES = [("ДЗ", "ГДН"), ("СС", "СС"), ("ТР", "ТР"), ("ДЗ", "ДЗ"), ("ТР", "ГДН"), ("СС", "ТР"), ("ДЗ", "СС"), ("ТР", "ДЗ"), ("СС", "ГДН"), ("ДЗ", "ТР")]

async def start_simple_fight(update: Update, context: CallbackContext):
    state = context.user_data
    state["mode"] = "simple"
    state["fight_sequence"] = random.sample(MOVES, 10)
    state["current_step"] = 0
    state["correct_count"] = 0
    state["control_count"] = 0
    state["hint_count"] = 0
    nickname = state.get("nickname", "Боец")
    await update.callback_query.message.reply_text(
        f"⚔️ {nickname}, начинаем бой!", parse_mode="HTML"
    )
    await show_move(update, context)

async def simple_fight_defense(update: Update, context: CallbackContext):
    query = update.callback_query
    state = context.user_data
    chosen_defense = query.data.replace("defense_", "")
    control, attack = state["fight_sequence"][state["current_step"]]
    
    is_success, partial_success, correct_defenses = check_move(control, attack, chosen_defense)
    
    if is_success:
        state["correct_count"] += 1
        state["control_count"] += 1
    elif control in DEFENSE_MOVES.get(chosen_defense, {}).get("control", []):
        state["control_count"] += 1
    
    nickname = state.get("nickname", "Боец")
    log = generate_detailed_log(control, attack, chosen_defense, is_success, nickname)
    await query.message.reply_text(log, parse_mode="HTML")
    
    state["current_step"] += 1
    if state["current_step"] >= 10:
        state["last_fight_stats"] = {
            "correct_count": state["correct_count"],
            "control_count": state["control_count"],
            "hint_count": state["hint_count"]
        }
        stats_message = (
            f"📊 Статистика боя для {nickname}:\n"
            f"✅ Чистых побед: {state['correct_count']} из 10\n"
            f"🎯 Контролей отбито: {state['control_count']} из 10\n"
            f"💡 Подсказок использовано: {state['hint_count']}"
        )
        await query.message.reply_text(stats_message, parse_mode="HTML", reply_markup=end_fight_keyboard())
        return
    
    await show_move(update, context)

async def last_stats(update: Update, context: CallbackContext):
    state = context.user_data
    stats = state.get("last_fight_stats", None)
    nickname = state.get("nickname", "Боец")
    if stats:
        message = (
            f"📊 Прошлая статистика для {nickname}:\n"
            f"✅ Чистых побед: {stats['correct_count']} из 10\n"
            f"🎯 Контролей отбито: {stats['control_count']} из 10\n"
            f"💡 Подсказок использовано: {stats['hint_count']}"
        )
    else:
        message = "📊 Нет сохранённой статистики."
    await update.callback_query.message.reply_text(message, parse_mode="HTML")

async def pvp_fight_attack(update: Update, context: CallbackContext):
    query = update.callback_query
    state = context.user_data
    data = query.data
    
    if data.startswith("attack_control_"):
        state["player_control"] = data.replace("attack_control_", "")
        logger.info(f"PvP: control set to {state['player_control']}")
        reply_markup = pvp_attack_keyboard("attack", state["player_control"])
        await query.message.reply_text("Выбери атаку:", reply_markup=reply_markup)
