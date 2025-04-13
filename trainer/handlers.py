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
    message = await update.message.reply_text(
        reply_text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )
    context.user_data["state"].last_message_id = message.message_id

async def handle_first_message(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    if not state.nickname and not state.awaiting_nick:
        await update.message.reply_text(
            "🥋 Нажмите /start, чтобы начать!",
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )
    else:
        logger.debug("handle_first_message: user already started, ignoring")

async def setnick(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    state.awaiting_nick = True
    context.user_data["state"] = state
    await update.message.reply_text(
        TEXTS["setnick_prompt"],
        parse_mode="HTML"
    )

async def handle_nick_reply(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    logger.debug(f"handle_nick_reply: awaiting_nick={state.awaiting_nick}")
    if not state.awaiting_nick:
        logger.debug("handle_nick_reply: awaiting_nick is False, ignoring")
        return
    nick = update.message.text.strip()
    logger.info(f"User input nick: {nick}")
    if len(nick) > 20:
        await update.message.reply_text(
            TEXTS["nick_too_long"],
            parse_mode="HTML"
        )
        return
    state.nickname = nick or "Вы"
    state.awaiting_nick = False
    context.user_data["state"] = state
    reply_text = TEXTS["nick_set"].format(nick=state.nickname) + "\nГотовы к сражениям?\nВыберите, что Вы хотите:"
    message = await update.message.reply_text(
        reply_text,
        parse_mode="HTML",
        reply_markup=game_menu_keyboard()
    )
    state.last_message_id = message.message_id
    context.user_data["state"] = state

async def game(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    reply_text = TEXTS["nick_set"].format(nick=state.nickname or "Боец") + "\nГотовы к сражениям?\nВыберите, что Вы хотите:"
    message = await update.message.reply_text(
        reply_text,
        parse_mode="HTML",
        reply_markup=game_menu_keyboard()
    )
    state.last_message_id = message.message_id
    context.user_data["state"] = state

def game_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Учебный бой", callback_data="training_menu"),
            InlineKeyboardButton("Бой с Ботом", callback_data="pvp_menu"),
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
        reply_text = TEXTS["nick_set"].format(nick=nickname) + "\nГотовы к сражениям?\nВыберите, что Вы хотите:"
        await query.message.edit_text(
            reply_text,
            parse_mode="HTML",
            reply_markup=game_menu_keyboard()
        )
        state.last_message_id = query.message.message_id
    elif data == "choose_nick":
        state.awaiting_nick = True
        await query.message.edit_text(
            TEXTS["choose_own_nick"],
            parse_mode="HTML",
            reply_markup=None
        )
    elif data == "training_menu":
        reply_text = "🥊 Учебный бой: выберите действие:"
        await query.message.edit_text(
            reply_text,
            parse_mode="HTML",
            reply_markup=training_menu_keyboard()
        )
        state.last_message_id = query.message.message_id
    elif data == "pvp_menu":
        await query.message.edit_text(
            TEXTS["pvp_bot_menu"],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Начать бой", callback_data="pvp_fight"),
                    InlineKeyboardButton("Правила", callback_data="pvp_rules")
                ]
            ])
        )
        state.last_message_id = query.message.message_id
    elif data == "pvp_arena":
        await query.message.edit_text(
            "🏟 PvP Арена в разработке! Скоро сможете сражаться с другими игроками!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data="back_to_menu")]
            ])
        )
        state.last_message_id = query.message.message_id
    elif data == "training_memo":
        await query.message.edit_text(
            TEXTS["training_memo"],
            parse_mode="HTML",
            reply_markup=training_menu_keyboard(exclude="training_memo")
        )
        state.last_message_id = query.message.message_id
    elif data == "training_rules":
        await query.message.edit_text(
            TEXTS["training_rules"],
            parse_mode="HTML",
            reply_markup=training_menu_keyboard(exclude="training_rules")
        )
        state.last_message_id = query.message.message_id
    elif data == "pvp_rules":
        await query.message.edit_text(
            TEXTS["pvp_rules"],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Начать бой", callback_data="pvp_fight"),
                    InlineKeyboardButton("Назад", callback_data="pvp_menu")
                ]
            ])
        )
        state.last_message_id = query.message.message_id
    elif data == "simple_fight":
        await start_simple_fight(update, context)
    elif data == "timed_fight":
        await query.message.edit_text(
            "⏱ Бой на время в разработке!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Назад", callback_data="training_menu")]
            ])
        )
        state.last_message_id = query.message.message_id
    elif data == "back_to_training":
        await query.message.edit_text(
            "🥊 Учебный бой: выберите действие:",
            parse_mode="HTML",
            reply_markup=training_menu_keyboard()
        )
        state.last_message_id = query.message.message_id
    elif data == "back_to_menu":
        reply_text = TEXTS["nick_set"].format(nick=state.nickname or "Боец") + "\nГотовы к сражениям?\nВыберите, что Вы хотите:"
        await query.message.edit_text(
            reply_text,
            parse_mode="HTML",
            reply_markup=game_menu_keyboard()
        )
        state.last_message_id = query.message.message_id
    elif data == "pvp_fight":
        state.mode = "pvp"
        state.step = 1
        await query.message.edit_text(
            TEXTS["pvp_start"].format(step=state.step),
            parse_mode="HTML",
            reply_markup=pvp_attack_keyboard("control")
        )
        state.last_message_id = query.message.message_id
    elif data.startswith("defense_"):
        await simple_fight_defense(update, context)
    elif data.startswith("attack_"):
        await pvp_fight_attack(update, context)
    elif data == "last_stats":
        await last_stats(update, context)
    elif data == "hint":
        control, attack = state.fight_sequence[state.current_step]
        correct_defenses = [d for d, v in DEFENSE_MOVES.items() if control in v.get("control", []) and attack in v.get("attack", [])]
        hint_text = f"\n\n💡 <i>Подсказка</i>: правильная защита — <b>{', '.join(correct_defenses) if correct_defenses else 'нет подходящей защиты'}</b>"
        task_text = (
            f"<u>⚔️ Схватка {state.current_step + 1} из 10</u>\n\n"
            f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
            f"💥 <i>Атака</i>: <b>{attack}</b>{hint_text}"
        )
        state.hint_count += 1
        await context.bot.edit_message_text(
            text=task_text,
            chat_id=query.message.chat_id,
            message_id=state.last_fight_message_id,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Аге уке", callback_data="defense_Аге уке"),
                    InlineKeyboardButton("Сото уке", callback_data="defense_Сото уке")
                ],
                [
                    InlineKeyboardButton("Учи уке", callback_data="defense_Учи уке"),
                    InlineKeyboardButton("Гедан барай", callback_data="defense_Гедан барай")
                ],
                [
                    InlineKeyboardButton("💡 Подсказка", callback_data="hint")
                ]
            ])
        )
    context.user_data["state"] = state

