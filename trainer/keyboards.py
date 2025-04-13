from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from trainer.data import CONTROLS, ATTACKS

def pvp_attack_keyboard(step, control=None):
    if step == "control":
        buttons = [
            [InlineKeyboardButton(text, callback_data=f"attack_control_{text}")]
            for text in CONTROLS
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text, callback_data=f"attack_{text}")]
            for text in ATTACKS
            if text != control
        ]
    return InlineKeyboardMarkup(buttons)

def end_fight_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Простой бой", callback_data="simple_fight"),
            InlineKeyboardButton("Бой на время", callback_data="timed_fight")
        ],
        [
            InlineKeyboardButton("Правила", callback_data="training_rules"),
            InlineKeyboardButton("Памятка", callback_data="training_memo")
        ],
        [
            InlineKeyboardButton("Назад", callback_data="back_to_training")
        ]
    ])
