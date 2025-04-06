import logging
from telegram import InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from .keyboards import get_keyboard_by_step, get_rules_keyboard, get_memo_keyboard, get_hint_keyboard
from .utils import MOVES, get_correct_answer, get_question_text

logger = logging.getLogger(__name__)

def init_user_data_if_empty(context: CallbackContext):
    if context.user_data is None:
        context.user_data = {}

def build_move_text(step: int, control: str, attack: str, remaining: int) -> str:
    return (
        f"<code>⚔️ Шаг {step + 1} из {len(MOVES)}</code>\n\n"
        f"🎯 Контроль: <b>{control}</b>\n"
        f"💥 Атака: <b>{attack}</b>\n"
        f"Осталось: {remaining} сек"
    )

def clean_previous_message(context: CallbackContext):
    message_id = context.user_data.get("message_id")
    if message_id:
        try:
            context.bot.delete_message(chat_id=context.user_data["chat_id"], message_id=message_id)
        except BadRequest as e:
            logger.warning("Could not delete message: %s", e)
        context.user_data.pop("message_id", None)

def handle_rules(query):
    query.edit_message_text(
        text="📜 Правила боя:\n\n1. Выбирай сторону защиты.\n2. Угадывай атаку врага.\n3. Успей до окончания таймера!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_rules_keyboard()
    )

def handle_memo(query):
    query.edit_message_text(
        text="📕 Памятка по уязвимостям:\n\n🛡️ Сторона защиты зависит от типа атаки.\nИзучи атаки, чтобы лучше угадывать!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_memo_keyboard()
    )

def handle_hint(query, context):
    step = context.user_data.get("step", 0)
    if step < len(MOVES):
        attack = MOVES[step]["attack"]
        query.answer(text=f"💡 Подсказка: {attack}", show_alert=True)
    else:
        query.answer(text="Нет подсказки", show_alert=True)

def handle_fight_start(query, context):
    context.user_data["step"] = 0
    context.user_data["score"] = 0
    context.user_data["sequence"] = MOVES
    context.user_data["chat_id"] = query.message.chat_id

    step = 0
    question_data = context.user_data["sequence"][step]
    question_text = get_question_text(question_data)
    reply_markup = InlineKeyboardMarkup(get_keyboard_by_step(step))

    query.edit_message_text(
        text=question_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

def handle_defense_choice(query, context):
    step = context.user_data.get("step", 0)
    sequence = context.user_data.get("sequence", MOVES)
    if step >= len(sequence):
        query.answer()
        return

    correct_answer = get_correct_answer(sequence[step])
    chosen_answer = query.data

    if chosen_answer == correct_answer:
        context.user_data["score"] += 1

    context.user_data["step"] += 1
    next_step = context.user_data["step"]

    if next_step >= len(sequence):
        score = context.user_data.get("score", 0)
        query.edit_message_text(
            text=f"✅ Бой завершен!\n\n🏆 Правильных ответов: <b>{score} из {len(sequence)}</b>",
            parse_mode=ParseMode.HTML
        )
        return

    next_question = sequence[next_step]
    question_text = get_question_text(next_question)
    reply_markup = InlineKeyboardMarkup(get_keyboard_by_step(next_step))

    query.edit_message_text(
        text=question_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

async def button(update: Update, context: CallbackContext):
    init_user_data_if_empty(context)

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "rules":
        handle_rules(query)

    elif data == "memo":
        handle_memo(query)

    elif data == "hint":
        handle_hint(query, context)

    elif data == "fight":
        handle_fight_start(query, context)

    else:
        handle_defense_choice(query, context)

