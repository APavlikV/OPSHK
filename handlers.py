from aiogram import types, Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from logic import process_combat_turn, get_available_blocks

router = Router()

# --- Кастомная клавиатура на команду /start ---
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Игра")]],
    resize_keyboard=True
)

# --- Инлайн клавиатура для "Игра" ---
game_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Правила", callback_data="rules")],
    [InlineKeyboardButton(text="Памятка", callback_data="memo")],
    [InlineKeyboardButton(text="Тренировка", callback_data="training")],
    [InlineKeyboardButton(text="Арена", callback_data="arena")]
])

# --- Инлайн клавиатура для "Тренировка" ---
training_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Простой бой", callback_data="simple_fight")],
    [InlineKeyboardButton(text="Бой на время", callback_data="timed_fight")]
])

# --- Инлайн клавиатура с вариантами блоков ---
def block_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=block, callback_data=f"block:{block}")] for block in get_available_blocks()
    ])

# --- ИСХОДНЫЕ ТЕКСТЫ ---
RULES_TEXT = (
    "📌 ПРАВИЛА\n"
    "1. Противник наносит удар в одну из зон: СС, ТР, ДЗ, ГДН.\n"
    "2. Вы выбираете блок. У каждого блока своя зона защиты.\n"
    "3. Если блок сработал — вы можете контратаковать и добить.\n"
    "4. Если блок не сработал — получаете урон.\n"
    "Задача: выстоять и победить!"
)

MEMO_TEXT = (
    "🧠 ПАМЯТКА\n"
    "➖\n"
    "👊🏻 Зоны контроля и атаки:\n"
    "• СС — Чудан (солнечное сплетение)\n"
    "• ТР — Чудан (трахея)\n"
    "• ДЗ — Дзедан (голова)\n"
    "• ГДН — Годан (ниже пояса)\n\n"
    "🛡️ Блоки:\n"
    "▫️ Аге уке\n"
    "   • Защита: СС\n"
    "   • Контратака: ДЗ / ТР\n"
    "   • Добивание: ДЗ\n\n"
    "▫️ Учи уке\n"
    "   • Защита: СС\n"
    "   • Контратака: ДЗ / ТР\n"
    "   • Добивание: ДЗ / ТР / СС\n\n"
    "▫️ Сото уке\n"
    "   • Защита: ТР\n"
    "   • Контратака: ДЗ / СС\n"
    "   • Добивание: ДЗ / ТР / СС\n\n"
    "▫️ Гедан барай\n"
    "   • Защита: ДЗ\n"
    "   • Контратака: ТР / СС\n"
    "   • Добивание: ТР / СС / ГДН"
)

# --- Хендлеры ---

@router.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer("Привет! Выбери режим:", reply_markup=start_keyboard)

@router.message(F.text == "Игра")
async def game_menu_handler(message: Message):
    await message.answer("Выбери действие:", reply_markup=game_menu_keyboard)

@router.callback_query(F.data == "rules")
async def rules_handler(callback: CallbackQuery):
    await callback.message.edit_text(RULES_TEXT)

@router.callback_query(F.data == "memo")
async def memo_handler(callback: CallbackQuery):
    await callback.message.edit_text(MEMO_TEXT)

@router.callback_query(F.data == "training")
async def training_handler(callback: CallbackQuery):
    await callback.message.edit_text("Выбери тренировку:", reply_markup=training_keyboard)

@router.callback_query(F.data == "arena")
async def arena_handler(callback: CallbackQuery):
    await callback.message.edit_text("⚠️ Арена в разработке. Скоро!")

# --- Запуск тренировочного боя ---
@router.callback_query(F.data == "simple_fight")
async def simple_fight_handler(callback: CallbackQuery):
    await callback.message.edit_text("Выбери блок:", reply_markup=block_keyboard())

# --- Обработка выбранного блока ---
@router.callback_query(F.data.startswith("block:"))
async def block_choice_handler(callback: CallbackQuery):
    block = callback.data.split(":")[1]
    result = process_combat_turn(block)
    await callback.message.edit_text(result, reply_markup=block_keyboard())
