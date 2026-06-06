from datetime import datetime
from typing import Any

import pandas as pd

from src.database import read_table, upsert_progression_state


MAIN_LIFTS = {
    "Trap Bar Deadlift",
    "Squat",
    "Bench Press",
    "Weighted Pull-Up",
}


def estimate_1rm(weight: float, reps: int) -> float:
    if weight <= 0 or reps <= 0:
        return 0.0

    return round(weight * (1 + reps / 30), 1)


def get_load_jump(exercise_name: str) -> float:
    if exercise_name in {"Trap Bar Deadlift", "Squat"}:
        return 5.0

    if exercise_name in {"Bench Press", "Weighted Pull-Up"}:
        return 2.5

    return 5.0


def update_progression_from_workout(workout_id: int, readiness_category: str) -> list[dict[str, Any]]:
    """
    Conservative progression logic.

    Main rules:
    - Green/Yellow days can update progression.
    - Orange/Red days do not punish long-term progression.
    - Two successful exposures are required before increasing load.
    - High RPE means repeat the load.
    - Missed reps usually means repeat the load.
    """

    planned = read_table("planned_exercises")
    completed = read_table("completed_sets")
    current_state = read_table("progression_state")

    planned = planned[planned["workout_id"] == workout_id]
    completed = completed[completed["workout_id"] == workout_id]

    if planned.empty or completed.empty:
        return []

    updates = []

    for _, planned_row in planned.iterrows():
        exercise_name = planned_row["exercise_name"]

        if exercise_name not in MAIN_LIFTS:
            continue

        exercise_sets = completed[completed["exercise_name"] == exercise_name]

        if exercise_sets.empty:
            continue

        planned_sets = int(planned_row["planned_sets"])
        reps_min = int(planned_row["planned_reps_min"])
        reps_max = int(planned_row["planned_reps_max"])
        planned_weight = float(planned_row["planned_weight"] or 0)
        target_rpe = float(planned_row["target_rpe"] or 8)

        completed_set_count = len(exercise_sets)
        min_reps_completed = exercise_sets["reps"].min()
        max_rpe = exercise_sets["rpe"].max()
        avg_rpe = exercise_sets["rpe"].mean()

        best_e1rm = 0.0
        for _, set_row in exercise_sets.iterrows():
            set_e1rm = estimate_1rm(float(set_row["weight"] or 0), int(set_row["reps"] or 0))
            best_e1rm = max(best_e1rm, set_e1rm)

        state_match = current_state[current_state["exercise_name"] == exercise_name]

        if not state_match.empty:
            state = state_match.iloc[0].to_dict()
            current_load = float(state.get("current_training_load") or planned_weight)
            last_successful_load = float(state.get("last_successful_load") or planned_weight)
            performance_credit = int(state.get("performance_credit") or 0)
            previous_e1rm = float(state.get("estimated_1rm") or 0)
        else:
            current_load = planned_weight
            last_successful_load = planned_weight
            performance_credit = 0
            previous_e1rm = 0

        if readiness_category in {"Orange", "Red"}:
            decision = "No progression change because readiness was reduced."
            next_load = current_load
            new_credit = performance_credit

        else:
            completed_prescription = (
                completed_set_count >= planned_sets
                and min_reps_completed >= reps_min
            )

            high_quality = completed_prescription and max_rpe <= target_rpe

            completed_but_too_hard = completed_prescription and max_rpe > target_rpe

            missed_reps = not completed_prescription

            if high_quality:
                new_credit = performance_credit + 1

                if new_credit >= 2:
                    jump = get_load_jump(exercise_name)
                    next_load = current_load + jump
                    current_load = next_load
                    last_successful_load = planned_weight
                    new_credit = 0
                    decision = f"Progressed conservatively by {jump} lb after repeated successful exposures."
                else:
                    next_load = current_load
                    last_successful_load = planned_weight
                    decision = "Successful exposure. One more strong exposure needed before increasing load."

            elif completed_but_too_hard:
                next_load = current_load
                new_credit = max(0, performance_credit)
                decision = "Completed work, but RPE was high. Repeat load next time."

            elif missed_reps:
                next_load = current_load
                new_credit = max(0, performance_credit - 1)
                decision = "Missed prescribed reps or sets. Repeat load next time."

            else:
                next_load = current_load
                new_credit = performance_credit
                decision = "No clear progression change."

        updated_e1rm = max(previous_e1rm, best_e1rm)

        updated_state = {
            "exercise_name": exercise_name,
            "movement_pattern": planned_row["movement_pattern"],
            "exercise_category": planned_row["exercise_category"],
            "current_training_load": current_load,
            "target_sets": planned_sets,
            "target_reps_min": reps_min,
            "target_reps_max": reps_max,
            "last_successful_load": last_successful_load,
            "performance_credit": new_credit,
            "estimated_1rm": updated_e1rm,
            "next_recommended_load": next_load,
            "last_updated": datetime.now().isoformat(),
        }

        upsert_progression_state(updated_state)

        updates.append(
            {
                "exercise_name": exercise_name,
                "decision": decision,
                "completed_sets": completed_set_count,
                "planned_sets": planned_sets,
                "min_reps_completed": int(min_reps_completed),
                "max_rpe": round(float(max_rpe), 1),
                "avg_rpe": round(float(avg_rpe), 1),
                "best_estimated_1rm": updated_e1rm,
                "next_recommended_load": next_load,
                "performance_credit": new_credit,
            }
        )

    return updates
