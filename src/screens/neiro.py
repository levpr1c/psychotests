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
    QUESTIONS = NEIRO_QUESTIONS

    def finish_test(self):
        result = score_neiro(self.answers)
        interpretation = get_neiro_interpretation(result["total"])

        self.query_one("#question_label", Static).update("")
        self.query_one("#answer_set").disabled = True
        self.query_one("#nav_buttons").display = False
        self._show_result(
            f"[bold yellow]Общий балл:[/bold yellow] [cyan]{result['total']}[/cyan]\n"
            f"[bold yellow]Уровень:[/bold yellow] [cyan]{result['level']}[/cyan]\n\n{interpretation}",
            title="Неврологический тест",
            border_style="green",
        )

        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Неврологический тест",
            scores=result,
            interpretation=interpretation,
        ))
        self.test_completed = True
        self.notify("Результат сохранён", severity="information")
