from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

def menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Тренировка защиты", callback_data="training_fight")],
        [InlineKeyboardButton("Спортивный бой", callback_data="pvp_bot")]
    ]
    return InlineKeyboardMarkup(keyboard)

def training_fight_keyboard():
    keyboard = [
        [InlineKeyboardButton("Правила", callback_data="training_rules"),
         InlineKeyboardButton("Памятка", callback_data="training_memo")],
        [InlineKeyboardButton("Простой бой", callback_data="simple_fight"),
         InlineKeyboardButton("Бой на время", callback_data="timed_fight")]
    ]
    return InlineKeyboardMarkup(keyboard)

def training_rules_keyboard():
    keyboard = [
        [InlineKeyboardButton("Памятка", callback_data="training_memo")],
        [InlineKeyboardButton("Простой бой", callback_data="simple_fight"),
         InlineKeyboardButton("Бой на время", callback_data="timed_fight")]
    ]
    return InlineKeyboardMarkup(keyboard)

def training_memo_keyboard():
    keyboard = [
        [InlineKeyboardButton("Правила", callback_data="training_rules")],
        [InlineKeyboardButton("Простой бой", callback_data="simple_fight"),
         InlineKeyboardButton("Бой на время", callback_data="timed_fight")]
    ]
    return InlineKeyboardMarkup(keyboard)

def answer_keyboard(send_hint=False):
    keyboard = [
        [InlineKeyboardButton("Аге уке", callback_data="Аге уке"), InlineKeyboardButton("Сото уке", callback_data="Сото уке")],
        [InlineKeyboardButton("Учи уке", callback_data="Учи уке"), InlineKeyboardButton("Гедан барай", callback_data="Гедан барай")]
    ]
    if send_hint:
        keyboard.append([InlineKeyboardButton("💡 Подсказка", callback_data="hint")])
    return InlineKeyboardMarkup(keyboard)

def pvp_bot_keyboard():
    keyboard = [
        [InlineKeyboardButton("Начать бой", callback_data="pvp_start")],
        [InlineKeyboardButton("Правила", callback_data="pvp_rules")]
    ]
    return InlineKeyboardMarkup(keyboard)

def pvp_attack_keyboard(mode):
    keyboard = [
        [InlineKeyboardButton("ДЗ", callback_data=f"attack_{mode}_ДЗ")],
        [InlineKeyboardButton("СС", callback_data=f"attack_{mode}_СС"), InlineKeyboardButton("ТР", callback_data=f"attack_{mode}_ТР")]
    ]
    return InlineKeyboardMarkup(keyboard)

def pvp_move_keyboard():
    keyboard = [
        [InlineKeyboardButton("Подтвердить ход", callback_data="pvp_move")]
    ]
    return InlineKeyboardMarkup(keyboard)
