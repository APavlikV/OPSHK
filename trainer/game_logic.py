from trainer.data import DEFENSE_MOVES, CONTROL_PHRASES, ATTACK_PHRASES, DEFENSE_PHRASES
import random

def check_move(control, attack, defense):
    defense_data = DEFENSE_MOVES.get(defense, {})
    control_match = control in defense_data.get("control_defense", [])
    attack_match = attack in defense_data.get("attack_defense", [])
    
    is_success = control_match and attack_match
    partial_success = control_match or attack_match
    points = 3 if is_success else (1 if partial_success else 0)
    
    correct_defenses = [
        d for d, v in DEFENSE_MOVES.items()
        if control in v.get("control_defense", []) and attack in v.get("attack_defense", [])
    ]
    
    return is_success, partial_success, correct_defenses, points

def generate_detailed_log(control, attack, defense, is_success, nickname):
    control_phrase = random.choice(CONTROL_PHRASES.get(control, ["атакует"]))
    attack_phrase = random.choice(ATTACK_PHRASES.get(attack, ["бьёт"]))
    defense_phrase = random.choice(DEFENSE_PHRASES.get(defense, ["защищается"]))
    
    defense_data = DEFENSE_MOVES.get(defense, {})
    control_match = control in defense_data.get("control_defense", [])
    attack_match = attack in defense_data.get("attack_defense", [])
    
    counterattack_zone = random.choice(defense_data.get("counterattack", ["неизвестно"]))
    
    if is_success:
        return (
            f"⚔️ Тори Бот Вася {control_phrase} ({control}) ❌, "
            f"{attack_phrase} ({attack}) ❌\n"
            f"🛡️ Уке {nickname} {defense_phrase} ({defense})! ✅\n"
            f"💥 ВЖУХ! {nickname} добивает в {counterattack_zone}! ЧИСТАЯ ПОБЕДА!"
        )
    elif control_match:
        return (
            f"⚔️ Тори Бот Вася {control_phrase} ({control}) ❌, "
            f"{attack_phrase} ({attack}) ✅\n"
            f"🛡️ Уке {nickname} {defense_phrase} ({defense})! ✅ Контроль отбит!\n"
            f"💥 {nickname} контратакует в {counterattack_zone}! ЧАСТИЧНЫЙ УСПЕХ!"
        )
    elif attack_match:
        return (
            f"⚔️ Тори Бот Вася {control_phrase} ({control}) ✅, "
            f"{attack_phrase} ({attack}) ❌\n"
            f"🛡️ Уке {nickname} {defense_phrase} ({defense})! ✅ Атака отбита!\n"
            f"💥 {nickname} держится! ЧАСТИЧНЫЙ УСПЕХ!"
        )
    else:
        return (
            f"⚔️ Тори Бот Вася {control_phrase} ({control}) ✅, "
            f"{attack_phrase} ({attack}) ✅\n"
            f"🛡️ Уке {nickname} {defense_phrase} ({defense})! ❌\n"
            f"💥 КРАХ! {nickname} пропускает удар! ПОРАЖЕНИЕ!"
        )
