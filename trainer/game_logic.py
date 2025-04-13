import random

# Определяем ходы и защиты (пример структуры, подставь свою, если отличается)
DEFENSE_MOVES = {
    "Гедан барай": {"control": ["ДЗ", "СС", "ТР"], "attack_defense": ["ГДН"], "counter": ["ТР", "СС"]},
    "Учи уке": {"control": ["СС", "ТР"], "attack_defense": ["СС", "ТР"], "counter": ["ДЗ"]},
    "Сото уке": {"control": ["ТР"], "attack_defense": ["ТР", "СС"], "counter": ["ГДН"]},
    "Аге уке": {"control": ["ДЗ"], "attack_defense": ["ДЗ"], "counter": ["СС"]}
}

# Фразы
CONTROL_PHRASES = {
    "ДЗ": ["метит в голову", "целится в нос", "хочет захватить волосы", "проверяет чердак", "идёт за мозгами"],
    "СС": ["метит в печень", "целится в центр", "идёт за селезёнкой", "хочет пробить пузо", "нацеливается на котлетницу"],
    "ТР": ["метит в трахею", "хитро целится в грудь", "пытается взять за грудки", "идёт за сердцем", "целится в рёбра"]
}
ATTACK_PHRASES = {
    "ДЗ": ["бьёт в нос", "атакует челюсть", "наносит удар в голову", "залепил в нос", "пробил чердак", "настучал по макушке", "вмазал по мозгам"],
    "СС": ["бьёт в печень", "атакует селезёнку", "идёт в центр", "вмазал по кишкам", "залепил по котлетнице", "прописал по пузику", "дал по животному отсеку"],
    "ТР": ["бьёт в трахею", "атакует грудь", "целит в сердце", "зарядил в грудь", "пробил по грудине", "дал по сердцу"],
    "ГДН": ["бьёт по бубенчикам", "атакует живот", "ломает ноги", "зарядил по семейным драгоценностям", "прописал по зоне 18+", "врезал по нижнему этажу", "дал по нижнему регистру"]
}
DEFENSE_PHRASES = {
    "Гедан барай": ["ставит Гедан барай", "оформляет Гедан барай", "применяет Гедан барай", "закрывает Гедан барай", "бьёт Гедан барай"],
    "Учи уке": ["вкручивает Учи уке", "ставит Учи уке", "ловко использует Учи уке", "вертит Учи уке", "держит Учи уке"],
    "Сото уке": ["ставит Сото уке", "соображает Сото уке", "твёрдо держит Сото уке", "блокирует Сото уке", "выставляет Сото уке"],
    "Аге уке": ["подбрасывает Аге уке", "запечатлеет Аге уке", "выписывает Аге уке", "взлетает с Аге уке", "швыряет Аге уке"]
}
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