def training_menu_keyboard(exclude=None):
    buttons = [
        [
            InlineKeyboardButton("Простой бой", callback_data="simple_fight"),
            InlineKeyboardButton("Бой на время", callback_data="timed_fight")
        ],
        [
            InlineKeyboardButton("Правила", callback_data="training_rules"),
            InlineKeyboardButton("Памятка", callback_data="training_memo")
        ],
        [
            InlineKeyboardButton("Назад", callback_data="back_to_menu")
        ]
    ]
    if exclude == "training_rules":
        buttons[1] = [InlineKeyboardButton("Памятка", callback_data="training_memo")]
    elif exclude == "training_memo":
        buttons[1] = [InlineKeyboardButton("Правила", callback_data="training_rules")]
    return InlineKeyboardMarkup(buttons)

async def start_simple_fight(update: Update, context: CallbackContext):
    query = update.callback_query
    state = context.user_data.get("state", GameState())
    state.mode = "simple"
    state.fight_sequence = random.sample(MOVES, 10)
    state.current_step = 0
    state.correct_count = 0
    state.control_count = 0
    state.missed_attacks = 0
    state.hint_count = 0
    context.user_data["state"] = state
    nickname = state.nickname or "Боец"
    await query.message.edit_text(
        f"⚔️ <b>{nickname}</b>, начинаем бой! ⚔️",
        parse_mode="HTML",
        reply_markup=None
    )
    state.last_message_id = query.message.message_id
    context.user_data["state"] = state
    await show_move(update, context)

async def show_move(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    if state.current_step >= len(state.fight_sequence):
        return
    control, attack = state.fight_sequence[state.current_step]
    reply_text = (
        f"<u>⚔️ Схватка {state.current_step + 1} из 10</u>\n\n"
        f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
        f"💥 <i>Атака</i>: <b>{attack}</b>"
    )
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Аге уке", callback_data="defense_Аге уке"),
            InlineKeyboardButton("Сото уке", callback_data="defense_Сото уке")
        ],
        [
            InlineKeyboardButton("Учи уке", callback_data="defense_Учи уке"),
            InlineKeyboardButton("Гедан барай", callback_data="defense_Гедан барай")
        ],
        [
            InlineKeyboardButton("💡 Подсказка", callback_data="hint")
        ]
    ])
    message = await update.callback_query.message.reply_text(
        reply_text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )
    state.last_fight_message_id = message.message_id
    context.user_data["state"] = state

