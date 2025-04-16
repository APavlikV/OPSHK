import logging
import random
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from .keyboards import get_nickname_keyboard
from .texts import (
    RULES_TEXT, TIPS_TEXT, START_FIGHT_PHRASES,
    CONTROL_SUCCESS_PHRASES, CONTROL_FAIL_PHRASES,
    ATTACK_SUCCESS_PHRASES, ATTACK_FAIL_PHRASES,
    DEFENSE_CONTROL_SUCCESS_PHRASES, DEFENSE_CONTROL_FAIL_PHRASES,
    DEFENSE_ATTACK_SUCCESS_PHRASES, DEFENSE_ATTACK_FAIL_PHRASES,
    DRAW_PHRASES
)
from .state import FightState
from .data import save_fighter, save_fight, get_db_connection, DEFENSE_MOVES, MOVES
from .game_logic import check_defense

logger = logging.getLogger(__name__)

BOT_NAMES = ["Бот Вася", "Бот Сэнсэй", "Бот Каратист", "Бот Татами", "Бот Кимоно"]

def get_fight_keyboard(show_hint=False, control=None, attack=None) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Гедан барай", callback_data="defense_Гедан барай")],
        [InlineKeyboardButton(text="Аге уке", callback_data="defense_Аге уке")],
        [InlineKeyboardButton(text="Сото уке", callback_data="defense_Сото уке")],
        [InlineKeyboardButton(text="Учи уке", callback_data="defense_Учи уке")],
    ]
    if not show_hint:
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

