# Разработка TUI-приложения психологических тестов

## 1. Архитектура приложения

```mermaid
flowchart TD
    run.py -->|sys.path + import| src/main.py
    src/main.py -->|init_db| src/models/database.py
    src/main.py -->|PsychoApp запуск| src/app.py

    src/app.py -->|push_screen user_select| src/screens/user_select.py
    src/app.py -->|SCREENS dict| src/screens/user_create.py

    src/screens/user_select.py -->|выбрать| src/screens/main_menu.py
    src/screens/user_select.py -->|статистика| src/screens/statistics.py

    src/screens/main_menu.py -->|выбрать тест| src/screens/biorhythm.py
    src/screens/main_menu.py -->|выбрать тест| src/screens/eysenck.py
    src/screens/main_menu.py -->|выбрать тест| src/screens/stress.py
    src/screens/main_menu.py -->|выбрать тест| src/screens/neiro.py
    src/screens/main_menu.py -->|выбрать тест| src/screens/connect.py
    src/screens/main_menu.py -->|выбрать тест| src/screens/economy.py
    src/screens/main_menu.py -->|выбрать тест| src/screens/heart.py
    src/screens/main_menu.py -->|выбрать тест| src/screens/selftest.py
    src/screens/main_menu.py -->|выбрать тест| src/screens/luscher.py

    src/screens/_base_test.py -.->|базовый класс| src/screens/stress.py
    src/screens/_base_test.py -.->|базовый класс| src/screens/neiro.py
    src/screens/_base_test.py -.->|базовый класс| src/screens/connect.py
    src/screens/_base_test.py -.->|базовый класс| src/screens/economy.py
    src/screens/_base_test.py -.->|базовый класс| src/screens/heart.py
    src/screens/_base_test.py -.->|базовый класс| src/screens/selftest.py

    src/screens/confirm_modal.py -.->|подтверждение| src/screens/user_select.py
    src/screens/confirm_modal.py -.->|подтверждение| src/screens/main_menu.py
    src/screens/confirm_modal.py -.->|подтверждение| src/screens/_base_test.py
    src/screens/confirm_modal.py -.->|подтверждение| src/screens/biorhythm.py
    src/screens/confirm_modal.py -.->|подтверждение| src/screens/luscher.py
```

## 2. Поток пользователя

```mermaid
flowchart LR
    A[UserSelectScreen] -->|создать| B[UserCreateScreen]
    A -->|выбрать| C[MainMenuScreen]
    A -->|статистика| D[StatisticsScreen]
    D -->|фильтр по тесту| D
    D -->|выбрать результат| E[ResultViewScreen]
    C -->|тест 1-9| F[TestScreen]
    F -->|finish_test| G[Сохранение в SQLite]
    G -->|pop_screen| C
    F -->|escape| H[ConfirmModal]
    H -->|Да| C
    H -->|Нет| F
```

## 3. Навигация и клавиши

```mermaid
flowchart TD
    subgraph App-level
        Q["q/й"] --> QuitConfirm["ConfirmModal"]
        QuitConfirm -->|Да| Exit["app.exit()"]
        QuitConfirm -->|Нет| Stay["остаться"]
    end

    subgraph Screen-level
        ESC["escape"] --> BackConfirm["ConfirmModal (контекст)"]
        BackConfirm -->|Да| Pop["pop_screen / exit"]
        BackConfirm -->|Нет| Stay2["остаться"]
    end

    subgraph TestScreen-level
        UP["↑/←"] --> FocusPrev["focus_previous (intelligent)"]
        DOWN["↓/→"] --> FocusNext["focus_next (intelligent)"]
        NUM["1-5 / 1-2 / 1-8"] --> Select["выбрать ответ"]
        ENTER["enter (priority)"] --> NextOrBack["action_next или действие кнопки"]
    end
```

## 4. Иерархия экранов

