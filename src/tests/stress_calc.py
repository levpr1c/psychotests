"""Stress test scoring. 0-4 scale per question."""


def score_stress(answers: list[int]) -> dict:
    total = sum(answers)
    level = "normal"
    if total > 100:
        level = "critical"
    elif total > 75:
        level = "high"
    elif total > 50:
        level = "elevated"
    elif total > 30:
        level = "moderate"
    else:
        level = "low"

    return {"total": total, "level": level}
