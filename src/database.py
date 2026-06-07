import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "training_tracker.db"


USER_SCOPED_TABLES = {
    "settings",
    "daily_checkins",
    "workout_sessions",
    "planned_exercises",
    "completed_sets",
    "progression_state",
}


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_active_user_id(default: int = 1) -> int:
    try:
        import streamlit as st

        return int(st.session_state.get("active_user_id", default))
    except Exception:
        return default


def set_active_user(user_id: int, user_name: str = "") -> None:
    try:
        import streamlit as st

        st.session_state["active_user_id"] = int(user_id)
        if user_name:
            st.session_state["active_user_name"] = user_name
    except Exception:
        pass


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    row = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = ?;
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def column_exists(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    if not table_exists(cursor, table_name):
        return False

    rows = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
    return any(row["name"] == column_name for row in rows)


def create_users_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT,
            pin TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def seed_default_users(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, name, display_name, active)
        VALUES (1, 'Jamie', 'Jamie', 1);
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, name, display_name, active)
        VALUES (2, 'Cat', 'Cat', 1);
        """
    )


def migrate_settings_table(cursor: sqlite3.Cursor) -> None:
    if not table_exists(cursor, "settings"):
        cursor.execute(
            """
            CREATE TABLE settings (
                user_id INTEGER NOT NULL DEFAULT 1,
                key TEXT NOT NULL,
                value TEXT,
                PRIMARY KEY (user_id, key),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        return

    has_user_id = column_exists(cursor, "settings", "user_id")

    if has_user_id:
        return

    cursor.execute(
        """
        ALTER TABLE settings
        RENAME TO settings_legacy;
        """
    )

    cursor.execute(
        """
        CREATE TABLE settings (
            user_id INTEGER NOT NULL DEFAULT 1,
            key TEXT NOT NULL,
            value TEXT,
            PRIMARY KEY (user_id, key),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO settings (user_id, key, value)
        SELECT 1, key, value
        FROM settings_legacy;
        """
    )

    cursor.execute("DROP TABLE settings_legacy;")


def migrate_progression_state_table(cursor: sqlite3.Cursor) -> None:
    if not table_exists(cursor, "progression_state"):
        cursor.execute(
            """
            CREATE TABLE progression_state (
                user_id INTEGER NOT NULL DEFAULT 1,
                exercise_name TEXT NOT NULL,
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
                last_updated TEXT,
                PRIMARY KEY (user_id, exercise_name),
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )
        return

    has_user_id = column_exists(cursor, "progression_state", "user_id")

    if has_user_id:
        return

    cursor.execute(
        """
        ALTER TABLE progression_state
        RENAME TO progression_state_legacy;
        """
    )

    cursor.execute(
        """
        CREATE TABLE progression_state (
            user_id INTEGER NOT NULL DEFAULT 1,
            exercise_name TEXT NOT NULL,
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
            last_updated TEXT,
            PRIMARY KEY (user_id, exercise_name),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO progression_state (
            user_id,
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
        SELECT
            1,
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
        FROM progression_state_legacy;
        """
    )

    cursor.execute("DROP TABLE progression_state_legacy;")


def add_user_id_column_if_missing(cursor: sqlite3.Cursor, table_name: str) -> None:
    if not table_exists(cursor, table_name):
        return

    if not column_exists(cursor, table_name, "user_id"):
        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN user_id INTEGER DEFAULT 1;
            """
        )

        cursor.execute(
            f"""
            UPDATE {table_name}
            SET user_id = 1
            WHERE user_id IS NULL;
            """
        )


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    create_users_table(cursor)
    seed_default_users(cursor)

    migrate_settings_table(cursor)

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
            user_id INTEGER DEFAULT 1,
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            date TEXT NOT NULL,
            workout_type TEXT,
            focus TEXT,
            readiness_category TEXT,
            estimated_duration INTEGER,
            generation_reason TEXT,
            completed INTEGER DEFAULT 0,
            session_rpe REAL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS planned_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
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
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(workout_id) REFERENCES workout_sessions(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS completed_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            workout_id INTEGER,
            exercise_name TEXT,
            set_number INTEGER,
            weight REAL,
            reps INTEGER,
            rpe REAL,
            notes TEXT,
            completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(workout_id) REFERENCES workout_sessions(id)
        );
        """
    )

    migrate_progression_state_table(cursor)

    for table_name in [
        "daily_checkins",
        "workout_sessions",
        "planned_exercises",
        "completed_sets",
    ]:
        add_user_id_column_if_missing(cursor, table_name)

    conn.commit()
    conn.close()

    seed_personalization_defaults()


def get_users() -> pd.DataFrame:
    init_db_if_needed_safe()
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT id, name, display_name, active, created_at
        FROM users
        WHERE active = 1
        ORDER BY id;
        """,
        conn,
    )
    conn.close()
    return df


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id, name, display_name, active
        FROM users
        WHERE id = ?;
        """,
        (user_id,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def create_user(name: str, display_name: str | None = None, pin: str | None = None) -> int:
    clean_name = str(name).strip()

    if not clean_name:
        raise ValueError("User name cannot be blank.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (name, display_name, pin, active)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(name) DO UPDATE SET
            display_name = excluded.display_name,
            pin = excluded.pin,
            active = 1;
        """,
        (clean_name, display_name or clean_name, pin),
    )

    row = cursor.execute(
        """
        SELECT id
        FROM users
        WHERE name = ?;
        """,
        (clean_name,),
    ).fetchone()

    conn.commit()
    conn.close()

    user_id = int(row["id"])
    seed_personalization_defaults(user_id=user_id)
    return user_id


def init_db_if_needed_safe() -> None:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        exists = table_exists(cursor, "users")
        conn.close()

        if not exists:
            init_db()
    except Exception:
        init_db()


def seed_setting(key: str, value: Any, user_id: int | None = None) -> None:
    uid = int(user_id or get_active_user_id())

    conn = get_connection()
    conn.execute(
        """
        INSERT OR IGNORE INTO settings (user_id, key, value)
        VALUES (?, ?, ?);
        """,
        (uid, key, str(value)),
    )
    conn.commit()
    conn.close()


def set_setting(key: str, value: Any, user_id: int | None = None) -> None:
    uid = int(user_id or get_active_user_id())

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO settings (user_id, key, value)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value;
        """,
        (uid, key, str(value)),
    )
    conn.commit()
    conn.close()


def get_setting(key: str, default: Optional[Any] = None, user_id: int | None = None) -> Any:
    uid = int(user_id or get_active_user_id())

    conn = get_connection()
    row = conn.execute(
        """
        SELECT value
        FROM settings
        WHERE user_id = ?
        AND key = ?;
        """,
        (uid, key),
    ).fetchone()
    conn.close()

    return row["value"] if row else default


def parse_csv_setting(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()

    if not text:
        return []

    return [item.strip() for item in text.split(",") if item.strip()]


def csv_from_list(values: list[str]) -> str:
    return ",".join([str(value).strip() for value in values if str(value).strip()])


def seed_personalization_defaults(user_id: int | None = None) -> None:
    uid = int(user_id or get_active_user_id())

    defaults = {
        "current_bodyweight": "218",
        "goal_bodyweight": "200",
        "primary_goal": "Cut while maintaining strength and improving conditioning",
        "selected_template_key": "balanced",
        "trap_bar_deadlift_max": "375",
        "bench_press_max": "245",
        "squat_max": "365",
        "weighted_pullup_max": "45",
        "preferred_equipment": "barbell,dumbbells,cable,machine,bodyweight,trap bar,landmine,pull-up bar,bands,foam roller",
        "avoided_exercises": "",
        "favorite_exercises": "",
        "mobility_priorities": "hips,t-spine,shoulders",
        "cardio_preference": "Mixed",
        "strength_method_preference": "App decides",
        "max_session_fatigue_preference": "0",
        "exercise_variety_preference": "Balanced",
    }

    for key, value in defaults.items():
        seed_setting(key, value, user_id=uid)


def get_personalization_settings(user_id: int | None = None) -> dict[str, Any]:
    uid = int(user_id or get_active_user_id())

    return {
        "preferred_equipment": parse_csv_setting(
            get_setting(
                "preferred_equipment",
                "barbell,dumbbells,cable,machine,bodyweight,trap bar,landmine,pull-up bar,bands,foam roller",
                user_id=uid,
            )
        ),
        "avoided_exercises": parse_csv_setting(get_setting("avoided_exercises", "", user_id=uid)),
        "favorite_exercises": parse_csv_setting(get_setting("favorite_exercises", "", user_id=uid)),
        "mobility_priorities": parse_csv_setting(get_setting("mobility_priorities", "hips,t-spine,shoulders", user_id=uid)),
        "cardio_preference": get_setting("cardio_preference", "Mixed", user_id=uid),
        "strength_method_preference": get_setting("strength_method_preference", "App decides", user_id=uid),
        "max_session_fatigue_preference": int(float(get_setting("max_session_fatigue_preference", 0, user_id=uid) or 0)),
        "exercise_variety_preference": get_setting("exercise_variety_preference", "Balanced", user_id=uid),
    }


def save_personalization_settings(settings: dict[str, Any], user_id: int | None = None) -> None:
    uid = int(user_id or get_active_user_id())

    list_keys = {
        "preferred_equipment",
        "avoided_exercises",
        "favorite_exercises",
        "mobility_priorities",
    }

    for key, value in settings.items():
        if key in list_keys:
            if isinstance(value, list):
                set_setting(key, csv_from_list(value), user_id=uid)
            else:
                set_setting(key, str(value), user_id=uid)
        else:
            set_setting(key, value, user_id=uid)


def insert_checkin(data: dict[str, Any], user_id: int | None = None) -> int:
    uid = int(user_id or get_active_user_id())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO daily_checkins (
            user_id,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            uid,
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


def insert_workout_session(data: dict[str, Any], user_id: int | None = None) -> int:
    uid = int(user_id or get_active_user_id())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO workout_sessions (
            user_id,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            uid,
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


def insert_planned_exercise(workout_id: int, exercise: dict[str, Any], user_id: int | None = None) -> int:
    uid = int(user_id or get_active_user_id())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO planned_exercises (
            user_id,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            uid,
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


def insert_completed_set(workout_id: int, set_data: dict[str, Any], user_id: int | None = None) -> int:
    uid = int(user_id or get_active_user_id())

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO completed_sets (
            user_id,
            workout_id,
            exercise_name,
            set_number,
            weight,
            reps,
            rpe,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            uid,
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
    uid = get_active_user_id()

    conn = get_connection()
    conn.execute(
        """
        UPDATE workout_sessions
        SET completed = 1,
            session_rpe = ?,
            notes = ?
        WHERE id = ?
        AND user_id = ?;
        """,
        (session_rpe, notes, workout_id, uid),
    )
    conn.commit()
    conn.close()


def read_table(table_name: str, user_id: int | None = None, include_all_users: bool = False) -> pd.DataFrame:
    allowed_tables = {
        "users",
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

    if (
        table_name in USER_SCOPED_TABLES
        and not include_all_users
        and column_exists(conn.cursor(), table_name, "user_id")
    ):
        uid = int(user_id or get_active_user_id())
        df = pd.read_sql_query(
            f"SELECT * FROM {table_name} WHERE user_id = ?;",
            conn,
            params=(uid,),
        )
    else:
        df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)

    conn.close()
    return df


def get_progression_state(user_id: int | None = None) -> pd.DataFrame:
    return read_table("progression_state", user_id=user_id)


def upsert_progression_state(data: dict[str, Any], user_id: int | None = None) -> None:
    uid = int(user_id or get_active_user_id())

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO progression_state (
            user_id,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, exercise_name) DO UPDATE SET
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
            uid,
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
        "users",
    ]

    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")

    conn.commit()
    conn.close()

    init_db()


def delete_workout(workout_id: int) -> None:
    uid = get_active_user_id()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM completed_sets WHERE workout_id = ? AND user_id = ?;", (workout_id, uid))
    cursor.execute("DELETE FROM planned_exercises WHERE workout_id = ? AND user_id = ?;", (workout_id, uid))
    cursor.execute("DELETE FROM workout_sessions WHERE id = ? AND user_id = ?;", (workout_id, uid))

    conn.commit()
    conn.close()


def delete_checkin(checkin_id: int) -> None:
    uid = get_active_user_id()

    conn = get_connection()
    conn.execute("DELETE FROM daily_checkins WHERE id = ? AND user_id = ?;", (checkin_id, uid))
    conn.commit()
    conn.close()


def get_latest_completed_workout_id() -> int | None:
    uid = get_active_user_id()

    conn = get_connection()
    row = conn.execute(
        """
        SELECT id
        FROM workout_sessions
        WHERE completed = 1
        AND user_id = ?
        ORDER BY id DESC
        LIMIT 1;
        """,
        (uid,),
    ).fetchone()
    conn.close()

    if row:
        return int(row["id"])

    return None


def get_workout_count() -> int:
    uid = get_active_user_id()

    conn = get_connection()
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM workout_sessions
        WHERE user_id = ?;
        """,
        (uid,),
    ).fetchone()
    conn.close()
    return int(row["count"]) if row else 0


def get_completed_workout_count() -> int:
    uid = get_active_user_id()

    conn = get_connection()
    row = conn.execute(
        """
        SELECT COUNT(*) AS count
        FROM workout_sessions
        WHERE completed = 1
        AND user_id = ?;
        """,
        (uid,),
    ).fetchone()
    conn.close()
    return int(row["count"]) if row else 0
