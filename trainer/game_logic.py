import random
from data import MOVES, DEFENSE_MOVES, ATTACK_PHRASES, DEFENSE_PHRASES

def generate_fight_sequence():
    sequence = MOVES.copy()
    random.shuffle(sequence)
    return sequence

def check_move(control, attack, chosen_defense):
    defense_data = DEFENSE_MOVES.get(chosen_defense, {})
    control_success = control == defense_data.get("control")
    attack_success = attack in defense_data.get("attack_defense", [])
    is_success = control_success and attack_success
    partial_success = not control_success and attack_success
    correct_answer = next((move for move, data in DEFENSE_MOVES.items() if control == data["control"] and attack in data["attack_defense"]), None)
    return is_success, partial_success, correct_answer

def generate_short_log(step, control, attack, chosen_defense, is_success, partial_success, correct_answer):
    result_emoji = "🟢" if is_success else "🟠" if partial_success else "🔴"
    return (
        f"<code>⚔️ Схватка {step + 1}</code>\n\n"
        f"🎯 Контроль: <b>{control}</b>\n"
        f"💥 Атака: <b>{attack}</b>\n"
        f"Защита и контратака: <b>{chosen_defense}</b>\n"
        f"{result_emoji} <b>{'УСПЕХ' if is_success else 'ПОРАЖЕНИЕ'}</b>"
        + (f" (правильно: {correct_answer})" if not is_success and correct_answer else "")
    )

def generate_detailed_log(control, attack, chosen_defense, is_success):
    attacker_control_success = random.choice([True, False])
    attacker_attack_success = random.choice([True, False])
    defense_data = DEFENSE_MOVES.get(chosen_defense, {})
    counter_zone = random.choice(defense_data.get("counter", ["ДЗ"])) if is_success else random.choice(["ГДН", "СС", "ТР", "ДЗ"])
    
    attacker_name = "<b>Bot Вася</b>"
    attack_text = f"{attacker_name} {'яростно атаковал' if attacker_attack_success else 'недолго думая ринулся в атаку'}: " \
                  f"<i>{random.choice(ATTACK_PHRASES['control_success' if attacker_control_success else 'control_fail'][control])}</i> " \
                  f"<i>{random.choice(ATTACK_PHRASES['attack_success' if attacker_attack_success else 'attack_fail'][attack])}</i> ⚔️ "
    defense_text = f"{random.choice(DEFENSE_PHRASES['defense_success' if control == defense_data.get('control') else 'defense_fail'][control if control == defense_data.get('control') else random.choice(list(DEFENSE_PHRASES['defense_fail'].keys()))])} " \
                   f"{random.choice(DEFENSE_PHRASES['counter_success' if is_success else 'counter_fail'][chosen_defense])}"
    return f"{attack_text}{defense_text}"

def generate_final_stats(correct_count, control_count, hint_count, total):
    return (
        f"<b>Статистика боя:</b>\n\n"
        f"✅ <code>Правильных контр действий</code>: <b>{correct_count}</b>\n"
        f"💡 <code>С подсказкой</code>: <b>{hint_count}</b>\n"
        f"🛡️ <code>Отбито контролей</code>: <b>{control_count}</b>\n"
        f"❌ <code>Пропущено атак</code>: <b>{total - correct_count}</b>"
    )

def check_round(control, attack, defense):
    from data import MOVES, DEFENSE_MOVES
    result = {
        "control_success": False,
        "attack_success": False,
        "defense_control_success": False,
        "counter_success": False,
        "defense_attack_success": False
    }
    if (control, attack) in MOVES:
        result["control_success"] = True
        result["attack_success"] = True
    defense_data = DEFENSE_MOVES.get(defense, {})
    if defense_data.get("control") == control:
        result["defense_control_success"] = True
    if attack in defense_data.get("counter", []):
        result["counter_success"] = True
    if attack in defense_data.get("attack_defense", []):
        result["defense_attack_success"] = True
    return result

def get_hint(control, attack):
    correct_defense = next(
        (move for move, data in DEFENSE_MOVES.items() if control == data["control"] and attack in data["attack_defense"]),
        "Аге уке"  # Запасной вариант
    )
    return f"Попробуйте защиту: {correct_defense}"
