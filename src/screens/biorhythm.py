"""Biorhythm test screen."""

from datetime import date

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Label, Static, Button, Input
from textual.containers import Vertical, Horizontal

from src.tests.biorhythm_calc import calculate_biorhythms
from src.data.interpretations import BIO_INTERPRETATION
from src.screens.confirm_modal import ConfirmModal
from src.models.database import get_user, save_result
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
        self.test_completed = False
        user = get_user(user_id)
        self.username = user.name if user else "Неизвестный"

    def action_back(self):
        if self.test_completed:
            self.app.pop_screen()
            return
        self.app.push_screen(ConfirmModal("Хотите выйти из теста?"), self._on_exit_confirm)

    def _on_exit_confirm(self, result: bool):
        if result:
            self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label(f"👤 {self.username}", id="user_label"),
            Label("Биоритмы", id="title"),
            Label("Дата (ГГГГ-ММ-ДД):", id="date_label"),
            Horizontal(
                Input(id="target_date", value=date.today().isoformat()),
                Button("Рассчитать", id="calc_btn", variant="primary"),
                id="date_input_group",
            ),
            Static(id="result_area"),
            id="main_content",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "calc_btn":
            self.calculate()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "target_date":
            self.calculate()

    def calculate(self):
        target_str = self.query_one("#target_date", Input).value.strip()
        try:
            target = date.fromisoformat(target_str) if target_str else date.today()
        except (ValueError, TypeError):
            self.notify("Неверный формат даты. Используйте ГГГГ-ММ-ДД", severity="error")
            return

        user = get_user(self.user_id)
        if not user or not user.birth_date:
            self.notify("У пользователя не указана дата рождения", severity="error")
            return

        birth = user.birth_date
        result = calculate_biorhythms(birth, target)

        bar_width = 20
        cycle_names = {
            "physical": ("Физический", "🔴"),
            "emotional": ("Эмоциональный", "🟡"),
            "intellectual": ("Интеллектуальный", "🟢"),
        }

        lines = [
            f"[bold]ДР:[/bold] {birth}  [bold]Расчёт:[/bold] {target}  [bold]Дней:[/bold] {result['days']}"
        ]
        name_width = max(len(n) for n, _ in cycle_names.values()) + 1
        for key, (name, icon) in cycle_names.items():
            data = result[key]
            val = data["value"]
            phase = BIO_INTERPRETATION.get(data["phase"], "")
            filled = max(0, min(bar_width, int((val + 1) / 2 * bar_width)))
            pct = f"{val * 100:+.0f}%"
            name_col = f"{name}:".ljust(name_width)
            pct_col = pct.rjust(6)
            lines.append(
                f"{icon} [bold]{name_col}[/bold] {pct_col}  "
                f"[cyan]{'█' * filled}[/cyan][bright_black]{'░' * (bar_width - filled)}[/bright_black]  "
                f"[dim]{phase}[/dim]"
            )
        lines.append("[dim]Enter — рассчитать, Esc — назад[/dim]")

        from rich.panel import Panel
        self.query_one("#result_area", Static).update(
            Panel("\n".join(lines), title="Биоритмы", border_style="cyan", padding=(0, 1))
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
        self.test_completed = True
        self.notify("Результат сохранён", severity="information")
