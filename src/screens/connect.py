"""Communication test screen."""

from textual.widgets import Static

from src.screens._base_test import BaseTestScreen
from src.data.questions import CONNECT_QUESTIONS
from src.tests.connect_calc import score_connect
from src.data.interpretations import get_connect_interpretation
from src.models.database import save_result
from src.models.test_result import TestResultCreate


class ConnectScreen(BaseTestScreen):
    TITLE = "Тест на совместимость"
    QUESTIONS = CONNECT_QUESTIONS

    def finish_test(self):
        result = score_connect(self.answers)
        interpretation = get_connect_interpretation(result["total"])

        self.query_one("#question_label", Static).update("")
        self.query_one("#answer_set").disabled = True
        self.query_one("#nav_buttons").display = False
        self.query_one("#result_area", Static).update(
            f"[bold]Результат теста на совместимость[/bold]\n\n"
            f"Общий балл: {result['total']}\n\n"
            f"{interpretation}"
        )

        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Тест на совместимость",
            scores=result,
            interpretation=interpretation,
        ))
        self.test_completed = True
        self.notify("Результат сохранён", severity="information")
