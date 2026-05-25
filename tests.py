#!/usr/bin/env python3
"""Tests for psychotests application."""

import asyncio
import sys
import os
from pathlib import Path
from datetime import date, datetime
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

# ── test harness ──────────────────────────────────────────────

PASS = 0
FAIL = 0

def ok(msg: str):
    global PASS; PASS += 1; print(f"  ✅ {msg}")

def fail(msg: str):
    global FAIL; FAIL += 1; print(f"  ❌ {msg}")

def okfail(pred: bool, msg: str):
    (ok if pred else fail)(msg)

def eq(a, b, msg: str):
    okfail(a == b, f"{msg} ({a} == {b})")

def in_(sub, full, msg: str):
    okfail(sub in full, f"{msg}")

# ── helpers ───────────────────────────────────────────────────

def clean_db():
    from src.models.database import init_db, get_all_users, delete_user
    init_db()
    for u in get_all_users():
        delete_user(u.id)

# ═══════════════════════════════════════════════════════════════
# Calculators
# ═══════════════════════════════════════════════════════════════

def test_biorhythm():
    from src.tests.biorhythm_calc import calculate_biorhythms, get_phase, cycle_value

    r = calculate_biorhythms(date(1990, 1, 1))
    for k in ("physical", "emotional", "intellectual"):
        assert k in r, f"missing {k}"
        assert abs(r[k]["value"]) <= 1.0, f"{k} out of range"
        assert "phase" in r[k], f"{k} missing phase"
    assert r["days"] > 0 and isinstance(r["days"], int)
    ok("biorhythm calculation")

    r0 = calculate_biorhythms(date.today(), date.today())
    assert r0["days"] == 0
    ok("biorhythm same date → 0 days")

    r1 = calculate_biorhythms(date(2099, 1, 1))
    assert r1["days"] < 0
    ok("biorhythm future birth → negative days")

    phases = {
        0.9: "high", 0.3: "rising", 0.0: "critical",
        -0.3: "falling", -0.9: "low",
    }
    for val, expected in phases.items():
        eq(get_phase(val), expected, f"biorhythm phase({val})")


def test_eysenck():
    from src.tests.eysenck_calc import score_eysenck
    from src.data.questions import EYSENCK_QUESTIONS

    answers = [True, False, True, False, True, True, False, True]
    scales = ["E", "N", "E", "L", "E", "E", "N", "L"]
    r = score_eysenck(answers, scales)
    eq(r["extraversion"], 4, "eysenck E")
    eq(r["neuroticism"], 0, "eysenck N")
    eq(r["lie"], 1, "eysenck L")
    ok("eysenck partial scoring")

    n = len(EYSENCK_QUESTIONS)
    scales_all = [s for _, s in EYSENCK_QUESTIONS]
    e_count = scales_all.count("E")
    n_count = scales_all.count("N")
    l_count = scales_all.count("L")

    r_all = score_eysenck([True] * n, scales_all)
    eq(r_all["extraversion"], e_count, "eysenck all true E")
    eq(r_all["neuroticism"], n_count, "eysenck all true N")
    eq(r_all["lie"], l_count, "eysenck all true L")
    ok("eysenck all true")

    r_none = score_eysenck([False] * n, scales_all)
    eq(r_none["extraversion"], 0, "eysenck all false E")
    eq(r_none["neuroticism"], 0, "eysenck all false N")
    eq(r_none["lie"], 0, "eysenck all false L")
    ok("eysenck all false")

    r_edge = score_eysenck([], [])
    eq(r_edge["extraversion"], 0, "eysenck empty")
    eq(r_edge["neuroticism"], 0, "eysenck empty")
    eq(r_edge["lie"], 0, "eysenck empty")
    ok("eysenck empty input")


def test_luscher():
    from src.tests.luscher_calc import calculate_luscher, consistency

    c1 = list(range(8))
    r = calculate_luscher(c1, c1)
    eq(r["consistency"], 1.0, "luscher identical choices consistency")
    for k in ("anxiety_pct", "compensation_pct", "activity_pct", "performance_pct", "vegetative_pct"):
        assert 0 <= r[k] <= 100, f"luscher {k} out of range"
    ok("luscher identical choices")

    c2 = list(reversed(range(8)))
    r2 = calculate_luscher(c1, c2)
    assert r2["consistency"] < 0.5, "luscher reversed low consistency"
    ok("luscher reversed")

    r_same = calculate_luscher([0] * 8, [0] * 8)
    assert isinstance(r_same["anxiety_pct"], float)
    ok("luscher all same color (no crash)")

    r_edge = calculate_luscher(c1, c1)
    assert isinstance(r_edge["choices1"], list) and len(r_edge["choices1"]) == 8
    assert isinstance(r_edge["choices2"], list) and len(r_edge["choices2"]) == 8
    ok("luscher returns both choice lists")


