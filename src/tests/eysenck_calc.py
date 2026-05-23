"""Eysenck EPI scoring logic."""


def score_eysenck(answers: list[bool], question_indices: list[str]) -> dict:
    e_score = 0
    n_score = 0
    l_score = 0

    for i, (answer, scale) in enumerate(zip(answers, question_indices)):
        if answer:
            if scale == "E":
                e_score += 1
            elif scale == "N":
                n_score += 1
            elif scale == "L":
                l_score += 1

    return {
        "extraversion": e_score,
        "neuroticism": n_score,
        "lie": l_score,
        "total": e_score + n_score,
    }
