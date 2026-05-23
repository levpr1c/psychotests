# AGENTS.md (RU)

## Shell и окружение
- Shell пользователя — **fish**; `source venv/bin/activate` не работает. Использовать `venv/bin/python3` напрямую.
- Arch Linux, PEP 668; всегда использовать существующий `venv/`.
- **Wayland**: нет X11, нет ImageMagick для скриншотов.

## Команды
```bash
venv/bin/python3 run.py          # запуск приложения
venv/bin/python3 tests.py        # запуск тестов (нет pytest, один файл)
```
- После любого изменения кода: `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null` (старые .pyc вызывают трудноуловимые баги).

## Textual 8.x: особенности
- `RadioSet` не имеет публичного API `index`. Сброс через приватные атрибуты с `prevent`:
  ```python
  with radio.prevent(RadioButton.Changed):
      for btn in radio.query(RadioButton): btn.value = False
  radio._pressed_button = None
  radio._selected = None
  ```
- `RadioSet` имеет встроенный `Binding("enter")` → `toggle_button`, который **потребляет** Enter. На тестовых экранах используется `priority=True` на своём `enter` для перехвата.
- `ListView.clear()` и `.append()` — **асинхронные** — всегда `await`, иначе `DuplicateIds`.
- `ConfirmModal` использует `Screen` (не `ModalScreen`), чтобы избежать унаследованных `layout: vertical` + `overflow-y: auto`. В `on_mount` устанавливается `dlg.styles.width = "auto"`.
- Навигация стрелками требует явных методов `action_focus_next`/`action_focus_previous`. RadioSet: интеллектуальная навигация — стрелки внутри набора, на границе → переход к следующему виджету.

## Горячие клавиши
| Клавиша | Действие | Уровень |
|---------|----------|---------|
| `q`/`й` | Выход (ConfirmModal → exit) | App |
| `escape` | Назад (контекст экрана) | Screen |
| `1`–`5` | Выбор ответа (Likert-тесты) | Test screen |
| `enter` | Следующий вопрос (`priority=True`) | Test screen |

`action_next` проверяет `self.focused.id == "prev_btn"` → вместо "далее" идёт назад.

## База данных и модели
- SQLite3, файл `data/psycho.db` (автосоздание через `init_db()`).
- `scores: dict[str, Any]` в `TestResult` — был `dict[str, float]`, падало на Stress/Neiro.
- `user.name` обязателен, `birth_date` опционален (ISO-строка, `Input`, не `DatePicker` — в Textual 8.x нет DatePicker).

## Тесты
- **Айзенк**: 57 вопросов, шкалы **24E / 24N / 9L**. Ответы `bool`: `self.current_answer == 0` (индекс 0 = "Да").
- **Люшер**: для Pydantic-валидации нужен фильтр `flat_scores`.
- **Биоритмы**: 3 цикла (physical/emotional/intellectual), диапазон значений ±1.0.
- **Heart**: 6 шкал (IBC/PPS/DE/AG/NCD/ZM), пустой список — защита от `ZeroDivisionError`.
- **Luscher `_safe_index`**: `choices.index()` падает при дубликатах цветов; заменён на `_safe_index` с default=4.

## DOS-происхождение (CODE.DAT отсутствует)
- Банки вопросов восстановлены по стандартным психологическим методикам (оригинальный `CODE.DAT` утерян).
- Luscher использует реальные DOS-данные: `LUSHER.DAT`, `LUSHER.INT`, `LUSHER.CAT` в CP866.
- Полный отчёт по реверс-инжинирингу: `docs/analysis.md`.

## Архитектура
```
run.py → src/main.py → init_db() + PsychoApp().run()
                        ↓
                   UserSelectScreen (вход)
                        ↓
                   MainMenuScreen (9 тестов)
                        ↓
                   Экран теста (BaseTestScreen или отдельный)
                        ↓
                   HistoryScreen (просмотр результатов)
```
- 9 тестов: Биоритмы, Айзенк, Стресс, Неврология, Совместимость, Деловая сфера, Сердечно-сосудистая, Самооценка, Люшер.
- Расчёты: `src/tests/`, вопросы: `src/data/questions.py`, интерпретации: `src/data/interpretations.py`.

## Баги, найденные и исправленные при аудите
1. **history.py** — `on_mount` был sync, `list_view.append()` без `await` → race condition
2. **eysenck.py** — мёртвый код (дублирующийся `elif` для `prev_btn`)
3. **biorhythm.py** — результат не сохранялся в БД
4. **luscher_calc.py** — `list.index()` падал на дубликатах цветов
5. **heart_calc.py** — `ZeroDivisionError` при пустом списке ответов шкалы
