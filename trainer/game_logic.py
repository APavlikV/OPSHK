import random
from typing import Tuple
from .data import MOVES, DEFENSE_MOVES, CONTROL_PHRASES, ATTACK_PHRASES, DEFENSE_PHRASES

async def check_defense(control: str, attack: str, defense: str) -> Tuple[int, str, list, str]:
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
    
    result = "ЧИСТАЯ ПОБЕДА" if is_success else ("ЧАСТИЧНЫЙ УСПЕХ" if partial_success else "ПОРАЖЕНИЕ")
    
    control_phrase = random.choice(CONTROL_PHRASES.get(control, ["атакует"]))
    attack_phrase = random.choice(ATTACK_PHRASES.get(attack, ["бьёт"]))
    defense_phrase = random.choice(DEFENSE_PHRASES.get(defense, ["защищается"]))
    counterattack_zone = random.choice(defense_data.get("counterattack", ["неизвестно"]))
    
    if is_success:
        log = (
            f"⚔️ Тори {control_phrase} ({control}) ❌, "
            f"{attack_phrase} ({attack}) ❌\n"
            f"🛡️ Уке {defense_phrase} ({defense})! ✅\n"
            f"💥 ВЖУХ! Уке добивает в {counterattack_zone}!"
        )
    elif control_match:
        log = (
            f"⚔️ Тори {control_phrase} ({control}) ❌, "
            f"{attack_phrase} ({attack}) ✅\n"
            f"🛡️ Уке {defense_phrase} ({defense})! ✅ Контроль отбит!\n"
            f"💥 Уке контратакует в {counterattack_zone}!"
        )
    elif attack_match:
        log = (
            f"⚔️ Тори {control_phrase} ({control}) ✅, "
            f"{attack_phrase} ({attack}) ❌\n"
            f"🛡️ Уке {defense_phrase} ({defense})! ✅ Атака отбита!\n"
            f"💥 Уке держится!"
        )
    else:
        log = (
            f"⚔️ Тори {control_phrase} ({control}) ✅, "
            f"{attack_phrase} ({attack}) ✅\n"
            f"🛡️ Уке {defense_phrase} ({defense})! ❌\n"
            f"💥 КРАХ! Уке пропускает удар!"
        )
    
    return points, result, correct_defenses, log