async def simple_fight_defense(update: Update, context: CallbackContext):
    query = update.callback_query
    state = context.user_data.get("state", GameState())
    chosen_defense = query.data.replace("defense_", "")
    control, attack = state.fight_sequence[state.current_step]
    
    logger.debug(f"simple_fight_defense: control={control}, attack={attack}, chosen_defense={chosen_defense}")
    
    is_success, partial_success, correct_defenses = check_move(control, attack, chosen_defense)
    
    if is_success:
        state.correct_count += 1
        state.control_count += 1
    elif control in DEFENSE_MOVES.get(chosen_defense, {}).get("control", []):
        state.control_count += 1
    else:
        state.missed_attacks += 1
    
    nickname = state.nickname or "Боец"
    log = generate_detailed_log(control, attack, chosen_defense, is_success, nickname)
    
    # Перезаписываем сообщение с заданием, без подсказки
    task_text = (
        f"<u>⚔️ Схватка {state.current_step + 1} из 10</u>\n\n"
        f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
        f"💥 <i>Атака</i>: <b>{attack}</b>\n"
        f"🛡️ <i>Ваша защита</i>: <b>{chosen_defense}</b>\n\n"
    )
    result_text = "✅ <b>УСПЕХ</b>" if is_success else (
        f"❌ <b>ПОРАЖЕНИЕ</b>\n<i>Правильно</i>: <b>{', '.join(correct_defenses) if correct_defenses else 'нет защиты'}</b>"
    )
    await context.bot.edit_message_text(
        text=task_text + result_text,
        chat_id=query.message.chat_id,
        message_id=state.last_fight_message_id,
        parse_mode="HTML",
        reply_markup=None
    )
    
    # Отправляем лог схватки
    await query.message.reply_text(
        log,
        parse_mode="HTML"
    )
    
    state.current_step += 1
    context.user_data["state"] = state
    
    if state.current_step >= 10:
        # Бой завершён
        await query.message.reply_text(
            "<b>🏁 Бой завершён!</b>",
            parse_mode="HTML"
        )
        # Статистика
        stats_message = (
            f"<b>Статистика боя:</b>\n\n"
            f"✅ <i>Правильных контр действий</i>: <b>{state.correct_count}</b>\n"
            f"💡 <i>С подсказкой</i>: <b>{state.hint_count}</b>\n"
            f"🛡️ <i>Отбито контролей</i>: <b>{state.control_count}</b>\n"
            f"❌ <i>Пропущено атак</i>: <b>{state.missed_attacks}</b>"
        )
        await query.message.reply_text(
            stats_message,
            parse_mode="HTML"
        )
        # Возврат в главное меню
        reply_text = TEXTS["nick_set"].format(nick=nickname) + "\nГотовы к сражениям?\nВыберите, что Вы хотите:"
        message = await query.message.reply_text(
            reply_text,
            parse_mode="HTML",
            reply_markup=game_menu_keyboard()
        )
        state.last_message_id = message.message_id
        state.last_fight_stats = {
            "correct_count": state.correct_count,
            "control_count": state.control_count,
            "missed_attacks": state.missed_attacks,
            "hint_count": state.hint_count
        }
        context.user_data["state"] = state
        return
    
    await show_move(update, context)

async def last_stats(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    stats = state.last_fight_stats
    nickname = state.nickname or "Боец"
    if stats:
        message = (
            f"<b>Статистика боя:</b>\n\n"
            f"✅ <i>Правильных контр действий</i>: <b>{stats['correct_count']}</b>\n"
            f"💡 <i>С подсказкой</i>: <b>{stats['hint_count']}</b>\n"
            f"🛡️ <i>Отбито контролей</i>: <b>{stats['control_count']}</b>\n"
            f"❌ <i>Пропущено атак</i>: <b>{stats['missed_attacks']}</b>"
        )
    else:
        message = "📊 Нет сохранённой статистики."
    await update.callback_query.message.reply_text(
        message,
        parse_mode="HTML"
    )

async def pvp_fight_attack(update: Update, context: CallbackContext):
    query = update.callback_query
    state = context.user_data.get("state", GameState())
    data = query.data
    
    if data.startswith("attack_control_"):
        state.player_control = data.replace("attack_control_", "")
        logger.info(f"PvP: control set to {state.player_control}")
        reply_markup = pvp_attack_keyboard("attack", state.player_control)
        await query.message.edit_text(
            TEXTS["pvp_attack"].format(step=state.step),
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        state.last_message_id = query.message.message_id
    context.user_data["state"] = state
