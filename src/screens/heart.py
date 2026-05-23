"""Cardiovascular/vegetative system test screen."""

from textual.widgets import Static

from src.screens._base_test import BaseTestScreen
from src.data.questions import HEART_QUESTIONS
from src.tests.heart_calc import score_heart
from src.data.interpretations import get_heart_interpretation
from src.models.database import save_result
from src.models.test_result import TestResultCreate


class HeartScreen(BaseTestScreen):
    TITLE = "Оценка сердечно-сосудистой системы"
    SUBTITLE = "Оцените частоту симптомов (1-5)"
    QUESTIONS = [q for q, _ in HEART_QUESTIONS]
    SCALES = [s for _, s in HEART_QUESTIONS]

    def finish_test(self):
        answers_by_scale: dict[str, list[int]] = {}
        for i, (a, scale) in enumerate(zip(self.answers, self.SCALES)):
            if scale not in answers_by_scale:
                answers_by_scale[scale] = []
            answers_by_scale[scale].append(a)

        result = score_heart(answers_by_scale)
        interpretation = get_heart_interpretation(
            result.get("ibc", 0),
            result.get("pps", 0),
            result.get("de", 0),
            result.get("ag", 0),
            result.get("ncd", 0),
            result.get("zm", 0),
        )

        self.query_one("#question_label", Static).update("")
        self.query_one("#answer_set").disabled = True
        self.query_one("#nav_buttons").display = False
        self.query_one("#result_area", Static).update(interpretation)

        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Сердечно-сосудистая система",
            scores=result,
            interpretation=interpretation,
        ))
        self.notify("Результат сохранён", severity="information")
