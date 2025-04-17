import logging
import random
import asyncio
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from .keyboards import get_nickname_keyboard
from .texts import (
    RULES_TEXT, TIPS_TEXT, START_FIGHT_PHRASES, TIMED_FIGHT_START_PHRASES, TIMED_FIGHT_END_PHRASES,
    TIMED_FIGHT_TIMEOUT_PHRASE, TIMED_FIGHT_TICK_PHRASES, CONTROL_SUCCESS_PHRASES, CONTROL_FAIL_PHRASES,
    ATTACK_SUCCESS_PHRASES, ATTACK_FAIL_PHRASES, DEFENSE_CONTROL_SUCCESS_PHRASES, DEFENSE_CONTROL_FAIL_PHRASES,
    DEFENSE_ATTACK_SUCCESS_PHRASES, DEFENSE_ATTACK_FAIL_PHRASES, DRAW_PHRASES
)
from .state import FightState
from .data import save_fighter, save_fight, get_db_connection, DEFENSE_MOVES, MOVES
from .game_logic import check_defense

logger = logging.getLogger(__name__)

def get_start_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Старт", callback_data="start_button")]])

def get_fight_keyboard(is_timed=False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Гедан барай", callback_data="defense_Гедан барай")],
        [InlineKeyboardButton(text="Аге уке", callback_data="defense_Аге уке")],
        [InlineKeyboardButton(text="Сото уке", callback_data="defense_Сото уке")],
        [InlineKeyboardButton(text="Учи уке", callback_data="defense_Учи уке")],
    ]
    if not is_timed:
        buttons.append([InlineKeyboardButton(text="💡 Подсказка", callback_data="hint")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Бой 🥊", callback_data="fight_menu")],
        [InlineKeyboardButton(text="Профиль 📊", callback_data="show_profile")]
    ])

def get_profile_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Бой 🥊", callback_data="fight_menu")],
        [InlineKeyboardButton(text="Сменить ник", callback_data="custom_nick")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ])

def get_fight_modes_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Простой бой", callback_data="simple_fight_menu")],
        [InlineKeyboardButton(text="Бой на время", callback_data="timed_fight")],
        [InlineKeyboardButton(text="PvP с ботом", callback_data="pvp_bot")],
        [InlineKeyboardButton(text="PvP Арена", callback_data="pvp_arena")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
    ])

def get_simple_fight_menu(exclude=None) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Правила", callback_data="show_rules")],
        [InlineKeyboardButton(text="Памятка", callback_data="show_tips")],
        [InlineKeyboardButton(text="Начать бой", callback_data="start_simple_fight")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_fight_modes")]
    ]
    if exclude:
        buttons = [b for b in buttons if b[0].text != exclude]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def clear_keyboard(bot, chat_id, message_id, fight_id):
    for _ in range(2):
        try:
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
            logger.info(f"Fight {fight_id}: Cleared keyboard for message {message_id}")
            return True
        except Exception as e:
            logger.warning(f"Fight {fight_id}: Failed to clear keyboard for message {message_id}: {e}")
            await asyncio.sleep(0.5)
    logger.error(f"Fight {fight_id}: Failed to clear keyboard for message {message_id} after retries")
    return False

