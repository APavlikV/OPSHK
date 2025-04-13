import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from trainer.game_logic import check_move, generate_detailed_log
from trainer.keyboards import pvp_attack_keyboard, end_fight_keyboard
from trainer.texts import TEXTS
from trainer.state import GameState
from trainer.data import MOVES, DEFENSE_MOVES

logger = logging.getLogger(__name__)

# Кастомная клавиатура с /start
def get_start_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("/start")]],
        resize_keyboard=True
    )

async def start(update: Update, context: CallbackContext):
    context.user_data["state"] = GameState()
    user = update.effective_user
    username = user.username or user.first_name
    if username:
        reply_text = TEXTS["start_welcome"].format(username=username)
        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Использовать Telegram ник", callback_data=f"use_nick_{username}"),
                InlineKeyboardButton("Выбрать свой ник", callback_data="choose_nick")
            ]
        ])
    else:
        reply_text = TEXTS["start_no_username"]
        reply_markup = None
        context.user_data["state"].awaiting_nick = True
    await update.message.reply_text(
        reply_text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )

async def setnick(update: Update, context: CallbackContext):
    context.user_data["state"].awaiting_nick = True
    await update.message.reply_text(
        TEXTS["setnick_prompt"],
        parse_mode="HTML",
        reply_markup=get_start_keyboard()
    )

async def handle_nick_reply(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    if not state.awaiting_nick:
        logger.debug("handle_nick_reply: awaiting_nick is False, ignoring")
        return
    nick = update.message.text.strip()
    logger.info(f"User input nick: {nick}")
    if len(nick) > 20:
        await update.message.reply_text(
            TEXTS["nick_too_long"],
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )
        return
    state.nickname = nick or "Вы"
    state.awaiting_nick = False
    context.user_data["state"] = state
    reply_text = TEXTS["nick_set"].format(nick=state.nickname)
    await update.message.reply_text(
        reply_text,
        parse_mode="HTML",
        reply_markup=game_menu_keyboard()
    )
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )

async def game(update: Update, context: CallbackContext):
    await update.message.reply_text(
        TEXTS["game_menu"],
        parse_mode="HTML",
        reply_markup=game_menu_keyboard()
    )
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )

