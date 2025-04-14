from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

def get_nickname_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ник Telegram", callback_data="use_telegram_nick"),
            InlineKeyboardButton(text="Свой ник", callback_data="custom_nick")
        ]
    ])
    return keyboard