def test_likert_calculators():
    from src.tests.stress_calc import score_stress
    from src.tests.neiro_calc import score_neiro
    from src.tests.connect_calc import score_connect
    from src.tests.economy_calc import score_economy
    from src.tests.heart_calc import score_heart
    from src.tests.selftest_calc import score_selftest

    # stress
    r = score_stress([1, 2, 3, 4] * 6)
    eq(r["total"], 60, "stress scoring")
    in_(r["level"], ("low", "moderate", "elevated", "high", "critical"), "stress has level")
    rmin = score_stress([0] * 24)
    eq(rmin["total"], 0, "stress min")
    eq(rmin["level"], "low", "stress min level")
    rmax = score_stress([4] * 24)
    eq(rmax["total"], 96, "stress max")
    eq(rmax["level"], "high", "stress max level")
    ok("stress")

    # neiro
    r = score_neiro([1, 2, 3] * 8)
    eq(r["total"], 48, "neiro scoring")
    in_(r["level"], ("normal", "mild", "moderate", "severe"), "neiro has level")
    rnmin = score_neiro([0] * 24)
    eq(rnmin["level"], "normal", "neiro min level")
    rnmax = score_neiro([5] * 24)
    eq(rnmax["total"], 120, "neiro max")
    eq(rnmax["level"], "severe", "neiro max level")
    ok("neiro")

    # connect
    r = score_connect([3] * 25)
    assert r["total"] >= 0, "connect scoring"
    r_inv = score_connect([5] * 25)
    assert isinstance(r_inv["total"], float), "connect inverted"
    ok("connect")

    # economy
    r = score_economy([3] * 25)
    assert r["total"] >= 0, "economy scoring"
    ok("economy")

    # heart
    data = {"ibc": [1, 2], "pps": [3, 4], "de": [1], "ag": [5], "ncd": [2, 2], "zm": [3]}
    r = score_heart(data)
    for k in data:
        assert k in r, f"heart missing scale {k}"
        assert isinstance(r[k], float), f"heart {k} not float"
    r_e = score_heart({"ibc": []})
    eq(r_e["ibc"], 0.0, "heart empty scale")
    ok("heart")

    # selftest
    r = score_selftest([3] * 20)
    assert r["total"] >= 0, "selftest scoring"
    r_inv = score_selftest([5] * 20)
    assert isinstance(r_inv["total"], float), "selftest inverted"
    ok("selftest")


# ═══════════════════════════════════════════════════════════════
# Database
# ═══════════════════════════════════════════════════════════════

def test_database():
    from src.models.database import (
        init_db, get_all_users, create_user, get_user, delete_user,
        save_result, get_results_for_user, get_all_results, get_test_names,
    )
    from src.models.user import UserCreate
    from src.models.test_result import TestResultCreate

    clean_db()

    u = create_user(UserCreate(name="Alice"))
    assert u.id is not None and u.name == "Alice"
    all_u = get_all_users()
    assert len(all_u) == 1 and all_u[0].name == "Alice"
    ok("create user")

    u2 = create_user(UserCreate(name="Bob", birth_date=date(1990, 6, 15)))
    eq(u2.birth_date, date(1990, 6, 15), "user birth date saved")
    ok("create user with birth date")

    tr = TestResultCreate(user_id=u.id, test_name="TestX", scores={"a": 1.0})
    save_result(tr)
    rows = get_results_for_user(u.id)
    eq(len(rows), 1, "result saved")
    eq(rows[0].test_name, "TestX", "result name")
    eq(rows[0].scores, {"a": 1.0}, "result scores")
    assert isinstance(rows[0].created_at, datetime)
    ok("save & read result")

    tr_c = TestResultCreate(
        user_id=u.id, test_name="Complex",
        scores={"int": 1, "str": "x", "list": [1, 2], "dict": {"k": "v"}},
    )
    save_result(tr_c)
    rows = get_results_for_user(u.id)
    cr = [r for r in rows if r.test_name == "Complex"]
    eq(len(cr), 1, "complex result saved")
    eq(cr[0].scores["int"], 1, "complex int")
    eq(cr[0].scores["dict"]["k"], "v", "complex nested dict")
    ok("save complex scores")

    empty = get_results_for_user(99999)
    eq(empty, [], "no results for unknown user")
    ok("empty results for unknown user")

    names = get_test_names()
    assert "TestX" in names and "Complex" in names
    assert isinstance(names, list)
    ok("get_test_names")

    delete_user(u.id)
    assert get_user(u.id) is None
    eq(get_results_for_user(u.id), [], "results cleaned after user delete")
    delete_user(u2.id)
    ok("delete user")


