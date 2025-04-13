from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥊 Тренировочный бой", callback_data="training_fight")],
        [InlineKeyboardButton("⚔️ Спортивный бой", callback_data="pvp_bot")],
        [InlineKeyboardButton("📖 Правила", callback_data="training_rules")],
        [InlineKeyboardButton("📝 Памятка", callback_data="training_memo")]
    ])

def training_fight_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ Бой на время", callback_data="timed_fight")],
        [InlineKeyboardButton("📌 Простой бой", callback_data="simple_fight")],
        [InlineKeyboardButton("🔙 Назад", callback_data="game")]
    ])

def training_rules_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="game")]
    ])

def training_memo_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="game")]
    ])

def answer_keyboard(send_hint=False):
    keyboard = [
        [
            InlineKeyboardButton("Аге уке", callback_data="Аге уке"),
            InlineKeyboardButton("Сото уке", callback_data="Сото уке")
        ],
        [
            InlineKeyboardButton("Учи уке", callback_data="Учи уке"),
            InlineKeyboardButton("Гедан барай", callback_data="Гедан барай")
        ]
    ]
    if send_hint:
        keyboard.append([InlineKeyboardButton("💡 Подсказка", callback_data="hint")])
    return InlineKeyboardMarkup(keyboard)

def pvp_bot_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Начать бой", callback_data="pvp_start")],
        [InlineKeyboardButton("📖 Правила", callback_data="pvp_rules")],
        [InlineKeyboardButton("🔙 Назад", callback_data="game")]
    ])

def pvp_attack_keyboard(step, control=None):
    if step == "control":
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("ДЗ", callback_data="attack_control_ДЗ"),
                InlineKeyboardButton("СС", callback_data="attack_control_СС"),
                InlineKeyboardButton("ТР", callback_data="attack_control_ТР")
            ]
        ])
    elif step == "attack":
        if control == "ДЗ":
            moves = ["СС", "ТР", "ГДН"]
        elif control == "ТР":
            moves = ["ДЗ", "СС", "ТР", "ГДН"]
        elif control == "СС":
            moves = ["СС", "ТР", "ДЗ"]
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(move, callback_data=f"attack_hit_{move}") for move in moves]
        ])

def pvp_move_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить ход", callback_data="pvp_move")]
    ])