async def timed_fight_timer(context: FSMContext, message: Message, user_id: int, step: int, fight_message: Message, fight_id: str):
    for seconds in range(4, -1, -1):
        user_data = await context.get_data()
        if user_data.get("fight_type") != "timed" or user_data.get("step") != step or not user_data.get("is_fighting"):
            logger.info(f"Fight {fight_id}: Timer stopped for step {step}")
            return
        tick_phrase = random.choice(TIMED_FIGHT_TICK_PHRASES).format(seconds=seconds)
        await fight_message.edit_text(
            f"⚔️ <code>Схватка {step}</code>\n\n"
            f"🎯 <i>Контроль</i>: <b>{user_data['current_move'][0]}</b>\n"
            f"💥 <i>Атака</i>: <b>{user_data['current_move'][1]}</b>\n\n"
            f"Выбери защиту ({seconds} сек):\n{tick_phrase}",
            parse_mode="HTML",
            reply_markup=get_fight_keyboard(is_timed=True)
        )
        await asyncio.sleep(1)
    user_data = await context.get_data()
    if user_data.get("fight_type") == "timed" and user_data.get("step") == step and user_data.get("is_fighting"):
        await context.update_data(is_fighting=False)
        stats = user_data.get("stats", {"wins": 0, "partial": 0, "losses": 0})
        score = user_data.get("score", 0)
        stats["losses"] += 1
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT fighter_name FROM users_dev WHERE user_id = %s", (user_id,))
        user_nick = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        save_fight(user_id, "timed", score)
        if await clear_keyboard(message.bot, message.chat.id, fight_message.message_id, fight_id):
            await message.answer(TIMED_FIGHT_TIMEOUT_PHRASE, parse_mode="HTML")
            end_phrase = random.choice(TIMED_FIGHT_END_PHRASES)
            await message.answer(
                f"🏆 <b>Бой на время завершён!</b>\n"
                f"🥋 {end_phrase}\n"
                f"⭐ <b>{user_nick}</b> набрал <code>Баллы: {score}</code>",
                parse_mode="HTML"
            )
            await message.answer(
                f"<code>Статистика боя</code>\n\n"
                f"<i>Схваток</i>: <b>{step}</b>\n"
                f"<i>Чистая победа</i>: <b>{stats['wins']}</b>\n"
                f"<i>Частичный успех</i>: <b>{stats['partial']}</b>\n"
                f"<i>Поражение</i>: <b>{stats['losses']}</b>",
                parse_mode="HTML",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer("Ошибка: не удалось завершить бой корректно.", reply_markup=get_main_menu())
        await context.clear()

def setup_handlers(dp: Dispatcher):
    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        await message.answer(
            f"🥋 <b>Добро пожаловать в КАРАТЭ тренажер!</b>\nНажми, чтобы начать:",
            parse_mode="HTML",
            reply_markup=get_start_button()
        )

    @dp.callback_query(F.data == "start_button")
    async def start_button(callback: CallbackQuery, state: FSMContext):
        username = callback.from_user.username or "Fighter"
        await callback.message.edit_text(
            f"🥋 <b>Добро пожаловать в КАРАТЭ тренажер!</b>\n"
            f"Использовать ваш <b>ник Telegram ({username})</b> или <b>выбрать свой</b>?",
            parse_mode="HTML",
            reply_markup=get_nickname_keyboard()
        )
        await callback.answer()

    @dp.message(Command("menu"))
    async def cmd_menu(message: Message):
        await message.answer("Главное меню:", reply_markup=get_main_menu())

    @dp.message(Command("profile"))
    async def cmd_profile(message: Message):
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT fighter_name, life, strength, agility, spirit, belt "
                "FROM users_dev JOIN profiles_dev ON users_dev.user_id = profiles_dev.user_id "
                "WHERE users_dev.user_id = %s",
                (message.from_user.id,)
            )
            result = cursor.fetchone()
            if result:
                name, life, strength, agility, spirit, belt = result
                await message.answer(
                    f"📊 <b>Твой профиль</b>\n"
                    f"Имя: <b>{name}</b>\nЖизнь: <b>{life}</b> ❤️\nСила: <b>{strength}</b> 💪\n"
                    f"Ловкость: <b>{agility}</b> 🌀\nДух: <b>{spirit}</b> ✨\nПояс: <b>{belt}</b> 🟡",
                    parse_mode="HTML",
                    reply_markup=get_profile_menu()
                )
            else:
                await message.answer("Профиль не найден!")
        except Exception as e:
            logger.error(f"Profile fetch failed: {e}")
            await message.answer(f"Ошибка: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    @dp.callback_query(F.data == "use_telegram_nick")
    async def use_telegram_nick(callback: CallbackQuery, state: FSMContext):
        username = callback.from_user.username or f"User{callback.from_user.id}"
        user_id = callback.from_user.id
        try:
            save_fighter(user_id, username)
            await callback.message.edit_text(
                f"Ник сохранён: <b>{username}</b>! Готов к бою? 💪",
                parse_mode="HTML",
                reply_markup=get_main_menu()
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
                reply_markup=get_main_menu()
            )
            await state.clear()
        except Exception as e:
            logger.error(f"Save fighter failed: {e}")
            await message.answer(f"Ошибка сохранения: {e}")
            await state.clear()

    @dp.callback_query(F.data == "fight_menu")
    async def fight_menu(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_text("Выберите режим боя:", reply_markup=get_fight_modes_menu())
        await callback.answer()

    @dp.callback_query(F.data == "simple_fight_menu")
    async def simple_fight_menu(callback: CallbackQuery):
        await callback.message.edit_text("Готовы начать простой бой!?", reply_markup=get_simple_fight_menu())
        await callback.answer()

    @dp.callback_query(F.data == "show_rules")
    async def show_rules(callback: CallbackQuery):
        await callback.message.edit_text(RULES_TEXT, parse_mode="HTML", reply_markup=get_simple_fight_menu(exclude="Правила"))
        await callback.answer()

    @dp.callback_query(F.data == "show_tips")
    async def show_tips(callback: CallbackQuery):
        await callback.message.edit_text(TIPS_TEXT, parse_mode="HTML", reply_markup=get_simple_fight_menu(exclude="Памятка"))
        await callback.answer()

    @dp.callback_query(F.data == "timed_fight")
    async def timed_fight(callback: CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        fight_id = f"{user_id}_{random.randint(1000, 9999)}"
        await state.update_data(
            fight_type="timed",
            is_fighting=True,
            is_processing=False,
            user_id=user_id,
            step=1,
            score=0,
            stats={"wins": 0, "partial": 0, "losses": 0},
            fight_sequence=random.sample(MOVES, 10),
            last_fight_message_id=None,
            fight_id=fight_id
        )
        start_phrase = random.choice(TIMED_FIGHT_START_PHRASES)
        await callback.message.edit_text(
            f"<b>Бой на время начался!</b>\n🥋 {start_phrase}",
            parse_mode="HTML"
        )
        fight_data = await state.get_data()
        control, attack = fight_data["fight_sequence"][0]
        await state.update_data(current_move=(control, attack))
        fight_message = await callback.message.answer(
            f"⚔️ <code>Схватка 1</code>\n\n"
            f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
            f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
            f"Выбери защиту (5 сек):",
            parse_mode="HTML",
            reply_markup=get_fight_keyboard(is_timed=True)
        )
        await state.update_data(last_fight_message_id=fight_message.message_id)
        asyncio.create_task(timed_fight_timer(state, callback.message, user_id, 1, fight_message, fight_id))
        await callback.answer()

    @dp.callback_query(F.data == "pvp_bot")
    async def pvp_bot(callback: CallbackQuery):
        await callback.message.edit_text(
            "PvP с ботом пока в разработке! Скоро будет доступен.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="fight_menu")]])
        )
        await callback.answer()

    @dp.callback_query(F.data == "pvp_arena")
    async def pvp_arena(callback: CallbackQuery):
        await callback.message.edit_text(
            "PvP Арена пока в разработке! Скоро будет доступна.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="fight_menu")]])
        )
        await callback.answer()

    @dp.callback_query(F.data == "back_to_main")
    async def back_to_main(callback: CallbackQuery):
        await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu())
        await callback.answer()

    @dp.callback_query(F.data == "back_to_fight_modes")
    async def back_to_fight_modes(callback: CallbackQuery):
        await callback.message.edit_text("Выберите режим боя:", reply_markup=get_fight_modes_menu())
        await callback.answer()

    @dp.callback_query(F.data == "start_simple_fight")
    async def start_simple_fight(callback: CallbackQuery, state: FSMContext):
        fight_id = f"{callback.from_user.id}_{random.randint(1000, 9999)}"
        await state.update_data(
            fight_sequence=random.sample(MOVES, 10),
            fight_type="simple",
            step=1,
            score=0,
            stats={"wins": 0, "partial": 0, "losses": 0, "hints": 0},
            last_fight_message_id=None,
            is_processing=False,
            fight_id=fight_id
        )
        fight_data = await state.get_data()
        control, attack = fight_data["fight_sequence"][0]
        start_phrase = random.choice(START_FIGHT_PHRASES)
        await callback.message.edit_text(
            f"<b>Бой начался!</b>\n🥋 {start_phrase}",
            parse_mode="HTML"
        )
        fight_message = await callback.message.answer(
            f"⚔️ <code>Схватка 1 из 10</code>\n\n"
            f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
            f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
            f"Выбери защиту:",
            parse_mode="HTML",
            reply_markup=get_fight_keyboard()
        )
        await state.update_data(last_fight_message_id=fight_message.message_id)
        await callback.answer()

    @dp.callback_query(F.data.startswith("defense_"))
    async def process_defense(callback: CallbackQuery, state: FSMContext):
        fight_data = await state.get_data()
        fight_id = fight_data.get("fight_id", "unknown")
        if fight_data.get("is_processing"):
            logger.info(f"Fight {fight_id}: Ignored duplicate callback from user {callback.from_user.id}")
            await callback.answer()
            return
        await state.update_data(is_processing=True)
        try:
            defense = callback.data.replace("defense_", "")
            fight_type = fight_data.get("fight_type", "simple")
            step = fight_data.get("step", 1)
            score = fight_data.get("score", 0)
            stats = fight_data.get("stats", {"wins": 0, "partial": 0, "losses": 0, "hints": 0})
            is_fighting = fight_data.get("is_fighting", True)
            last_fight_message_id = fight_data.get("last_fight_message_id")

            if not is_fighting:
                await callback.message.edit_text("Бой завершён!")
                await callback.answer()
                return

            sequence = fight_data.get("fight_sequence", MOVES)
            control, attack = sequence[step-1]

            points, result, correct_defenses, log = await check_defense(control, attack, defense)
            score += points
            if points == 3:
                stats["wins"] += 1
            elif points == 1:
                stats["partial"] += 1
            else:
                stats["losses"] += 1

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fighter_name FROM users_dev WHERE user_id = %s", (callback.from_user.id,))
            user_nick = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            bot_nick = "Бот Вася"
            control_success = control in DEFENSE_MOVES.get(defense, {}).get("control_defense", [])
            attack_success = attack in DEFENSE_MOVES.get(defense, {}).get("attack_defense", [])

            target_map = {"ДЗ": "голову", "ТР": "грудь", "СС": "живот"}
            control_phrase = random.choice(
                CONTROL_FAIL_PHRASES[control] if control_success else CONTROL_SUCCESS_PHRASES[control]
            ).format(nick=bot_nick, target=target_map.get(control, control))

            defense_control_phrase = random.choice(
                DEFENSE_CONTROL_SUCCESS_PHRASES[control] if control_success else DEFENSE_CONTROL_FAIL_PHRASES[control]
            ).format(nick=user_nick, target=target_map.get(control, control))

            attack_target_map = {"ДЗ": "лоб", "ТР": "грудь", "СС": "живот", "ГДН": "ноги"}
            attack_phrase = random.choice(
                ATTACK_FAIL_PHRASES[attack] if attack_success else ATTACK_SUCCESS_PHRASES[attack]
            ).format(nick=bot_nick, target=attack_target_map.get(attack, attack))

            defense_attack_phrase = random.choice(
                DEFENSE_ATTACK_SUCCESS_PHRASES[attack] if attack_success else DEFENSE_ATTACK_FAIL_PHRASES[attack]
            ).format(nick=user_nick, target=attack_target_map.get(attack, attack))

            log_message = (
                f"⚔️ {control_phrase} {'✅' if not control_success else '❌'}\n"
                f"🛡️ {defense_control_phrase} {'✅' if control_success else '❌'}\n"
                f"💥 {attack_phrase} {'✅' if not attack_success else '❌'}\n"
                f"🛡️ {defense_attack_phrase} {'✅' if attack_success else '❌'}"
            ).strip()

            await callback.message.edit_text(
                f"⚔️ <code>Схватка {step}</code>\n\n"
                f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
                f"💥 <i>Атака</i>: <b>{attack}</b>\n"
                f"🛡️ <i>Защита</i>: <b>{defense}</b>\n\n"
                f"<i>Результат</i>: <b>{result}</b> (<b>+{points} баллов</b>)",
                parse_mode="HTML"
            )
            await callback.message.answer(log_message, parse_mode="HTML")

            # Очистка клавиатуры текущей схватки
            if last_fight_message_id:
                if not await clear_keyboard(callback.message.bot, callback.message.chat.id, last_fight_message_id, fight_id):
                    logger.error(f"Fight {fight_id}: Failed to proceed due to keyboard cleanup error")
                    await callback.message.answer("Ошибка: не удалось очистить клавиатуру.", reply_markup=get_main_menu())
                    await state.clear()
                    await callback.answer()
                    return

            if fight_type == "simple" and step >= 10 or fight_type == "timed" and step >= 10:
                user_id = callback.from_user.id
                save_fight(user_id, fight_type, score)
                await callback.message.answer(
                    f"🏆 <b>Бой завершён!</b>\n\n"
                    f"⭐ <b>{user_nick}</b> набрал <code>Баллы: {score}</code>",
                    parse_mode="HTML"
                )
                draw_phrase = random.choice(DRAW_PHRASES) if score == 0 else ""
                if fight_type == "simple":
                    await callback.message.answer(
                        f"<code>Статистика боя</code>\n\n"
                        f"<i>Чистая победа</i>: <b>{stats['wins']}</b>\n"
                        f"<i>Частичный успех</i>: <b>{stats['partial']}</b>\n"
                        f"<i>Поражение</i>: <b>{stats['losses']}</b>\n"
                        f"<i>Подсказок</i>: <b>{stats['hints']}</b>\n\n"
                        f"{draw_phrase}",
                        parse_mode="HTML",
                        reply_markup=get_main_menu()
                    )
                else:
                    await callback.message.answer(
                        f"<code>Статистика боя</code>\n\n"
                        f"<i>Схваток</i>: <b>{step}</b>\n"
                        f"<i>Чистая победа</i>: <b>{stats['wins']}</b>\n"
                        f"<i>Частичный успех</i>: <b>{stats['partial']}</b>\n"
                        f"<i>Поражение</i>: <b>{stats['losses']}</b>\n\n"
                        f"{draw_phrase}",
                        parse_mode="HTML",
                        reply_markup=get_main_menu()
                    )
                await state.clear()
            elif fight_type == "timed":
                step += 1
                await state.update_data(step=step, score=score, stats=stats, is_fighting=True)
                control, attack = sequence[step-1]
                await state.update_data(current_move=(control, attack))
                fight_message = await callback.message.answer(
                    f"⚔️ <code>Схватка {step}</code>\n\n"
                    f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
                    f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
                    f"Выбери защиту (5 сек):",
                    parse_mode="HTML",
                    reply_markup=get_fight_keyboard(is_timed=True)
                )
                await state.update_data(last_fight_message_id=fight_message.message_id)
                asyncio.create_task(timed_fight_timer(state, callback.message, callback.from_user.id, step, fight_message, fight_id))
            else:
                step += 1
                await state.update_data(step=step, score=score, stats=stats)
                control, attack = sequence[step-1]
                fight_message = await callback.message.answer(
                    f"⚔️ <code>Схватка {step} из 10</code>\n\n"
                    f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
                    f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
                    f"Выбери защиту:",
                    parse_mode="HTML",
                    reply_markup=get_fight_keyboard()
                )
                await state.update_data(last_fight_message_id=fight_message.message_id)
        finally:
            await state.update_data(is_processing=False)
        await callback.answer()

    @dp.callback_query(F.data == "hint")
    async def show_hint(callback: CallbackQuery, state: FSMContext):
        fight_data = await state.get_data()
        fight_id = fight_data.get("fight_id", "unknown")
        if fight_data.get("is_processing"):
            logger.info(f"Fight {fight_id}: Ignored duplicate hint callback from user {callback.from_user.id}")
            await callback.answer()
            return
        await state.update_data(is_processing=True)
        try:
            fight_type = fight_data.get("fight_type", "simple")
            step = fight_data.get("step", 1)
            stats = fight_data.get("stats", {"wins": 0, "partial": 0, "losses": 0, "hints": 0})
            last_fight_message_id = fight_data.get("last_fight_message_id")
            if fight_type != "simple":
                await callback.message.edit_text("Подсказки недоступны в этом режиме!")
                await callback.answer()
                return
            stats["hints"] += 1
            await state.update_data(stats=stats)
            sequence = fight_data.get("fight_sequence", MOVES)
            control, attack = sequence[step-1]
            correct_defenses = [
                d for d, v in DEFENSE_MOVES.items()
                if control in v.get("control_defense", []) and attack in v.get("attack_defense", [])
            ]
            await callback.message.edit_text(
                f"⚔️ <code>Схватка {step} из 10</code>\n\n"
                f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
                f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
                f"💡 <i>Подсказка</i>: <b>{', '.join(correct_defenses) or 'нет защиты'}</b>\n\n"
                f"Выбери защиту:",
                parse_mode="HTML",
                reply_markup=get_fight_keyboard()
            )
            if last_fight_message_id:
                if not await clear_keyboard(callback.message.bot, callback.message.chat.id, last_fight_message_id, fight_id):
                    await callback.message.answer("Ошибка: не удалось очистить клавиатуру.", reply_markup=get_main_menu())
                    await state.clear()
                    await callback.answer()
                    return
        finally:
            await state.update_data(is_processing=False)
        await callback.answer()

    @dp.callback_query(F.data == "show_profile")
    async def show_profile(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_text("📊 Загружаю профиль...", parse_mode="HTML")
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT fighter_name, life, strength, agility, spirit, belt "
                "FROM users_dev JOIN profiles_dev ON users_dev.user_id = profiles_dev.user_id "
                "WHERE users_dev.user_id = %s",
                (callback.from_user.id,)
            )
            result = cursor.fetchone()
            if result:
                name, life, strength, agility, spirit, belt = result
                await callback.message.edit_text(
                    f"📊 <b>Твой профиль</b>\n"
                    f"Имя: <b>{name}</b>\nЖизнь: <b>{life}</b> ❤️\nСила: <b>{strength}</b> 💪\n"
                    f"Ловкость: <b>{agility}</b> 🌀\nДух: <b>{spirit}</b> ✨\nПояс: <b>{belt}</b> 🟡",
                    parse_mode="HTML",
                    reply_markup=get_profile_menu()
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
