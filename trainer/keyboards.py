from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_nickname_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Ник Telegram", callback_data="use_telegram_nick"),
            InlineKeyboardButton(text="Свой ник", callback_data="custom_nick")
        ]
    ])
