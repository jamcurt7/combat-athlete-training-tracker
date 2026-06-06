from typing import Dict

import pandas as pd

from src.database import read_table


def get_all_data() -> Dict[str, pd.DataFrame]:
    """Load all major app tables into DataFrames."""
    tables = [
        "daily_checkins",
        "workout_sessions",
        "planned_exercises",
        "completed_sets",
        "progression_state",
        "exercise_library",
        "settings",
    ]

    data = {}

    for table in tables:
        try:
            data[table] = read_table(table)
        except Exception:
            data[table] = pd.DataFrame()

    return data


def clean_dates(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    if df.empty or date_col not in df.columns:
        return df

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df


def calculate_set_metrics() -> pd.DataFrame:
    completed_sets = read_table("completed_sets")

    if completed_sets.empty:
        return pd.DataFrame()

    df = completed_sets.copy()

    df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(0)
    df["reps"] = pd.to_numeric(df["reps"], errors="coerce").fillna(0)
    df["rpe"] = pd.to_numeric(df["rpe"], errors="coerce").fillna(0)

    df["volume_load"] = df["weight"] * df["reps"]
    df["estimated_1rm"] = df.apply(
        lambda row: estimate_1rm(row["weight"], row["reps"]),
        axis=1,
    )

    return df


def estimate_1rm(weight: float, reps: float) -> float:
    if weight <= 0 or reps <= 0:
        return 0.0

    return round(weight * (1 + reps / 30), 1)


def calculate_exercise_summary() -> pd.DataFrame:
    sets = calculate_set_metrics()

    if sets.empty:
        return pd.DataFrame()

    summary = (
        sets.groupby("exercise_name")
        .agg(
            total_sets=("set_number", "count"),
            total_reps=("reps", "sum"),
            total_volume=("volume_load", "sum"),
            avg_rpe=("rpe", "mean"),
            best_estimated_1rm=("estimated_1rm", "max"),
            max_weight=("weight", "max"),
        )
        .reset_index()
    )

    summary["avg_rpe"] = summary["avg_rpe"].round(1)
    summary["total_volume"] = summary["total_volume"].round(1)

    return summary.sort_values("total_volume", ascending=False)


def calculate_readiness_summary() -> pd.DataFrame:
    checkins = read_table("daily_checkins")

    if checkins.empty:
        return pd.DataFrame()

    df = clean_dates(checkins)

    numeric_cols = [
        "bodyweight",
        "hours_slept",
        "sleep_quality",
        "energy",
        "mood",
        "motivation",
        "stress",
        "soreness",
        "hydration",
        "readiness_score",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.sort_values("date", ascending=False)


def calculate_weekly_volume() -> pd.DataFrame:
    sets = calculate_set_metrics()
    planned = read_table("planned_exercises")
    sessions = read_table("workout_sessions")

    if sets.empty or sessions.empty:
        return pd.DataFrame()

    sessions = sessions[["id", "date"]].rename(columns={"id": "workout_id"})
    sessions["date"] = pd.to_datetime(sessions["date"], errors="coerce")

    merged = sets.merge(sessions, on="workout_id", how="left")

    if not planned.empty:
        planned_patterns = planned[["workout_id", "exercise_name", "movement_pattern"]]
        merged = merged.merge(
            planned_patterns,
            on=["workout_id", "exercise_name"],
            how="left",
        )
    else:
        merged["movement_pattern"] = "unknown"

    merged["week"] = merged["date"].dt.to_period("W").astype(str)

    weekly = (
        merged.groupby(["week", "movement_pattern"])
        .agg(
            total_sets=("set_number", "count"),
            total_reps=("reps", "sum"),
            total_volume=("volume_load", "sum"),
            avg_rpe=("rpe", "mean"),
        )
        .reset_index()
    )

    weekly["avg_rpe"] = weekly["avg_rpe"].round(1)
    weekly["total_volume"] = weekly["total_volume"].round(1)

    return weekly.sort_values(["week", "movement_pattern"])


def calculate_workout_summary() -> pd.DataFrame:
    sessions = read_table("workout_sessions")

    if sessions.empty:
        return pd.DataFrame()

    df = clean_dates(sessions)

    return df.sort_values("date", ascending=False)


def calculate_bodyweight_trend() -> pd.DataFrame:
    checkins = read_table("daily_checkins")

    if checkins.empty or "bodyweight" not in checkins.columns:
        return pd.DataFrame()

    df = checkins[["date", "bodyweight", "readiness_score"]].copy()
    df = clean_dates(df)
    df["bodyweight"] = pd.to_numeric(df["bodyweight"], errors="coerce")
    df["readiness_score"] = pd.to_numeric(df["readiness_score"], errors="coerce")

    df = df.dropna(subset=["bodyweight"])

    return df.sort_values("date")


def calculate_estimated_1rm_trend() -> pd.DataFrame:
    sets = calculate_set_metrics()
    sessions = read_table("workout_sessions")

    if sets.empty or sessions.empty:
        return pd.DataFrame()

    sessions = sessions[["id", "date"]].rename(columns={"id": "workout_id"})
    sessions["date"] = pd.to_datetime(sessions["date"], errors="coerce")

    merged = sets.merge(sessions, on="workout_id", how="left")

    merged = merged[merged["estimated_1rm"] > 0]

    if merged.empty:
        return pd.DataFrame()

    trend = (
        merged.groupby(["date", "exercise_name"])
        .agg(best_estimated_1rm=("estimated_1rm", "max"))
        .reset_index()
    )

    return trend.sort_values("date")


def calculate_average_rpe_by_exercise() -> pd.DataFrame:
    sets = calculate_set_metrics()

    if sets.empty:
        return pd.DataFrame()

    summary = (
        sets.groupby("exercise_name")
        .agg(avg_rpe=("rpe", "mean"), sets_logged=("set_number", "count"))
        .reset_index()
    )

    summary["avg_rpe"] = summary["avg_rpe"].round(1)

    return summary.sort_values("avg_rpe", ascending=False)


def calculate_summary_metrics() -> dict:
    checkins = read_table("daily_checkins")
    sessions = read_table("workout_sessions")
    sets = read_table("completed_sets")
    progression = read_table("progression_state")

    metrics = {
        "checkins_logged": len(checkins),
        "workouts_generated": len(sessions),
        "completed_sets_logged": len(sets),
        "main_lifts_tracked": len(progression),
    }

    if not checkins.empty and "readiness_score" in checkins.columns:
        metrics["avg_readiness"] = round(
            pd.to_numeric(checkins["readiness_score"], errors="coerce").mean(),
            1,
        )
    else:
        metrics["avg_readiness"] = 0

    if not sets.empty:
        set_metrics = calculate_set_metrics()
        metrics["total_volume_load"] = round(set_metrics["volume_load"].sum(), 1)
    else:
        metrics["total_volume_load"] = 0

    return metrics
