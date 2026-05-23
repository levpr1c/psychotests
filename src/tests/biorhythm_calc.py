"""Biorhythm calculation based on standard 23/28/33 day cycles."""

import math
from datetime import date


PHYSICAL = 23
EMOTIONAL = 28
INTELLECTUAL = 33


def days_between(birth: date, target: date | None = None) -> int:
    if target is None:
        target = date.today()
    return (target - birth).days


def cycle_value(days: int, period: int) -> float:
    return math.sin(2 * math.pi * days / period)


def calculate_biorhythms(birth: date, target: date | None = None) -> dict:
    days = days_between(birth, target)
    return {
        "days": days,
        "physical": {
            "value": cycle_value(days, PHYSICAL),
            "period": PHYSICAL,
            "phase": get_phase(cycle_value(days, PHYSICAL)),
        },
        "emotional": {
            "value": cycle_value(days, EMOTIONAL),
            "period": EMOTIONAL,
            "phase": get_phase(cycle_value(days, EMOTIONAL)),
        },
        "intellectual": {
            "value": cycle_value(days, INTELLECTUAL),
            "period": INTELLECTUAL,
            "phase": get_phase(cycle_value(days, INTELLECTUAL)),
        },
    }


def get_phase(value: float) -> str:
    if abs(value) < 0.05:
        return "critical"
    if value > 0.5:
        return "high"
    if value > 0:
        return "rising"
    if value > -0.5:
        return "falling"
    return "low"
