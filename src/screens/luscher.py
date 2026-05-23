"""Luscher Color Test screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Label, Button, Static
from textual.containers import Vertical, Horizontal
from rich.table import Table
from rich.panel import Panel

from src.tests.luscher_calc import calculate_luscher, COLORS
from src.data.interpretations import get_luscher_interpretation
from src.models.database import save_result
from src.models.test_result import TestResultCreate
from src.screens.confirm_modal import ConfirmModal


COLOR_NAMES_RU = {
    0: "Серый",
    1: "Синий",
    2: "Зелёный",
    3: "Красный",
    4: "Жёлтый",
    5: "Фиолетовый",
    6: "Коричневый",
    7: "Чёрный",
}

COLOR_BG = {
    0: "#E0E0E0",
    1: "blue",
    2: "green",
    3: "red",
    4: "yellow",
    5: "magenta",
    6: "#8B4513",
    7: "black",
}


class LuscherScreen(Screen):
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
        self.round = 1
        self.remaining_colors = list(range(8))
        self.choices1: list[int] = []
        self.choices2: list[int] = []
        self.current_rank = 0

    def action_back(self):
        self.app.push_screen(ConfirmModal("Хотите выйти из теста?"), self._on_exit_confirm)

    def _on_exit_confirm(self, result: bool):
        if result:
            self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Цветовой тест Люшера", id="title"),
            Static("Выберите самый приятный цвет из оставшихся", id="round_label"),
            Label(id="instruction"),
            Horizontal(id="color_buttons"),
            Static(id="progress"),
            Static(id="result_area"),
            id="main_content",
        )
        yield Footer()

    def on_mount(self):
        color_box = self.query_one("#color_buttons", Horizontal)
        for c in range(8):
            name = COLOR_NAMES_RU[c]
            bg = COLOR_BG[c]
            btn = Button(f"{name}", id=f"color_{c}", variant="default")
            btn.styles.background = bg
            if bg in ("black", "blue"):
                btn.styles.color = "white"
            color_box.mount(btn)
        self.start_round()

    def start_round(self):
        self.current_rank = 0
        self.remaining_colors = list(range(8))
        for c in range(8):
            btn = self.query_one(f"#color_{c}", Button)
            btn.display = True
        self.show_colors()

    def show_colors(self):
        round_num = 1 if self.round == 1 else 2
        self.query_one("#round_label", Static).update(
            f"Раунд {round_num} — Выберите цвет #{self.current_rank + 1} из 8"
        )

        for c in self.remaining_colors:
            self.query_one(f"#color_{c}", Button).display = True
        for c in set(range(8)) - set(self.remaining_colors):
            self.query_one(f"#color_{c}", Button).display = False

        self.query_one("#progress", Static).update(
            f"Выбрано: {self.current_rank} / 8"
        )
        self.query_one("#result_area", Static).update("")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id and event.button.id.startswith("color_"):
            color = int(event.button.id.split("_")[1])
            self.select_color(color)

    def select_color(self, color: int):
        if self.round == 1:
            self.choices1.append(color)
        else:
            self.choices2.append(color)

        self.remaining_colors.remove(color)
        self.current_rank += 1

        if self.current_rank >= 8:
            if self.round == 1:
                self.round = 2
                self.query_one("#instruction", Label).update(
                    "А теперь повторите выбор — снова выберите самый приятный цвет"
                )
                self.start_round()
            else:
                self.finish_test()
        else:
            self.show_colors()

    def finish_test(self):
        result = calculate_luscher(self.choices1, self.choices2)
        interpretation = get_luscher_interpretation(
            result["choices1"],
            result["choices2"],
            result["anxiety_pct"],
            result["compensation_pct"],
            result["activity_pct"],
            result["performance_pct"],
            result["vegetative_pct"],
            result["consistency"],
        )

        self.query_one("#round_label", Static).update("Тест завершён")
        self.query_one("#color_buttons", Horizontal).remove_children()
        self.query_one("#instruction", Label).update("")
        self.query_one("#progress", Static).update("")

        self.query_one("#result_area", Static).update(interpretation)

        flat_scores = {k: v for k, v in result.items() if isinstance(v, (int, float))}
        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Цветовой тест Люшера",
            raw_data=f"{result['choices1']}/{result['choices2']}",
            scores=flat_scores,
            interpretation=interpretation,
        ))
        self.notify("Результат сохранён", severity="information")
