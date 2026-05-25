# AGENTS.md

## Commands
```bash
./venv/bin/python run.py                     # run app
./venv/bin/python tests.py                   # run all 147 tests
```
- After code changes: `find . -type d -name __pycache__ -exec rm -rf {} +`
- If tests fail inexplicably, delete `data/psycho.db` and `~/.local/share/psychotests/psycho.db`.
- App entrypoint: `run.py → src/main.py → init_db() + PsychoApp().run()`

## Textual 8.x — non-obvious traps
- **`RadioSet` has no public `index` API.** Reset via private attrs:
  ```python
  with radio.prevent(RadioButton.Changed):
      for btn in radio.query(RadioButton): btn.value = False
  radio._pressed_button = None; radio._selected = None
  ```
- **`ListView.clear()` / `.append()` are async** — must `await` or get `DuplicateIds`.
- **`Static.update()` does NOT render Markdown.** Use Rich markup (`[bold]text[/bold]`) — `##`/`**bold**` silently produce no output.
- Arrow nav needs explicit `action_focus_next` / `action_focus_previous` methods (statistics delegates to `list_view.cursor_down/up` when focused on list).
- `on_mount` must be `async` if it calls `await list_view.append()`.
- Tests: use `pilot.app.screen.query_one(...)`, not `pilot.app.query_one(...)`.
- `ConfirmModal` uses `Screen` (not `ModalScreen`), sets `dlg.styles.width = "auto"` in `on_mount`.

## Critical guards (do not omit)
- **Every `finish_test()` must set `self.test_completed = True`.** Missing it breaks Escape-after-test and the guard below.
- **Guard `action_next` and `_select_num` with `self.test_completed`.** Otherwise pressing 5+Enter after finishing appends answers and recalculates score.
- **Selecting an answer:** `action_back` goes without confirm when `test_completed`. Use `action_back` not bare `pop_screen`.

## Architecture
```
run.py → src/main.py → init_db() + PsychoApp().run()
                        ↓
                   UserSelectScreen → MainMenuScreen → 9 test screens
                         │
                         └→ StatisticsScreen (charts + filter + multi-line list)
```
- `src/tests/` — calculators; `src/data/` — questions + interpretations.
- `src/screens/_base_test.py` — Likert base (1-5 RadioSet). Subclassed by stress/neiro/connect/economy/heart/selftest.
- `src/screens/eysenck.py` — standalone Screen with 2-button RadioSet (Да/Нет).
- `src/screens/luscher.py` — 8-color pick, 2 rounds. In-place button style updates via `_rebuild_buttons()` (no `remove_children()`/`mount()` — avoids `DuplicateIds`).
- `src/screens/biorhythm.py` — date `Input` + calc button, centered layout.
- `src/screens/statistics.py` — **NOT** in `SCREENS` dict. Pushed as `StatisticsScreen()` instance (fresh data each time).
- `src/screens/result_view.py` — read-only result detail, scrollable. Used by `statistics.py` and test screens.
- `scores: dict[str, Any]` in `TestResult` — was `float`, crashes Stress/Neiro if reverted.
- `birth_date` = optional ISO string via `Input` (Textual 8.x has no `DatePicker`).

## Question shuffling
- **`shuffle_questions()`** in `_base_test.py` (module-level function). If `key_fn` is given (Eysenck: `q[1]` scale letter, Heart: `q[1]` scale name), groups by key, sorts groups by size descending, then interleaves — same-type questions spread apart. Without `key_fn`, plain `random.shuffle`.
- **EysenckScreen.on_mount**: `self._questions = shuffle_questions(EYSENCK_QUESTIONS, key_fn=lambda q: q[1])` — uses `self._questions` not `QUESTIONS`.
- **BaseTestScreen.on_mount**: shuffles `self.QUESTIONS` (and `self.SCALES` if present) in place.

