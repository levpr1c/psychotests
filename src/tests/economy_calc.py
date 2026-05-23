"""Economy/dealing style test scoring."""


def score_economy(answers: list[int]) -> dict:
    inverted = {2, 4, 6, 8, 12, 16, 18, 19, 22, 24}
    total = 0
    for i, a in enumerate(answers):
        if i in inverted:
            total += 5 - a
        else:
            total += a

    total = round(total / len(answers) * 20, 1)

    return {"total": total}
