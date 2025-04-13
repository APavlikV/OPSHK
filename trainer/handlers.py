from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, ConversationHandler
from trainer.data import MOVES, DEFENSE_MOVES
from trainer.game_logic import check_move, generate_detailed_log
from trainer.state import GameState
import random

# Состояния для ConversationHandler
NICKNAME = 0

async def start(update: Update, context: CallbackContext):
    state = GameState()
    telegram_nick = update.effective_user.username or update.effective_user.first_name
    context.user_data["state"] = state

    keyboard = [
        [InlineKeyboardButton(f"Использовать {telegram_nick}", callback_data=f"nick_{telegram_nick}")],
        [InlineKeyboardButton("Выбрать свой", callback_data="nick_custom")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🥋 Добро пожаловать в КАРАТЭ тренажер!\n"
        f"Использовать ваш ник Telegram ({telegram_nick}) или выбрать свой?",
        reply_markup=reply_markup
    )

async def setnick(update: Update, context: CallbackContext):
    await update.message.reply_text("💡 Напиши свой новый ник:")
    return NICKNAME

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    state = context.user_data.get("state", GameState())

    if query.data.startswith("nick_"):
        if query.data == "nick_custom":
            await query.message.reply_text("💡 Напиши свой новый ник:")
            return NICKNAME
        else:
            state.nickname = query.data.replace("nick_", "")
            context.user_data["state"] = state
            await context.bot.edit_message_text(
                text=f"✅ Ник установлен: {state.nickname}\nГотов к бою? Напиши /game",
                chat_id=query.message.chat_id,
                message_id=query.message.message_id
            )
    elif query.data.startswith("defense_"):
        await simple_fight_defense(update, context)
    
    await query.answer()
    return ConversationHandler.END

async def handle_nick_reply(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    state.nickname = update.message.text.strip()
    context.user_data["state"] = state
    await update.message.reply_text(f"✅ Ник установлен: {state.nickname}\nГотов к бою? Напиши /game")
    return ConversationHandler.END

async def handle_first_message(update: Update, context: CallbackContext):
    await start(update, context)

async def game(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    if not state.nickname:
        telegram_nick = update.effective_user.username or update.effective_user.first_name
        state.nickname = telegram_nick
    state.mode = "training"
    context.user_data["state"] = state
    await start_fight(update, context)

async def start_fight(update: Update, context: CallbackContext):
    state = context.user_data.get("state", GameState())
    state.fight_sequence = random.sample(MOVES, 10)
    state.current_step = 0
    state.correct_count = 0
    state.control_count = 0
    state.missed_attacks = 0
    state.total_points = 0
    context.user_data["state"] = state

    keyboard = [
        [InlineKeyboardButton("Аге уке", callback_data="defense_Аге уке")],
        [InlineKeyboardButton("Сото уке", callback_data="defense_Сото уке")],
        [InlineKeyboardButton("Учи уке", callback_data="defense_Учи уке")],
        [InlineKeyboardButton("Гедан барай", callback_data="defense_Гедан барай")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    control, attack = state.fight_sequence[state.current_step]
    message = await update.message.reply_text(
        f"<code>⚔️ Схватка 1 из 10</code>\n\n"
        f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
        f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
        f"Выберите защиту:",
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
    
    is_success, partial_success, correct_defenses, points = check_move(control, attack, chosen_defense)
    
    if is_success:
        state.correct_count += 1
        state.control_count += 1
    elif control in DEFENSE_MOVES.get(chosen_defense, {}).get("control_defense", []):
        state.control_count += 1
    elif attack in DEFENSE_MOVES.get(chosen_defense, {}).get("attack_defense", []):
        pass
    else:
        state.missed_attacks += 1
    
    state.total_points += points
    
    nickname = state.nickname or "Боец"
    log = generate_detailed_log(control, attack, chosen_defense, is_success, nickname)
    
    task_text = (
        f"<code>⚔️ Схватка {state.current_step + 1} из 10</code>\n\n"
        f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
        f"💥 <i>Атака</i>: <b>{attack}</b>\n"
        f"🛡️ <i>Ваша защита</i>: <b>{chosen_defense}</b>\n\n"
    )
    result_text = (
        f"✅ <b>ЧИСТАЯ ПОБЕДА</b> (+{points} баллов)"
        if is_success else (
            f"✅ <b>ЧАСТИЧНЫЙ УСПЕХ</b> (+{points} баллов)"
            if partial_success else
            f"❌ <b>ПОРАЖЕНИЕ</b> (+{points} баллов)"
        )
    )
    hint_text = (
        f"💡 <b>Подсказка</b>: правильная защита — {', '.join(correct_defenses) if correct_defenses else 'нет подходящей защиты'}"
    )
    
    await context.bot.edit_message_text(
        text=task_text + result_text + "\n\n" + hint_text,
        chat_id=query.message.chat_id,
        message_id=state.last_fight_message_id,
        parse_mode="HTML",
        reply_markup=None
    )
    
    await query.message.reply_text(
        log,
        parse_mode="HTML"
    )
    
    state.current_step += 1
    
    if state.current_step >= 10:
        total_text = (
            f"🏆 <b>Бой завершён!</b>\n\n"
            f"👊 Чистых побед: <b>{state.correct_count}</b>\n"
            f"🛡️ Контролей отбито: <b>{state.control_count}</b>\n"
            f"💥 Пропущено атак: <b>{state.missed_attacks}</b>\n"
            f"⭐ Всего баллов: <b>{state.total_points}</b>"
        )
        await query.message.reply_text(total_text, parse_mode="HTML")
        state.fight_sequence = []
        state.current_step = 0
        state.last_fight_message_id = None
    else:
        control, attack = state.fight_sequence[state.current_step]
        keyboard = [
            [InlineKeyboardButton("Аге уке", callback_data="defense_Аге уке")],
            [InlineKeyboardButton("Сото уке", callback_data="defense_Сото уке")],
            [InlineKeyboardButton("Учи уке", callback_data="defense_Учи уке")],
            [InlineKeyboardButton("Гедан барай", callback_data="defense_Гедан барай")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = await query.message.reply_text(
            f"<code>⚔️ Схватка {state.current_step + 1} из 10</code>\n\n"
            f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
            f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
            f"Выберите защиту:",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        state.last_fight_message_id = message.message_id
    
    context.user_data["state"] = state
