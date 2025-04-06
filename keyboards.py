from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_start_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Игра", callback_data="game")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Правила", callback_data="rules"),
            InlineKeyboardButton("Памятка", callback_data="memo")
        ],
        [
            InlineKeyboardButton("Тренировка", callback_data="training_fight"),
            InlineKeyboardButton("Арена", callback_data="karate_arena")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_training_mode_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Простой бой", callback_data="simple_fight"),
            InlineKeyboardButton("Бой на время", callback_data="timed_fight")
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_answer_keyboard(send_hint: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Аге уке", callback_data="Аге уке"),
            InlineKeyboardButton("Сото уке", callback_data="Сото уке")
        ],
        [
            InlineKeyboardButton("Учи уке", callback_data="Учи уке"),
            InlineKeyboardButton("Гедан барай", callback_data="Гедан барай")
        ],
    ]
    if send_hint:
        keyboard.append([
            InlineKeyboardButton("💡 Подсказка", callback_data="hint")
        ])
    return InlineKeyboardMarkup(keyboard)
