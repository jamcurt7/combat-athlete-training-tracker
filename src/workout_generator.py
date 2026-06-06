from datetime import date
from typing import Any

import pandas as pd

from src.database import get_progression_state


def get_day_name() -> str:
    return date.today().strftime("%A")


def get_progression_load(exercise_name: str, default_load: float = 0) -> float:
    progression = get_progression_state()

    if progression.empty:
        return default_load

    match = progression[progression["exercise_name"] == exercise_name]

    if match.empty:
        return default_load

    value = match.iloc[0].get("next_recommended_load", default_load)

    if pd.isna(value):
        return default_load

    return float(value)


def round_to_nearest_5(weight: float) -> float:
    if weight <= 0:
        return 0
    return round(weight / 5) * 5


def adjust_load(base_load: float, readiness_category: str) -> float:
    if base_load <= 0:
        return 0

    if readiness_category == "Green":
        multiplier = 1.00
    elif readiness_category == "Yellow":
        multiplier = 0.95
    elif readiness_category == "Orange":
        multiplier = 0.85
    else:
        multiplier = 0.65

    return round_to_nearest_5(base_load * multiplier)


def generate_workout(checkin: dict[str, Any]) -> dict[str, Any]:
    readiness_category = checkin.get("readiness_category", "Yellow")
    time_available = int(checkin.get("time_available", 60))
    goal_today = checkin.get("goal_today", "normal")
    day_name = get_day_name()

    focus = determine_focus(
        day_name=day_name,
        readiness_category=readiness_category,
        goal_today=goal_today,
        soreness=int(checkin.get("soreness", 5)),
        combat_later_today=bool(checkin.get("combat_later_today", False)),
    )

    if readiness_category == "Green":
        exercises = green_day_workout(focus, time_available)
        workout_type = "Full-Body Strength"
        reason = "High readiness. The app generated a productive full-body strength session."
    elif readiness_category == "Yellow":
        exercises = yellow_day_workout(focus, time_available)
        workout_type = "Full-Body Strength"
        reason = "Moderate readiness. The app generated a normal full-body session."
    elif readiness_category == "Orange":
        exercises = orange_day_workout(focus, time_available)
        workout_type = "Light / Accessory"
        reason = "Reduced readiness. The app lowered intensity and shifted toward accessories."
    else:
        exercises = red_day_workout(time_available)
        workout_type = "Recovery"
        reason = "Low readiness. The app generated a recovery-focused session."

    return {
        "date": date.today().isoformat(),
        "workout_type": workout_type,
        "focus": focus,
        "readiness_category": readiness_category,
        "estimated_duration": time_available,
        "generation_reason": reason,
        "exercises": exercises,
    }


def determine_focus(
    day_name: str,
    readiness_category: str,
    goal_today: str,
    soreness: int,
    combat_later_today: bool,
) -> str:
    if readiness_category == "Red" or goal_today == "recovery":
        return "Recovery"

    if readiness_category == "Orange" or soreness >= 7:
        return "Accessory / Light Full Body"

    if combat_later_today:
        return "Upper / Accessory Emphasis"

    if day_name == "Monday":
        return "Lower Emphasis Full Body"

    if day_name == "Wednesday":
        return "Upper Emphasis Full Body"

    if day_name == "Saturday":
        return "Full Body / Posterior Chain Emphasis"

    return "Full Body"


def make_exercise(
    exercise_name: str,
    movement_pattern: str,
    exercise_category: str,
    sets: int,
    reps_min: int,
    reps_max: int,
    weight: float,
    target_rpe: float,
    notes: str,
) -> dict[str, Any]:
    return {
        "exercise_name": exercise_name,
        "movement_pattern": movement_pattern,
        "exercise_category": exercise_category,
        "planned_sets": sets,
        "planned_reps_min": reps_min,
        "planned_reps_max": reps_max,
        "planned_weight": weight,
        "target_rpe": target_rpe,
        "notes": notes,
    }


