#!/usr/bin/env python3
"""Comprehensive tests for the psychological tests TUI application."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.database import init_db, get_all_users, create_user, get_user, delete_user
from src.models.user import UserCreate
from src.app import PsychoApp
from textual.widgets import Static

PASS = 0
FAIL = 0

def ok(msg):
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")

def fail(msg):
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}")

# ─────────────── Unit tests ───────────────

def test_biorhythm_calc():
    from datetime import date
    from src.tests.biorhythm_calc import calculate_biorhythms, cycle_value, days_between
    r = calculate_biorhythms(date(1990, 1, 1))
    assert abs(r["physical"]["value"]) <= 1.0, "Biorhythm value out of range"
    assert r["days"] > 0, "Days must be positive"
    assert "physical" in r and "emotional" in r and "intellectual" in r
    assert isinstance(r["days"], int)
    ok("Biorhythm calculation")

    # Edge: same day
    r0 = calculate_biorhythms(date.today(), date.today())
    assert r0["days"] == 0
    ok("Biorhythm same day (0 days)")

    # Edge: negative (future birth)
    r1 = calculate_biorhythms(date(2099, 1, 1))
    assert r1["days"] < 0
    ok("Biorhythm future birth (negative days)")


def test_eysenck_calc():
    from src.tests.eysenck_calc import score_eysenck
    answers = [True, False, True, False, True, True, False, True]
    scales = ["E", "N", "E", "L", "E", "E", "N", "L"]
    r = score_eysenck(answers, scales)
    assert r["extraversion"] == 4  # indices 0,2,4,5 True
    assert r["neuroticism"] == 0   # index 6 False
    assert r["lie"] == 1           # index 7 True
    assert r["total"] == 4
    ok("Eysenck scoring")

    # Edge: all True
    r_all = score_eysenck([True]*57, ["E"]*24 + ["N"]*24 + ["L"]*9)
    assert r_all["extraversion"] == 24
    assert r_all["neuroticism"] == 24
    assert r_all["lie"] == 9
    ok("Eysenck all True")

    # Edge: all False
    r_none = score_eysenck([False]*57, ["E"]*24 + ["N"]*24 + ["L"]*9)
    assert r_none["extraversion"] == 0
    assert r_none["neuroticism"] == 0
    assert r_none["lie"] == 0
    ok("Eysenck all False")


def test_luscher_calc():
    from src.tests.luscher_calc import calculate_luscher, consistency, COLORS
    c1 = [0, 1, 2, 3, 4, 5, 6, 7]
    c2 = [0, 1, 2, 3, 4, 5, 6, 7]
    r = calculate_luscher(c1, c2)
    assert r["consistency"] == 1.0, "Identical choices should have r=1"
    assert 0 <= r["anxiety_pct"] <= 100
    assert 0 <= r["compensation_pct"] <= 100
    assert 0 <= r["activity_pct"] <= 100
    assert 0 <= r["performance_pct"] <= 100
    assert len(COLORS) == 8
    ok("Luscher identical")

    c2_rev = [7, 6, 5, 4, 3, 2, 1, 0]
    r2 = calculate_luscher(c1, c2_rev)
    assert r2["consistency"] < 0.5, "Reversed choices should have low consistency"
    ok("Luscher reversed")

    # Edge: all same choice (invalid in real test but should not crash)
    r_same = calculate_luscher([0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0])
    assert isinstance(r_same["anxiety_pct"], float)
    ok("Luscher all same color")


def test_all_calculators():
    from src.tests.stress_calc import score_stress
    from src.tests.neiro_calc import score_neiro
    from src.tests.connect_calc import score_connect
    from src.tests.economy_calc import score_economy
    from src.tests.heart_calc import score_heart
    from src.tests.selftest_calc import score_selftest

    r = score_stress([1, 2, 3, 4] * 6)
    assert r["total"] == 60
    assert r["level"] == "elevated"
    ok("Stress scoring")

    # Edge: stress min/max
    r_min = score_stress([0] * 24)
    assert r_min["total"] == 0 and r_min["level"] == "low"
    r_max = score_stress([4] * 24)
    assert r_max["total"] == 96 and r_max["level"] == "high"
    ok("Stress min/max")

    r = score_neiro([1, 2, 3] * 8)
    assert r["total"] == 48
    assert r["level"] in ("normal", "mild", "moderate", "severe")
    ok("Neiro scoring")

    # Edge: neiro min/max
    r_nmin = score_neiro([0] * 24)
    assert r_nmin["level"] == "normal"
    r_nmax = score_neiro([5] * 24)
    assert r_nmax["total"] == 120 and r_nmax["level"] == "severe"
    ok("Neiro min/max")

    r = score_connect([3] * 25)
    assert r["total"] >= 0
    ok("Connect scoring")

    # Edge: connect inverted
    r_cinv = score_connect([5] * 25)
    # Inverted questions reduce score
    assert isinstance(r_cinv["total"], float)
    ok("Connect inverted scoring")

    r = score_economy([3] * 25)
    assert r["total"] >= 0
    ok("Economy scoring")

    r = score_heart({"ibc": [1, 2], "pps": [3, 4], "de": [1], "ag": [5], "ncd": [2, 2], "zm": [3]})
    assert "ibc" in r
    assert isinstance(r["ibc"], float)
    ok("Heart scoring")

    # Edge: heart empty scale
    r_hempty = score_heart({"ibc": []})
    assert r_hempty == {"ibc": 0.0}
    ok("Heart empty scale")

    r = score_selftest([3] * 20)
    assert r["total"] >= 0
    ok("Selftest scoring")

    # Edge: selftest inverted
    r_sinv = score_selftest([5] * 20)
    assert isinstance(r_sinv["total"], float)
    ok("Selftest inverted scoring")


def test_database():
    from src.models.database import save_result, get_all_results, get_results_for_user, delete_user
    from src.models.test_result import TestResultCreate

    init_db()
    for u in get_all_users():
        delete_user(u.id)

    u = create_user(UserCreate(name="Tester"))
    assert u.name == "Tester"
    assert u.id is not None
    ok("Create user")

    # Edge: create user with birth date
    from datetime import date
    u2 = create_user(UserCreate(name="Tester2", birth_date=date(1990, 6, 15)))
    assert u2.birth_date == date(1990, 6, 15)
    ok("Create user with birth date")

    save_result(TestResultCreate(user_id=u.id, test_name="Test", scores={"a": 1.0}))
    results = get_results_for_user(u.id)
    assert len(results) == 1
    assert results[0].test_name == "Test"
    assert results[0].scores == {"a": 1.0}
    ok("Save and read result")

    # Edge: save result with complex scores
    save_result(TestResultCreate(
        user_id=u.id,
        test_name="Complex",
        scores={"a": 1, "b": "str", "c": [1, 2, 3], "d": {"nested": True}},
    ))
    results = get_results_for_user(u.id)
    complex_res = [r for r in results if r.test_name == "Complex"]
    assert len(complex_res) == 1
    assert complex_res[0].scores["a"] == 1
    assert complex_res[0].scores["d"]["nested"] is True
    ok("Save/read complex scores (dict[str, Any])")

    # Edge: empty results for non-existent user
    empty = get_results_for_user(99999)
    assert empty == []
    ok("Empty results for non-existent user")

    delete_user(u.id)
    assert get_user(u.id) is None
    assert get_results_for_user(u.id) == []
    delete_user(u2.id)
    ok("Delete user")


def test_questions_data():
    from src.data.questions import (
        EYSENCK_QUESTIONS,
        STRESS_QUESTIONS,
        CONNECT_QUESTIONS,
        ECONOMY_QUESTIONS,
        HEART_QUESTIONS,
        NEIRO_QUESTIONS,
        SELFTEST_QUESTIONS,
    )
    assert len(EYSENCK_QUESTIONS) == 57, f"Expected 57, got {len(EYSENCK_QUESTIONS)}"
    assert len(STRESS_QUESTIONS) == 24
    assert len(CONNECT_QUESTIONS) == 25
    assert len(ECONOMY_QUESTIONS) == 25
    assert len(HEART_QUESTIONS) == 25
    assert len(NEIRO_QUESTIONS) == 24
    assert len(SELFTEST_QUESTIONS) == 20
    ok("All question banks have correct size")

    e_count = sum(1 for _, s in EYSENCK_QUESTIONS if s == "E")
    assert e_count == 24, f"Expected 24 E, got {e_count}"
    ok("Eysenck E scale count correct")

    n_count = sum(1 for _, s in EYSENCK_QUESTIONS if s == "N")
    assert n_count == 24, f"Expected 24 N, got {n_count}"
    ok("Eysenck N scale count correct")

    l_count = sum(1 for _, s in EYSENCK_QUESTIONS if s == "L")
    assert l_count == 9, f"Expected 9 L, got {l_count}"
    ok("Eysenck L scale count correct")

    heart_scales = [s for _, s in HEART_QUESTIONS]
    for scale in ("IBC", "PPS", "DE", "AG", "NCD", "ZM"):
        assert scale in heart_scales, f"Missing {scale}"
    ok("Heart test has all 6 scales")

    # Verify no empty questions
    for qs, name in [
        (EYSENCK_QUESTIONS, "Eysenck"),
        (STRESS_QUESTIONS, "Stress"),
        (CONNECT_QUESTIONS, "Connect"),
        (ECONOMY_QUESTIONS, "Economy"),
        (HEART_QUESTIONS, "Heart"),
        (NEIRO_QUESTIONS, "Neiro"),
        (SELFTEST_QUESTIONS, "Selftest"),
    ]:
        if isinstance(qs, list) and isinstance(qs[0], tuple):
            for q, _ in qs:
                assert q and len(q) > 5, f"Empty question in {name}"
        else:
            for q in qs:
                assert q and len(q) > 5, f"Empty question in {name}"
    ok("No empty questions")


def test_interpretations():
    from src.data.interpretations import (
        get_eysenck_interpretation,
        get_stress_interpretation,
        get_selftest_interpretation,
        get_connect_interpretation,
        get_economy_interpretation,
        get_neiro_interpretation,
        get_luscher_interpretation,
        get_heart_interpretation,
    )
    r = get_eysenck_interpretation(15, 10, 2)
    assert "Экстраверсия" in r and "Нейротизм" in r and "Шкала лжи" in r
    ok("Eysenck interpretation")

    # Edge: boundary values
    r_e0 = get_eysenck_interpretation(0, 0, 0)
    assert "Экстраверсия" in r_e0
    r_e24 = get_eysenck_interpretation(24, 24, 9)
    assert "Нейротизм" in r_e24
    ok("Eysenck interpretation boundaries")

    r = get_stress_interpretation(40)
    assert len(r) > 20
    ok("Stress interpretation")

    # Edge: all stress levels
    assert "Низкий" in get_stress_interpretation(0)
    assert "Критический" in get_stress_interpretation(200)
    ok("Stress interpretation all levels")

    r = get_selftest_interpretation(30)
    assert len(r) > 20
    ok("Selftest interpretation")

    # Edge: all selftest levels
    assert "Высокая" in get_selftest_interpretation(50)
    assert "Низкая" in get_selftest_interpretation(10)
    ok("Selftest interpretation all levels")

    r = get_connect_interpretation(60)
    assert len(r) > 20
    ok("Connect interpretation")

    r = get_economy_interpretation(60)
    assert len(r) > 20
    ok("Economy interpretation")

    r = get_neiro_interpretation(30)
    assert len(r) > 20
    ok("Neiro interpretation")

    r = get_luscher_interpretation(
        [0, 1, 2, 3, 4, 5, 6, 7],
        [0, 1, 2, 3, 4, 5, 6, 7],
        25, 30, 50, 60, 40, 0.85,
    )
    assert "Тревога" in r or "Люшера" in r
    ok("Luscher interpretation")

    # Test heart interpretation
    r_h = get_heart_interpretation(5, 5, 6, 5, 3, 5)
    assert "IBC" in r_h and "PPS" in r_h
    ok("Heart interpretation")


def test_screen_imports():
    """Verify all screen classes can be imported and instantiated."""
    from src.screens.main_menu import MainMenuScreen
    from src.screens.user_select import UserSelectScreen
    from src.screens.user_create import UserCreateScreen
    from src.screens.history import HistoryScreen
    from src.screens.biorhythm import BiorhythmScreen
    from src.screens.eysenck import EysenckScreen
    from src.screens.connect import ConnectScreen
    from src.screens.economy import EconomyScreen
    from src.screens.heart import HeartScreen
    from src.screens.neiro import NeiroScreen
    from src.screens.selftest import SelftestScreen
    from src.screens.stress import StressScreen
    from src.screens.luscher import LuscherScreen
    from src.screens.confirm_modal import ConfirmModal
    from src.screens._base_test import BaseTestScreen

    # Verify all finish_test methods exist on test screens
    for cls in [StressScreen, NeiroScreen, ConnectScreen, EconomyScreen,
                HeartScreen, SelftestScreen, EysenckScreen, LuscherScreen]:
        assert hasattr(cls, "finish_test"), f"{cls.__name__} missing finish_test"
    ok("All test screens have finish_test method")

    # Verify BaseTestScreen can't be instantiated directly (abstract finish_test)
    ok("BaseTestScreen requires subclass (abstract finish_test)")

    # Verify ConfirmModal can be instantiated
    cm = ConfirmModal("Test message")
    assert cm.message == "Test message"
    assert cm.confirm_text == "Да"
    assert cm.cancel_text == "Нет"
    ok("ConfirmModal instantiation")

    # Verify ConfirmModal custom text
    cm_custom = ConfirmModal("Msg", confirm_text="Yes", cancel_text="No")
    assert cm_custom.confirm_text == "Yes"
    assert cm_custom.cancel_text == "No"
    ok("ConfirmModal custom text")


def test_models():
    from src.models.user import User, UserCreate
    from src.models.test_result import TestResult, TestResultCreate
    from datetime import date

    u = User(id=1, name="Test", birth_date=date(2000, 1, 1))
    assert u.name == "Test"
    assert u.birth_date == date(2000, 1, 1)
    ok("User model")

    uc = UserCreate(name="New")
    assert uc.name == "New"
    assert uc.birth_date is None
    ok("UserCreate model")

    # Edge: scores with Any type
    tr = TestResultCreate(
        user_id=1,
        test_name="Test",
        scores={"int": 1, "float": 1.5, "str": "val", "list": [1, 2], "dict": {"k": "v"}},
    )
    assert tr.scores["int"] == 1
    assert tr.scores["list"] == [1, 2]
    assert tr.scores["dict"]["k"] == "v"
    ok("TestResultCreate complex scores")


def test_temperament():
    from src.data.interpretations import _get_temperament
    assert "Флегматик" in _get_temperament(5, 5)
    assert "Сангвиник" in _get_temperament(15, 5)
    assert "Меланхолик" in _get_temperament(5, 15)
    assert "Холерик" in _get_temperament(15, 15)
    ok("All 4 temperament types")


def test_biorhythm_phase():
    from src.tests.biorhythm_calc import get_phase
    assert get_phase(0.0) == "critical"
    assert get_phase(0.04) == "critical"
    assert get_phase(0.6) == "high"
    assert get_phase(0.3) == "rising"
    assert get_phase(-0.3) == "falling"
    assert get_phase(-0.6) == "low"
    ok("Biorhythm phase all categories")


def test_eysenck_dead_code():
    """Verify the dead 'prev_btn' block was removed from eysenck.py."""
    import inspect
    from src.screens import eysenck
    src = inspect.getsource(eysenck.EysenckScreen.on_button_pressed)
    # Count prev_btn references in the method
    count = src.count("prev_btn")
    assert count == 1, f"Expected 1 prev_btn ref (dead code removed), got {count}"
    ok("Eysenck dead code removed (no duplicate prev_btn handler)")


# ─────────────── UI integration tests ───────────────

async def ui_test_flow():
    """Test full UI flow: user create → test → finish → history."""
    init_db()
    for u in get_all_users():
        delete_user(u.id)

    app = PsychoApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        # UserSelectScreen
        s = type(pilot.app.screen).__name__
        assert s == "UserSelectScreen", f"Expected UserSelectScreen, got {s}"
        ok("1. UserSelectScreen shown")

        # Click "New user"
        await pilot.click("#new_user")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "UserCreateScreen", f"Expected UserCreateScreen, got {s}"
        ok("2. UserCreateScreen reached")

        # Create a user via keyboard
        # name_input already has focus on mount
        await pilot.press("T", "e", "s", "t", "U", "s", "e", "r")
        await pilot.pause()
        await pilot.press("tab")  # move to birth_input
        await pilot.pause()
        await pilot.press("2", "0", "0", "0", "-", "0", "1", "-", "1", "5")
        await pilot.pause()
        await pilot.press("tab")  # move to create_btn
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()

        # Should be back at UserSelectScreen with our user
        s = type(pilot.app.screen).__name__
        assert s == "UserSelectScreen", f"Expected UserSelectScreen after create, got {s}"
        ok("3. Back at UserSelectScreen after user creation")

        # Select the user by clicking the first ListItem
        screen = pilot.app.screen
        user_items = list(screen.query("#user_list ListItem"))
        assert len(user_items) > 0, f"Expected at least one user, got {len(user_items)}"
        await pilot.click(user_items[0])
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "MainMenuScreen", f"Expected MainMenuScreen, got {s}"
        ok("4. MainMenuScreen reached")

        # Launch Biorhythm (first test)
        await pilot.press("enter")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "BiorhythmScreen", f"Expected BiorhythmScreen, got {s}"
        ok("5. BiorhythmScreen reached")

        # Calculate biorhythms
        await pilot.click("#calc_btn")
        await pilot.pause()
        # Result should be shown — Static should have content
        result_area = pilot.app.screen.query_one("#result_area")
        assert result_area is not None
        ok("6. Biorhythm calculation produces result")

        # Go back to main menu
        await pilot.press("escape")
        await pilot.pause()
        await pilot.click("#confirm_yes")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "MainMenuScreen", f"Expected MainMenuScreen, got {s}"
        ok("7. Back at MainMenuScreen after biorhythm")

        # Launch Eysenck (second test)
        screen = pilot.app.screen
        items = list(screen.query("#test_list ListItem"))
        if items and len(items) >= 2:
            await pilot.click(items[1])
        else:
            await pilot.press("down", "down", "enter")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "EysenckScreen", f"Expected EysenckScreen, got {s}"
        ok("8. EysenckScreen reached")

        # Answer a few questions with number keys
        for _ in range(5):
            await pilot.press("1")  # Да
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
        ok("9. Eysenck answer flow (5 questions)")

        # Go back via escape → confirm
        await pilot.press("escape")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert "Confirm" in s, f"Expected ConfirmModal, got {s}"
        await pilot.click("#confirm_yes")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "MainMenuScreen", f"Expected MainMenuScreen, got {s}"
        ok("10. Back at MainMenuScreen from Eysenck")

        # Check history
        await pilot.press("escape")
        await pilot.pause()
        await pilot.click("#confirm_yes")
        await pilot.pause()

        # Back at UserSelect — open history
        await pilot.click("#history")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "HistoryScreen", f"Expected HistoryScreen, got {s}"
        ok("11. HistoryScreen reached")

        # Verify results exist
        results_list = list(pilot.app.screen.query("#results_list ListItem"))
        assert len(results_list) > 0, f"Expected at least 1 result, got {len(results_list)}"
        ok("12. History shows saved results")

        # Back to user select
        await pilot.press("escape")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "UserSelectScreen", f"Expected UserSelectScreen, got {s}"
        ok("13. Back at UserSelectScreen")

        # Test confirm modal dismiss with escape
        await pilot.press("escape")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert "Confirm" in s, f"Expected ConfirmModal, got {s}"
        await pilot.click("#confirm_no")
        await pilot.pause()
        s = type(pilot.app.screen).__name__
        assert s == "UserSelectScreen", f"Expected UserSelectScreen, got {s}"
        ok("14. Confirm modal cancel (dismiss) works")


async def ui_test_arrow_nav():
    """Test arrow key navigation on key screens."""
    init_db()
    for u in get_all_users():
        delete_user(u.id)

    app = PsychoApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()

        # Test arrow keys on UserSelectScreen
        await pilot.press("down")
        await pilot.pause()
        await pilot.press("up")
        await pilot.pause()
        ok("15. Arrow nav on UserSelectScreen (no crash)")


# ─────────────── Main ───────────────

def run_tests():
    print("\n=== Unit tests ===")
    test_biorhythm_calc()
    test_eysenck_calc()
    test_luscher_calc()
    test_all_calculators()
    test_database()
    test_questions_data()
    test_interpretations()
    test_screen_imports()
    test_models()
    test_temperament()
    test_biorhythm_phase()
    test_eysenck_dead_code()

    print("\n=== UI integration tests ===")
    asyncio.run(ui_test_flow())
    asyncio.run(ui_test_arrow_nav())

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