def setup_handlers(dp: Dispatcher):
    @dp.message(Command("start", "menu"))
    async def cmd_start(message: Message):
        username = message.from_user.username or "PAndrew"
        await message.answer(
            f"🥋 <b>Добро пожаловать в КАРАТЭ тренажер!</b>\n"
            f"Использовать ваш <b>ник Telegram ({username})</b> или <b>выбрать свой</b>?",
            parse_mode="HTML",
            reply_markup=get_nickname_keyboard()
        )

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
                    f"Имя: <b>{name}</b>\n"
                    f"Жизнь: <b>{life}</b> ❤️\n"
                    f"Сила: <b>{strength}</b> 💪\n"
                    f"Ловкость: <b>{agility}</b> 🌀\n"
                    f"Дух: <b>{spirit}</b> ✨\n"
                    f"Пояс: <b>{belt}</b> 🟡",
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
    async def fight_menu(callback: CallbackQuery):
        await callback.message.edit_text(
            "Выберите режим боя:",
            reply_markup=get_fight_modes_menu()
        )
        await callback.answer()

    @dp.callback_query(F.data == "simple_fight_menu")
    async def simple_fight_menu(callback: CallbackQuery):
        await callback.message.edit_text(
            "Готовы начать простой бой!?",
            reply_markup=get_simple_fight_menu()
        )
        await callback.answer()

    @dp.callback_query(F.data == "show_rules")
    async def show_rules(callback: CallbackQuery):
        await callback.message.edit_text(
            RULES_TEXT,
            parse_mode="HTML",
            reply_markup=get_simple_fight_menu(exclude="Правила")
        )
        await callback.answer()

    @dp.callback_query(F.data == "show_tips")
    async def show_tips(callback: CallbackQuery):
        await callback.message.edit_text(
            TIPS_TEXT,
            parse_mode="HTML",
            reply_markup=get_simple_fight_menu(exclude="Памятка")
        )
        await callback.answer()

    @dp.callback_query(F.data == "timed_fight")
    async def timed_fight(callback: CallbackQuery):
        await callback.message.edit_text(
            "Бой на время пока в разработке! Скоро будет доступен.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="fight_menu")]
            ])
        )
        await callback.answer()

    @dp.callback_query(F.data == "pvp_bot")
    async def pvp_bot(callback: CallbackQuery):
        await callback.message.edit_text(
            "PvP с ботом пока в разработке! Скоро будет доступен.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="fight_menu")]
            ])
        )
        await callback.answer()

    @dp.callback_query(F.data == "pvp_arena")
    async def pvp_arena(callback: CallbackQuery):
        await callback.message.edit_text(
            "PvP Арена пока в разработке! Скоро будет доступна.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Назад", callback_data="fight_menu")]
            ])
        )
        await callback.answer()

    @dp.callback_query(F.data == "back_to_main")
    async def back_to_main(callback: CallbackQuery):
        await callback.message.edit_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )
        await callback.answer()

    @dp.callback_query(F.data == "back_to_fight_modes")
    async def back_to_fight_modes(callback: CallbackQuery):
        await callback.message.edit_text(
            "Выберите режим боя:",
            reply_markup=get_fight_modes_menu()
        )
        await callback.answer()

    @dp.callback_query(F.data == "start_simple_fight")
    async def start_simple_fight(callback: CallbackQuery, state: FSMContext):
        await state.update_data(
            fight_sequence=random.sample(MOVES, 10),
            step=1,
            score=0,
            stats={"wins": 0, "partial": 0, "losses": 0, "hints": 0}
        )
        fight_data = await state.get_data()
        control, attack = fight_data["fight_sequence"][0]
        start_phrase = random.choice(START_FIGHT_PHRASES)
        await callback.message.edit_text(
            f"<b>Бой начался!</b>\n"
            f"🥋 {start_phrase}",
            parse_mode="HTML"
        )
        await callback.message.answer(
            f"⚔️ <code>Схватка 1 из 10</code>\n\n"
            f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
            f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
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
        stats = fight_data.get("stats", {"wins": 0, "partial": 0, "losses": 0, "hints": 0})
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
        cursor.execute(
            "SELECT fighter_name FROM users_dev WHERE user_id = %s",
            (callback.from_user.id,)
        )
        user_nick = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        # Логика логов
        bot_nick = random.choice(BOT_NAMES)
        control_success = control in DEFENSE_MOVES.get(defense, {}).get("control_defense", [])
        attack_success = attack in DEFENSE_MOVES.get(defense, {}).get("attack_defense", [])

        # Контроль
        target_map = {"ДЗ": "голову", "ТР": "грудь", "СС": "живот"}
        control_phrase = random.choice(
            CONTROL_FAIL_PHRASES[control] if control_success else CONTROL_SUCCESS_PHRASES[control]
        ).format(nick=bot_nick, target=target_map.get(control, control))

        # Защита контроля
        defense_control_phrase = random.choice(
            DEFENSE_CONTROL_SUCCESS_PHRASES[control] if control_success else DEFENSE_CONTROL_FAIL_PHRASES[control]
        ).format(nick=user_nick, target=target_map.get(control, control))

        # Атака
        attack_target_map = {"ДЗ": "лоб", "ТР": "грудь", "СС": "живот", "ГДН": "ноги"}
        attack_phrase = random.choice(
            ATTACK_FAIL_PHRASES[attack] if attack_success else ATTACK_SUCCESS_PHRASES[attack]
        ).format(nick=bot_nick, target=attack_target_map.get(attack, attack))

        # Защита атаки
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
            f"⚔️ <code>Схватка {step} из 10</code>\n\n"
            f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
            f"💥 <i>Атака</i>: <b>{attack}</b>\n"
            f"🛡️ <i>Защита</i>: <b>{defense}</b>\n\n"
            f"<i>Результат</i>: <b>{result}</b> (<b>+{points} баллов</b>)",
            parse_mode="HTML"
        )
        await callback.message.answer(log_message, parse_mode="HTML")

        if step >= 10:
            user_id = callback.from_user.id
            save_fight(user_id, "simple", score)
            await callback.message.answer(
                f"🏆 <b>Бой завершён!</b>\n\n"
                f"⭐ <b>{user_nick}</b> набрал <code>Баллы: {score}</code>",
                parse_mode="HTML"
            )
            draw_phrase = random.choice(DRAW_PHRASES) if score == 0 else ""
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
            await state.clear()
        else:
            await state.update_data(step=step+1, score=score, stats=stats)
            control, attack = sequence[step]
            await callback.message.answer(
                f"⚔️ <code>Схватка {step+1} из 10</code>\n\n"
                f"🎯 <i>Контроль</i>: <b>{control}</b>\n"
                f"💥 <i>Атака</i>: <b>{attack}</b>\n\n"
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
        stats = fight_data.get("stats", {"wins": 0, "partial": 0, "losses": 0, "hints": 0})
        stats["hints"] += 1
        await state.update_data(stats=stats)
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
            reply_markup=get_fight_keyboard(show_hint=True, control=control, attack=attack)
        )
        await callback.answer()

    @dp.callback_query(F.data == "show_profile")
    async def show_profile(callback: CallbackQuery):
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
                    f"Имя: <b>{name}</b>\n"
                    f"Жизнь: <b>{life}</b> ❤️\n"
                    f"Сила: <b>{strength}</b> 💪\n"
                    f"Ловкость: <b>{agility}</b> 🌀\n"
                    f"Дух: <b>{spirit}</b> ✨\n"
                    f"Пояс: <b>{belt}</b> 🟡",
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
