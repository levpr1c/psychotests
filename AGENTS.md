# AGENTS.md

## Commands
```
pip install textual pydantic rich            # setup
python3 run.py                               # run app
python3 tests.py                             # run all 68 tests
```
- After code changes: `find . -type d -name __pycache__ -exec rm -rf {} +`

## Textual 8.x — non-obvious traps
- **`RadioSet` has no public `index` API.** Reset via private attrs:
  ```python
  with radio.prevent(RadioButton.Changed):
      for btn in radio.query(RadioButton): btn.value = False
  radio._pressed_button = None; radio._selected = None
  ```
- **Enter** on `RadioSet` → `toggle_button` (consumed). Screen-level `enter` binding needs `priority=True`.
- `ListView.clear()` / `.append()` are **async** — `await` or get `DuplicateIds`.
- `ConfirmModal` uses `Screen` (not `ModalScreen`), sets `dlg.styles.width = "auto"` in `on_mount`.
- Arrow nav needs explicit `action_focus_next` / `action_focus_previous` methods.
- `on_mount` must be `async` if it calls `await list_view.append()`.
- Tests: use `pilot.app.screen.query_one(...)`, not `pilot.app.query_one(...)`.

## Navigation (UserSelectScreen)
- **List**: Up/Down moves cursor within list; at bottom → jumps to "New User" button; at top → jumps to "History" button
- **Buttons**: Left/Right moves between "New User" ↔ "History"; Up goes to list; Down wraps to top of list
- **Cycle**: list → New User → History → list ...

## Navigation (BaseTestScreen)
- **RadioSet**: Up/Down moves between radio buttons; at boundaries → moves to next/prev widget (nav buttons)
- **Nav buttons**: Left/Right moves between "Prev" ↔ "Next"; Up/Down returns to RadioSet

## Navigation (BiorhythmScreen)
- Standard focus cycle: header → inputs → buttons → result_area → footer

## Tests (`tests.py`, 68 passed, 0 failed)
- No pytest — single file, UI tests use `asyncio.run()`.
- Eysenck: 57 questions, **24E / 24N / 9L**. Answer = `bool` (index 0 = "Да").
- Luscher: `_safe_index()` wraps `list.index()` — crashes on duplicates (default pos = 4).
- Heart: returns `0.0` on empty scale lists (guards `ZeroDivisionError`).
- Biorhythm: cycles 23/28/33, range ±1.0, phases: high/low/critical/rising/falling.

## Architecture
```
run.py → src/main.py → init_db() + PsychoApp().run()
                        ↓
                   UserSelectScreen → MainMenuScreen → 9 test screens → HistoryScreen
```
- `src/tests/` — calculators; `src/data/` — questions + interpretations.
- `src/screens/_base_test.py` — Likert base (1-5 radio). Has `test_completed` flag.
- `eysenck.py` — 2-button RadioSet; `luscher.py` — 8-color pick flow; `biorhythm.py` — date input.
- `scores: dict[str, Any]` in `TestResult` — was `float`, crashes Stress/Neiro if reverted.
- `birth_date` = optional ISO string via `Input` (Textual 8.x has no `DatePicker`).

## Database
- `DB_PATH` = `data/psycho.db` when running as script; `~/.local/share/psychotests/psycho.db` when running as binary (via `platformdirs`).
- If tests fail inexplicably, delete `data/psycho.db` and `~/.local/share/psychotests/psycho.db`.

## Known Bugs Fixed (do not reintroduce)
1. `history.py`: sync `on_mount`, `list_view.append()` without `await`.
2. `eysenck.py`: dead duplicate `elif` for `prev_btn`.
3. `biorhythm.py`: result not saved to DB.
4. `luscher_calc.py`: `list.index()` on duplicates → `_safe_index()`.
5. `heart_calc.py`: `ZeroDivisionError` on empty scale list.
6. `database.py`: DB path resolved to temp dir in PyInstaller → now uses `platformdirs` when frozen.

## Key Bindings
- `q` / `й` → quit (with confirm) — App-level
- `escape` → back — Screen-level. After test completion (`test_completed=True`), goes back without confirm.
- `1`–`5` → select answer — Test screen
- `enter` → next (`priority=True`) — Test screen

## Build binaries
Linux:
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "src/app.tcss:src/" --add-data "src/data:src/data" --name psychotests run.py
```
Windows (via Docker, Python 3.13):
```bash
docker run --rm -e DISPLAY= -v "$(pwd):/src" ddemuro/pyinstaller:py3-win64-3.13.3-6.13.0 \
  "pip install -r /src/requirements.txt && pyinstaller --onefile --add-data 'src/app.tcss;src/' --add-data 'src/data;src/data' --name psychotests /src/run.py"
```
Auto-build on tag push via `.github/workflows/build.yml` (GitHub Actions).

## DOS Origin
- `CODE.DAT` missing — questions reconstructed from standard methodologies.
- Luscher data files in CP866 included: `LUSHER.DAT`, `.INT`, `.CAT`.
- Full RE report: `docs/analysis.md`. Dev docs (mermaid): `docs/development.md`.
- Russian AGENTS: `AGENTS_RU.md`.
