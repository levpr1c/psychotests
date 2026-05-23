"""Economy/dealing style test screen."""

from textual.widgets import Static

from src.screens._base_test import BaseTestScreen
from src.data.questions import ECONOMY_QUESTIONS
from src.tests.economy_calc import score_economy
from src.data.interpretations import get_economy_interpretation
from src.models.database import save_result
from src.models.test_result import TestResultCreate


class EconomyScreen(BaseTestScreen):
    TITLE = "Деловая сфера"
    SUBTITLE = "Оцените, насколько Вы согласны с утверждениями (1-5)"
    QUESTIONS = ECONOMY_QUESTIONS

    def finish_test(self):
        result = score_economy(self.answers)
        interpretation = get_economy_interpretation(result["total"])

        self.query_one("#question_label", Static).update("")
        self.query_one("#answer_set").disabled = True
        self.query_one("#nav_buttons").display = False
        self.query_one("#result_area", Static).update(
            f"## Результат: Деловая сфера\n\n"
            f"**Общий балл:** {result['total']}\n\n"
            f"{interpretation}"
        )

        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Деловая сфера",
            scores=result,
            interpretation=interpretation,
        ))
        self.notify("Результат сохранён", severity="information")