def green_day_workout(focus: str, time_available: int) -> list[dict[str, Any]]:
    trap_load = adjust_load(get_progression_load("Trap Bar Deadlift", 300), "Green")
    bench_load = adjust_load(get_progression_load("Bench Press", 195), "Green")
    squat_load = adjust_load(get_progression_load("Squat", 275), "Green")
    pullup_load = adjust_load(get_progression_load("Weighted Pull-Up", 25), "Green")

    if "Lower" in focus:
        exercises = [
            make_exercise("Trap Bar Deadlift", "hinge", "main_lift", 4, 3, 5, trap_load, 8.0, "Strong but smooth. Leave 1-2 reps in reserve."),
            make_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 8.0, "Do not grind reps."),
            make_exercise("Weighted Pull-Up", "vertical_pull", "main_lift", 3, 3, 6, pullup_load, 8.0, "Use added weight if strong today; otherwise bodyweight."),
            make_exercise("Back Extension", "posterior_chain", "accessory", 3, 10, 15, 0, 7.5, "Controlled posterior chain volume."),
            make_exercise("Farmer Carry", "carry_grip", "gpp", 3, 30, 60, 0, 7.5, "Distance or seconds. Strong posture."),
            make_exercise("Neck Isometrics", "neck", "recovery_accessory", 2, 10, 20, 0, 5.0, "Easy controlled neck work."),
        ]
    elif "Upper" in focus:
        exercises = [
            make_exercise("Bench Press", "horizontal_push", "main_lift", 4, 4, 6, bench_load, 8.0, "Main upper-body strength work."),
            make_exercise("Weighted Pull-Up", "vertical_pull", "main_lift", 4, 3, 6, pullup_load, 8.0, "Prioritize quality reps."),
            make_exercise("Squat", "squat", "main_lift", 3, 4, 6, squat_load, 7.5, "Moderate lower work, no grinders."),
            make_exercise("Chest-Supported Row", "horizontal_pull", "secondary_lift", 3, 8, 12, 0, 8.0, "Upper back volume for grappling."),
            make_exercise("Lateral Raise", "shoulder_accessory", "accessory", 2, 12, 20, 0, 7.0, "Shoulder accessory work."),
            make_exercise("Hammer Curl", "forearm_grip", "accessory", 2, 10, 15, 0, 7.5, "Arm and grip support."),
        ]
    else:
        exercises = [
            make_exercise("Squat", "squat", "main_lift", 3, 4, 6, squat_load, 8.0, "Main lower-body strength work."),
            make_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 8.0, "Main press."),
            make_exercise("Weighted Pull-Up", "vertical_pull", "main_lift", 3, 3, 6, pullup_load, 8.0, "Main pull."),
            make_exercise("Romanian Deadlift", "hinge", "secondary_lift", 3, 6, 10, 0, 7.5, "Posterior-chain accessory."),
            make_exercise("Suitcase Carry", "carry_grip", "gpp", 3, 30, 60, 0, 7.0, "Anti-lateral flexion and grip."),
            make_exercise("GHR Sit-Up", "core", "accessory", 2, 8, 12, 0, 7.0, "Core strength."),
        ]

    return trim_for_time(exercises, time_available)


