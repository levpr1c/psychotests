"""Stress test screen."""

from textual.widgets import Static

from src.screens._base_test import BaseTestScreen
from src.data.questions import STRESS_QUESTIONS
from src.tests.stress_calc import score_stress
from src.data.interpretations import get_stress_interpretation
from src.models.database import save_result
from src.models.test_result import TestResultCreate


class StressScreen(BaseTestScreen):
    TITLE = "Тест на стресс"
    SUBTITLE = "Оцените, насколько часто Вы испытываете эти состояния (1-5)"
    QUESTIONS = STRESS_QUESTIONS

    def finish_test(self):
        result = score_stress(self.answers)
        interpretation = get_stress_interpretation(result["total"])

        self.query_one("#question_label", Static).update("")
        self.query_one("#answer_set").disabled = True
        self.query_one("#nav_buttons").display = False
        self.query_one("#result_area", Static).update(
            f"## Результат теста на стресс\n\n"
            f"**Общий балл:** {result['total']}\n\n"
            f"{interpretation}"
        )

        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Тест на стресс",
            scores=result,
            interpretation=interpretation,
        ))
        self.notify("Результат сохранён", severity="information")
