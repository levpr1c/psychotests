"""Eysenck EPI test screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Label, Button, RadioSet, RadioButton, Static
from textual.containers import Vertical, Horizontal

from src.data.questions import EYSENCK_QUESTIONS
from src.tests.eysenck_calc import score_eysenck
from src.data.interpretations import get_eysenck_interpretation
from src.models.database import save_result
from src.models.test_result import TestResultCreate
from src.screens.confirm_modal import ConfirmModal
from src.models.database import get_user
from src.screens._base_test import shuffle_questions


class EysenckScreen(Screen):
    BINDINGS = [
        Binding("up", "focus_previous", "↑", priority=True),
        Binding("down", "focus_next", "↓", priority=True),
        Binding("left", "focus_previous", "←", priority=True),
        Binding("right", "focus_next", "→", priority=True),
        Binding("escape", "back", "Назад"),
        Binding("enter", "next", show=False, priority=True),
        Binding("1", "select_1", show=False),
        Binding("2", "select_2", show=False),
    ]

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
        self.answers: list[bool] = []
        self.current_answer: int | None = None
        self.test_completed = False
        user = get_user(user_id)
        self.username = user.name if user else "Неизвестный"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label(f"👤 {self.username}", id="user_label"),
            Label("Тест Айзенка (EPI)", id="title"),
            Label(id="question_label"),
            Static("1 — Да    2 — Нет", id="key_legend"),
            RadioSet(
                RadioButton("Да", id="ans_yes"),
                RadioButton("Нет", id="ans_no"),
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
        self._questions = shuffle_questions(EYSENCK_QUESTIONS, key_fn=lambda q: q[1])
        self.show_question()

    def show_question(self):
        if self.current_q >= len(self._questions):
            self.finish_test()
            return

        q_text, scale = self._questions[self.current_q]
        self.query_one("#question_label", Label).update(
            f"{self.current_q + 1}/{len(self._questions)} [{scale}]: {q_text}"
        )
        self._clear_radio()
        self.current_answer = None
        self.query_one("#result_area", Static).update("")

    def on_radio_set_changed(self, event: RadioSet.Changed):
        self.current_answer = event.index

    def action_back(self):
        if self.test_completed:
            self.app.pop_screen()
            return
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
        self.answers.append(self.current_answer == 0)
        self.current_q += 1
        self.show_question()

    def _select_num(self, index: int):
        if self.test_completed:
            return
        radio = self.query_one("#answer_set", RadioSet)
        buttons = list(radio.query(RadioButton))
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

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "next_btn":
            self.action_next()

        elif event.button.id == "prev_btn":
            if self.current_q > 0:
                self.current_q -= 1
                self.show_question()
            else:
                self.app.push_screen(ConfirmModal("Хотите выйти из теста?"), self._on_exit_confirm)

    def finish_test(self):
        scales = [s for _, s in self._questions]
        result = score_eysenck(self.answers, scales)
        interpretation = get_eysenck_interpretation(
            result["extraversion"], result["neuroticism"], result["lie"]
        )

        self.query_one("#question_label", Label).update("")
        self.query_one("#answer_set", RadioSet).disabled = True
        self.query_one("#nav_buttons", Horizontal).display = False
        self.query_one("#result_area", Static).update(interpretation)

        save_result(TestResultCreate(
            user_id=self.user_id,
            test_name="Тест Айзенка (EPI)",
            scores=result,
            interpretation=interpretation,
        ))

        self.test_completed = True
        self.notify("Результат сохранён", severity="information")