# ═══════════════════════════════════════════════════════════════
# Data integrity
# ═══════════════════════════════════════════════════════════════

def test_question_banks():
    from src.data.questions import (
        EYSENCK_QUESTIONS, STRESS_QUESTIONS, CONNECT_QUESTIONS,
        ECONOMY_QUESTIONS, HEART_QUESTIONS, NEIRO_QUESTIONS, SELFTEST_QUESTIONS,
    )

    sizes = [
        (EYSENCK_QUESTIONS, 57, "Eysenck"),
        (STRESS_QUESTIONS, 24, "Stress"),
        (CONNECT_QUESTIONS, 25, "Connect"),
        (ECONOMY_QUESTIONS, 25, "Economy"),
        (HEART_QUESTIONS, 25, "Heart"),
        (NEIRO_QUESTIONS, 24, "Neiro"),
        (SELFTEST_QUESTIONS, 20, "Selftest"),
    ]
    for qs, n, name in sizes:
        eq(len(qs), n, f"{name} question count")
        for q in qs:
            text = q[0] if isinstance(q, tuple) else q
            assert len(text) > 5, f"Empty/short question in {name}"
    ok("question bank sizes & no empties")

    ec = sum(1 for _, s in EYSENCK_QUESTIONS if s == "E")
    nc = sum(1 for _, s in EYSENCK_QUESTIONS if s == "N")
    lc = sum(1 for _, s in EYSENCK_QUESTIONS if s == "L")
    eq(ec, 24, "Eysenck E count")
    eq(nc, 24, "Eysenck N count")
    eq(lc, 9, "Eysenck L count")
    ok("Eysenck scale counts")

    heart_scales = {s for _, s in HEART_QUESTIONS}
    for scale in ("IBC", "PPS", "DE", "AG", "NCD", "ZM"):
        assert scale in heart_scales, f"Heart missing scale {scale}"
    ok("Heart all 6 scales")


def test_interpretations():
    from src.data.interpretations import (
        get_eysenck_interpretation, get_stress_interpretation,
        get_selftest_interpretation, get_connect_interpretation,
        get_economy_interpretation, get_neiro_interpretation,
        get_luscher_interpretation, get_heart_interpretation,
        _get_temperament,
    )

    r = get_eysenck_interpretation(15, 10, 2)
    in_("Экстраверсия", r, "eysenck interp has extroversion")
    in_("Нейротизм", r, "eysenck interp has neuroticism")
    in_("Шкала лжи", r, "eysenck interp has lie")
    r0 = get_eysenck_interpretation(0, 0, 0)
    in_("Экстраверсия", r0, "eysenck interp min")
    r24 = get_eysenck_interpretation(24, 24, 9)
    in_("Нейротизм", r24, "eysenck interp max")
    ok("Eysenck interpretation")

    in_("Низкий", get_stress_interpretation(0), "stress interp low")
    in_("Критический", get_stress_interpretation(200), "stress interp critical")
    ok("Stress interpretation")

    in_("Высокая", get_selftest_interpretation(50), "selftest interp high")
    in_("Низкая", get_selftest_interpretation(10), "selftest interp low")
    ok("Selftest interpretation")

    assert len(get_connect_interpretation(60)) > 20
    ok("Connect interpretation")

    assert len(get_economy_interpretation(60)) > 20
    ok("Economy interpretation")

    assert len(get_neiro_interpretation(30)) > 20
    ok("Neiro interpretation")

    rl = get_luscher_interpretation(
        list(range(8)), list(range(8)), 25, 30, 50, 60, 40, 0.85,
    )
    assert len(rl) > 20
    ok("Luscher interpretation")

    rh = get_heart_interpretation(5, 5, 6, 5, 3, 5)
    in_("IBC", rh, "heart interp")
    in_("PPS", rh, "heart interp")
    ok("Heart interpretation")

    in_("Флегматик", _get_temperament(5, 5), "temperament phlegmatic")
    in_("Сангвиник", _get_temperament(15, 5), "temperament sanguine")
    in_("Меланхолик", _get_temperament(5, 15), "temperament melancholic")
    in_("Холерик", _get_temperament(15, 15), "temperament choleric")
    ok("Temperament 4 types")


# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

def test_models():
    from src.models.user import User, UserCreate
    from src.models.test_result import TestResult, TestResultCreate

    u = User(id=1, name="Test", birth_date=date(2000, 1, 1))
    eq(u.name, "Test", "User model")
    eq(u.birth_date, date(2000, 1, 1), "User birth date")

    uc = UserCreate(name="New")
    eq(uc.name, "New", "UserCreate model")
    assert uc.birth_date is None
    ok("models: User & UserCreate")

    tr = TestResultCreate(
        user_id=1, test_name="T",
        scores={"int": 1, "float": 1.5, "str": "x", "list": [1], "dict": {"k": "v"}},
    )
    eq(tr.scores["int"], 1, "TestResult int")
    eq(tr.scores["dict"]["k"], "v", "TestResult nested dict")
    ok("models: TestResultCreate")


# ═══════════════════════════════════════════════════════════════
# Screen imports & invariants
# ═══════════════════════════════════════════════════════════════

def test_screens():
    from src.screens._base_test import BaseTestScreen
    from src.screens.stress import StressScreen
    from src.screens.neiro import NeiroScreen
    from src.screens.connect import ConnectScreen
    from src.screens.economy import EconomyScreen
    from src.screens.heart import HeartScreen
    from src.screens.selftest import SelftestScreen
    from src.screens.eysenck import EysenckScreen
    from src.screens.luscher import LuscherScreen
    from src.screens.confirm_modal import ConfirmModal

    test_screens = [
        StressScreen, NeiroScreen, ConnectScreen, EconomyScreen,
        HeartScreen, SelftestScreen, EysenckScreen, LuscherScreen,
    ]
    for cls in test_screens:
        assert hasattr(cls, "finish_test"), f"{cls.__name__} missing finish_test"
    ok("all test screens have finish_test")

    cm = ConfirmModal("msg")
    eq(cm.message, "msg", "ConfirmModal message")
    eq(cm.confirm_text, "Да", "ConfirmModal default confirm")
    eq(cm.cancel_text, "Нет", "ConfirmModal default cancel")

    cm2 = ConfirmModal("m", confirm_text="Y", cancel_text="N")
    eq(cm2.confirm_text, "Y", "ConfirmModal custom confirm")
    eq(cm2.cancel_text, "N", "ConfirmModal custom cancel")
    ok("ConfirmModal")


def test_eysenck_dead_code():
    import inspect
    from src.screens import eysenck
    src = inspect.getsource(eysenck.EysenckScreen.on_button_pressed)
    assert src.count("prev_btn") == 1, "duplicate prev_btn handler still present"
    ok("no duplicate prev_btn in eysenck")


# ═══════════════════════════════════════════════════════════════
# UI integration
# ═══════════════════════════════════════════════════════════════

