"""Read-only result detail screen with scrolling."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Static
from textual.containers import ScrollableContainer


class ResultViewScreen(Screen):
    BINDINGS = [
        Binding("escape", "dismiss", "Назад"),
        Binding("up", "scroll_up", "↑", priority=True),
        Binding("down", "scroll_down", "↓", priority=True),
    ]

    def __init__(self, title: str, content: str):
        super().__init__()
        self._title = title
        self._content = content

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Static(self._content, id="detail_content"),
            id="detail_scroll",
        )
        yield Footer()

    def action_dismiss(self):
        self.app.pop_screen()

    def action_scroll_up(self):
        self.query_one("#detail_scroll", ScrollableContainer).scroll_up()

    def action_scroll_down(self):
        self.query_one("#detail_scroll", ScrollableContainer).scroll_down()