## Navigation patterns
- **UserSelectScreen**: list ↔ "Новый пользователь" ↔ "Статистика" — focus cycles through all three.
- **BaseTestScreen**: `RadioSet` arrow boundaries move to nav buttons. Left/Right on nav buttons moves between "Назад"/"Далее". Enter with `priority=True` prevents `RadioSet` from swallowing it.
- **Biorhythm**: Header → user_label → title → date_label → input+button row → result → Footer.
- **Luscher**: Header → user_label → title → round_label → 2×4 color grid → progress → result_scroll → Footer.
- **Statistics**: filter buttons → results_list (multi-line ListItem with single `Static`). Arrow nav delegates to `list_view.cursor_down/up`.

## Layout conventions
- All test screens use `Vertical` (not `ScrollableContainer`) as `#main_content` with CSS `align: center middle` for vertical centering.
- `StatisticsScreen` keeps `ScrollableContainer` (lots of content — chart, filters, list).
- CSS in `src/app.tcss` — moderate padding throughout. Text centered via `text-align: center` + `width: 100%`. Buttons: `margin: 0 1`.

## Database
- `DB_PATH` = `data/psycho.db` when running as script; `~/.local/share/psychotests/psycho.db` when frozen (via `platformdirs`).
- Raw SQLite3 via `sqlite3` module. `scores` column is JSON string (parsed with `json.loads`). No migrations.
- `get_test_names()` returns `DISTINCT test_name` from `test_results`.

## Statistics results display
- Each `ListItem` contains a single `Static` with Rich markup, date+name on first line, interpretation/scores on second (separated by `\n`).
- Lüscher detail: `_show_luscher_detail()` parses `raw_data` (`"choices1/choices2"`), rebuilds color `Table` matching in-test display.
- Arrow nav: `action_focus_next/previous` checks if `results_list` is focused; if so calls `list_view.cursor_down/up`.

## Tests (`tests.py`, 147 tests)
- No pytest — single file with manual `ok()`/`fail()` + `asyncio.run()` for UI tests.
- `run_tests()` wipes test users at start; `_ui_flow()` wipes them at end.
- Eysenck: 57 questions, 24E / 24N / 9L. Answer = `bool` (index 0 = "Да").
- Luscher: `_safe_index()` wraps `list.index()` — crashes on duplicates (default pos = 4).
- Heart: returns `0.0` on empty scale lists (guards `ZeroDivisionError`).
- Biorhythm: cycles 23/28/33, range ±1.0, phases: high/low/critical/rising/falling.

## Known Bugs Fixed (do not reintroduce)
1. `history.py`: sync `on_mount` + `list_view.append()` without `await` → `DuplicateIds`. (File deleted.)
2. `eysenck.py`: dead duplicate `elif` for `prev_btn`.
3. `biorhythm.py`: result not saved to DB.
4. `luscher_calc.py`: `list.index()` on duplicates → `_safe_index()`.
5. `heart_calc.py`: `ZeroDivisionError` on empty scale list.
6. `database.py`: DB path resolves to temp dir in PyInstaller → `platformdirs` when frozen.
7. `stress/neiro/connect/economy/heart/selftest.py`: missing `self.test_completed = True` in `finish_test()`.
8. `stress/neiro/connect/economy/selftest.py`: `Static.update()` with Markdown (`##`/`**bold**`) instead of Rich markup.
9. `_base_test.py` + `eysenck.py`: `action_next()` / `_select_num()` not guarded by `test_completed`.
10. `app.tcss`: `#date_label` missing `width: 100%` → date text left-aligned in biorhythm.
11. `luscher.py`: `_rebuild_buttons()` used `remove_children()`+`mount()` → `DuplicateIds`. Fixed with in-place button style updates.
12. `apps.py`: `StatisticsScreen` in `SCREENS` dict → cached stale data. Removed from dict, pushed as new instance.

## Key Bindings
- `q` / `й` → quit (with confirm) — App-level
- `escape` → back — Screen-level. After test completion, goes back without confirm.
- `1`–`5` → select answer (Likert tests); `1`–`8` → select color (Luscher)
- `enter` → next (`priority=True`) — Test screens. In Eysenck, also enters confirm when focused on "Закончить".

## Build binaries
Linux:
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "src/app.tcss:src/" --add-data "src/data:src/data" --name psychotests run.py
```
Windows:
```bash
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --add-data "src/app.tcss;src/" --add-data "src/data;src/data" --name psychotests run.py
```
Auto-build on tag push via `.github/workflows/build.yml`.