async def _ui_flow():
    from src.app import PsychoApp
    from src.models.database import init_db, get_all_users, delete_user

    init_db()
    for u in get_all_users():
        delete_user(u.id)

    app = PsychoApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        screen = lambda: type(pilot.app.screen).__name__
        click = lambda s: pilot.click(s)
        press = lambda *k: pilot.press(*k)
        pause = lambda: pilot.pause()

        # 1. UserSelectScreen on start
        eq(screen(), "UserSelectScreen", "UI: start screen")
        ok("UI 1: UserSelectScreen")

        # 2. Navigate to UserCreateScreen
        await click("#new_user")
        await pause()
        eq(screen(), "UserCreateScreen", "UI: user create reached")
        ok("UI 2: UserCreateScreen")

        # 3. Create user
        await press(*"TestUser")
        await pause()
        await press("tab")
        await pause()
        await press(*"2000-01-15")
        await pause()
        await press("tab", "enter")
        await pause()
        await pause()
        eq(screen(), "UserSelectScreen", "UI: back after create")
        ok("UI 3: back at UserSelectScreen")

        # 4. Select user → MainMenuScreen
        ulist = list(pilot.app.screen.query("#user_list ListItem"))
        assert len(ulist) > 0
        await click(ulist[0])
        await pause()
        eq(screen(), "MainMenuScreen", "UI: main menu")
        ok("UI 4: MainMenuScreen")

        # 5. Biorhythm
        await press("enter")
        await pause()
        eq(screen(), "BiorhythmScreen", "UI: biorhythm")
        ok("UI 5: BiorhythmScreen")

        # 6. Calculate biorhythm
        await click("#calc_btn")
        await pause()
        ra = pilot.app.screen.query_one("#result_area")
        assert ra is not None
        ok("UI 6: biorhythm calculation")

        # 7. Back to main menu
        await press("escape")
        await pause()
        eq(screen(), "MainMenuScreen", "UI: back from biorhythm")
        ok("UI 7: back at MainMenuScreen")

        # 8. Eysenck
        items = list(pilot.app.screen.query("#test_list ListItem"))
        await click(items[1])
        await pause()
        eq(screen(), "EysenckScreen", "UI: eysenck")
        ok("UI 8: EysenckScreen")

        # 9. Answer 5 questions
        for _ in range(5):
            await press("1", "enter")
            await pause()
        ok("UI 9: answer 5 questions")

        # 10. Exit eysenck → confirm modal
        await press("escape")
        await pause()
        assert "Confirm" in screen()
        await click("#confirm_yes")
        await pause()
        eq(screen(), "MainMenuScreen", "UI: back from eysenck")
        ok("UI 10: back at MainMenuScreen")

        # 11. UserSelectScreen
        await press("escape")
        await pause()
        await click("#confirm_yes")
        await pause()
        eq(screen(), "UserSelectScreen", "UI: user select")
        ok("UI 11: UserSelectScreen")

        # 12. StatisticsScreen
        await click("#history")
        await pause()
        eq(screen(), "StatisticsScreen", "UI: statistics")
        ok("UI 12: StatisticsScreen")

        # 13. Results exist
        rlist = list(pilot.app.screen.query("#results_list ListItem"))
        assert len(rlist) > 0
        ok("UI 13: results in list")

        # 14. Back to user select
        await press("escape")
        await pause()
        eq(screen(), "UserSelectScreen", "UI: back to user select")
        ok("UI 14: back at UserSelectScreen")

        # 15. Confirm modal dismiss
        await press("escape")
        await pause()
        assert "Confirm" in screen()
        await click("#confirm_no")
        await pause()
        eq(screen(), "UserSelectScreen", "UI: stayed after cancel")
        ok("UI 15: confirm dismiss stays")

    # cleanup test data
    from src.models.database import get_all_users, delete_user
    for u in get_all_users():
        if u.name in ("TestUser", "Alice", "Bob"):
            delete_user(u.id)


async def _ui_arrow_nav():
    from src.app import PsychoApp
    from src.models.database import init_db, get_all_users, delete_user

    init_db()
    for u in get_all_users():
        delete_user(u.id)

    app = PsychoApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        await pilot.press("down", "up")
        await pilot.pause()
        ok("UI 16: arrow nav no crash")


# ── dead code guard: verify StatisticsScreen not in SCREENS dict ──

def test_statistics_not_cached():
    from src.app import PsychoApp
    assert "history" not in PsychoApp.SCREENS
    assert "statistics" not in PsychoApp.SCREENS
    ok("StatisticsScreen not in SCREENS dict (fresh instance)")


def test_result_view_import():
    from src.screens.result_view import ResultViewScreen
    rv = ResultViewScreen("t", "c")
    eq(rv._title, "t", "ResultViewScreen title")
    eq(rv._content, "c", "ResultViewScreen content")
    ok("ResultViewScreen import & init")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

RUN = [
    ("Unit: biorhythm",        test_biorhythm),
    ("Unit: eysenck",          test_eysenck),
    ("Unit: luscher",          test_luscher),
    ("Unit: likert calculators", test_likert_calculators),
    ("Unit: database",         test_database),
    ("Unit: question banks",   test_question_banks),
    ("Unit: interpretations",  test_interpretations),
    ("Unit: models",           test_models),
    ("Unit: screens",          test_screens),
    ("Guard: eysenck dead code", test_eysenck_dead_code),
    ("Guard: statistics fresh", test_statistics_not_cached),
    ("Guard: result view",     test_result_view_import),
]


def run_tests():
    # wipe any stale test data from previous runs
    from src.models.database import init_db, get_all_users, delete_user
    init_db()
    for u in get_all_users():
        if u.name in ("TestUser", "Alice", "Bob"):
            delete_user(u.id)

    print("\n=== Unit tests ===")
    for name, fn in RUN:
        try:
            fn()
        except Exception as e:
            fail(f"{name}: {e}")

    print("\n=== UI integration tests ===")
    try:
        asyncio.run(_ui_flow())
    except Exception as e:
        fail(f"UI flow: {e}")

    try:
        asyncio.run(_ui_arrow_nav())
    except Exception as e:
        fail(f"UI arrow nav: {e}")

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
