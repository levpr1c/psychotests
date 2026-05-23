"""Neurological test scoring."""


def score_neiro(answers: list[int]) -> dict:
    total = sum(answers)
    level = "normal"
    if total > 60:
        level = "severe"
    elif total > 40:
        level = "moderate"
    elif total > 20:
        level = "mild"
    else:
        level = "normal"

    return {"total": total, "level": level}
