# AGENTS.md

## Commands
```bash
./venv/bin/python run.py       # run app
./venv/bin/python tests.py     # all 147 tests (no pytest — single file, asyncio.run)
```
- App entrypoint: `run.py → src/main.py → init_db() + PsychoApp().run()`
- Dependencies: `textual pydantic rich typing-extensions` (no pinned versions, `requirements.txt`)

## Textual 8.x — non-obvious traps
- **`RadioSet` has no public `index` API.** Reset via private attrs:
  ```python
  with radio.prevent(RadioButton.Changed):
      for btn in radio.query(RadioButton): btn.value = False
  radio._pressed_button = None; radio._selected = None
  ```
- **`ListView.clear()` / `.append()` are async** — must `await` or get `DuplicateIds`.
- **`Static.update()` does NOT render Markdown.** Use Rich markup (`[bold]text[/bold]`).
- Arrow nav requires explicit `action_focus_next/previous`. On `RadioSet` boundaries, delegate to next widget (not wrap inside set).
- `ConfirmModal` uses `Screen` (not `ModalScreen`) — sets `dlg.styles.width = "auto"` in `on_mount`.
- `ResultViewScreen` type hint says `content: str` but accepts Rich renderables (`Group`, `Table`).
- Tests: use `pilot.app.screen.query_one(...)`, not `pilot.app.query_one(...)`.
- Removing a widget via `remove_children()` + re-mounting can cause `DuplicateIds`. Prefer in-place style updates.

## Critical guards (do not omit)
- **Every `finish_test()` must set `self.test_completed = True`** after saving result. Missing it breaks escape-after-test.
- **Guard `action_next` and `_select_num` with `self.test_completed`.** Otherwise pressing 5+Enter after finish appends answers.
- **Escape after test completion** goes back directly (no confirm). Use `action_back` not bare `pop_screen`.

## Architecture
```
run.py → src/main.py → PsychoApp().run()
                 ↓
UserSelectScreen → MainMenuScreen → 9 test screens
      │                              │
      └→ StatisticsScreen            └→ ResultViewScreen
```
- `src/tests/` — calculators; `src/data/` — questions + interpretations.
- `src/screens/_base_test.py` — Likert base (1-5 `RadioSet`). Subclassed by stress/neiro/connect/economy/heart/selftest.
- `src/screens/eysenck.py` — standalone `Screen` with 2-button `RadioSet` (Да/Нет).
- `src/screens/luscher.py` — 8-color pick, 2 rounds. Colors shuffled each round (`random.shuffle` in `start_round`), 1×8 button row, abbreviated labels.
- `src/screens/biorhythm.py` — date `Input` + calc button, centered layout with column-aligned results.
- `src/screens/statistics.py` — **NOT** in `SCREENS` dict. Pushed as `StatisticsScreen()` instance (fresh data each time).
- `src/screens/result_view.py` — read-only scrollable detail. Has arrow scroll bindings (`scroll_up`/`scroll_down`).
- `scores: dict[str, Any]` in `TestResult` — was `dict[str, float]`, crashes Stress/Neiro if reverted.
- `birth_date` = optional ISO string via `Input` (Textual 8.x has no `DatePicker`).

## Question shuffling
- **`shuffle_questions()`** in `_base_test.py` (module-level). If `key_fn` given (Eysenck: `q[1]` scale letter, Heart: `q[1]` scale name), groups by key, sorts groups by size descending, interleaves — same-type spread apart. Without `key_fn`, plain `random.shuffle`.
- **EysenckScreen.on_mount**: shuffles into `self._questions` (not `QUESTIONS`).
- **BaseTestScreen.on_mount**: shuffles `self.QUESTIONS` (and `self.SCALES`) in place.

## Result display — Rich Panels
- All test results are wrapped in `rich.panel.Panel` with colored borders via `_show_result(text, title, border_style)`:
  - stress → `yellow`, neiro/selftest → `green`, connect → `magenta`, economy → `blue`, heart/eysenck → `cyan`, luscher → `magenta`
- `#result_area` has **no border in CSS** — the `Panel` provides the frame only when result is shown.
- During the test `#result_area` is empty (`""`) and invisible.
- `#answer_set` has **no border** — just plain radio buttons.

