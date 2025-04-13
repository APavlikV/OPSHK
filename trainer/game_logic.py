import random
from data import MOVES, DEFENSE_MOVES, ATTACK_PHRASES, DEFENSE_PHRASES
from texts import TEXTS

def generate_fight_sequence():
    """Генерирует последовательность ходов для тренировочного боя."""
    if not MOVES:
        raise ValueError("MOVES is empty")
    return random.sample(MOVES, len(MOVES))

def check_move(control, attack, chosen_defense):
    """
    Проверяет, успешна ли защита против контроля и атаки.
    Возвращает (is_success, partial_success, correct_answer).
    """
    if chosen_defense not in DEFENSE_MOVES:
        return False, False, None
    defense_data = DEFENSE_MOVES[chosen_defense]
    control_success = control in defense_data.get("control", [])
    attack_success = attack in defense_data.get("attack_defense", [])
    is_success = control_success and attack_success
    partial_success = control_success != attack_success

    correct_answer = next(
        (
            move
            for move, data in DEFENSE_MOVES.items()
            if control in data.get("control", []) and attack in data.get("attack_defense", [])
        ),
        None,
    )

    return is_success, partial_success, correct_answer

def generate_short_log(step, control, attack, chosen_defense, is_success, partial_success, correct_answer):
    """Генерирует краткий лог схватки."""
    result = "✅ ЧИСТАЯ ПОБЕДА" if is_success else "⚠️ ЧАСТИЧНЫЙ УСПЕХ" if partial_success else "❌ ПОРАЖЕНИЕ"
    log = (
        f"<u>⚔️ Схватка {step + 1}</u>\n\n"
        f"🎯 <i>Контроль:</i> <b>{control}</b>\n"
        f"💥 <i>Атака:</i> <b>{attack}</b>\n"
        f"🛡️ <i>Защита:</i> <b>{chosen_defense}</b>\n\n"
        f"<b>{result}</b>"
    )
    if not is_success:
        log += f"\n<i>Правильно:</i> 🛡 <b>{correct_answer or 'Нет ответа'}</b>"
    return log

def generate_detailed_log(control, attack, chosen_defense, is_success):
    """Генерирует подробный лог схватки."""
    defense_data = DEFENSE_MOVES.get(chosen_defense, {})
    control_success = control in defense_data.get("control", [])
    attack_success = attack in defense_data.get("attack_defense", [])

    attack_phrase = random.choice(ATTACK_PHRASES.get(attack, ["Неизвестная атака"]))
    defense_phrase = random.choice(DEFENSE_PHRASES.get(chosen_defense, ["Неизвестная защита"]))

    log = f"{attack_phrase}\n"
    log += f"🛡️ Вы: {defense_phrase}\n"

    if is_success:
        counter_zone = random.choice(defense_data.get("counter", ["ДЗ"]))
        log += f"✅ <b>ЧИСТАЯ ПОБЕДА:</b> Полный блок! Контратака в <b>{counter_zone}</b>!"
    else:
        if control_success:
            log += "✅ <b>Контроль отбит!</b> "
        else:
            log += "❌ <b>Контроль прошёл!</b> "
        if attack_success:
            log += "Атака заблокирована! "
        else:
            log += "Атака достигла цели! "
        counter_zone = random.choice(["ГДН", "СС", "ТР", "ДЗ"])
        log += f"Добивание в <b>{counter_zone}</b>."

    return log

def generate_final_stats(correct_count, control_count, hint_count, total_steps):
    """Генерирует финальную статистику тренировочного боя."""
    stats = f"<b>📊 Статистика боя:</b>\n"
    stats += f"✅ Чистых побед: <b>{correct_count}</b> из {total_steps}\n"
    stats += f"🎯 Контролей отбито: <b>{control_count}</b> из {total_steps}\n"
    stats += f"💡 Подсказок использовано: <b>{hint_count}</b>\n"
    return stats