def yellow_day_workout(focus: str, time_available: int) -> list[dict[str, Any]]:
    trap_load = adjust_load(get_progression_load("Trap Bar Deadlift", 300), "Yellow")
    bench_load = adjust_load(get_progression_load("Bench Press", 195), "Yellow")
    squat_load = adjust_load(get_progression_load("Squat", 275), "Yellow")
    pullup_load = adjust_load(get_progression_load("Weighted Pull-Up", 25), "Yellow")

    if "Lower" in focus:
        exercises = [
            make_exercise("Trap Bar Deadlift", "hinge", "main_lift", 3, 3, 5, trap_load, 7.5, "Productive but conservative."),
            make_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Smooth reps."),
            make_exercise("Pull-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 8.0, "Bodyweight volume."),
            make_exercise("Split Squat", "single_leg", "accessory", 2, 8, 12, 0, 7.0, "Moderate single-leg work."),
            make_exercise("Dead Bug", "core", "recovery_accessory", 2, 8, 12, 0, 5.0, "Controlled core work."),
        ]
    elif "Upper" in focus:
        exercises = [
            make_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Main upper-body work."),
            make_exercise("Pull-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 8.0, "Quality pulling."),
            make_exercise("Goblet Squat", "squat", "accessory", 3, 8, 12, 0, 7.0, "Light lower-body volume."),
            make_exercise("Chest-Supported Row", "horizontal_pull", "secondary_lift", 3, 8, 12, 0, 8.0, "Upper-back volume."),
            make_exercise("Triceps Pressdown", "arm_accessory", "accessory", 2, 10, 15, 0, 7.0, "Pressing support."),
            make_exercise("Wrist Curl", "forearm_grip", "accessory", 2, 12, 20, 0, 7.0, "Forearm support."),
        ]
    else:
        exercises = [
            make_exercise("Squat", "squat", "main_lift", 3, 4, 6, squat_load, 7.5, "Controlled lower-body strength."),
            make_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Controlled pressing."),
            make_exercise("Pull-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 8.0, "Pulling volume."),
            make_exercise("Back Extension", "posterior_chain", "accessory", 2, 10, 15, 0, 7.0, "Posterior-chain accessory."),
            make_exercise("Plank", "core", "accessory", 2, 30, 60, 0, 7.0, "Core stability."),
        ]

    return trim_for_time(exercises, time_available)


def orange_day_workout(focus: str, time_available: int) -> list[dict[str, Any]]:
    trap_load = adjust_load(get_progression_load("Trap Bar Deadlift", 300), "Orange")
    bench_load = adjust_load(get_progression_load("Bench Press", 195), "Orange")

    exercises = [
        make_exercise("Trap Bar Deadlift", "hinge", "main_lift", 2, 3, 5, trap_load, 6.5, "Technique work. Keep it easy."),
        make_exercise("Landmine Press", "vertical_push", "secondary_lift", 3, 6, 10, 0, 7.0, "Moderate pressing without grinding."),
        make_exercise("Chest-Supported Row", "horizontal_pull", "secondary_lift", 3, 8, 12, 0, 7.5, "Upper-back work."),
        make_exercise("Goblet Squat", "squat", "accessory", 2, 8, 12, 0, 6.5, "Light lower-body work."),
        make_exercise("Lateral Raise", "shoulder_accessory", "accessory", 2, 12, 20, 0, 7.0, "Accessory work."),
        make_exercise("Hammer Curl", "forearm_grip", "accessory", 2, 10, 15, 0, 7.0, "Forearm and grip support."),
        make_exercise("Dead Bug", "core", "recovery_accessory", 2, 8, 12, 0, 5.0, "Easy core control."),
    ]

    if "Upper" in focus:
        exercises[0] = make_exercise("Bench Press", "horizontal_push", "main_lift", 2, 4, 6, bench_load, 6.5, "Easy technique pressing.")

    return trim_for_time(exercises, time_available)


def red_day_workout(time_available: int) -> list[dict[str, Any]]:
    exercises = [
        make_exercise("Incline Walk", "conditioning", "recovery", 1, 10, 20, 0, 4.0, "Easy pace. Nasal breathing if possible."),
        make_exercise("Mobility Flow", "mobility", "recovery", 1, 5, 10, 0, 3.0, "Move smoothly. Do not force range."),
        make_exercise("Hip Airplane", "mobility", "recovery", 2, 5, 8, 0, 4.0, "Balance and hip control."),
        make_exercise("Back Extension", "posterior_chain", "accessory", 2, 10, 15, 0, 5.0, "Very easy blood-flow work."),
        make_exercise("Dead Bug", "core", "recovery_accessory", 2, 8, 12, 0, 4.0, "Controlled breathing and bracing."),
        make_exercise("Neck Isometrics", "neck", "recovery_accessory", 2, 10, 20, 0, 4.0, "Light neck work."),
        make_exercise("Reverse Wrist Curl", "forearm_grip", "accessory", 2, 12, 20, 0, 5.0, "Light forearm work."),
    ]

    return trim_for_time(exercises, time_available)


def trim_for_time(exercises: list[dict[str, Any]], time_available: int) -> list[dict[str, Any]]:
    if time_available <= 30:
        return exercises[:4]

    if time_available <= 45:
        return exercises[:5]

    if time_available <= 60:
        return exercises[:6]

    return exercises
