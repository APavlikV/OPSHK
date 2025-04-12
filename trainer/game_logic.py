# ... (предыдущий код без изменений: generate_fight_sequence, check_move, generate_short_log, generate_detailed_log, generate_final_stats)

def calculate_pvp_scores(player_control, player_attack, player_defense, bot_control, bot_attack, bot_defense):
    """Рассчитывает очки для PvP схватки."""
    player_score_delta = 0
    bot_score_delta = 0

    # Игрок атакует, бот защищается
    player_control_success = DEFENSE_MOVES[bot_defense]["control"] != player_control
    player_attack_success = player_attack not in DEFENSE_MOVES[bot_defense]["attack_defense"]
    bot_control_defense_success = not player_control_success
    bot_attack_defense_success = player_attack not in DEFENSE_MOVES[bot_defense]["attack_defense"]
    bot_dobivanie = bot_control_defense_success and bot_attack_defense_success
    bot_attack_defense = not bot_control_defense_success and bot_attack_defense_success

    if player_control_success:
        player_score_delta += 1
    if player_attack_success:
        player_score_delta += (2 if player_control_success else 1)
    if bot_control_defense_success:
        bot_score_delta += 1
    if bot_dobivanie:
        bot_score_delta += 2
    elif bot_attack_defense:
        bot_score_delta += 1

    # Бот атакует, игрок защищается
    bot_control_success = DEFENSE_MOVES[player_defense]["control"] != bot_control
    bot_attack_success = bot_attack not in DEFENSE_MOVES[player_defense]["attack_defense"]
    player_control_defense_success = not bot_control_success
    player_attack_defense_success = bot_attack not in DEFENSE_MOVES[player_defense]["attack_defense"]
    player_dobivanie = player_control_defense_success and player_attack_defense_success
    player_attack_defense = not player_control_defense_success and player_attack_defense_success

    if bot_control_success:
        bot_score_delta += 1
    if bot_attack_success:
        bot_score_delta += (2 if bot_control_success else 1)
    if player_control_defense_success:
        player_score_delta += 1
    if player_dobivanie:
        player_score_delta += 2
    elif player_attack_defense:
        player_score_delta += 1

    return player_score_delta, bot_score_delta

def generate_pvp_log(step, player_name, player_control, player_attack, player_defense, bot_control, bot_attack, bot_defense, player_score, bot_score):
    """Форматирует лог PvP схватки."""
    # Игрок атакует, бот защищается
    player_control_success = DEFENSE_MOVES[bot_defense]["control"] != player_control
    player_attack_success = player_attack not in DEFENSE_MOVES[bot_defense]["attack_defense"]
    bot_control_defense_success = not player_control_success
    bot_attack_defense_success = player_attack not in DEFENSE_MOVES[bot_defense]["attack_defense"]
    bot_dobivanie = bot_control_defense_success and bot_attack_defense_success
    bot_attack_defense = not bot_control_defense_success and bot_attack_defense_success

    # Бот атакует, игрок защищается
    bot_control_success = DEFENSE_MOVES[player_defense]["control"] != bot_control
    bot_attack_success = bot_attack not in DEFENSE_MOVES[player_defense]["attack_defense"]
    player_control_defense_success = not bot_control_success
    player_attack_defense_success = bot_attack not in DEFENSE_MOVES[player_defense]["attack_defense"]
    player_dobivanie = player_control_defense_success and player_attack_defense_success
    player_attack_defense = not player_control_defense_success and player_attack_defense_success

    return TEXTS["pvp_log_template"].format(
        step=step,
        player_name=player_name,
        player_control=player_control,
        player_control_result="✅" if player_control_success else "❌",
        player_control_points=1 if player_control_success else 0,
        player_attack=player_attack,
        player_attack_result="✅" if player_attack_success else "❌",
        player_attack_points=2 if player_control_success and player_attack_success else 1 if player_attack_success else 0,
        bot_defense=bot_defense,
        bot_control_defense_result="✅" if bot_control_defense_success else "❌",
        bot_control_defense_points=1 if bot_control_defense_success else 0,
        bot_counter_result="✅" if bot_control_defense_success else "❌",
        bot_counter_points=1 if bot_control_defense_success else 0,
        bot_dobivanie_text="Добивание" if bot_dobivanie else "Защита от атаки",
        bot_dobivanie_result="✅" if bot_dobivanie or bot_attack_defense else "❌",
        bot_dobivanie_points=2 if bot_dobivanie else 1 if bot_attack_defense else 0,
        bot_control=bot_control,
        bot_control_result="✅" if bot_control_success else "❌",
        bot_control_points=1 if bot_control_success else 0,
        bot_attack=bot_attack,
        bot_attack_result="✅" if bot_attack_success else "❌",
        bot_attack_points=2 if bot_control_success and bot_attack_success else 1 if bot_attack_success else 0,
        player_defense=player_defense,
        player_control_defense_result="✅" if player_control_defense_success else "❌",
        player_control_defense_points=1 if player_control_defense_success else 0,
        player_counter_result="✅" if player_control_defense_success else "❌",
        player_counter_points=1 if player_control_defense_success else 0,
        player_dobivanie_text="Добивание" if player_dobivanie else "Защита от атаки",
        player_dobivanie_result="✅" if player_dobivanie or player_attack_defense else "❌",
        player_dobivanie_points=2 if player_dobivanie else 1 if player_attack_defense else 0,
        player_score=player_score,
        bot_score=bot_score
    )
