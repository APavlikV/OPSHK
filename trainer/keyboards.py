from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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
        moves = ["СС", "ТР", "ДЗ"]  # Дефолт
        if control == "ДЗ":
            moves = ["СС", "ТР", "ГДН"]
        elif control == "ТР":
            moves = ["ДЗ", "СС", "ТР", "ГДН"]
        elif control == "СС":
            moves = ["СС", "ТР", "ДЗ"]
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(move, callback_data=f"attack_hit_{move}") for move in moves]
        ])
    return InlineKeyboardMarkup([])

def end_fight_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Продолжить тренировку", callback_data="simple_fight"),
            InlineKeyboardButton("Бой на время", callback_data="timed_fight"),
        ],
        [InlineKeyboardButton("Прошлая статистика", callback_data="last_stats")]
    ])
