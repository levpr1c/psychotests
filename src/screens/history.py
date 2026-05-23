"""Test results history screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, ListView, ListItem, Label
from textual.containers import Vertical

from src.models.database import get_all_results


class HistoryScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Назад"),
    ]

    def action_back(self):
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("История результатов", id="title"),
            ListView(id="results_list"),
            id="main_content",
        )
        yield Footer()

    async def on_mount(self):
        list_view = self.query_one("#results_list", ListView)
        results = get_all_results()
        if not results:
            await list_view.append(ListItem(Label("Нет сохранённых результатов.")))
        for r in results:
            date_str = r.created_at.strftime("%d.%m.%Y %H:%M")
            await list_view.append(
                ListItem(
                    Label(f"[{date_str}] {r.test_name} (пользователь #{r.user_id})"),
                    id=f"result_{r.id}",
                )
            )
