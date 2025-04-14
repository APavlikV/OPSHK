from aiogram import types

def get_fight_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton("Гедан-барай"),
        types.KeyboardButton("Аге-укэ"),
        types.KeyboardButton("Сото-укэ"),
        types.KeyboardButton("Учи-укэ"),
        types.KeyboardButton("💡 Подсказка"),
    ]
    keyboard.add(*buttons)
    return keyboard
