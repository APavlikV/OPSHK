import random
from data import MOVES, DEFENSE_MOVES

def generate_fight_sequence():
    return random.sample(MOVES, len(MOVES))

def check_move(control, attack, chosen_defense):
    control_blocked = control == DEFENSE_MOVES[chosen_defense]["control"]
    attack_blocked = attack in DEFENSE_MOVES[chosen_defense]["attack_defense"]
    
    is_success = control_blocked and attack_blocked
    partial_success = control_blocked != attack_blocked
    
    correct_answer = None
    for defense, params in DEFENSE_MOVES.items():
        if control == params["control"] and attack in params["attack_defense"]:
            correct_answer = defense
            break
    
    return is_success, partial_success, correct_answer

def generate_short_log(step, control, attack, chosen_defense, is_success, partial_success, correct_answer):
    result = "<b>УСПЕХ</b> ✅" if is_success else "<b>ЧАСТИЧНЫЙ УСПЕХ</b> ⚠️" if partial_success else "<b>ПОРАЖЕНИЕ</b> ❌"
    text = (
        f"<u>⚔️ Схватка {step + 1}</u>\n\n"
        f"🎯 <i>Контроль:</i> <b>{control}</b>\n"
        f"💥 <i>Атака:</i> <b>{attack}</b>\n"
        f"🛡 <i>Защита:</i> <b>{chosen_defense}</b>\n\n"
        f"{result}"
    )
    if correct_answer and not is_success:
        text += f"\n💡 <i>Правильно:</i> <b>{correct_answer}</b>"
    return text

def generate_detailed_log(control, attack, chosen_defense, is_success):
    control_blocked = control == DEFENSE_MOVES[chosen_defense]["control"]
    attack_blocked = attack in DEFENSE_MOVES[chosen_defense]["attack_defense"]
    
    control_result = "✅ <b>Контроль отбит!</b>" if control_blocked else "❌ <b>Контроль не отбит!</b>"
    attack_result = "✅ <b>Атака заблокирована!</b>" if attack_blocked else "❌ <b>Атака пропущена!</b>"
    
    text = (
        f"<u>📝 Результат:</u>\n"
        f"{control_result}\n"
        f"{attack_result}"
    )
    if is_success:
        text += "\n\n🎉 <b>Превосходно!</b> Полная защита и контратака!"
    return text

def generate_final_stats(correct_count, control_count, hint_count, total_moves):
    correct_percent = (correct_count / total_moves) * 100
    control_percent = (control_count / total_moves) * 100
    
    text = (
        f"<b>🏆 Итоги боя:</b>\n"
        f"➖\n"
        f"🥋 <b>Полных побед:</b> {correct_count} из {total_moves} ({correct_percent:.0f}%)\n"
        f"🎯 <b>Контролей отбито:</b> {control_count} из {total_moves} ({control_percent:.0f}%)\n"
        f"💡 <b>Подсказок использовано:</b> {hint_count}"
    )
    return text
