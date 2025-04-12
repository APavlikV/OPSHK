import random
from data import MOVES, DEFENSE_MOVES

def generate_fight_sequence():
    return random.sample(MOVES, len(MOVES))

def check_move(control, attack, chosen_defense):
    defense = DEFENSE_MOVES[chosen_defense]
    control_blocked = control == defense["control"]
    attack_blocked = attack in defense["attack_defense"]
    
    is_success = control_blocked and attack_blocked
    partial_success = control_blocked != attack_blocked
    
    correct_answer = next(
        (move for move, data in DEFENSE_MOVES.items() if control == data["control"] and attack in data["attack_defense"]),
        chosen_defense
    )
    
    return is_success, partial_success, correct_answer

def generate_short_log(step, control, attack, chosen_defense, is_success, partial_success, correct_answer):
    result = "✅ УСПЕХ" if is_success else "⚠️ ЧАСТИЧНЫЙ УСПЕХ" if partial_success else "❌ ПОРАЖЕНИЕ"
    text = (
        f"<u>⚔️ Схватка {step + 1}</u>\n\n"
        f"🎯 <i>Контроль:</i> <b>{control}</b>\n"
        f"💥 <i>Атака:</i> <b>{attack}</b>\n"
        f"🛡 <i>Ваша защита:</i> <b>{chosen_defense}</b>\n\n"
        f"<b>{result}</b>"
    )
    if not is_success:
        text += f"\n💡 <i>Правильно:</i> <b>{correct_answer}</b>"
    return text

def generate_detailed_log(control, attack, chosen_defense, is_success):
    defense = DEFENSE_MOVES[chosen_defense]
    control_blocked = control == defense["control"]
    attack_blocked = attack in defense["attack_defense"]
    
    control_result = "✅ Отражён" if control_blocked else "❌ Пропущен"
    attack_result = "✅ Заблокирован" if attack_blocked else "❌ Пропущен"
    
    text = (
        f"<b>Детали:</b>\n"
        f"🎯 <i>Контроль ({control}):</i> <b>{control_result}</b>\n"
        f"💥 <i>Атака ({attack}):</i> <b>{attack_result}</b>"
    )
    
    if is_success:
        text += f"\n\n🔥 <b>Добивание успешно!</b>"
    return text

def generate_final_stats(correct_count, control_count, hint_count, total_moves):
    accuracy = (correct_count / total_moves) * 100 if total_moves > 0 else 0
    control_accuracy = (control_count / total_moves) * 100 if total_moves > 0 else 0
    
    text = (
        f"<b>📊 Статистика боя:</b>\n"
        f"✅ <i>Полные успехи:</i> <b>{correct_count}/{total_moves}</b> ({accuracy:.1f}%)\n"
        f"🎯 <i>Контроль отражён:</i> <b>{control_count}/{total_moves}</b> ({control_accuracy:.1f}%)\n"
        f"💡 <i>Подсказки:</i> <b>{hint_count}</b>"
    )
    
    if accuracy >= 80:
        text += f"\n\n🏆 <b>Отличный результат, мастер!</b>"
    elif accuracy >= 50:
        text += f"\n\n🥋 <b>Хорошая работа, продолжай тренироваться!</b>"
    else:
        text += f"\n\n💪 <b>Не сдавайся, практика делает мастера!</b>"
    
    return text
