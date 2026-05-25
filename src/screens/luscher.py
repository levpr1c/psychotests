"""Luscher Color Test screen."""

import random

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Label, Button, Static
from textual.containers import Vertical, Horizontal, ScrollableContainer
from rich.table import Table
from rich.panel import Panel

from src.tests.luscher_calc import calculate_luscher
from src.data.interpretations import get_luscher_interpretation
from src.models.database import save_result
from src.models.test_result import TestResultCreate
from src.screens.confirm_modal import ConfirmModal
from src.models.database import get_user


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

COLOR_FG = {
    0: "black",
    1: "white",
    2: "white",
    3: "white",
    4: "black",
    5: "white",
    6: "white",
    7: "white",
}


class LuscherScreen(Screen):
    BINDINGS = [
        Binding("up", "focus_previous", "↑", priority=True),
        Binding("down", "focus_next", "↓", priority=True),
        Binding("left", "focus_previous", "←", priority=True),
        Binding("right", "focus_next", "→", priority=True),
        Binding("escape", "back", "Назад"),
        Binding("1", "select_1", show=False),
        Binding("2", "select_2", show=False),
        Binding("3", "select_3", show=False),
        Binding("4", "select_4", show=False),
        Binding("5", "select_5", show=False),
        Binding("6", "select_6", show=False),
        Binding("7", "select_7", show=False),
        Binding("8", "select_8", show=False),
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
        self.test_completed = False
        self.color_positions = list(range(8))
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
            Label("Цветовой тест Люшера", id="title"),
            Static(id="round_label"),
            Horizontal(
                Button(id="color_0"), Button(id="color_1"),
                Button(id="color_2"), Button(id="color_3"),
                Button(id="color_4"), Button(id="color_5"),
                Button(id="color_6"), Button(id="color_7"),
                id="color_buttons",
            ),
            Static(id="progress"),
            ScrollableContainer(Static(id="result_area"), id="result_scroll"),
            id="main_content",
        )
        yield Footer()

    def _setup_button(self, btn: Button, color: int, pos: int, visible: bool):
        if visible:
            name = COLOR_NAMES_RU[color][:4]
            bg = COLOR_BG[color]
            fg = COLOR_FG[color]
            btn.label = f"{pos+1}.{name}"
            btn.styles.background = bg
            btn.styles.color = fg
            btn.styles.width = 8
        btn.display = visible

    def _rebuild_buttons(self):
        visible = set(self.remaining_colors)
        visual_rank = 0
        for pos in range(8):
            color = self.color_positions[pos]
            btn = self.query_one(f"#color_{pos}", Button)
            if color in visible:
                self._setup_button(btn, color, visual_rank, True)
                visual_rank += 1
            else:
                self._setup_button(btn, color, 0, False)

    def start_round(self):
        self.current_rank = 0
        self.remaining_colors = list(range(8))
        random.shuffle(self.color_positions)
        self._rebuild_buttons()
        self.show_colors()

    def on_mount(self):
        self.start_round()

    def show_colors(self):
        round_num = 1 if self.round == 1 else 2
        self.query_one("#round_label", Static).update(
            f"Р{round_num}: осталось {len(self.remaining_colors)}"
        )
        self.query_one("#progress", Static).update(
            f"Выбрано: {self.current_rank} / 8"
        )
        self.query_one("#result_area", Static).update("")

    def _select_by_number(self, num: int):
        visible = [c for c in self.color_positions if c in set(self.remaining_colors)]
        if num < 0 or num >= len(visible):
            return
        self.select_color(visible[num])

    def action_select_1(self): self._select_by_number(0)
    def action_select_2(self): self._select_by_number(1)
    def action_select_3(self): self._select_by_number(2)
    def action_select_4(self): self._select_by_number(3)
    def action_select_5(self): self._select_by_number(4)
    def action_select_6(self): self._select_by_number(5)
    def action_select_7(self): self._select_by_number(6)
    def action_select_8(self): self._select_by_number(7)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id and event.button.id.startswith("color_"):
            pos = int(event.button.id.split("_")[1])
            color = self.color_positions[pos]
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
                self.query_one("#round_label", Static).update(
                    "Р2: выберите самый приятный цвет (1-8)"
                )
                self.start_round()
            else:
                self.finish_test()
        else:
            self._rebuild_buttons()
            self.show_colors()

    def _color_block(self, color: int) -> str:
        bg = COLOR_BG[color]
        fg = COLOR_FG[color]
        return f"[{fg} on {bg}]  {COLOR_NAMES_RU[color]}  [/]"

    def finish_test(self):
        from rich.console import Group
        from rich.text import Text

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

        self.query_one("#color_buttons", Horizontal).display = False
        self.query_one("#round_label", Static).update("[bold]Тест завершён[/bold]")
        self.query_one("#progress", Static).update("")

        table = Table(show_header=False, box=None, padding=(0, 2), collapse_padding=True)
        table.add_column("Ранг", justify="right", style="bold")
        table.add_column("1-й выбор", no_wrap=True)
        table.add_column("2-й выбор", no_wrap=True)
        for i in range(8):
            c1 = self.choices1[i]
            c2 = self.choices2[i]
            table.add_row(
                str(i + 1),
                self._color_block(c1),
                self._color_block(c2),
            )

        stats = (
            f"[bold yellow]Тревожность:[/bold yellow] [cyan]{result['anxiety_pct']:.0f}%[/cyan]  |  "
            f"[bold yellow]Компенсация:[/bold yellow] [cyan]{result['compensation_pct']:.0f}%[/cyan]  |  "
            f"[bold yellow]Активность:[/bold yellow] [cyan]{result['activity_pct']:.0f}%[/cyan]  |  "
            f"[bold yellow]Работоспособность:[/bold yellow] [cyan]{result['performance_pct']:.0f}%[/cyan]  |  "
            f"[bold yellow]Вегетатика:[/bold yellow] [cyan]{result['vegetative_pct']:.0f}%[/cyan]"
        )

        group = Group(
            Panel(table, title="Ваш выбор цветов", padding=(0, 1)),
            Text(""),
            Text.from_markup(stats),
            Text(""),
            Panel(interpretation, title="Интерпретация", padding=(0, 1)),
        )
        self.query_one("#result_area", Static).update(
            Panel(group, title="Цветовой тест Люшера", border_style="magenta", padding=(0, 1))
        )
        self.notify("Результат сохранён", severity="information")

        flat_scores = {k: v for k, v in result.items() if isinstance(v, (int, float))}
        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Цветовой тест Люшера",
            raw_data=f"{result['choices1']}/{result['choices2']}",
            scores=flat_scores,
            interpretation=interpretation,
        ))
        self.test_completed = True
