import logging
import random
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from .keyboards import get_nickname_keyboard
from .texts import PROFILE_TEXT
from .state import FightState
from .data import save_fighter, save_fight
from .game_logic import check_defense, MOVES

logger = logging.getLogger(__name__)

def get_fight_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Гедан барай", callback_data="defense_Гедан барай")],
        [InlineKeyboardButton(text="Аге уке", callback_data="defense_Аге уке")],
        [InlineKeyboardButton(text="Сото уке", callback_data="defense_Сото уке")],
        [InlineKeyboardButton(text="Учи уке", callback_data="defense_Учи уке")],
        [InlineKeyboardButton(text="💡 Подсказка", callback_data="hint")]
    ])

def get_next_steps_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Бой 🥊", callback_data="start_fight"),
            InlineKeyboardButton(text="Профиль 📊", callback_data="show_profile")
        ]
    ])

def setup_handlers(dp: Dispatcher):
    @dp.message(Command("profile"))
    async def cmd_profile(message: types.Message):
        await message.answer(PROFILE_TEXT)

    @dp.message(Command("fight"))
    async def cmd_fight(message: types.Message, state: FSMContext):
        await state.update_data(fight_sequence=random.sample(MOVES, 10), step=1, score=0)
        fight_data = await state.get_data()
        control, attack = fight_data["fight_sequence"][0]
        await message.answer(
            f"<code>⚔️ Схватка 1 из 10</code>\n"
            f"🎯 Контроль: {control}\n"
            f"💥 Атака: {attack}\n"
            f"Выбери защиту:",
            parse_mode="HTML",
            reply_markup=get_fight_keyboard()
        )

    @dp.callback_query(F.data == "use_telegram_nick")
    async def use_telegram_nick(callback: CallbackQuery, state: FSMContext):
        username = callback.from_user.username or f"User{callback.from_user.id}"
        user_id = callback.from_user.id
        try:
            save_fighter(user_id, username)
            await callback.message.edit_text(
                f"Ник сохранён: <b>{username}</b>! Готов к бою? 💪",
                parse_mode="HTML",
                reply_markup=get_next_steps_keyboard()
            )
            await state.clear()
        except Exception as e:
            logger.error(f"Save fighter failed: {e}")
            await callback.message.edit_text(f"Ошибка сохранения: {e}")
        await callback.answer()

    @dp.callback_query(F.data == "custom_nick")
    async def custom_nick(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_text("Введи свой уникальный ник:")
        await state.set_state(FightState.waiting_for_name)
        await callback.answer()

    @dp.message(FightState.waiting_for_name)
    async def process_custom_nick(message: Message, state: FSMContext):
        nickname = message.text.strip()
        user_id = message.from_user.id
        try:
            save_fighter(user_id, nickname)
            await message.answer(
                f"Ник сохранён: <b>{nickname}</b>! Готов к бою? 💪",
                parse_mode="HTML",
                reply_markup=get_next_steps_keyboard()
            )
            await state.clear()
        except Exception as e:
            logger.error(f"Save fighter failed: {e}")
            await message.answer(f"Ошибка сохранения: {e}")
            await state.clear()

    @dp.callback_query(F.data == "start_fight")
    async def start_fight(callback: CallbackQuery, state: FSMContext):
        await state.update_data(fight_sequence=random.sample(MOVES, 10), step=1, score=0)
        fight_data = await state.get_data()
        control, attack = fight_data["fight_sequence"][0]
        await callback.message.edit_text(
            f"<code>⚔️ Схватка 1 из 10</code>\n"
            f"🎯 Контроль: {control}\n"
            f"💥 Атака: {attack}\n"
            f"Выбери защиту:",
            parse_mode="HTML",
            reply_markup=get_fight_keyboard()
        )
        await callback.answer()

    @dp.callback_query(F.data.startswith("defense_"))
    async def process_defense(callback: CallbackQuery, state: FSMContext):
        defense = callback.data.replace("defense_", "")
        fight_data = await state.get_data()
        step = fight_data.get("step", 1)
        score = fight_data.get("score", 0)
        sequence = fight_data.get("fight_sequence", MOVES)
        control, attack = sequence[step-1]
        
        points, result, correct_defenses, log = await check_defense(control, attack, defense)
        score += points
        
        await callback.message.edit_text(
            f"<code>⚔️ Схватка {step} из 10</code>\n"
            f"🎯 Контроль: {control}\n"
            f"💥 Атака: {attack}\n"
            f"🛡️ Защита: {defense}\n"
            f"Результат: {result} (+{points} баллов)\n"
            f"💡 Подсказка: {', '.join(correct_defenses) or 'нет защиты'}\n\n"
            f"{log}",
            parse_mode="HTML"
        )
        
        if step >= 10:
            user_id = callback.from_user.id
            save_fight(user_id, "simple", score)
            await callback.message.reply_text(
                f"🏆 Бой завершён!\n"
                f"⭐ Баллы: {score}",
                parse_mode="HTML"
            )
            await state.clear()
        else:
            await state.update_data(step=step+1, score=score)
            control, attack = sequence[step]
            await callback.message.reply_text(
                f"<code>⚔️ Схватка {step+1} из 10</code>\n"
                f"🎯 Контроль: {control}\n"
                f"💥 Атака: {attack}\n"
                f"Выбери защиту:",
                parse_mode="HTML",
                reply_markup=get_fight_keyboard()
            )
        
        await callback.answer()

    @dp.callback_query(F.data == "hint")
    async def show_hint(callback: CallbackQuery, state: FSMContext):
        fight_data = await state.get_data()
        step = fight_data.get("step", 1)
        sequence = fight_data.get("fight_sequence", MOVES)
        control, attack = sequence[step-1]
        correct_defenses = [
            d for d, v in DEFENSE_MOVES.items()
            if control in v.get("control_defense", []) and attack in v.get("attack_defense", [])
        ]
        await callback.message.reply_text(
            f"💡 Подсказка: {', '.join(correct_defenses) or 'нет защиты'}",
            parse_mode="HTML"
        )
        await callback.answer()

    @dp.callback_query(F.data == "show_profile")
    async def show_profile(callback: CallbackQuery):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fighter_name, life, strength, agility, spirit, belt FROM users JOIN profiles ON users.user_id = profiles.user_id WHERE users.user_id = %s", (callback.from_user.id,))
            result = cursor.fetchone()
            if result:
                name, life, strength, agility, spirit, belt = result
                await callback.message.edit_text(
                    f"📊 <b>Твой профиль</b>\n"
                    f"Имя: {name}\n"
                    f"Жизнь: {life} ❤️\n"
                    f"Сила: {strength} 💪\n"
                    f"Ловкость: {agility} 🌀\n"
                    f"Дух: {spirit} ✨\n"
                    f"Пояс: {belt} 🟡",
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text("Профиль не найден!")
        except Exception as e:
            logger.error(f"Profile fetch failed: {e}")
            await callback.message.edit_text(f"Ошибка: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()
        await callback.answer()

    @dp.callback_query()
    async def debug_callback(callback: CallbackQuery):
        logger.info(f"Received callback: {callback.data} from {callback.from_user.id}")
        await callback.answer()
