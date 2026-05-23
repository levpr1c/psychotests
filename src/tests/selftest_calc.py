"""Self-evaluation test scoring.

Based on reverse-engineered parameters from SELFTEST.COM.
"""


def score_selftest(answers: list[int]) -> dict:
    # Inverted questions: 2, 5, 8, 9, 11, 12, 14, 15, 17, 19
    inverted = {1, 4, 8, 9, 10, 11, 13, 14, 16, 18}
    total = 0
    for i, a in enumerate(answers):
        if i in inverted:
            total += 5 - a
        else:
            total += a

    total = round(total / len(answers) * 25, 1)

    return {"total": total}
