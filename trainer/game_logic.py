async def check_defense(control: str, attack: str, defense: str) -> int:
    # Логика проверки защиты
    if control == "СС" and attack == "ТР" and defense == "Сото-укэ":
        return 3  # Чистая победа
    return 0  # Поражение (упрощённо)
