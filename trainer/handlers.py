from state import GameState
from texts import TEXTS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Получена команда /start")
    if not context.user_data.get("state"):
        context.user_data["state"] = GameState()
    state = context.user_data["state"]

    telegram_username = update.effective_user.username or update.effective_user.first_name
    if telegram_username:
        keyboard = [
            [InlineKeyboardButton("Использовать Telegram", callback_data="use_telegram_nick")],
            [InlineKeyboardButton("Выбрать свой", callback_data="choose_own_nick")]
        ]
        await update.message.reply_text(
            TEXTS["start_welcome"].format(username=telegram_username),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            TEXTS["start_no_username"],
            parse_mode="HTML",
            reply_markup=ForceReply(selective=True)
        )

async def handle_nick_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    state = context.user_data.get("state", GameState())
    context.user_data["state"] = state
    nick = update.message.text.strip()
    if len(nick) > 20:
        await update.message.reply_text(
            TEXTS["nick_too_long"],
            reply_markup=get_start_keyboard()
        )
    elif nick:
        state.nickname = nick
        await update.message.reply_text(
            TEXTS["nick_set"].format(nick=nick),
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )
    else:
        state.nickname = "Вы"
        await update.message.reply_text(
            TEXTS["nick_default"],
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Нажата кнопка 'Игра'")
    if not context.user_data.get("state"):
        context.user_data["state"] = GameState()
    await update.message.reply_text(
        TEXTS["game_menu"],
        reply_markup=menu_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"Нажата кнопка: {query.data}")
    state = context.user_data.get("state", GameState())
    context.user_data["state"] = state

    if query.data == "use_telegram_nick":
        telegram_username = update.effective_user.username or update.effective_user.first_name
        state.nickname = telegram_username
        await query.message.reply_text(
            TEXTS["use_telegram_nick"].format(username=telegram_username),
            parse_mode="HTML",
            reply_markup=get_start_keyboard()
        )
        try:
            await query.message.delete()
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
    elif query.data == "choose_own_nick":
        await query.message.reply_text(
            TEXTS["choose_own_nick"],
            reply_markup=ForceReply(selective=True)
        )
        try:
            await query.message.delete()
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
    elif query.data == "training_fight":
        await query.edit_message_text(
            TEXTS["training_fight_menu"],
            reply_markup=training_fight_keyboard(),
            parse_mode="HTML"
        )
    elif query.data == "training_rules":
        await query.edit_message_text(
            TEXTS["training_rules"],
            parse_mode="HTML",
            reply_markup=training_rules_keyboard()
        )
    elif query.data == "training_memo":
        await query.edit_message_text(
            TEXTS["training_memo"],
            parse_mode="HTML",
            reply_markup=training_memo_keyboard()
        )
    elif query.data in ["simple_fight", "timed_fight"]:
        state.reset()
        state.mode = query.data
        state.fight_sequence = generate_fight_sequence()
        state.current_step = 0
        state.correct_count = 0
        state.control_count = 0
        state.hint_count = 0
        await show_next_move(context, query.message.chat_id, query.data, state.fight_sequence, 0)
        await query.delete_message()
    elif query.data == "hint":
        if state.mode == "simple_fight" and state.fight_sequence and state.current_step is not None and query.message.message_id == state.last_message_id:
            control, attack = state.fight_sequence[state.current_step]
            correct_answer = next((move for move, data in DEFENSE_MOVES.items() if control == data["control"] and attack in data["attack_defense"]), None)
            text = TEXTS["training_hint"].format(
                step=state.current_step + 1,
                total=len(MOVES),
                control=control,
                attack=attack,
                correct_answer=correct_answer
            )
            await query.edit_message_text(text, reply_markup=answer_keyboard(send_hint=True), parse_mode="HTML")
            state.hint_count += 1
    elif query.data == "pvp_bot":
        logger.info("Переход в режим PvP: отображение меню")
        stop_timer(context)
        await query.edit_message_text(
            TEXTS["pvp_bot_menu"],
            reply_markup=pvp_bot_keyboard(),
            parse_mode="HTML"
        )
    elif query.data == "pvp_rules":
        await query.edit_message_text(
            TEXTS["pvp_rules"],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Начать бой", callback_data="pvp_start")]])
        )
    elif query.data == "pvp_start":
        logger.info("Начало PvP боя")
        state.reset()
        state.mode = "pvp"
        state.step = 0
        state.bot_control = random.choice(["СС", "ТР", "ДЗ"])
        state.bot_attack = random.choice(["СС", "ТР", "ДЗ"])
        await query.edit_message_text(
            TEXTS["pvp_start"].format(step=state.step + 1),
            reply_markup=pvp_attack_keyboard("control"),
            parse_mode="HTML"
        )
    elif query.data.startswith("attack_control_"):
        control = query.data.split("_")[2]
        logger.info(f"Выбран контроль: {control}, state={state.to_dict()}")
        state.player_control = control
        try:
            await query.edit_message_text(
                TEXTS["pvp_attack"].format(step=state.step + 1),
                reply_markup=pvp_attack_keyboard("attack"),
                parse_mode="HTML"
            )
        except BadRequest as e:
            logger.error(f"Ошибка Telegram API в attack_control_: {e}")
            await query.message.reply_text(TEXTS["error_generic"], reply_markup=get_start_keyboard())
        except Exception as e:
            logger.error(f"Неизвестная ошибка в attack_control_: {e}", exc_info=True)
            await query.message.reply_text(TEXTS["error_generic"], reply_markup=get_start_keyboard())
    elif query.data.startswith("attack_hit_"):
        logger.info(f"attack_hit_ started: query.data={query.data}, state={state.to_dict()}")
        attack = query.data.split("_")[2]
        state.player_attack = attack
        logger.info(f"Атака сохранена: player_attack={attack}, step={state.step}")
        try:
            logger.info(f"Попытка обновить сообщение: chat_id={query.message.chat_id}, message_id={query.message.message_id}")
            await query.edit_message_text(
                TEXTS["pvp_defense"].format(step=state.step + 1, control=state.player_control, attack=state.player_attack),
                reply_markup=answer_keyboard(),
                parse_mode="HTML"
            )
            logger.info("Сообщение успешно обновлено")
        except BadRequest as e:
            logger.error(f"Ошибка Telegram API в attack_hit_: {e}")
            await query.message.reply_text(TEXTS["error_generic"], reply_markup=get_start_keyboard())
        except Exception as e:
            logger.error(f"Неизвестная ошибка в attack_hit_: {e}", exc_info=True)
            await query.message.reply_text(TEXTS["error_generic"], reply_markup=get_start_keyboard())
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"] and state.mode == "pvp":
        logger.info(f"Выбрана защита: {query.data}")
        state.player_defense = query.data
        try:
            await query.edit_message_text(
                TEXTS["pvp_confirm"].format(
                    control=state.player_control,
                    attack=state.player_attack,
                    defense=state.player_defense
                ),
                reply_markup=pvp_move_keyboard(),
                parse_mode="HTML"
            )
        except BadRequest as e:
            logger.error(f"Ошибка Telegram API в выборе защиты: {e}")
            await query.message.reply_text(TEXTS["error_generic"], reply_markup=get_start_keyboard())
        except Exception as e:
            logger.error(f"Неизвестная ошибка в выборе защиты: {e}", exc_info=True)
            await query.message.reply_text(TEXTS["error_generic"], reply_markup=get_start_keyboard())
    elif query.data == "pvp_move":
        logger.info(f"Подтверждение хода в PvP, state={state.to_dict()}")
        if not all([state.player_control, state.player_attack, state.player_defense, state.bot_control, state.bot_attack]):
            logger.error(f"Неполные данные хода: {state.to_dict()}")
            await query.message.reply_text(TEXTS["error_state"], reply_markup=get_start_keyboard())
            return

        bot_defense = random.choice(["Аге уке", "Сото уке", "Учи уке", "Гедан барай"])
        player_name = state.nickname or "Вы"

        player_score_delta, bot_score_delta = calculate_pvp_scores(
            state.player_control, state.player_attack, state.player_defense,
            state.bot_control, state.bot_attack, bot_defense
        )
        state.player_score += player_score_delta
        state.bot_score += bot_score_delta

        state.step += 1
        log = generate_pvp_log(
            state.step, player_name,
            state.player_control, state.player_attack, state.player_defense,
            state.bot_control, state.bot_attack, bot_defense,
            state.player_score, state.bot_score
        )
        await query.message.reply_text(log, parse_mode="HTML")
        try:
            await query.message.delete()
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")

        if state.step >= 5:
            winner = player_name if state.player_score > state.bot_score else "Бот" if state.bot_score > state.player_score else "Ничья"
            await query.message.reply_text(
                TEXTS["pvp_final"].format(
                    player_score=state.player_score,
                    bot_score=state.bot_score,
                    winner=winner
                ),
                reply_markup=get_start_keyboard(),
                parse_mode="HTML"
            )
            state.reset()
        else:
            state.player_control = None
            state.player_attack = None
            state.player_defense = None
            state.bot_control = random.choice(["СС", "ТР", "ДЗ"])
            state.bot_attack = random.choice(["СС", "ТР", "ДЗ"])
            await query.message.reply_text(
                TEXTS["pvp_start"].format(step=state.step + 1),
                reply_markup=pvp_attack_keyboard("control"),
                parse_mode="HTML"
            )
    elif query.data in ["Аге уке", "Сото уке", "Учи уке", "Гедан барай"]:
        if state.fight_sequence and state.current_step is not None and query.message.message_id == state.last_message_id:
            stop_timer(context)
            await query.delete_message()
            control, attack = state.fight_sequence[state.current_step]
            chosen_defense = query.data
            is_success, partial_success, correct_answer = check_move(control, attack, chosen_defense)
            short_log = generate_short_log(state.current_step, control, attack, chosen_defense, is_success, partial_success, correct_answer)
            short_msg = await query.message.reply_text(short_log, parse_mode="HTML")
            detailed_log = generate_detailed_log(control, attack, chosen_defense, is_success)
            await query.message.reply_text(detailed_log, parse_mode="HTML", reply_to_message_id=short_msg.message_id)
            if is_success:
                state.correct_count += 1
            if control == DEFENSE_MOVES[chosen_defense]["control"]:
                state.control_count += 1
            if state.current_step >= len(state.fight_sequence) - 1:
                await query.message.reply_text(TEXTS["training_end"], parse_mode="HTML")
                final_stats = generate_final_stats(
                    state.correct_count,
                    state.control_count,
                    state.hint_count,
                    len(MOVES)
                )
                await query.message.reply_text(final_stats, parse_mode="HTML", reply_markup=get_start_keyboard())
                state.reset()
            else:
                state.current_step += 1
                await show_next_move(context, query.message.chat_id, state.mode, state.fight_sequence, state.current_step)

def stop_timer(context):
    """Останавливает активный таймер."""
    state = context.user_data.get("state", GameState())
    if state.current_timer and state.current_timer.data.get("active", False):
        state.current_timer.data["active"] = False
        try:
            state.current_timer.schedule_removal()
        except Exception as e:
            logger.warning(f"Не удалось удалить таймер: {e}")
        state.current_timer = None
