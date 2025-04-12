from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def start_keyboard():
    return ReplyKeyboardMarkup([["Игра"]], resize_keyboard=True)

def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Учебный бой", callback_data="training_fight")],
        [InlineKeyboardButton("Арена", callback_data="arena")],
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Памятка", callback_data="memo")]
    ])

def training_mode_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Простой бой", callback_data="simple_fight")],
        [InlineKeyboardButton("Бой на время", callback_data="timed_fight")]
    ])

def answer_keyboard(show_hint=False):
    buttons = [
        [InlineKeyboardButton("Аге уке", callback_data="Аге уке")],
        [InlineKeyboardButton("Сото уке", callback_data="Сото уке")],
        [InlineKeyboardButton("Учи уке", callback_data="Учи уке")],
        [InlineKeyboardButton("Гедан барай", callback_data="Гедан барай")]
    ]
    if not show_hint:
        buttons.append([InlineKeyboardButton("Подсказка", callback_data="hint")])
    return InlineKeyboardMarkup(buttons)
