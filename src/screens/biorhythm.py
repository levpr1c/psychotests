"""Biorhythm test screen."""

from datetime import date, datetime

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Label, Static, Button, Input
from textual.containers import Vertical, Horizontal
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

from src.tests.biorhythm_calc import calculate_biorhythms
from src.data.interpretations import BIO_INTERPRETATION
from src.screens.confirm_modal import ConfirmModal
from src.models.database import save_result
from src.models.test_result import TestResultCreate


class BiorhythmScreen(Screen):
    BINDINGS = [
        Binding("up", "focus_previous", "↑", priority=True),
        Binding("down", "focus_next", "↓", priority=True),
        Binding("left", "focus_previous", "←", priority=True),
        Binding("right", "focus_next", "→", priority=True),
        Binding("escape", "back", "Назад"),
    ]

    def action_focus_next(self):
        self.focus_next()

    def action_focus_previous(self):
        self.focus_previous()

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def action_back(self):
        self.app.push_screen(ConfirmModal("Хотите выйти из теста?"), self._on_exit_confirm)

    def _on_exit_confirm(self, result: bool):
        if result:
            self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Биоритмы", id="title"),
            Static("Расчёт физических, эмоциональных и интеллектуальных биоритмов", id="subtitle"),
            Label("Дата расчёта (ГГГГ-ММ-ДД, по умолчанию сегодня):", id="date_label"),
            Input(id="target_date", value=date.today().isoformat()),
            Button("Рассчитать", id="calc_btn", variant="primary"),
            Static(id="result_area"),
            id="main_content",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "calc_btn":
            self.calculate()

    def calculate(self):
        target_str = self.query_one("#target_date", Input).value.strip()
        try:
            target = date.fromisoformat(target_str) if target_str else date.today()
        except (ValueError, TypeError):
            self.notify("Неверный формат даты. Используйте ГГГГ-ММ-ДД", severity="error")
            return

        # Use birth date from user profile or prompt
        from src.models.database import get_user
        user = get_user(self.user_id)
        if not user or not user.birth_date:
            self.notify("У пользователя не указана дата рождения", severity="error")
            return

        birth = user.birth_date
        result = calculate_biorhythms(birth, target)

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Цикл", style="bold")
        table.add_column("Период (дни)")
        table.add_column("Значение")
        table.add_column("Фаза")

        cycle_names = {
            "physical": ("Физический", "🔴"),
            "emotional": ("Эмоциональный", "🟡"),
            "intellectual": ("Интеллектуальный", "🟢"),
        }

        for key, (name, icon) in cycle_names.items():
            data = result[key]
            val = f"{data['value']:+.2f}"
            phase = BIO_INTERPRETATION.get(data["phase"], "")
            table.add_row(f"{icon} {name}", str(data["period"]), val, phase)

        self.query_one("#result_area", Static).update(
            Panel(
                f"[bold]Дата рождения:[/bold] {birth}\n"
                f"[bold]Дата расчёта:[/bold] {target}\n"
                f"[bold]Прожито дней:[/bold] {result['days']}\n\n"
                f"{table}\n\n"
                "[dim]PgUp/PgDn — смена даты, Home/End — быстрая навигация[/dim]"
            )
        )

        flat_scores = {k: v for k, v in result.items() if isinstance(v, (int, float))}
        flat_scores |= {f"{k}_{kk}": vv for k, v in result.items() if isinstance(v, dict) for kk, vv in v.items() if isinstance(vv, (int, float))}
        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Биоритмы",
            scores=flat_scores,
            interpretation=f"Физический: {result['physical']['value']:.2f}, "
                          f"Эмоциональный: {result['emotional']['value']:.2f}, "
                          f"Интеллектуальный: {result['intellectual']['value']:.2f}",
        ))
        self.notify("Результат сохранён", severity="information")
