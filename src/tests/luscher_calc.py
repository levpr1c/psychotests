"""Luscher Color Test calculation.

Based on standard 8-color Luscher methodology and
reverse-engineered parameters from LUSHER.EXE / LUSHER.INT.
"""

import math


def rank_deviation(choices: list[int]) -> float:
    """Calculate deviation from ideal position for each color."""
    deviations = []
    for pos, color in enumerate(choices):
        deviations.append(abs(pos - color))
    return sum(deviations)


def consistency(choices1: list[int], choices2: list[int]) -> float:
    """Spearman rank correlation between two rounds."""
    n = len(choices1)
    d_sq = sum((choices1[i] - choices2[i]) ** 2 for i in range(n))
    return 1 - (6 * d_sq) / (n * (n ** 2 - 1))


def anxiety(choices: list[int]) -> float:
    """Anxiety based on colors in positions 5-8 (negative positions)."""
    # Higher deviation from center = higher anxiety
    deviation = sum(abs(4 - _safe_index(choices, c)) for c in range(8))
    return min(deviation / 16 * 100, 100)


def compensation(choices1: list[int], choices2: list[int]) -> float:
    """Compensation based on changes between rounds."""
    changes = sum(1 for a, b in zip(choices1, choices2) if a != b)
    return changes / 8 * 100


def active_colors(choices: list[int]) -> float:
    """Activity based on warm/cool color placement."""
    warm = {1, 3, 4}  # blue, red, yellow
    cool = {0, 2, 5, 6, 7}  # grey, green, violet, brown, black
    warm_score = sum(1 for c in choices[:4] if c in warm)
    return warm_score / 4 * 100


def _safe_index(lst: list[int], val: int, default: float = 4) -> float:
    try:
        return lst.index(val)
    except ValueError:
        return default


def calculate_luscher(choices1: list[int], choices2: list[int]) -> dict:
    return {
        "choices1": [int(c) for c in choices1],
        "choices2": [int(c) for c in choices2],
        "anxiety_pct": round(anxiety(choices1), 2),
        "compensation_pct": round(compensation(choices1, choices2), 2),
        "activity_pct": round(active_colors(choices1), 2),
        "performance_pct": round(100 - rank_deviation(choices1) / 16 * 100, 2),
        "vegetative_pct": round(50 + (_safe_index(choices1, 1) - _safe_index(choices1, 3)) * 5, 2),
        "consistency": round(consistency(choices1, choices2), 2),
    }
