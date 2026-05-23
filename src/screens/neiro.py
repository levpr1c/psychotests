"""Neurological test screen."""

from textual.widgets import Static

from src.screens._base_test import BaseTestScreen
from src.data.questions import NEIRO_QUESTIONS
from src.tests.neiro_calc import score_neiro
from src.data.interpretations import get_neiro_interpretation
from src.models.database import save_result
from src.models.test_result import TestResultCreate


class NeiroScreen(BaseTestScreen):
    TITLE = "Неврологический тест"
    SUBTITLE = "Оцените, как часто Вас беспокоят эти симптомы (1-5)"
    QUESTIONS = NEIRO_QUESTIONS

    def finish_test(self):
        result = score_neiro(self.answers)
        interpretation = get_neiro_interpretation(result["total"])

        self.query_one("#question_label", Static).update("")
        self.query_one("#answer_set").disabled = True
        self.query_one("#nav_buttons").display = False
        self.query_one("#result_area", Static).update(
            f"## Результат неврологического теста\n\n"
            f"**Общий балл:** {result['total']}\n"
            f"**Уровень:** {result['level']}\n\n"
            f"{interpretation}"
        )

        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Неврологический тест",
            scores=result,
            interpretation=interpretation,
        ))
        self.notify("Результат сохранён", severity="information")
