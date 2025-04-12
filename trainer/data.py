MOVES = [
    ("СС", "ДЗ"), ("СС", "ТР"), ("СС", "ГДН"),
    ("ТР", "ДЗ"), ("ТР", "СС"), ("ТР", "ГДН"),
    ("ДЗ", "ТР"), ("ДЗ", "СС"), ("ДЗ", "ГДН")
]

DEFENSE_MOVES = {
    "Аге уке": {
        "control": "СС",
        "attack_defense": ["ДЗ", "ТР"],
        "counter": ["ДЗ"]
    },
    "Учи уке": {
        "control": "СС",
        "attack_defense": ["ДЗ", "ТР"],
        "counter": ["ДЗ", "ТР", "СС"]
    },
    "Сото уке": {
        "control": "ТР",
        "attack_defense": ["ДЗ", "СС"],
        "counter": ["ДЗ", "ТР", "СС"]
    },
    "Гедан барай": {
        "control": "ДЗ",
        "attack_defense": ["ТР", "СС"],
        "counter": ["ТР", "СС", "ГДН"]
    }
}

ATTACK_PHRASES = {
    "control_success": {
        "СС": ["захватил вас за грудь", "держит вас за солнечное сплетение"],
        "ТР": ["схватил вас за шею", "контролирует вашу трахею"],
        "ДЗ": ["держит вас за голову", "сдавил вам виски"]
    },
    "control_fail": {
        "СС": ["пытался схватить за грудь", "промахнулся по солнечному сплетению"],
        "ТР": ["целился в шею, но промахнулся", "не дотянулся до трахеи"],
        "ДЗ": ["пытался схватить голову", "не смог удержать вас за голову"]
    },
    "attack_success": {
        "ДЗ": ["нанёс удар в голову", "попал вам в висок"],
        "ТР": ["ударил в горло", "попал в трахею"],
        "СС": ["пробил в солнечное сплетение", "ударил в грудь"],
        "ГДН": ["нанёс удар ниже пояса", "попал в бедро"]
    },
    "attack_fail": {
        "ДЗ": ["промахнулся по голове", "удар в голову не прошёл"],
        "ТР": ["мимо горла", "не попал в трахею"],
        "СС": ["удар в грудь заблокирован", "промахнулся по солнечному сплетению"],
        "ГДН": ["удар ниже пояса не удался", "не дотянулся до ног"]
    }
}

DEFENSE_PHRASES = {
    "defense_success": {
        "СС": ["Вы уверенно блокируете захват груди!", "Солнечное сплетение под защитой!"],
        "ТР": ["Шея в безопасности!", "Вы отбили захват трахеи!"],
        "ДЗ": ["Голова защищена!", "Вы увернулись от захвата головы!"]
    },
    "defense_fail": {
        "СС": ["Захват груди не остановлен!", "Солнечное сплетение под ударом!"],
        "ТР": ["Шея открыта!", "Трахея в опасности!"],
        "ДЗ": ["Голова под контролем противника!", "Не смогли защитить голову!"]
    },
    "counter_success": {
        "Аге уке": ["Вы контратаковали в голову!", "Удар в висок!"],
        "Учи уке": ["Контратака в горло прошла!", "Удар в грудь!"],
        "Сото уке": ["Контратака в солнечное сплетение!", "Удар в голову!"],
        "Гедан барай": ["Контратака в трахею!", "Удар ниже пояса!"]
    },
    "counter_fail": {
        "Аге уке": ["Контратака в голову не удалась!", "Промахнулись по виску!"],
        "Учи уке": ["Контратака в горло мимо!", "Удар в грудь не прошёл!"],
        "Сото уке": ["Контратака в грудь заблокирована!", "Удар в голову не удался!"],
        "Гедан барай": ["Контратака в трахею мимо!", "Удар ниже пояса не прошёл!"]
    }
}
