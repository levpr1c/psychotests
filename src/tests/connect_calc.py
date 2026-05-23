"""Communication/connection test scoring."""


def score_connect(answers: list[int]) -> dict:
    # Inverted questions (2, 7, 9, 13, 15, 16, 18, 20, 22)
    inverted = {2, 7, 9, 13, 15, 16, 18, 20, 22}
    total = 0
    for i, a in enumerate(answers):
        if i in inverted:
            total += 5 - a
        else:
            total += a

    total = round(total / len(answers) * 20, 1)

    return {"total": total}
