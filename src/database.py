import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "training_tracker.db"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS exercise_library (
            exercise_name TEXT PRIMARY KEY,
            movement_pattern TEXT,
            exercise_category TEXT,
            default_sets INTEGER,
            default_reps_min INTEGER,
            default_reps_max INTEGER,
            default_rpe REAL,
            preferred INTEGER DEFAULT 1
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            bodyweight REAL,
            hours_slept REAL,
            sleep_quality INTEGER,
            energy INTEGER,
            mood INTEGER,
            motivation INTEGER,
            stress INTEGER,
            soreness INTEGER,
            combat_last_24h INTEGER,
            hard_sparring_last_24h INTEGER,
            combat_later_today INTEGER,
            hydration INTEGER,
            protein_on_track TEXT,
            time_available INTEGER,
            goal_today TEXT,
            readiness_score REAL,
            readiness_category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            workout_type TEXT,
            focus TEXT,
            readiness_category TEXT,
            estimated_duration INTEGER,
            generation_reason TEXT,
            completed INTEGER DEFAULT 0,
            session_rpe REAL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS planned_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER,
            exercise_name TEXT,
            movement_pattern TEXT,
            exercise_category TEXT,
            planned_sets INTEGER,
            planned_reps_min INTEGER,
            planned_reps_max INTEGER,
            planned_weight REAL,
            target_rpe REAL,
            notes TEXT,
            FOREIGN KEY(workout_id) REFERENCES workout_sessions(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS completed_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER,
            exercise_name TEXT,
            set_number INTEGER,
            weight REAL,
            reps INTEGER,
            rpe REAL,
            notes TEXT,
            completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(workout_id) REFERENCES workout_sessions(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS progression_state (
            exercise_name TEXT PRIMARY KEY,
            movement_pattern TEXT,
            exercise_category TEXT,
            current_training_load REAL,
            target_sets INTEGER,
            target_reps_min INTEGER,
            target_reps_max INTEGER,
            last_successful_load REAL,
            performance_credit INTEGER DEFAULT 0,
            estimated_1rm REAL,
            next_recommended_load REAL,
            last_updated TEXT
        );
        """
    )

    conn.commit()
    conn.close()


def seed_setting(key: str, value: Any) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT OR IGNORE INTO settings (key, value)
        VALUES (?, ?);
        """,
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def set_setting(key: str, value: Any) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value;
        """,
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def get_setting(key: str, default: Optional[Any] = None) -> Any:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?;", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def insert_checkin(data: dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO daily_checkins (
            date,
            bodyweight,
            hours_slept,
            sleep_quality,
            energy,
            mood,
            motivation,
            stress,
            soreness,
            combat_last_24h,
            hard_sparring_last_24h,
            combat_later_today,
            hydration,
            protein_on_track,
            time_available,
            goal_today,
            readiness_score,
            readiness_category
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            data.get("date"),
            data.get("bodyweight"),
            data.get("hours_slept"),
            data.get("sleep_quality"),
            data.get("energy"),
            data.get("mood"),
            data.get("motivation"),
            data.get("stress"),
            data.get("soreness"),
            int(data.get("combat_last_24h", False)),
            int(data.get("hard_sparring_last_24h", False)),
            int(data.get("combat_later_today", False)),
            data.get("hydration"),
            data.get("protein_on_track"),
            data.get("time_available"),
            data.get("goal_today"),
            data.get("readiness_score"),
            data.get("readiness_category"),
        ),
    )

    checkin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return int(checkin_id)


def insert_workout_session(data: dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO workout_sessions (
            date,
            workout_type,
            focus,
            readiness_category,
            estimated_duration,
            generation_reason,
            completed,
            session_rpe,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            data.get("date"),
            data.get("workout_type"),
            data.get("focus"),
            data.get("readiness_category"),
            data.get("estimated_duration"),
            data.get("generation_reason"),
            int(data.get("completed", 0)),
            data.get("session_rpe"),
            data.get("notes"),
        ),
    )

    workout_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return int(workout_id)


def insert_planned_exercise(workout_id: int, exercise: dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO planned_exercises (
            workout_id,
            exercise_name,
            movement_pattern,
            exercise_category,
            planned_sets,
            planned_reps_min,
            planned_reps_max,
            planned_weight,
            target_rpe,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            workout_id,
            exercise.get("exercise_name"),
            exercise.get("movement_pattern"),
            exercise.get("exercise_category"),
            exercise.get("planned_sets"),
            exercise.get("planned_reps_min"),
            exercise.get("planned_reps_max"),
            exercise.get("planned_weight"),
            exercise.get("target_rpe"),
            exercise.get("notes"),
        ),
    )

    planned_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return int(planned_id)


def insert_completed_set(workout_id: int, set_data: dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO completed_sets (
            workout_id,
            exercise_name,
            set_number,
            weight,
            reps,
            rpe,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (
            workout_id,
            set_data.get("exercise_name"),
            set_data.get("set_number"),
            set_data.get("weight"),
            set_data.get("reps"),
            set_data.get("rpe"),
            set_data.get("notes"),
        ),
    )

    set_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return int(set_id)


def mark_workout_completed(workout_id: int, session_rpe: Optional[float] = None, notes: str = "") -> None:
    conn = get_connection()
    conn.execute(
        """
        UPDATE workout_sessions
        SET completed = 1,
            session_rpe = ?,
            notes = ?
        WHERE id = ?;
        """,
        (session_rpe, notes, workout_id),
    )
    conn.commit()
    conn.close()


def read_table(table_name: str) -> pd.DataFrame:
    allowed_tables = {
        "settings",
        "exercise_library",
        "daily_checkins",
        "workout_sessions",
        "planned_exercises",
        "completed_sets",
        "progression_state",
    }

    if table_name not in allowed_tables:
        raise ValueError(f"Table not allowed: {table_name}")

    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
    conn.close()
    return df


def get_progression_state() -> pd.DataFrame:
    return read_table("progression_state")


def upsert_progression_state(data: dict[str, Any]) -> None:
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO progression_state (
            exercise_name,
            movement_pattern,
            exercise_category,
            current_training_load,
            target_sets,
            target_reps_min,
            target_reps_max,
            last_successful_load,
            performance_credit,
            estimated_1rm,
            next_recommended_load,
            last_updated
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(exercise_name) DO UPDATE SET
            movement_pattern = excluded.movement_pattern,
            exercise_category = excluded.exercise_category,
            current_training_load = excluded.current_training_load,
            target_sets = excluded.target_sets,
            target_reps_min = excluded.target_reps_min,
            target_reps_max = excluded.target_reps_max,
            last_successful_load = excluded.last_successful_load,
            performance_credit = excluded.performance_credit,
            estimated_1rm = excluded.estimated_1rm,
            next_recommended_load = excluded.next_recommended_load,
            last_updated = excluded.last_updated;
        """,
        (
            data.get("exercise_name"),
            data.get("movement_pattern"),
            data.get("exercise_category"),
            data.get("current_training_load"),
            data.get("target_sets"),
            data.get("target_reps_min"),
            data.get("target_reps_max"),
            data.get("last_successful_load"),
            data.get("performance_credit", 0),
            data.get("estimated_1rm"),
            data.get("next_recommended_load"),
            data.get("last_updated", datetime.now().isoformat()),
        ),
    )

    conn.commit()
    conn.close()


def seed_exercise(exercise: dict[str, Any]) -> None:
    conn = get_connection()

    conn.execute(
        """
        INSERT OR IGNORE INTO exercise_library (
            exercise_name,
            movement_pattern,
            exercise_category,
            default_sets,
            default_reps_min,
            default_reps_max,
            default_rpe,
            preferred
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            exercise.get("exercise_name"),
            exercise.get("movement_pattern"),
            exercise.get("exercise_category"),
            exercise.get("default_sets"),
            exercise.get("default_reps_min"),
            exercise.get("default_reps_max"),
            exercise.get("default_rpe"),
            int(exercise.get("preferred", 1)),
        ),
    )

    conn.commit()
    conn.close()


def reset_database() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    tables = [
        "completed_sets",
        "planned_exercises",
        "workout_sessions",
        "daily_checkins",
        "progression_state",
        "exercise_library",
        "settings",
    ]

    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")

    conn.commit()
    conn.close()

    init_db()
