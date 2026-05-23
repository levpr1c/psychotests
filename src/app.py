"""Main Textual application."""

from textual.app import App
from textual.binding import Binding

from src.screens.main_menu import MainMenuScreen
from src.screens.user_select import UserSelectScreen
from src.screens.user_create import UserCreateScreen
from src.screens.history import HistoryScreen
from src.screens.confirm_modal import ConfirmModal


class PsychoApp(App):
    TITLE = "Психологические тесты"
    SUB_TITLE = "Сборка прог по психологии"
    CSS_PATH = "app.tcss"

    SCREENS = {
        "user_select": UserSelectScreen,
        "user_create": UserCreateScreen,
        "history": HistoryScreen,
    }

    BINDINGS = [
        Binding("q", "quit_program", "Выход"),
        Binding("й", "quit_program", "Выход"),
        Binding("escape", "back", "Назад"),
    ]

    async def action_back(self) -> None:
        if len(self.screen_stack) <= 1:
            await self.action_quit()
        else:
            self.pop_screen()

    def action_quit_program(self):
        self.push_screen(ConfirmModal("Хотите выйти из программы?"), self._on_quit_program)

    def _on_quit_program(self, result: bool):
        if result:
            self.exit()

    def on_mount(self):
        self.push_screen("user_select")
