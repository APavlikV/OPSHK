from aiogram.fsm.state import State, StatesGroup

class FightState(StatesGroup):
    waiting_for_name = State()
    waiting_for_defense = State()
