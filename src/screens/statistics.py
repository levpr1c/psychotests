"""Statistics screen with bar charts and result history."""

from collections import defaultdict

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button, Static
from textual.containers import Horizontal, ScrollableContainer

from src.models.database import (
    get_results_for_user,
    get_all_results,
    get_user,
    get_test_names,
)
from src.models.test_result import TestResult
from src.screens.result_view import ResultViewScreen


def _bar(value: float, max_val: float, width: int = 30) -> Text:
    if max_val <= 0:
        return Text("░" * width, style="bright_black")
    filled = int(value / max_val * width)
    t = Text()
    t.append("█" * filled, style="cyan")
    t.append("░" * (width - filled), style="bright_black")
    return t


def _main_score_key(test_name: str) -> str | None:
    key_map = {
        "Тест Айзенка (EPI)": "extraversion",
        "Тест на совместимость": "total",
        "Деловая сфера": "total",
        "Вегетативная система": "total",
        "Неврологический тест": "total",
        "Самооценка": "total",
        "Стресс": "total",
        "Цветовой тест Люшера": "activity_pct",
    }
    return key_map.get(test_name)


def _build_chart(results: list[TestResult]) -> Table:
    counts: dict[str, int] = {}
    scores_by_test: dict[str, list[float]] = defaultdict(list)

    for r in results:
        counts[r.test_name] = counts.get(r.test_name, 0) + 1
        score_key = _main_score_key(r.test_name)
        if score_key and score_key in r.scores:
            val = r.scores[score_key]
            if isinstance(val, (int, float)):
                scores_by_test[r.test_name].append(float(val))

    table = Table(show_header=False, box=None, padding=(0, 1), collapse_padding=True, expand=True)
    table.add_column("", no_wrap=True)
    table.add_column("", no_wrap=True)
    table.add_column("", justify="right", style="bold", no_wrap=True)

    all_keys = sorted(counts, key=lambda k: -counts[k])
    max_count = max(counts.values()) if counts else 1

    table.add_row(
        Text("Тест", style="bold underline"),
        Text("", style="bold underline"),
        Text("Кол-во", style="bold underline"),
    )
    for name in all_keys:
        c = counts[name]
        avg = ""
        if name in scores_by_test:
            vals = scores_by_test[name]
            avg_text = f"{sum(vals)/len(vals):.1f}"
            avg = f"  ø {avg_text}"
        table.add_row(name, _bar(c, max_count), f"{c}{avg}")
    return table



class StatisticsScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Назад"),
        Binding("up", "focus_previous", "↑", priority=True),
        Binding("down", "focus_next", "↓", priority=True),
        Binding("left", "focus_previous", "←", priority=True),
        Binding("right", "focus_next", "→", priority=True),
    ]

    def __init__(self, user_id: int | None = None):
        super().__init__()
        self.user_id = user_id
        self._all_results: list[TestResult] = []
        self._filter: str | None = None
        self._filter_names: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Label("Статистика", id="title"),
            Static(id="user_info"),
            Static(id="chart_area"),
            Label("Фильтр:", id="filter_label"),
            Horizontal(id="filter_buttons"),
            Label("Результаты:", id="history_heading"),
            ListView(id="results_list"),
            id="main_content",
        )
        yield Footer()

    def action_focus_next(self):
        focused = self.focused
        if isinstance(focused, ListView):
            lv = focused
            idx = lv.index
            if idx is None or idx < len(lv) - 1:
                lv.action_cursor_down()
                return
        self.focus_next()

    def action_focus_previous(self):
        focused = self.focused
        if isinstance(focused, ListView):
            lv = focused
            idx = lv.index
            if idx is not None and idx > 0:
                lv.action_cursor_up()
                return
        self.focus_previous()

    def action_back(self):
        self.app.pop_screen()

    async def on_mount(self):
        if self.user_id is not None:
            user = get_user(self.user_id)
            if user:
                self.query_one("#user_info", Static).update(
                    Panel(f"[bold]Пользователь:[/bold] {user.name}")
                )
            raw_results = get_results_for_user(self.user_id)
            if not raw_results:
                raw_results = get_all_results()
        else:
            self.query_one("#user_info", Static).update(
                Panel("[dim]Все пользователи[/dim]")
            )
            raw_results = get_all_results()

        self._all_results = raw_results

        chart = _build_chart(self._all_results)
        self.query_one("#chart_area", Static).update(Panel(chart, title="По тестам"))

        test_names = get_test_names()
        self._filter_names = list(test_names)
        filter_box = self.query_one("#filter_buttons", Horizontal)
        btn_all = Button("Все", id="filter_all", variant="primary")
        filter_box.mount(btn_all)
        for idx, name in enumerate(test_names):
            short = name[:20]
            btn = Button(short, id=f"filter_{idx}", variant="default")
            filter_box.mount(btn)

        await self._refresh_list()

    async def _refresh_list(self):
        filtered = self._all_results
        if self._filter:
            filtered = [r for r in filtered if r.test_name == self._filter]

        total = len(filtered)
        self.query_one("#history_heading", Label).update(
            f"Результаты ({total}):"
        )

        list_view = self.query_one("#results_list", ListView)
        await list_view.clear()
        if not filtered:
            await list_view.append(ListItem(Label("Нет результатов.")))
        for r in filtered:
            first_line = ""
            if r.interpretation:
                first_line = r.interpretation.split("\n")[0]
            else:
                vals = []
                for k, v in r.scores.items():
                    if isinstance(v, (int, float)):
                        vals.append(f"{k}={v:.1f}")
                if vals:
                    first_line = ", ".join(vals[:4])
            text = f"[{r.created_at.strftime('%d.%m.%Y %H:%M')}] [bold]{r.test_name}[/bold]"
            if first_line:
                text += "\n" + first_line
            await list_view.append(
                ListItem(Static(text), id=f"result_{r.id}")
            )

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "filter_all":
            self._filter = None
            for btn in self.query("#filter_buttons Button"):
                btn.variant = "default"
            self.query_one("#filter_all", Button).variant = "primary"
            await self._refresh_list()
        elif event.button.id and event.button.id.startswith("filter_"):
            idx = int(event.button.id.split("_")[1])
            self._filter = self._filter_names[idx]
            for btn in self.query("#filter_buttons Button"):
                btn.variant = "default"
            event.button.variant = "primary"
            await self._refresh_list()

    def on_list_view_selected(self, event: ListView.Selected):
        if event.item.id and event.item.id.startswith("result_"):
            rid = int(event.item.id.split("_")[1])
            result = next((r for r in self._all_results if r.id == rid), None)
            if result is not None:
                self._show_detail(result)

    def _show_detail(self, result: TestResult):
        if result.test_name == "Цветовой тест Люшера" and result.raw_data:
            self._show_luscher_detail(result)
            return

        scores_text = ""
        for k, v in result.scores.items():
            if isinstance(v, float):
                scores_text += f"{k}: {v:.2f}\n"
            else:
                scores_text += f"{k}: {v}\n"

        detail = (
            f"[bold]Тест:[/bold] {result.test_name}\n"
            f"[bold]Дата:[/bold] {result.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"[bold]Пользователь:[/bold] #{result.user_id}\n"
        )
        if scores_text:
            detail += f"\n[bold]Показатели:[/bold]\n{scores_text}\n"
        if result.interpretation:
            detail += f"\n[bold]Интерпретация:[/bold]\n{result.interpretation}"

        self.app.push_screen(ResultViewScreen("Результат", detail))

    def _show_luscher_detail(self, result: TestResult):
        import ast
        from rich.console import Group
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text

        parts = result.raw_data.split("/")
        choices1 = ast.literal_eval(parts[0])
        choices2 = ast.literal_eval(parts[1])

        from src.screens.luscher import COLOR_NAMES_RU, COLOR_BG, COLOR_FG

        table = Table(show_header=False, box=None, padding=(0, 2), collapse_padding=True)
        table.add_column("Ранг", justify="right", style="bold")
        table.add_column("1-й выбор", no_wrap=True)
        table.add_column("2-й выбор", no_wrap=True)
        for i in range(len(choices1)):
            c1 = choices1[i]
            c2 = choices2[i]
            n1 = COLOR_NAMES_RU.get(c1, "?")
            n2 = COLOR_NAMES_RU.get(c2, "?")
            b1 = COLOR_BG.get(c1, "default")
            b2 = COLOR_BG.get(c2, "default")
            f1 = COLOR_FG.get(c1, "white")
            f2 = COLOR_FG.get(c2, "white")
            table.add_row(
                str(i + 1),
                f"[{f1} on {b1}]  {n1}  [/]",
                f"[{f2} on {b2}]  {n2}  [/]",
            )

        stats = ""
        for k in ("anxiety_pct", "compensation_pct", "activity_pct", "performance_pct", "vegetative_pct"):
            v = result.scores.get(k)
            if v is not None:
                stats += f"{k}: {v:.0f}%  |  "
        stats = stats.rstrip("  |  ")

        group = Group(
            Panel(table, title="Ваш выбор цветов", padding=(0, 1)),
            Text(""),
            Text(stats, style="bold cyan") if stats else Text(""),
            Text(""),
            Panel(result.interpretation, title="Интерпретация", padding=(0, 1)) if result.interpretation else Text(""),
        )
        self.app.push_screen(ResultViewScreen("Цветовой тест Люшера", group))
