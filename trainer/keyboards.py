from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Памятка", callback_data="memo")],
        [InlineKeyboardButton("Тренировка", callback_data="training_fight")],
        [InlineKeyboardButton("Арена", callback_data="karate_arena")]
    ]
    return InlineKeyboardMarkup(keyboard)

def training_mode_keyboard():
    keyboard = [
        [InlineKeyboardButton("Тренировать защиту", callback_data="simple_fight")],
        [InlineKeyboardButton("Защита на время", callback_data="timed_fight")],
        [InlineKeyboardButton("Бой с ботом", callback_data="pvp_bot")]
    ]
    return InlineKeyboardMarkup(keyboard)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def pvp_bot_keyboard():
    keyboard = [
        [InlineKeyboardButton("Правила", callback_data="pvp_rules")],
        [InlineKeyboardButton("Начать бой", callback_data="pvp_start")]
    ]
    return InlineKeyboardMarkup(keyboard)

def pvp_attack_keyboard():
    keyboard = [
        [InlineKeyboardButton("СС", callback_data="attack_control_СС"), 
         InlineKeyboardButton("ТР", callback_data="attack_control_ТР"), 
         InlineKeyboardButton("ДЗ", callback_data="attack_control_ДЗ")],
        [InlineKeyboardButton("СС", callback_data="attack_hit_СС"), 
         InlineKeyboardButton("ТР", callback_data="attack_hit_ТР"), 
         InlineKeyboardButton("ДЗ", callback_data="attack_hit_ДЗ")]
    ]
    return InlineKeyboardMarkup(keyboard)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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

def pvp_move_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Сделать ход", callback_data="pvp_move")]])
