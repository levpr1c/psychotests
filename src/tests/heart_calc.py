"""Cardiovascular/vegetative system test scoring.

Based on reverse-engineered parameters from HEART.COM:
IBC, PPS, DE, AG, NCD, ZM scales.
"""


def score_heart(answers: dict[str, list[int]]) -> dict:
    result = {}
    for scale, values in answers.items():
        if not values:
            result[scale.lower()] = 0.0
        else:
            result[scale.lower()] = round(sum(values) / len(values) * 2, 1)
    return result
