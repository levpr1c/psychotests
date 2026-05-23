"""User creation screen."""

from datetime import date

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, Label, Button
from textual.containers import Vertical, Horizontal

from src.models.database import create_user
from src.models.user import UserCreate


class UserCreateScreen(Screen):
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

    def action_back(self):
        self.dismiss(False)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Новый пользователь", id="title"),
            Label("Имя пользователя", id="name_label"),
            Horizontal(Input(placeholder="Имя пользователя", id="name_input"), id="name_row"),
            Label("Дата рождения", id="birth_label"),
            Horizontal(Input(placeholder="ГГГГ-ММ-ДД", id="birth_input"), id="birth_row"),
            Horizontal(Button("Создать", id="create_btn", variant="primary"), id="create_row"),
            id="main_content",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create_btn":
            self.create_user()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "birth_input":
            self.create_user()
        elif event.input.id == "name_input":
            self.query_one("#birth_input", Input).focus()

    def create_user(self):
        name = self.query_one("#name_input", Input).value.strip()
        birth_str = self.query_one("#birth_input", Input).value.strip()

        if not name:
            self.notify("Введите имя пользователя", severity="error")
            return

        birth_date = None
        if birth_str:
            try:
                parts = birth_str.split("-")
                birth_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                self.notify("Неверный формат даты. Используйте ГГГГ-ММ-ДД", severity="error")
                return

        try:
            user = create_user(UserCreate(name=name, birth_date=birth_date))
        except Exception as e:
            self.notify(f"Ошибка: {e}", severity="error")
            return
        self.notify(f"Пользователь '{name}' создан", severity="information")
        self.dismiss(True)