def game_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Тренировка", callback_data="training_menu"),
            InlineKeyboardButton("Схватка с Ботом", callback_data="pvp_menu"),
            InlineKeyboardButton("PvP Арена", callback_data="pvp_arena")
        ]
    ])

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    state = context.user_data.get("state", GameState())

    if data.startswith("use_nick_"):
        nickname = data.replace("use_nick_", "")
        state.nickname = nickname
        context.user_data["state"] = state
        await query.message.reply_text(
            TEXTS["use_telegram_nick"].format(username=nickname),
            parse_mode="HTML",
            reply_markup=game_menu_keyboard()
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    elif data == "choose_nick":
        state.awaiting_nick = True
        context.user_data["state"] = state
        await query.message.reply_text(
            TEXTS["choose_own_nick"],
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )
    elif data == "training_menu":
        await query.message.reply_text(
            TEXTS["training_fight_menu"],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Простой бой", callback_data="simple_fight"),
                    InlineKeyboardButton("Бой на время", callback_data="timed_fight")
                ],
                [InlineKeyboardButton("Памятка", callback_data="training_memo")]
            ])
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    elif data == "pvp_menu":
        await query.message.reply_text(
            TEXTS["pvp_bot_menu"],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Начать бой", callback_data="pvp_fight"),
                    InlineKeyboardButton("Правила", callback_data="pvp_rules")
                ]
            ])
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    elif data == "pvp_arena":
        await query.message.reply_text(
            "🏟 PvP Арена в разработке! Скоро сможете сражаться с другими игроками!",
            parse_mode="HTML"
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    elif data == "training_memo":
        await query.message.reply_text(
            TEXTS["training_memo"],
            parse_mode="HTML"
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    elif data == "pvp_rules":
        await query.message.reply_text(
            TEXTS["pvp_rules"],
            parse_mode="HTML"
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    elif data == "simple_fight":
        await start_simple_fight(update, context)
    elif data == "pvp_fight":
        state.mode = "pvp"
        state.step = 1
        context.user_data["state"] = state
        await query.message.reply_text(
            TEXTS["pvp_start"].format(step=state.step),
            parse_mode="HTML",
            reply_markup=pvp_attack_keyboard("control")
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    elif data.startswith("defense_"):
        await simple_fight_defense(update, context)
    elif data.startswith("attack_"):
        await pvp_fight_attack(update, context)
    elif data == "last_stats":
        await last_stats(update, context)

async def start_simple_fight(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    state.mode = "simple"
    state.fight_sequence = random.sample(MOVES, 10)
    state.current_step = 0
    state.correct_count = 0
    state.control_count = 0
    state.hint_count = 0
    context.user_data["state"] = state
    nickname = state.nickname or "Боец"
    await update.callback_query.message.reply_text(
        f"⚔️ {nickname}, начинаем бой!",
        parse_mode="HTML"
    )
    await update.callback_query.message.reply_text(
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )
    await show_move(update, context)

async def show_move(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    if state.current_step >= len(state.fight_sequence):
        return
    control, attack = state.fight_sequence[state.current_step]
    reply_text = TEXTS["training_move_simple"].format(
        step=state.current_step + 1,
        total=len(state.fight_sequence),
        control=control,
        attack=attack
    )
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Аге уке", callback_data="defense_Аге уке"),
            InlineKeyboardButton("Учи уке", callback_data="defense_Учи уке")
        ],
        [
            InlineKeyboardButton("Сото уке", callback_data="defense_Сото уке"),
            InlineKeyboardButton("Гедан барай", callback_data="defense_Гедан барай")
        ]
    ])
    await update.callback_query.message.reply_text(
        reply_text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )
    await update.callback_query.message.reply_text(
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )

async def simple_fight_defense(update: Update, context: CallbackContext):
    query = update.callback_query
    state = context.user_data.get("state", GameState())
    chosen_defense = query.data.replace("defense_", "")
    control, attack = state.fight_sequence[state.current_step]
    
    is_success, partial_success, correct_defenses = check_move(control, attack, chosen_defense)
    
    if is_success:
        state.correct_count += 1
        state.control_count += 1
    elif control in DEFENSE_MOVES.get(chosen_defense, {}).get("control", []):
        state.control_count += 1
    
    nickname = state.nickname or "Боец"
    log = generate_detailed_log(control, attack, chosen_defense, is_success, nickname)
    await query.message.reply_text(
        log,
        parse_mode="HTML"
    )
    await query.message.reply_text(
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )
    
    state.current_step += 1
    context.user_data["state"] = state
    if state.current_step >= 10:
        state.last_fight_stats = {
            "correct_count": state.correct_count,
            "control_count": state.control_count,
            "hint_count": state.hint_count
        }
        stats_message = (
            f"📊 Статистика боя для {nickname}:\n"
            f"✅ Чистых побед: {state.correct_count} из 10\n"
            f"🎯 Контролей отбито: {state.control_count} из 10\n"
            f"💡 Подсказок использовано: {state.hint_count}"
        )
        await query.message.reply_text(
            stats_message,
            parse_mode="HTML",
            reply_markup=end_fight_keyboard()
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
        return
    
    await show_move(update, context)

async def last_stats(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    stats = state.last_fight_stats
    nickname = state.nickname or "Боец"
    if stats:
        message = (
            f"📊 Прошлая статистика для {nickname}:\n"
            f"✅ Чистых побед: {stats['correct_count']} из 10\n"
            f"🎯 Контролей отбито: {stats['control_count']} из 10\n"
            f"💡 Подсказок использовано: {stats['hint_count']}"
        )
    else:
        message = "📊 Нет сохранённой статистики."
    await update.callback_query.message.reply_text(
        message,
        parse_mode="HTML"
    )
    await update.callback_query.message.reply_text(
        "Выберите действие:",
        reply_markup=get_start_keyboard()
    )

async def pvp_fight_attack(update: Update, context: CallbackContext):
    query = update.callback_query
    state = context.user_data.get("state", GameState())
    data = query.data
    
    if data.startswith("attack_control_"):
        state.player_control = data.replace("attack_control_", "")
        logger.info(f"PvP: control set to {state.player_control}")
        reply_markup = pvp_attack_keyboard("attack", state.player_control)
        await query.message.reply_text(
            TEXTS["pvp_attack"].format(step=state.step),
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