## Statistics screen
- Chart: `_build_chart()` returns `Table(expand=True)` with 3 columns. Name column wraps (`no_wrap` removed), bar width = 15.
- List items: `[dim]date[/dim] [bold yellow]test_name[/bold yellow]` on line 1, `[cyan]first_line[/cyan]` on line 2.
- Detail view: Rich `Panel` with `title=result.test_name, border_style="cyan"`.
- Arrow nav delegates to `list_view.cursor_down/up` when `ListView` focused.
- Lüscher detail: parses `raw_data` (`"choices1/choices2"`), rebuilds color `Table`.

## CSS layout (`src/app.tcss`)
- `#main_content` (test screens): `Vertical`, `align: center middle`, `margin: 0 4`.
- `ScrollableContainer#main_content` (statistics): `margin: 0 2`, `align: left top`.
- `ScrollableContainer#main_content #results_list Static { text-align: left }`.
- `#result_area`: `text-align: left`, no border (Panel provides it).
- `#answer_set`: no border, `padding: 0 3`.
- `#filter_buttons Button { margin: 0 2 }`.
- `#color_buttons`: single `Horizontal`, buttons `min-width: 8`, `width: 8` (abbreviated labels).
- `Button:hover { text-style: bold }`, `Button:focus { text-style: bold reverse }`.

## Biorhythm column alignment
- Name column: padded to `max(len(name)) + 1`, colon appended: `"Физический:  "`.
- Percentage: right-aligned to 6 chars: `"  -98%"`, `"  +90%"`, `" -100%"`.
- Bar: 20 chars `█` + `░`.
- Phase text: `[dim]...[/dim]`.

## Database
- `DB_PATH` = `data/psycho.db` when running; `~/.local/share/psychotests/psycho.db` when frozen (`platformdirs`).
- **`.gitignore` covers `data/`** — stale DB won't be tracked.
- Raw SQLite3. `scores` column is JSON string (`json.loads`). No migrations.

## Tests (`tests.py`, 147 tests)
- No pytest — `ok()`/`fail()` harness + `asyncio.run()` for UI tests.
- `run_tests()` wipes "Alice"/"Bob"/"TestUser" at start; `_ui_flow()` wipes at end.
- Eysenck: 57 questions, 24E/24N/9L. Answer = `bool` (index 0 = "Да").
- Luscher: `_safe_index()` in `luscher_calc.py` wraps `list.index()` — crashes on duplicates (default pos = 4).
- Heart: returns `0.0` on empty scale lists (guards `ZeroDivisionError`).
- Biorhythm: cycles 23/28/33, range ±1.0, phases: high/low/critical/rising/falling.
- Dead code guard: `StatisticsScreen` not in `PsychoApp.SCREENS`.

## Known Bugs Fixed (do not reintroduce)
1. `finish_test()` must set `self.test_completed = True` — missing caused crashes.
2. `Static.update()` with Markdown instead of Rich markup — silent no-output.
3. `action_next()` / `_select_num()` not guarded — post-completion answer appends.
4. `_rebuild_buttons()` used `remove_children()`+`mount()` → `DuplicateIds`. In-place style updates instead.
5. `StatisticsScreen` in `SCREENS` dict → stale cached data. Removed, fresh instance each time.
6. `list.index()` on duplicate Luscher colors → `_safe_index()` wrapper.
7. `ZeroDivisionError` on empty Heart scale lists.
8. `history.py` — sync `on_mount` + `await`-less `list_view.append()` → `DuplicateIds`. File deleted.
9. DB path resolved to temp dir in PyInstaller → `platformdirs` for frozen builds.
10. Luscher `_select_by_number` used `remaining_colors[num]` (sorted) instead of shuffled visual order — keyboard shortcuts picked wrong colors.
11. `#result_area` CSS border visible even when empty during test — removed, Rich `Panel` provides frame only on result.

## Build binaries
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "src/app.tcss:src/" --add-data "src/data:src/data" --name psychotests run.py
```
Windows: replace `:` with `;` in `--add-data`. Auto-build on tag push via `.github/workflows/build.yml`.