```mermaid
classDiagram
    class Screen {
        +BINDINGS
        +compose()
        +on_mount()
        +action_back()
    }

    class BaseTestScreen {
        +QUESTIONS
        +current_q
        +answers
        +current_answer
        +action_next()
        +_select_num()
        +finish_test()*
        +show_question()
    }

    class EysenckScreen {
        +57 вопросов
        +24E/24N/9L
        +finish_test()
    }

    class BiorhythmScreen {
        +calculate()
        +3 цикла
    }

    class LuscherScreen {
        +2 раунда
        +8 цветов
        +finish_test()
    }

    class ConfirmModal {
        +dismiss(True/False)
    }

    Screen <|-- BaseTestScreen
    Screen <|-- EysenckScreen
    Screen <|-- BiorhythmScreen
    Screen <|-- LuscherScreen
    Screen <|-- ConfirmModal
    Screen <|-- MainMenuScreen
    Screen <|-- UserSelectScreen
    Screen <|-- UserCreateScreen
    Screen <|-- StatisticsScreen
    Screen <|-- ResultViewScreen
    BaseTestScreen <|-- StressScreen
    BaseTestScreen <|-- NeiroScreen
    BaseTestScreen <|-- ConnectScreen
    BaseTestScreen <|-- EconomyScreen
    BaseTestScreen <|-- HeartScreen
    BaseTestScreen <|-- SelftestScreen
```

## 5. Модели данных

```mermaid
erDiagram
    USERS {
        int id PK
        string name
        date birth_date
        datetime created_at
    }

    TEST_RESULTS {
        int id PK
        int user_id FK
        string test_name
        string raw_data
        string scores "JSON"
        string interpretation
        datetime created_at
    }

    USERS ||--o{ TEST_RESULTS : имеет
```

Pydantic-модели:

| Класс | Поля | Назначение |
|-------|------|------------|
| `User` | id, name, birth_date, created_at | Чтение из БД |
| `UserCreate` | name, birth_date | Создание пользователя |
| `TestResult` | id, user_id, test_name, raw_data, scores (`dict[str, Any]`), interpretation, created_at | Чтение из БД |
| `TestResultCreate` | user_id, test_name, raw_data, scores (`dict[str, Any]`), interpretation | Сохранение результата |

## 6. Тесты (9 тестов)

| Тест | Экран | Вопросов | Расчёт | Модуль |
|------|-------|----------|--------|--------|
| Биоритмы | `BiorhythmScreen` | — (расчёт по дате) | sin-циклы 23/28/33 дня | `biorhythm_calc.py` |
| Айзенк EPI | `EysenckScreen` | 57 (24E/24N/9L), shuffled | Да/Нет → баллы по шкалам | `eysenck_calc.py` |
| Стресс | `StressScreen` | 24 × Likert 1-5, shuffled | Сумма + уровни | `stress_calc.py` |
| Неврология | `NeiroScreen` | 24 × Likert 1-5, shuffled | Сумма + уровни | `neiro_calc.py` |
| Совместимость | `ConnectScreen` | 25 × Likert 1-5, shuffled | Инвертированные + среднее × 20 | `connect_calc.py` |
| Деловая сфера | `EconomyScreen` | 25 × Likert 1-5, shuffled | Инвертированные + среднее × 20 | `economy_calc.py` |
| Сердечно-сосуд. | `HeartScreen` | 25 × Likert 1-5, shuffled by scale | 6 шкал (IBC/PPS/DE/AG/NCD/ZM) | `heart_calc.py` |
| Самооценка | `SelftestScreen` | 20 × Likert 1-5, shuffled | Инвертированные + среднее × 25 | `selftest_calc.py` |
| Люшер | `LuscherScreen` | 2 раунда × 8 цветов | Тревога/компенсация/активность/работоспособность/вегетатика/консистентность | `luscher_calc.py` |

## 7. Исправленные баги (по аудиту)

