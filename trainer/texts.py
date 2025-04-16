RULES_TEXT = (
    "<b>Правила простого боя</b>\n\n"
    "1. Бой состоит из <b>10 схваток</b>.\n"
    "2. В каждой схватке противник выбирает <b>контроль</b> и <b>атаку</b>.\n"
    "3. Вы выбираете <b>защиту</b> из предложенных.\n"
    "4. <b>Чистая победа</b> (+3 балла): защита полностью блокирует атаку.\n"
    "5. <b>Частичный успех</b> (+1 балл): защита частично работает.\n"
    "6. <b>Поражение</b> (0 баллов): защита не сработала.\n"
    "7. Используйте <b>подсказку</b>, чтобы узнать правильную защиту."
)

TIPS_TEXT = (
    "<b>Памятка по защите</b>\n\n"
    "<b>Гедан барай</b>: Блокирует низкие атаки (ДЗ, ТР).\n"
    "<b>Аге уке</b>: Защита от высоких ударов (ДЗ, СС).\n"
    "<b>Сото уке</b>: Универсальная защита для СС и ТР.\n"
    "<b>Учи уке</b>: Блокирует внутренние атаки (СС, ДЗ)."
)

ATTACK_PHRASES = [
    "<b>{nick}</b> целишься в {target} (<b>{code}</b>) — мимо! 💨",
    "<b>{nick}</b> атакуешь {target} (<b>{code}</b>) — не попал! 😅",
    "<b>{nick}</b> бьёшь по {target} (<b>{code}</b>) — промах! ⚡",
    "<b>{nick}</b> метишь в {target} (<b>{code}</b>) — защита держит! 🛡️",
]

BLOCK_PHRASES = [
    "<b>{nick}</b> ставишь <b>{defense}</b> в стиле кёкусинкай! Классный блок! 🥋",
    "<b>{nick}</b> мощно отбиваешь <b>{defense}</b>! Сила в защите! 💪",
    "<b>{nick}</b> ловко блокируешь <b>{defense}</b>! Отличный ход! ✅",
    "<b>{nick}</b> твёрдо держишь <b>{defense}</b>! Никто не пройдёт! 🛑",
]

FINAL_PHRASES = [
    "Бам! <b>{nick}</b> завершает контрударом в <b>{target}</b>! 🏆",
    "Вот это блок! <b>{nick}</b> добивает в <b>{target}</b>! 💥",
    "Удар! <b>{nick}</b> красиво заканчивает в <b>{target}</b>! 🔥",
    "Сила духа! <b>{nick}</b> побеждает ударом в <b>{target}</b>! ✨",
]
