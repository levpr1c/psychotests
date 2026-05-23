"""Reusable confirmation modal screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Static, Button
from textual.containers import Vertical, Horizontal


class ConfirmModal(Screen[bool]):
    DEFAULT_CSS = """
    ConfirmModal {
        background: rgba(0, 0, 0, 0.45);
        align: center middle;
        overflow-y: hidden;
    }
    #confirm_dialog {
        width: auto;
        height: auto;
        border: solid $accent;
        padding: 1 3;
        background: $surface;
    }
    #confirm_message {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
    }
    #confirm_buttons {
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("up", "focus_previous", "↑", priority=True),
        Binding("down", "focus_next", "↓", priority=True),
        Binding("left", "focus_previous", "←", priority=True),
        Binding("right", "focus_next", "→", priority=True),
        Binding("escape", "back", "Нет"),
        Binding("q", "confirm", "Да"),
        Binding("й", "confirm", "Да"),
    ]

    def __init__(self, message: str, confirm_text: str = "Да", cancel_text: str = "Нет"):
        super().__init__()
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm_dialog"):
            yield Static(self.message, id="confirm_message")
            with Horizontal(id="confirm_buttons"):
                yield Button(self.confirm_text, id="confirm_yes", variant="primary")
                yield Button(self.cancel_text, id="confirm_no")

    def action_focus_next(self):
        self.focus_next()

    def action_focus_previous(self):
        self.focus_previous()

    def on_mount(self):
        dlg = self.query_one("#confirm_dialog")
        dlg.styles.width = "auto"
        dlg.styles.height = "auto"

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "confirm_yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_back(self):
        self.dismiss(False)

    def action_confirm(self):
        self.dismiss(True)