| # | Файл | Баг | Исправление |
|---|------|-----|-------------|
| 1 | `history.py:29-41` | `on_mount` sync, `list_view.append()` без `await` → `DuplicateIds` | `async def on_mount`, `await` для всех `append` |
| 2 | `eysenck.py:152-154` | Мёртвый код: второй `elif event.button.id == "prev_btn"` | Удалён |
| 3 | `biorhythm.py` | Результат не сохранялся в БД | Добавлен `save_result` после расчёта |
| 4 | `luscher_calc.py:42` | `list.index(x)` падает при дубликатах цветов | `_safe_index` с default 4 |
| 5 | `heart_calc.py:11` | `ZeroDivisionError` при пустом списке ответов шкалы | Проверка `if not values` |
| 6 | `database.py` | `DB_PATH` в PyInstaller ведёт в temp | `platformdirs` при `sys.frozen` |
| 7 | `stress/neiro/connect/economy/heart/selftest.py` | Отсутствует `self.test_completed = True` в `finish_test()` | Добавлен флаг |
| 8 | `stress/neiro/connect/economy/selftest.py` | `Static.update()` с Markdown вместо Rich | Заменён на Rich-разметку |
| 9 | `_base_test.py` + `eysenck.py` | `action_next()` и `_select_num()` без guard `test_completed` | Добавлена проверка |
| 10 | `app.tcss` | `#date_label` без `width: 100%` | Добавлен |
| 11 | `luscher.py` | `_rebuild_buttons()` через `remove_children()+mount()` → `DuplicateIds` | In-place style update |
| 12 | `app.py` | `StatisticsScreen` в `SCREENS` dict → кеширование устаревших данных | Удалён из dict, новый instance |

## 8. StatisticsScreen

Экран статистики (заменяет удалённый `history.py`). Показывает:

1. **Информация о пользователе** — имя текущего пользователя или "Все пользователи"
2. **Диаграмма** — горизонтальные баровые графики (Unicode-блоки) с количеством прохождений по каждому тесту и средним баллом
3. **Фильтр по тесту** — кнопки "Все" + по каждому типу теста; фильтрует список результатов
4. **Список результатов** — история с датой, названием и краткой интерпретацией; каждый элемент — `ListItem` с одним `Static` (Rich-разметка, дата+название на первой строке, интерпретация/баллы на второй)
5. **Детали результата** — при выборе элемента открывается `ResultViewScreen` с полными показателями и интерпретацией; для Люшера — таблица цветов через `_show_luscher_detail()`

```mermaid
flowchart LR
    A[StatisticsScreen on_mount] --> B[get_results_for_user / get_all_results]
    B --> C[_build_chart: counts + avg, Table expand=True]
    C --> D[показать Panel с Table]
    D --> E[кнопки фильтра]
    E --> F[_refresh_list]
    F --> G[ListView с многострочными ListItem]
    G -->|выбор| H[ResultViewScreen / _show_luscher_detail]
```

## 9. Перемешивание вопросов

`shuffle_questions()` в `_base_test.py` — модульная функция. Если передан `key_fn`, группирует по ключу (шкала), сортирует группы по размеру, интерливит — одинаковые шкалы не идут подряд. Без `key_fn` — `random.shuffle`.

- **EysenckScreen**: `self._questions = shuffle_questions(EYSENCK_QUESTIONS, key_fn=lambda q: q[1])`
- **BaseTestScreen**: shuffles `self.QUESTIONS` (и `self.SCALES` если есть) в `on_mount`

## 10. Тестовое покрытие (147 тестов, 0 падений)

```mermaid
pie title Распределение тестов
    "Расчёты + граничные" : 45
    "Интерпретации" : 18
    "БД + модели" : 14
    "Импорты + структура" : 12
    "UI интеграционные" : 16
```

## 11. Зависимости

- **textual** 8.x — TUI framework
- **pydantic** ≥ 2.0.0 — модели данных с валидацией
- **rich** ≥ 13.0.0 — форматирование (таблицы, панели)
- **SQLite3** — встроенная БД (без ORM)

## 12. Запуск и тестирование

```bash
# Запуск
./venv/bin/python run.py

# Тесты
./venv/bin/python tests.py

# Очистка кэша после изменений
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

Shell — **fish**; `source venv/bin/activate` не работает. Использовать `venv/bin/python3` напрямую.
