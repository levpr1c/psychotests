# AGENTS.md

## Commands
```fish
pip install -r requirements.txt                    # setup
python3 run.py                                     # run app
python3 tests.py                                   # run test suite
```
- After code changes, clear stale `.pyc`: `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null`

## Textual 8.x Quirks (critical)
- `RadioSet` has **no public `index` API**. Reset:
  ```python
  with radio.prevent(RadioButton.Changed):
      for btn in radio.query(RadioButton): btn.value = False
  radio._pressed_button = None
  radio._selected = None
  ```
- `RadioSet` binds `enter` → `toggle_button` consuming Enter. Test screens override with `priority=True`.
- `ListView.clear()` / `.append()` are **async** — must `await` or get `DuplicateIds`.
- `ConfirmModal` uses `Screen` (not `ModalScreen`), sets `dlg.styles.width = "auto"` in `on_mount`.
- Arrow nav needs explicit `action_focus_next`/`action_focus_previous` methods.
- `on_mount` must be `async` if it calls `await list_view.append()`.
- In tests: `pilot.app.screen.query_one(...)` — not `pilot.app.query_one(...)`.

## Tests (`tests.py`, 68 total, all pass)
- No pytest — single file with `asyncio.run()` for UI tests.
- Eysenck: 57 questions, **24E / 24N / 9L**. Answer is `bool` (`self.current_answer == 0` = "Да").
- Luscher uses `_safe_index()` — `list.index()` crashes on duplicates; default position = 4.
- Heart calc returns `0.0` on empty scale lists (no `ZeroDivisionError`).
- Biorhythm: cycles 23/28/33, range ±1.0, phases: high/low/critical/rising/falling.

## Architecture
```
run.py → src/main.py → init_db() + PsychoApp().run()
                        ↓
                   UserSelectScreen → MainMenuScreen → 9 test screens → HistoryScreen
```
- `src/tests/` — calculators; `src/data/` — questions + interpretations.
- `src/screens/_base_test.py` — base class for Likert tests (1-5 radio).
- `eysenck.py` — custom 2-button RadioSet.
- `luscher.py` — color-button flow with 8 colors.
- `biorhythm.py` — date input + calc.

## Database
- SQLite3 auto-creates `data/psycho.db` via `init_db()`.
- `scores: dict[str, Any]` in `TestResult` — not `float` (crashes Stress/Neiro).
- `birth_date` = optional ISO string via `Input` (no `DatePicker` — Textual 8.x lacks it).

## Key Bindings
| Key | Action | Scope |
|-----|--------|-------|
| `q` / `й` | Quit (confirm → exit) | App |
| `escape` | Back | Screen |
| `1`–`5` | Select answer | Test screen |
| `enter` | Next (`priority=True`) | Test screen |

## Known Bugs Fixed (do not reintroduce)
1. `history.py`: `on_mount` was sync, `list_view.append()` without `await`.
2. `eysenck.py`: dead duplicate `elif` for `prev_btn`.
3. `biorhythm.py`: result not saved to DB.
4. `luscher_calc.py`: `list.index()` crashed on duplicates → `_safe_index()`.
5. `heart_calc.py`: `ZeroDivisionError` on empty scale list.

## DOS Origin
- `CODE.DAT` missing — questions reconstructed from standard methodologies.
- Luscher data files (CP866) included: `LUSHER.DAT`, `LUSHER.INT`, `LUSHER.CAT`.
- Full RE report: `docs/analysis.md`. Mermaid diagrams: `docs/development.md`.
- DOSBox-X + TTF output + `chcp 866` for Cyrillic DOS rendering.
