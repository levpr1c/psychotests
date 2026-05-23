import sqlite3
from datetime import date, datetime
from pathlib import Path
from src.models.user import User, UserCreate
from src.models.test_result import TestResult, TestResultCreate


DB_PATH = Path(__file__).parent.parent.parent / "data" / "psycho.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                birth_date TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                test_name TEXT NOT NULL,
                raw_data TEXT DEFAULT '',
                scores TEXT DEFAULT '{}',
                interpretation TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)


def create_user(data: UserCreate) -> User:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, birth_date) VALUES (?, ?)",
            (data.name, data.birth_date.isoformat() if data.birth_date else None),
        )
        return User(
            id=cursor.lastrowid,
            name=data.name,
            birth_date=data.birth_date,
        )


def get_all_users() -> list[User]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [_row_to_user(row) for row in rows]


def get_user(user_id: int) -> User | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_user(row) if row else None


def delete_user(user_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.execute("DELETE FROM test_results WHERE user_id = ?", (user_id,))


def save_result(data: TestResultCreate) -> TestResult:
    import json

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO test_results (user_id, test_name, raw_data, scores, interpretation) VALUES (?, ?, ?, ?, ?)",
            (
                data.user_id,
                data.test_name,
                data.raw_data,
                json.dumps(data.scores, ensure_ascii=False),
                data.interpretation,
            ),
        )
        return TestResult(
            id=cursor.lastrowid,
            user_id=data.user_id,
            test_name=data.test_name,
            raw_data=data.raw_data,
            scores=data.scores,
            interpretation=data.interpretation,
        )


def get_results_for_user(user_id: int) -> list[TestResult]:
    import json

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM test_results WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        results = []
        for row in rows:
            result = _row_to_result(row)
            result.scores = json.loads(row["scores"]) if row["scores"] else {}
            results.append(result)
        return results


def get_all_results() -> list[TestResult]:
    import json

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM test_results ORDER BY created_at DESC"
        ).fetchall()
        results = []
        for row in rows:
            result = _row_to_result(row)
            result.scores = json.loads(row["scores"]) if row["scores"] else {}
            results.append(result)
        return results


def _row_to_user(row: sqlite3.Row) -> User:
    bd = row["birth_date"]
    return User(
        id=row["id"],
        name=row["name"],
        birth_date=date.fromisoformat(bd) if bd else None,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_result(row: sqlite3.Row) -> TestResult:
    scores = {}
    return TestResult(
        id=row["id"],
        user_id=row["user_id"],
        test_name=row["test_name"],
        raw_data=row["raw_data"],
        scores=scores,
        interpretation=row["interpretation"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
