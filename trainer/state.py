class GameState:
    def __init__(self):
        self.mode = None  # "training", "pvp"
        self.player_score = 0
        self.bot_score = 0
        self.step = 0
        self.player_control = None
        self.player_attack = None
        self.player_defense = None
        self.bot_control = None
        self.bot_attack = None
        self.fight_sequence = None
        self.current_step = 0
        self.correct_count = 0
        self.control_count = 0
        self.hint_count = 0
        self.last_message_id = None
        self.current_timer = None
        self.nickname = None

    def reset(self):
        # Сохраняем nickname между боями
        nickname = self.nickname
        self.__init__()
        self.nickname = nickname

    def to_dict(self):
        return vars(self)
