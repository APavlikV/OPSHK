import random
from data import MOVES, DEFENSE_MOVES

def generate_fight_sequence():
    return random.sample(MOVES, len(MOVES))

def check_move(control, attack, chosen_defense):
    correct_answer = None
    for defense, info in DEFENSE_MOVES.items():
        if info["control"] == control and attack in info["attack_defense"]:
            correct_answer = defense
            break
    if not correct_answer:
        correct_answer = random.choice(list(DEFENSE_MOVES.keys()))
    is_success = chosen_defense == correct_answer
    partial_success = DEFENSE_MOVES[chosen_defense]["control"] == control
    return is_success, partial_success, correct_answer

def generate_short_log(step, control, attack, chosen_defense, is_success, partial_success, correct_answer):
    status = "✅ Полная защита!" if is_success else "🟡 Частичная защита" if partial_success else "❌ Нет защиты"
    return (
        f"<u>⚔️ Схватка {step + 1}</u>\n\n"
        f"🎯 <i>Контроль:</i> <b>{control}</b>\n"
        f"💥 <i>Атака:</i> <b>{attack}</b>\n"
        f"🛡️ <i>Ваша защита:</i> <b>{chosen_defense}</b>\n\n"
        f"{status}\n"
        f"<i>Правильно:</i> <b>{correct_answer}</b>"
    )

def generate_detailed_log(control, attack, chosen_defense, is_success):
    return (
        f"<i>Детали:</i>\n"
        f"- <b>{chosen_defense}</b> защищает от атак: {', '.join(DEFENSE_MOVES[chosen_defense]['attack_defense'])}\n"
        f"- Контроль: {DEFENSE_MOVES[chosen_defense]['control']}"
    )

def generate_final_stats(correct_count, control_count, hint_count, total_moves):
    return (
        f"<b>Статистика боя:</b>\n"
        f"- Полных защит: {correct_count}/{total_moves}\n"
        f"- Контролей: {control_count}/{total_moves}\n"
        f"- Подсказок: {hint_count}"
    )
