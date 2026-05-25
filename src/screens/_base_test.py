"""Base questionnaire screen for Likert-scale tests."""

import random

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Label, Button, RadioSet, RadioButton, Static
from textual.containers import Vertical, Horizontal

from src.screens.confirm_modal import ConfirmModal
from src.models.database import get_user


def shuffle_questions(
    items: list,
    key_fn=None,
) -> list:
    """Shuffle items, spreading same-key items apart if key_fn is provided."""
    items = list(items)
    if key_fn is None:
        random.shuffle(items)
        return items

    groups = {}
    for item in items:
        k = key_fn(item)
        groups.setdefault(k, []).append(item)

    for g in groups.values():
        random.shuffle(g)

    sorted_groups = sorted(groups.values(), key=len, reverse=True)
    result = []
    while any(sorted_groups):
        for group in sorted_groups:
            if group:
                result.append(group.pop(0))
    return result


class BaseTestScreen(Screen):
    """Base class for tests with 1-5 Likert scale questions."""

    BINDINGS = [
        Binding("up", "focus_previous", "↑", priority=True),
        Binding("down", "focus_next", "↓", priority=True),
        Binding("left", "focus_previous", "←", priority=True),
        Binding("right", "focus_next", "→", priority=True),
        Binding("escape", "back", "Назад"),
        Binding("enter", "next", show=False, priority=True),
        Binding("1", "select_1", show=False),
        Binding("2", "select_2", show=False),
        Binding("3", "select_3", show=False),
        Binding("4", "select_4", show=False),
        Binding("5", "select_5", show=False),
    ]

    QUESTIONS: list[str] = []
    TITLE = ""

    def action_focus_next(self):
        focused = self.focused
        if isinstance(focused, RadioSet):
            rs = focused
            if rs.pressed_index < len(rs.children) - 1:
                rs.action_next_button()
                return
        self.focus_next()

    def action_focus_previous(self):
        focused = self.focused
        if isinstance(focused, RadioSet):
            rs = focused
            if rs.pressed_index > 0:
                rs.action_previous_button()
                return
        self.focus_previous()

    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id
        self.current_q = 0
        self.answers: list[int] = []
        self.current_answer: int | None = None
        self.test_completed: bool = False
        user = get_user(user_id)
        self.username = user.name if user else "Неизвестный"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label(f"👤 {self.username}", id="user_label"),
            Label(self.TITLE, id="title"),
            Label(id="question_label"),
            Static("1—Нет  2—Скорее нет  3—Не знаю  4—Скорее да  5—Да", id="key_legend"),
            RadioSet(
                RadioButton("1 — Нет", id="r1"),
                RadioButton("2 — Скорее нет", id="r2"),
                RadioButton("3 — Не знаю", id="r3"),
                RadioButton("4 — Скорее да", id="r4"),
                RadioButton("5 — Да", id="r5"),
                id="answer_set",
            ),
            Horizontal(
                Button("Далее", id="next_btn", variant="primary"),
                Button("Назад", id="prev_btn"),
                id="nav_buttons",
            ),
            Static(id="result_area"),
            id="main_content",
        )
        yield Footer()

    def _clear_radio(self):
        radio = self.query_one("#answer_set", RadioSet)
        with radio.prevent(RadioButton.Changed):
            for btn in radio.query(RadioButton):
                btn.value = False
        radio._pressed_button = None
        radio._selected = None

    def on_mount(self):
        if hasattr(self, "SCALES") and self.SCALES:
            pairs = list(zip(list(self.QUESTIONS), list(self.SCALES)))
            pairs = shuffle_questions(pairs, key_fn=lambda p: p[1])
            self.QUESTIONS = [p[0] for p in pairs]
            self.SCALES = [p[1] for p in pairs]
        else:
            self.QUESTIONS = shuffle_questions(list(self.QUESTIONS))
        self.show_question()

    def show_question(self):
        if self.current_q >= len(self.QUESTIONS):
            self.finish_test()
            return

        self.query_one("#question_label", Label).update(
            f"{self.current_q + 1}/{len(self.QUESTIONS)}: {self.QUESTIONS[self.current_q]}"
        )
        self.query_one("#answer_set", RadioSet).disabled = False
        self._clear_radio()
        self.current_answer = None
        self.query_one("#result_area", Static).update("")

    def on_radio_set_changed(self, event: RadioSet.Changed):
        self.current_answer = event.index

    def action_back(self):
        if self.test_completed:
            # After test completion, go back directly without confirmation
            self.app.pop_screen()
        else:
            # During test, show confirmation
            self.app.push_screen(ConfirmModal("Хотите выйти из теста?"), self._on_exit_confirm)

    def _on_exit_confirm(self, result: bool):
        if result:
            self.app.pop_screen()

    def action_next(self):
        if self.test_completed:
            return
        focused = self.focused
        if focused and focused.id == "prev_btn":
            if self.current_q > 0:
                self.current_q -= 1
                self.show_question()
            else:
                self.app.push_screen(ConfirmModal("Хотите выйти из теста?"), self._on_exit_confirm)
            return
        if self.current_answer is None:
            self.notify("Выберите ответ", severity="error")
            return
        self.answers.append(self.current_answer)
        self.current_q += 1
        self.show_question()

    def _select_num(self, index: int):
        if self.test_completed:
            return
        radio = self.query_one("#answer_set", RadioSet)
        buttons = list(radio.query(RadioButton))
        if 0 <= index < len(buttons):
            with radio.prevent(RadioButton.Changed):
                for i, btn in enumerate(buttons):
                    btn.value = (i == index)
            radio._pressed_button = buttons[index]
            radio._selected = index
            self.current_answer = index

    def action_select_1(self):
        self._select_num(0)
    def action_select_2(self):
        self._select_num(1)
    def action_select_3(self):
        self._select_num(2)
    def action_select_4(self):
        self._select_num(3)
    def action_select_5(self):
        self._select_num(4)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "next_btn":
            self.action_next()

        elif event.button.id == "prev_btn":
            if self.current_q > 0:
                self.current_q -= 1
                self.show_question()
            else:
                self.app.push_screen(ConfirmModal("Хотите выйти из теста?"), self._on_exit_confirm)

    def _show_result(self, text: str, title: str = "Результат", border_style: str = "cyan"):
        from rich.panel import Panel
        self.query_one("#result_area", Static).update(
            Panel(text, title=title, border_style=border_style, padding=(0, 1))
        )

    def finish_test(self):
        self.test_completed = True
        raise NotImplementedError
