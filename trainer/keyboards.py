from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Тренировать защиту", callback_data="training_fight")],
        [InlineKeyboardButton("Спортивный поединок", callback_data="pvp_bot")]
    ]
    return InlineKeyboardMarkup(keyboard)

def training_mode_keyboard():
    keyboard = [
        [InlineKeyboardButton("Без времени", callback_data="simple_fight")],
        [InlineKeyboardButton("На время", callback_data="timed_fight")]
    ]
    return InlineKeyboardMarkup(keyboard)

def answer_keyboard(send_hint=False):
    keyboard = [
        [InlineKeyboardButton("Аге уке", callback_data="Аге уке"),
         InlineKeyboardButton("Сото уке", callback_data="Сото уке")],
        [InlineKeyboardButton("Учи уке", callback_data="Учи уке"),
         InlineKeyboardButton("Гедан барай", callback_data="Гедан барай")]
    ]
    if send_hint:
        keyboard.append([InlineKeyboardButton("💡Подсказка", callback_data="hint")])
    return InlineKeyboardMarkup(keyboard)

def pvp_bot_keyboard():
    keyboard = [
        [InlineKeyboardButton("Правила", callback_data="pvp_rules")],
        [InlineKeyboardButton("Начать бой", callback_data="pvp_start")]
    ]
    return InlineKeyboardMarkup(keyboard)

def pvp_attack_keyboard(mode="control"):
    prefix = "attack_control_" if mode == "control" else "attack_hit_"
    keyboard = [
        [InlineKeyboardButton("СС", callback_data=f"{prefix}СС"),
         InlineKeyboardButton("ТР", callback_data=f"{prefix}ТР"),
         InlineKeyboardButton("ДЗ", callback_data=f"{prefix}ДЗ")]
    ]
    return InlineKeyboardMarkup(keyboard)

def pvp_move_keyboard():
    keyboard = [[InlineKeyboardButton("Подтвердить", callback_data="pvp_move")]]
    return InlineKeyboardMarkup(keyboard)
