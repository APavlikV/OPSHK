from enum import Enum
from typing import Tuple, Dict
from random import choice, randint

from data import Zone, MOVES, DEFENSE_MOVES, ATTACK_PHRASES, DEFENSE_PHRASES


class AttackResult(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"


class DefenseResult(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"


class CounterResult(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"


def get_attack() -> Tuple[Zone, Zone]:
    """Случайный выбор связки (контроль, атака)."""
    control, attack = choice(MOVES)
    return Zone(control), Zone(attack)


def get_attack_description(control: Zone, attack: Zone,
                           control_success: bool, attack_success: bool) -> str:
    """Возвращает описание атаки с учетом успеха или провала."""
    control_key = "control_success" if control_success else "control_fail"
    attack_key = "attack_success" if attack_success else "attack_fail"

    control_phrase = choice(ATTACK_PHRASES[control_key][control])
    attack_phrase = choice(ATTACK_PHRASES[attack_key][attack])
    return f"{control_phrase} {attack_phrase}"


def is_defense_successful(defense: str, incoming_attack: Zone) -> bool:
    """Проверяет, перекрывает ли выбранная защита зону атаки."""
    defense_info = DEFENSE_MOVES.get(defense)
    if not defense_info:
        return False
    return incoming_attack in defense_info["attack_defense"]


def is_counter_available(defense: str, control_zone: Zone) -> bool:
    """Проверяет, возможен ли контрудар по контролю."""
    defense_info = DEFENSE_MOVES.get(defense)
    if not defense_info:
        return False
    return control_zone in defense_info["counter"]


def get_defense_description(defense: str, attack_zone: Zone,
                            success: bool) -> str:
    """Формирует фразу описания защиты."""
    result_key = "defense_success" if success else "defense_fail"
    return choice(DEFENSE_PHRASES[result_key][attack_zone])


def get_counter_description(defense: str, success: bool) -> str:
    """Формирует фразу описания контрудара."""
    result_key = "counter_success" if success else "counter_fail"
    return choice(DEFENSE_PHRASES[result_key][defense])


def process_turn(defense: str, control: Zone, attack: Zone) -> Dict[str, str]:
    """Обработка одного хода: защита, результат защиты и контратаки."""
    defense_success = is_defense_successful(defense, attack)
    counter_possible = is_counter_available(defense, control)

    attack_text = get_attack_description(control, attack,
                                         control_success=True,
                                         attack_success=not defense_success)
    defense_text = get_defense_description(defense, attack, defense_success)

    counter_text = ""
    if defense_success and counter_possible:
        counter_text = get_counter_description(defense, success=randint(0, 1) == 1)

    return {
        "attack": attack_text,
        "defense": defense_text,
        "counter": counter_text
    }