def calculate_pvp_scores(player_control, player_attack, player_defense, bot_control, bot_attack, bot_defense):
    """Рассчитывает очки для PvP схватки."""
    player_score_delta = 0
    bot_score_delta = 0

    # Игрок атакует, бот защищается
    player_control_success = player_control not in DEFENSE_MOVES.get(bot_defense, {}).get("control", [])
    player_attack_success = player_attack not in DEFENSE_MOVES.get(bot_defense, {}).get("attack_defense", [])
    bot_control_defense_success = not player_control_success
    bot_attack_defense_success = not player_attack_success
    bot_dobivanie = bot_control_defense_success and bot_attack_defense_success

    if player_control_success:
        player_score_delta += 1
    if player_attack_success:
        player_score_delta += (2 if player_control_success else 1)
    if bot_control_defense_success:
        bot_score_delta += 1
    if bot_dobivanie:
        bot_score_delta += 2
    elif bot_attack_defense_success:
        bot_score_delta += 1

    # Бот атакует, игрок защищается
    bot_control_success = bot_control not in DEFENSE_MOVES.get(player_defense, {}).get("control", [])
    bot_attack_success = bot_attack not in DEFENSE_MOVES.get(player_defense, {}).get("attack_defense", [])
    player_control_defense_success = not bot_control_success
    player_attack_defense_success = not bot_attack_success
    player_dobivanie = player_control_defense_success and player_attack_defense_success

    if bot_control_success:
        bot_score_delta += 1
    if bot_attack_success:
        bot_score_delta += (2 if bot_control_success else 1)
    if player_control_defense_success:
        player_score_delta += 1
    if player_dobivanie:
        player_score_delta += 2
    elif player_attack_defense_success:
        player_score_delta += 1

    return player_score_delta, bot_score_delta

def generate_pvp_log(step, player_name, player_control, player_attack, player_defense, bot_control, bot_attack, bot_defense, player_score, bot_score):
    """Форматирует лог PvP схватки."""
    player_control_success = player_control not in DEFENSE_MOVES.get(bot_defense, {}).get("control", [])
    player_attack_success = player_attack not in DEFENSE_MOVES.get(bot_defense, {}).get("attack_defense", [])
    bot_control_defense_success = not player_control_success
    bot_attack_defense_success = not player_attack_success
    bot_dobivanie = bot_control_defense_success and bot_attack_defense_success

    bot_control_success = bot_control not in DEFENSE_MOVES.get(player_defense, {}).get("control", [])
    bot_attack_success = bot_attack not in DEFENSE_MOVES.get(player_defense, {}).get("attack_defense", [])
    player_control_defense_success = not bot_control_success
    player_attack_defense_success = not bot_attack_success
    player_dobivanie = player_control_defense_success and player_attack_defense_success

    return TEXTS["pvp_log_template"].format(
        step=step,
        player_name=player_name,
        player_control=player_control,
        player_control_result="✅" if player_control_success else "❌",
        player_control_points=1 if player_control_success else 0,
        player_attack=player_attack,
        player_attack_result="✅" if player_attack_success else "❌",
        player_attack_points=2 if player_control_success and player_attack_success else 1 if player_attack_success else 0,
        bot_defense=bot_defense,
        bot_control_defense_result="✅" if bot_control_defense_success else "❌",
        bot_control_defense_points=1 if bot_control_defense_success else 0,
        bot_dobivanie_result="✅" if bot_dobivanie else "❌",
        bot_dobivanie_points=2 if bot_dobivanie else 1 if bot_attack_defense_success else 0,
        bot_control=bot_control,
        bot_control_result="✅" if bot_control_success else "❌",
        bot_control_points=1 if bot_control_success else 0,
        bot_attack=bot_attack,
        bot_attack_result="✅" if bot_attack_success else "❌",
        bot_attack_points=2 if bot_control_success and bot_attack_success else 1 if bot_attack_success else 0,
        player_defense=player_defense,
        player_control_defense_result="✅" if player_control_defense_success else "❌",
        player_control_defense_points=1 if player_control_defense_success else 0,
        player_dobivanie_result="✅" if player_dobivanie else "❌",
        player_dobivanie_points=2 if player_dobivanie else 1 if player_attack_defense_success else 0,
        player_score=player_score,
        bot_score=bot_score
    )
