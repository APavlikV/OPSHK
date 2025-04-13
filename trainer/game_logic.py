import random
from trainer.data import DEFENSE_MOVES, CONTROL_PHRASES, ATTACK_PHRASES, DEFENSE_PHRASES

SUCCESS_PHRASES = ["УРА! Победа!", "Классный финт!", "Ты чемпион!", "Супер!"]
COUNTER_PHRASES = ["бьёт в ответ в", "наносит контратаку в", "завершает ударом в"]
FAIL_PHRASES = ["ОЙ! Мимо!", "АЙ! Не вышло...", "УПС! Промах!"]
BOT_WIN_PHRASES = ["добивает в", "побеждает ударом в", "завершает в"]

def check_move(control, attack, chosen_defense):
    if chosen_defense not in DEFENSE_MOVES:
        return False, False, []
    defense_data = DEFENSE_MOVES[chosen_defense]
    control_success = control in defense_data.get("control", [])
    attack_success = attack in defense_data.get("attack_defense", [])
    is_success = control_success and attack_success
    partial_success = control_success != attack_success
    correct_defenses = [
        move for move, data in DEFENSE_MOVES.items()
        if control in data.get("control", []) and attack in data.get("attack_defense", [])
    ]
    return is_success, partial_success, correct_defenses

def generate_detailed_log(control, attack, chosen_defense, is_success, nickname="Ник"):
    defense_data = DEFENSE_MOVES.get(chosen_defense, {})
    control_success = control in defense_data.get("control", [])
    attack_success = attack in defense_data.get("attack_defense", [])
    
    log = f"⚔️ Тори Бот Вася {random.choice(CONTROL_PHRASES.get(control, ['атакует']))} {'✅' if control_success else '❌'}, "
    log += f"{random.choice(ATTACK_PHRASES.get(attack, ['бьёт']))} {'✅' if attack_success else '❌'}\n"
    
    log += f"🛡️ Уке {nickname} {random.choice(DEFENSE_PHRASES.get(chosen_defense, ['блокирует']))}! "
    if is_success:
        counter_zone = random.choice(defense_data.get("counter", ["ДЗ"]))
        log += f"✅\n💥 ВЖУХ! {nickname} {random.choice(COUNTER_PHRASES)} {counter_zone}! {random.choice(SUCCESS_PHRASES)}"
    else:
        if control_success:
            log += f"Держит контроль! ✅ "
        else:
            log += f"Контроль проходит... ❌ "
        if attack_success:
            log += f"Атака заблокирована! ✅\n"
        else:
            log += f"Атака проходит... ❌\n"
            log += f"😓 {random.choice(FAIL_PHRASES)} "
        counter_zone = random.choice(["ДЗ", "СС", "ТР", "ГДН"])
        log += f"😈 КРАХ! Бот Вася {random.choice(BOT_WIN_PHRASES)} {counter_zone}! "
        
        correct_defenses = [
            move for move, data in DEFENSE_MOVES.items()
            if control in data.get("control", []) and attack in data.get("attack_defense", [])
        ]
        if correct_defenses:
            log += f"Правильный блок: {random.choice(correct_defenses)}."

    return log
