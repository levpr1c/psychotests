"""User selection screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, ListView, ListItem, Label, Button
from textual.containers import Vertical, Horizontal

from src.models.database import get_all_users, delete_user
from src.screens.main_menu import MainMenuScreen
from src.screens.confirm_modal import ConfirmModal


class UserSelectScreen(Screen):
    BINDINGS = [
        Binding("up", "focus_previous", "↑", priority=True),
        Binding("down", "focus_next", "↓", priority=True),
        Binding("left", "focus_previous", "←", priority=True),
        Binding("right", "focus_next", "→", priority=True),
        Binding("escape", "back", "Назад"),
    ]

    def action_focus_next(self):
        focused = self.focused
        if isinstance(focused, ListView):
            lv = focused
            if lv.index is None or lv.index < len(lv) - 1:
                lv.action_cursor_down()
                return
            # At bottom of list, move focus to next widget (New User button)
            self.focus_next()
            return
        elif isinstance(focused, Button):
            # In button group, move focus to next button or wrap to list
            if focused.id == "new_user":
                self.query_one("#history", Button).focus()
            elif focused.id == "history":
                self.query_one("#user_list", ListView).focus()
            return
        self.focus_next()

    def action_focus_previous(self):
        focused = self.focused
        if isinstance(focused, ListView):
            lv = focused
            if lv.index is not None and lv.index > 0:
                lv.action_cursor_up()
                return
            # At top of list, move focus to previous widget (History button)
            self.query_one("#history", Button).focus()
            return
        elif isinstance(focused, Button):
            # In button group, move focus to previous button or wrap to list
            if focused.id == "history":
                self.query_one("#new_user", Button).focus()
            elif focused.id == "new_user":
                self.query_one("#user_list", ListView).focus()
            return
        self.focus_previous()

    def action_back(self):
        self.app.push_screen(ConfirmModal("Хотите выйти из программы?"), self._on_exit_confirm)

    def _on_exit_confirm(self, result: bool):
        if result:
            self.app.exit()
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("Выберите пользователя", id="title"),
            ListView(id="user_list"),
            Horizontal(
                Button("Новый пользователь", id="new_user", variant="primary"),
                Button("История", id="history", variant="default"),
                id="actions",
            ),
            id="main_content",
        )
        yield Footer()

    async def on_mount(self):
        await self.refresh_users()

    async def refresh_users(self):
        list_view = self.query_one("#user_list", ListView)
        await list_view.clear()
        users = get_all_users()
        if not users:
            await list_view.append(ListItem(Label("Нет пользователей. Создайте нового.", id="empty_label")))
        for user in users:
            birth = f" ({user.birth_date})" if user.birth_date else ""
            await list_view.append(
                ListItem(
                    Label(f"{user.name}{birth}"),
                    id=f"user_{user.id}",
                )
            )

    def on_list_view_selected(self, event: ListView.Selected):
        item_id = event.item.id
        if item_id and item_id.startswith("user_"):
            user_id = int(item_id.split("_")[1])
            self.app.push_screen(MainMenuScreen(user_id=user_id))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "new_user":
            self.app.push_screen("user_create", self._on_user_created)
        elif event.button.id == "history":
            self.app.push_screen("history")

    async def _on_user_created(self, result):
        if result:
            await self.refresh_users()
