"""Main menu screen with test list."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static
from textual.containers import Vertical

from src.screens.biorhythm import BiorhythmScreen
from src.screens.eysenck import EysenckScreen
from src.screens.connect import ConnectScreen
from src.screens.economy import EconomyScreen
from src.screens.heart import HeartScreen
from src.screens.neiro import NeiroScreen
from src.screens.selftest import SelftestScreen
from src.screens.stress import StressScreen
from src.screens.luscher import LuscherScreen
from src.models.database import get_user
from src.screens.confirm_modal import ConfirmModal


TESTS = [
    ("1", "Биоритмы", "Расчёт физических, эмоциональных и интеллектуальных циклов", BiorhythmScreen),
    ("2", "Тест Айзенка (EPI)", "Оценка экстраверсии, нейротизма и типа темперамента", EysenckScreen),
    ("3", "Тест на совместимость", "Оценка коммуникативных способностей", ConnectScreen),
    ("4", "Деловая сфера", "Стиль делового поведения и экономического мышления", EconomyScreen),
    ("5", "Вегетативная система", "Оценка сердечно-сосудистой регуляции", HeartScreen),
    ("6", "Неврологический тест", "Скрининг неврологических симптомов", NeiroScreen),
    ("7", "Самооценка", "Оценка уровня самооценки", SelftestScreen),
    ("8", "Стресс", "Оценка уровня стресса", StressScreen),
    ("9", "Цветовой тест Люшера", "Проективная оценка психоэмоционального состояния", LuscherScreen),
]


class MainMenuScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Назад"),
    ]

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def compose(self) -> ComposeResult:
        user = get_user(self.user_id)
        name = user.name if user else "Неизвестный"
        yield Header()
        yield Vertical(
            Label(f"Пользователь: {name}", id="user_label"),
            Label("Выберите тест:", id="title"),
            ListView(
                *[
                    ListItem(Label(f"{num}. {name}"), id=f"test_{i}")
                    for i, (num, name, desc, _) in enumerate(TESTS)
                ],
                id="test_list",
            ),
            id="main_content",
        )
        yield Footer()

    def action_back(self):
        self.app.push_screen(ConfirmModal("Хотите выйти?"), self._on_exit_confirm)

    def _on_exit_confirm(self, result: bool):
        if result:
            self.app.pop_screen()

    def on_list_view_selected(self, event: ListView.Selected):
        if event.item.id and event.item.id.startswith("test_"):
            idx = int(event.item.id.split("_")[1])
            _, _, _, screen_cls = TESTS[idx]
            self.app.push_screen(screen_cls(user_id=self.user_id))
