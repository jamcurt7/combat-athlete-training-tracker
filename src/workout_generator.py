from datetime import date
from typing import Any

import pandas as pd

from src.database import (
    get_progression_state,
    get_completed_workout_count,
    get_setting,
)


MAX_LIFTS = {
    "Trap Bar Deadlift": 375,
    "Bench Press": 245,
    "Squat": 365,
    "Weighted Pull-Up": 45,  # Added weight only
    "Weighted Chin-Up": 45,  # Added weight only
}

DEFAULT_TRAINING_LOADS = {
    "Trap Bar Deadlift": 300,
    "Bench Press": 195,
    "Squat": 275,
    "Weighted Pull-Up": 25,
    "Weighted Chin-Up": 20,
}


def get_day_name() -> str:
    return date.today().strftime("%A")


def is_deload_day() -> bool:
    completed_count = get_completed_workout_count()

    if completed_count == 0:
        return False

    return completed_count % 4 == 0


def get_training_max(exercise_name: str) -> float:
    setting_key_map = {
        "Trap Bar Deadlift": "trap_bar_deadlift_max",
        "Bench Press": "bench_press_max",
        "Squat": "squat_max",
        "Weighted Pull-Up": "weighted_pullup_max",
        "Weighted Chin-Up": "weighted_pullup_max",
    }

    setting_key = setting_key_map.get(exercise_name)

    if setting_key:
        return float(get_setting(setting_key, MAX_LIFTS.get(exercise_name, 0)))

    return float(MAX_LIFTS.get(exercise_name, 0))


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


def round_to_nearest_25(weight: float) -> float:
    if weight <= 0:
        return 0
    return round(weight / 2.5) * 2.5


def safe_main_lift_load(
    exercise_name: str,
    readiness_category: str,
    fallback: float,
) -> float:
    """
    Generates conservative, capped load suggestions.

    Important:
    Weighted pull-ups/chin-ups use added weight only.
    Bench suggestions can never exceed bench max.
    """
    training_max = get_training_max(exercise_name)
    progression_load = get_progression_load(exercise_name, fallback)

    if training_max <= 0:
        base_load = fallback
    else:
        base_load = min(progression_load, training_max)

    if readiness_category == "Green":
        percent_cap = 0.82
    elif readiness_category == "Yellow":
        percent_cap = 0.75
    elif readiness_category == "Orange":
        percent_cap = 0.62
    else:
        percent_cap = 0.40

    max_allowed_today = training_max * percent_cap if training_max > 0 else base_load
    suggested = min(base_load, max_allowed_today)

    if exercise_name in {"Weighted Pull-Up", "Weighted Chin-Up"}:
        suggested = min(suggested, training_max * percent_cap)
        return round_to_nearest_25(suggested)

    return round_to_nearest_5(suggested)


def generate_workout(checkin: dict[str, Any]) -> dict[str, Any]:
    readiness_category = checkin.get("readiness_category", "Yellow")
    time_available = int(checkin.get("time_available", 60))
    goal_today = checkin.get("goal_today", "normal")
    day_name = get_day_name()

    deload = is_deload_day()

    training_focus = checkin.get("training_focus_today", "Let app decide")
    fun_workout = bool(checkin.get("fun_workout", False))
    focus_workout = bool(checkin.get("focus_workout", False))
    chaos_workout = bool(checkin.get("chaos_workout", False))

    if training_focus == "Let app decide":
        template_key = get_setting("selected_template_key", "balanced")
    else:
        template_key = map_training_focus_to_template(training_focus)

    focus = determine_focus(
        day_name=day_name,
        readiness_category=readiness_category,
        goal_today=goal_today,
        soreness=int(checkin.get("soreness", 5)),
        combat_later_today=bool(checkin.get("combat_later_today", False)),
        deload=deload,
        template_key=template_key,
        training_focus=training_focus,
    )

    if focus_workout:
        workout_modifier = "focus"
    elif chaos_workout:
        workout_modifier = "chaos"
    elif fun_workout:
        workout_modifier = "fun"
    else:
        workout_modifier = "normal"

    if template_key == "recovery":
        exercises = red_day_workout(time_available, workout_modifier)
        workout_type = "Recovery / Mobility"
        reason = "Recovery focus selected. The app generated a low-fatigue mobility and recovery session."

    elif template_key == "accessory" and readiness_category in {"Yellow", "Orange", "Red"}:
        exercises = accessory_day_workout(time_available, workout_modifier)
        workout_type = "Accessory / Hypertrophy Support"
        reason = "Accessory focus selected. The app generated lower-fatigue isolation, grip, core, and mobility work."

    elif deload and readiness_category in {"Green", "Yellow"}:
        workout_type = "Deload / Light Full Body"
        reason = (
            "Scheduled conservative deload. The app reduced intensity and volume to protect recovery "
            "while keeping movement quality high."
        )
        exercises = orange_day_workout(
            focus,
            time_available,
            deload=True,
            template_key=template_key,
            workout_modifier=workout_modifier,
        )

    elif readiness_category == "Green":
        exercises = green_day_workout(focus, time_available, template_key, workout_modifier)
        workout_type = "Full-Body Strength"
        reason = "High readiness. The app generated a productive full-body strength session."

    elif readiness_category == "Yellow":
        exercises = yellow_day_workout(focus, time_available, template_key, workout_modifier)
        workout_type = "Full-Body Strength"
        reason = "Moderate readiness. The app generated a normal full-body session."

    elif readiness_category == "Orange":
        exercises = orange_day_workout(
            focus,
            time_available,
            template_key=template_key,
            workout_modifier=workout_modifier,
        )
        workout_type = "Light / Accessory"
        reason = "Reduced readiness. The app lowered intensity and shifted toward accessories."

    else:
        exercises = red_day_workout(time_available, workout_modifier)
        workout_type = "Recovery"
        reason = "Low readiness. The app generated a recovery-focused session."

    if focus_workout:
        reason += " Focus workout selected, so the app kept the session tighter and less scattered."
    elif fun_workout:
        reason += " Fun workout selected, so the app added more variety where appropriate."
    elif chaos_workout:
        reason += " Chaos workout selected, so the app used more unusual but still safe variations."

    return {
        "date": date.today().isoformat(),
        "workout_type": workout_type,
        "focus": focus,
        "readiness_category": readiness_category,
        "estimated_duration": time_available,
        "generation_reason": reason,
        "deload": deload,
        "template_key": template_key,
        "workout_modifier": workout_modifier,
        "exercises": exercises,
    }


def map_training_focus_to_template(training_focus: str) -> str:
    mapping = {
        "Full body": "balanced",
        "Lower emphasis": "lower_strength",
        "Upper emphasis": "upper_grip",
        "Posterior chain / grappling": "posterior_chain",
        "Accessory / pump": "accessory",
        "Recovery / mobility": "recovery",
    }

    return mapping.get(training_focus, "balanced")


def determine_focus(
    day_name: str,
    readiness_category: str,
    goal_today: str,
    soreness: int,
    combat_later_today: bool,
    deload: bool,
    template_key: str,
    training_focus: str,
) -> str:
    if training_focus != "Let app decide":
        return training_focus

    if template_key == "posterior_chain":
        return "Posterior chain / grappling"

    if template_key == "upper_grip":
        return "Upper emphasis"

    if template_key == "lower_strength":
        return "Lower emphasis"

    if template_key == "accessory":
        return "Accessory / pump"

    if template_key == "recovery":
        return "Recovery / mobility"

    if deload:
        return "Deload / Accessory Full Body"

    if readiness_category == "Red" or goal_today == "recovery":
        return "Recovery / mobility"

    if readiness_category == "Orange" or soreness >= 7:
        return "Accessory / pump"

    if combat_later_today:
        return "Upper emphasis"

    if day_name == "Monday":
        return "Lower emphasis"

    if day_name == "Wednesday":
        return "Upper emphasis"

    if day_name == "Saturday":
        return "Posterior chain / grappling"

    return "Full body"


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
    prescription_type: str = "strength",
    equipment: str = "",
    modality: str = "",
    fatigue_cost: str = "medium",
    combat_transfer: str = "medium",
    duration_minutes: int | None = None,
    hold_seconds: int | None = None,
    distance: str = "",
    heart_rate_target: str = "",
    intensity_target: str = "",
    side: str = "",
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
        "prescription_type": prescription_type,
        "equipment": equipment,
        "modality": modality,
        "fatigue_cost": fatigue_cost,
        "combat_transfer": combat_transfer,
        "duration_minutes": duration_minutes,
        "hold_seconds": hold_seconds,
        "distance": distance,
        "heart_rate_target": heart_rate_target,
        "intensity_target": intensity_target,
        "side": side,
    }


def vertical_pull_choice(seed: int, weighted: bool = False) -> dict[str, str]:
    weighted_options = [
        {
            "name": "Weighted Pull-Up",
            "movement_pattern": "vertical_pull",
            "category": "main_lift",
            "equipment": "pull-up bar",
            "modality": "weighted bodyweight",
        },
        {
            "name": "Weighted Chin-Up",
            "movement_pattern": "vertical_pull",
            "category": "main_lift",
            "equipment": "pull-up bar",
            "modality": "weighted bodyweight",
        },
    ]

    bodyweight_options = [
        {
            "name": "Pull-Up",
            "movement_pattern": "vertical_pull",
            "category": "accessory",
            "equipment": "pull-up bar",
            "modality": "bodyweight",
        },
        {
            "name": "Chin-Up",
            "movement_pattern": "vertical_pull",
            "category": "accessory",
            "equipment": "pull-up bar",
            "modality": "bodyweight",
        },
        {
            "name": "Neutral-Grip Pull-Up",
            "movement_pattern": "vertical_pull",
            "category": "accessory",
            "equipment": "pull-up bar",
            "modality": "bodyweight",
        },
    ]

    options = weighted_options if weighted else bodyweight_options
    return options[seed % len(options)]


def accessory_rotation(index_seed: int, workout_modifier: str = "normal") -> list[dict[str, Any]]:
    rotations = [
        [
            make_exercise(
                "Farmer Carry",
                "carry_grip",
                "gpp",
                3,
                30,
                60,
                0,
                7.5,
                "Grip, trunk, and posture.",
                prescription_type="carry",
                equipment="dumbbells or kettlebells",
                modality="loaded carry",
                fatigue_cost="medium",
                combat_transfer="high",
                distance="30-60 sec",
            ),
            make_exercise(
                "GHR Sit-Up",
                "core",
                "accessory",
                2,
                8,
                12,
                0,
                7.0,
                "Core strength.",
                prescription_type="bodyweight",
                equipment="GHR bench",
                modality="bodyweight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                "Neck Isometrics",
                "neck",
                "recovery_accessory",
                2,
                10,
                20,
                0,
                5.0,
                "Controlled neck work. Do not strain.",
                prescription_type="mobility",
                equipment="bodyweight or hands",
                modality="isometric",
                fatigue_cost="low",
                combat_transfer="high",
                intensity_target="easy controlled pressure",
            ),
        ],
        [
            make_exercise(
                "Suitcase Carry",
                "carry_grip",
                "gpp",
                3,
                30,
                60,
                0,
                7.0,
                "Anti-lateral flexion and grip.",
                prescription_type="carry",
                equipment="dumbbell or kettlebell",
                modality="loaded carry",
                fatigue_cost="medium",
                combat_transfer="high",
                distance="30-60 sec each side",
                side="each side",
            ),
            make_exercise(
                "Hanging Knee Raise",
                "core",
                "accessory",
                2,
                8,
                12,
                0,
                7.0,
                "Abs and hip flexor control.",
                prescription_type="bodyweight",
                equipment="pull-up bar",
                modality="bodyweight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                "Reverse Wrist Curl",
                "forearm_grip",
                "accessory",
                2,
                12,
                20,
                0,
                7.0,
                "Forearm balance.",
                prescription_type="strength",
                equipment="dumbbell or barbell",
                modality="isolation",
                fatigue_cost="low",
                combat_transfer="medium",
            ),
        ],
        [
            make_exercise(
                "Back Extension",
                "posterior_chain",
                "accessory",
                3,
                10,
                15,
                0,
                7.0,
                "Posterior-chain volume.",
                prescription_type="bodyweight",
                equipment="back extension bench",
                modality="bodyweight or loaded",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Plank",
                "core",
                "accessory",
                2,
                30,
                60,
                0,
                7.0,
                "Trunk stiffness. Time is in seconds.",
                prescription_type="mobility",
                equipment="floor",
                modality="isometric",
                fatigue_cost="low",
                combat_transfer="medium",
                hold_seconds=45,
                intensity_target="strong brace",
            ),
            make_exercise(
                "Hammer Curl",
                "forearm_grip",
                "accessory",
                2,
                10,
                15,
                0,
                7.5,
                "Arm and grip support.",
                prescription_type="strength",
                equipment="dumbbells",
                modality="isolation",
                fatigue_cost="low",
                combat_transfer="medium",
            ),
        ],
        [
            make_exercise(
                "Hip Airplane",
                "mobility",
                "recovery",
                2,
                5,
                8,
                0,
                4.0,
                "Hip control and balance.",
                prescription_type="mobility",
                equipment="bodyweight",
                modality="mobility",
                fatigue_cost="low",
                combat_transfer="medium",
                intensity_target="controlled range",
                side="each side",
            ),
            make_exercise(
                "Dead Bug",
                "core",
                "recovery_accessory",
                2,
                8,
                12,
                0,
                5.0,
                "Breathing and bracing.",
                prescription_type="mobility",
                equipment="floor",
                modality="bodyweight",
                fatigue_cost="low",
                combat_transfer="medium",
                intensity_target="controlled breathing",
            ),
            make_exercise(
                "Wrist Curl",
                "forearm_grip",
                "accessory",
                2,
                12,
                20,
                0,
                7.0,
                "Forearm support.",
                prescription_type="strength",
                equipment="dumbbell or barbell",
                modality="isolation",
                fatigue_cost="low",
                combat_transfer="medium",
            ),
        ],
    ]

    selected = rotations[index_seed % len(rotations)]

    if workout_modifier == "focus":
        return selected[:2]

    if workout_modifier == "fun":
        return selected + [
            make_exercise(
                "Bike",
                "conditioning",
                "cardio",
                1,
                8,
                12,
                0,
                5.0,
                "Easy finisher. Keep it playful, not brutal.",
                prescription_type="cardio",
                equipment="bike",
                modality="cyclical cardio",
                fatigue_cost="low",
                combat_transfer="medium",
                duration_minutes=10,
                heart_rate_target="Zone 2 or nasal breathing",
                intensity_target="easy-moderate",
            )
        ]

    if workout_modifier == "chaos":
        return selected + [
            make_exercise(
                "Mobility Flow",
                "mobility",
                "mobility",
                1,
                5,
                10,
                0,
                4.0,
                "Odd-object style cooldown: move creatively but safely.",
                prescription_type="mobility",
                equipment="bodyweight",
                modality="flow",
                fatigue_cost="low",
                combat_transfer="medium",
                duration_minutes=8,
                intensity_target="smooth and controlled",
            )
        ]

    return selected


def green_day_workout(
    focus: str,
    time_available: int,
    template_key: str,
    workout_modifier: str,
) -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()

    trap_load = safe_main_lift_load("Trap Bar Deadlift", "Green", DEFAULT_TRAINING_LOADS["Trap Bar Deadlift"])
    bench_load = safe_main_lift_load("Bench Press", "Green", DEFAULT_TRAINING_LOADS["Bench Press"])
    squat_load = safe_main_lift_load("Squat", "Green", DEFAULT_TRAINING_LOADS["Squat"])

    pull_choice = vertical_pull_choice(completed_count, weighted=True)
    pull_name = pull_choice["name"]
    pull_load = safe_main_lift_load(pull_name, "Green", DEFAULT_TRAINING_LOADS.get(pull_name, 20))

    if focus in {"Posterior chain / grappling", "posterior_chain"}:
        exercises = [
            make_exercise(
                "Trap Bar Deadlift",
                "hinge",
                "main_lift",
                4,
                3,
                5,
                trap_load,
                8.0,
                "Main posterior-chain strength. Smooth reps only.",
                prescription_type="strength",
                equipment="trap bar",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                pull_name,
                "vertical_pull",
                "main_lift",
                4,
                3,
                6,
                pull_load,
                8.0,
                "Added weight only. Grappling pull strength.",
                prescription_type="strength",
                equipment="pull-up bar",
                modality="weighted bodyweight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Romanian Deadlift",
                "hinge",
                "secondary_lift",
                3,
                6,
                10,
                0,
                7.5,
                "Hamstrings and trunk.",
                prescription_type="strength",
                equipment="barbell or dumbbells",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Chest-Supported Row",
                "horizontal_pull",
                "secondary_lift",
                3,
                8,
                12,
                0,
                8.0,
                "Upper-back strength.",
                prescription_type="strength",
                equipment="machine or bench + dumbbells",
                modality="supported pull",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
        ]

    elif focus in {"Upper emphasis", "upper_grip"}:
        exercises = [
            make_exercise(
                "Bench Press",
                "horizontal_push",
                "main_lift",
                4,
                4,
                6,
                bench_load,
                8.0,
                "Main press. No grinders.",
                prescription_type="strength",
                equipment="barbell",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="medium",
            ),
            make_exercise(
                pull_name,
                "vertical_pull",
                "main_lift",
                4,
                3,
                6,
                pull_load,
                8.0,
                "Added weight only. Prioritize clean reps.",
                prescription_type="strength",
                equipment="pull-up bar",
                modality="weighted bodyweight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Chest-Supported Row",
                "horizontal_pull",
                "secondary_lift",
                3,
                8,
                12,
                0,
                8.0,
                "Upper back volume.",
                prescription_type="strength",
                equipment="machine or bench + dumbbells",
                modality="supported pull",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Landmine Press",
                "vertical_push",
                "secondary_lift",
                3,
                6,
                10,
                0,
                7.5,
                "Athletic pressing.",
                prescription_type="strength",
                equipment="landmine",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
        ]

    elif focus in {"Lower emphasis", "lower_strength"}:
        exercises = [
            make_exercise(
                "Squat",
                "squat",
                "main_lift",
                4,
                4,
                6,
                squat_load,
                8.0,
                "Main squat pattern.",
                prescription_type="strength",
                equipment="barbell",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Trap Bar Deadlift",
                "hinge",
                "main_lift",
                3,
                3,
                5,
                trap_load,
                8.0,
                "Main hinge pattern.",
                prescription_type="strength",
                equipment="trap bar",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Bench Press",
                "horizontal_push",
                "main_lift",
                3,
                4,
                6,
                bench_load,
                7.5,
                "Keep pressing maintained.",
                prescription_type="strength",
                equipment="barbell",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                "Step-Up",
                "single_leg",
                "accessory",
                3,
                8,
                12,
                0,
                7.5,
                "Single-leg strength.",
                prescription_type="strength",
                equipment="box + dumbbells optional",
                modality="single-leg",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
        ]

    else:
        exercises = [
            make_exercise(
                "Trap Bar Deadlift",
                "hinge",
                "main_lift",
                3,
                3,
                5,
                trap_load,
                8.0,
                "Main hinge strength.",
                prescription_type="strength",
                equipment="trap bar",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Bench Press",
                "horizontal_push",
                "main_lift",
                3,
                4,
                6,
                bench_load,
                8.0,
                "Main press.",
                prescription_type="strength",
                equipment="barbell",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                pull_name,
                "vertical_pull",
                "main_lift",
                3,
                3,
                6,
                pull_load,
                8.0,
                "Added weight only. Main pull.",
                prescription_type="strength",
                equipment="pull-up bar",
                modality="weighted bodyweight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Split Squat",
                "single_leg",
                "accessory",
                3,
                8,
                12,
                0,
                7.5,
                "Single-leg strength.",
                prescription_type="strength",
                equipment="dumbbells optional",
                modality="single-leg",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
        ]

    exercises.extend(accessory_rotation(completed_count, workout_modifier))
    return trim_for_time(exercises, time_available)


def yellow_day_workout(
    focus: str,
    time_available: int,
    template_key: str,
    workout_modifier: str,
) -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()

    trap_load = safe_main_lift_load("Trap Bar Deadlift", "Yellow", DEFAULT_TRAINING_LOADS["Trap Bar Deadlift"])
    bench_load = safe_main_lift_load("Bench Press", "Yellow", DEFAULT_TRAINING_LOADS["Bench Press"])
    squat_load = safe_main_lift_load("Squat", "Yellow", DEFAULT_TRAINING_LOADS["Squat"])

    weighted_pull_choice = vertical_pull_choice(completed_count + 1, weighted=True)
    weighted_pull_name = weighted_pull_choice["name"]
    weighted_pull_load = safe_main_lift_load(
        weighted_pull_name,
        "Yellow",
        DEFAULT_TRAINING_LOADS.get(weighted_pull_name, 20),
    )

    body_pull_choice = vertical_pull_choice(completed_count + 1, weighted=False)
    body_pull_name = body_pull_choice["name"]

    if focus in {"Posterior chain / grappling", "posterior_chain"}:
        exercises = [
            make_exercise(
                "Trap Bar Deadlift",
                "hinge",
                "main_lift",
                3,
                3,
                5,
                trap_load,
                7.5,
                "Main hinge work.",
                prescription_type="strength",
                equipment="trap bar",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                body_pull_name,
                "vertical_pull",
                "accessory",
                3,
                5,
                10,
                0,
                8.0,
                "Bodyweight pulling volume.",
                prescription_type="bodyweight",
                equipment="pull-up bar",
                modality="bodyweight",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Back Extension",
                "posterior_chain",
                "accessory",
                3,
                10,
                15,
                0,
                7.0,
                "Posterior-chain support.",
                prescription_type="bodyweight",
                equipment="back extension bench",
                modality="bodyweight or loaded",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Chest-Supported Row",
                "horizontal_pull",
                "secondary_lift",
                3,
                8,
                12,
                0,
                8.0,
                "Upper back support.",
                prescription_type="strength",
                equipment="machine or bench + dumbbells",
                modality="supported pull",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
        ]

    elif focus in {"Upper emphasis", "upper_grip"}:
        exercises = [
            make_exercise(
                "Bench Press",
                "horizontal_push",
                "main_lift",
                3,
                4,
                6,
                bench_load,
                7.5,
                "Main press.",
                prescription_type="strength",
                equipment="barbell",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                weighted_pull_name,
                "vertical_pull",
                "main_lift",
                3,
                3,
                6,
                weighted_pull_load,
                7.5,
                "Added weight only. Main pull.",
                prescription_type="strength",
                equipment="pull-up bar",
                modality="weighted bodyweight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "DB Row",
                "horizontal_pull",
                "accessory",
                3,
                8,
                12,
                0,
                8.0,
                "Rowing volume.",
                prescription_type="strength",
                equipment="dumbbell",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Hammer Curl",
                "forearm_grip",
                "accessory",
                3,
                10,
                15,
                0,
                7.5,
                "Grip and arm support.",
                prescription_type="strength",
                equipment="dumbbells",
                modality="isolation",
                fatigue_cost="low",
                combat_transfer="medium",
            ),
        ]

    elif focus in {"Lower emphasis", "lower_strength"}:
        exercises = [
            make_exercise(
                "Squat",
                "squat",
                "main_lift",
                3,
                4,
                6,
                squat_load,
                7.5,
                "Main squat work.",
                prescription_type="strength",
                equipment="barbell",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Trap Bar Deadlift",
                "hinge",
                "main_lift",
                3,
                3,
                5,
                trap_load,
                7.5,
                "Main hinge work.",
                prescription_type="strength",
                equipment="trap bar",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Step-Up",
                "single_leg",
                "accessory",
                2,
                8,
                12,
                0,
                7.0,
                "Single-leg support.",
                prescription_type="strength",
                equipment="box + dumbbells optional",
                modality="single-leg",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                "Dead Bug",
                "core",
                "recovery_accessory",
                2,
                8,
                12,
                0,
                5.0,
                "Core control.",
                prescription_type="mobility",
                equipment="floor",
                modality="bodyweight",
                fatigue_cost="low",
                combat_transfer="medium",
                intensity_target="controlled breathing",
            ),
        ]

    else:
        exercises = [
            make_exercise(
                "Trap Bar Deadlift",
                "hinge",
                "main_lift",
                3,
                3,
                5,
                trap_load,
                7.5,
                "Productive but conservative.",
                prescription_type="strength",
                equipment="trap bar",
                modality="free weight",
                fatigue_cost="high",
                combat_transfer="high",
            ),
            make_exercise(
                "Bench Press",
                "horizontal_push",
                "main_lift",
                3,
                4,
                6,
                bench_load,
                7.5,
                "Smooth reps.",
                prescription_type="strength",
                equipment="barbell",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                body_pull_name,
                "vertical_pull",
                "accessory",
                3,
                5,
                10,
                0,
                8.0,
                "Bodyweight pulling volume.",
                prescription_type="bodyweight",
                equipment="pull-up bar",
                modality="bodyweight",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Step-Up",
                "single_leg",
                "accessory",
                2,
                8,
                12,
                0,
                7.0,
                "Moderate single-leg work.",
                prescription_type="strength",
                equipment="box + dumbbells optional",
                modality="single-leg",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
        ]

    exercises.extend(accessory_rotation(completed_count + 1, workout_modifier))
    return trim_for_time(exercises, time_available)


def orange_day_workout(
    focus: str,
    time_available: int,
    deload: bool = False,
    template_key: str = "balanced",
    workout_modifier: str = "normal",
) -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()

    trap_load = safe_main_lift_load("Trap Bar Deadlift", "Orange", DEFAULT_TRAINING_LOADS["Trap Bar Deadlift"])
    bench_load = safe_main_lift_load("Bench Press", "Orange", DEFAULT_TRAINING_LOADS["Bench Press"])

    rpe_cap = 6.0 if deload else 6.5
    body_pull_choice = vertical_pull_choice(completed_count + 2, weighted=False)
    body_pull_name = body_pull_choice["name"]

    if focus in {"Upper emphasis", "upper_grip"}:
        exercises = [
            make_exercise(
                "Bench Press",
                "horizontal_push",
                "main_lift",
                2,
                4,
                6,
                bench_load,
                rpe_cap,
                "Easy technique pressing.",
                prescription_type="strength",
                equipment="barbell",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                body_pull_name,
                "vertical_pull",
                "accessory",
                3,
                5,
                8,
                0,
                7.0,
                "Easy pulling. No grinders.",
                prescription_type="bodyweight",
                equipment="pull-up bar",
                modality="bodyweight",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Chest-Supported Row",
                "horizontal_pull",
                "secondary_lift",
                3,
                8,
                12,
                0,
                7.0,
                "Upper-back volume.",
                prescription_type="strength",
                equipment="machine or bench + dumbbells",
                modality="supported pull",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Landmine Press",
                "vertical_push",
                "secondary_lift",
                2,
                6,
                10,
                0,
                7.0,
                "Moderate pressing.",
                prescription_type="strength",
                equipment="landmine",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
        ]
    else:
        exercises = [
            make_exercise(
                "Trap Bar Deadlift",
                "hinge",
                "main_lift",
                2,
                3,
                5,
                trap_load,
                rpe_cap,
                "Technique work. Keep it easy.",
                prescription_type="strength",
                equipment="trap bar",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Landmine Press",
                "vertical_push",
                "secondary_lift",
                3,
                6,
                10,
                0,
                7.0,
                "Moderate pressing without grinding.",
                prescription_type="strength",
                equipment="landmine",
                modality="free weight",
                fatigue_cost="medium",
                combat_transfer="medium",
            ),
            make_exercise(
                "Chest-Supported Row",
                "horizontal_pull",
                "secondary_lift",
                3,
                8,
                12,
                0,
                7.5,
                "Upper-back work.",
                prescription_type="strength",
                equipment="machine or bench + dumbbells",
                modality="supported pull",
                fatigue_cost="medium",
                combat_transfer="high",
            ),
            make_exercise(
                "Goblet Squat",
                "squat",
                "accessory",
                2,
                8,
                12,
                0,
                6.5,
                "Light lower-body work.",
                prescription_type="strength",
                equipment="dumbbell or kettlebell",
                modality="free weight",
                fatigue_cost="low",
                combat_transfer="medium",
            ),
        ]

    exercises.extend(accessory_rotation(completed_count + 2, workout_modifier))
    return trim_for_time(exercises, time_available)


def accessory_day_workout(time_available: int, workout_modifier: str = "normal") -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()
    body_pull_choice = vertical_pull_choice(completed_count + 3, weighted=False)
    body_pull_name = body_pull_choice["name"]

    exercises = [
        make_exercise(
            "Landmine Press",
            "vertical_push",
            "secondary_lift",
            3,
            8,
            12,
            0,
            7.0,
            "Athletic pressing without heavy fatigue.",
            prescription_type="strength",
            equipment="landmine",
            modality="free weight",
            fatigue_cost="medium",
            combat_transfer="medium",
        ),
        make_exercise(
            body_pull_name,
            "vertical_pull",
            "accessory",
            3,
            5,
            10,
            0,
            7.5,
            "Vertical pull variation.",
            prescription_type="bodyweight",
            equipment="pull-up bar",
            modality="bodyweight",
            fatigue_cost="medium",
            combat_transfer="high",
        ),
        make_exercise(
            "Chest-Supported Row",
            "horizontal_pull",
            "secondary_lift",
            3,
            8,
            12,
            0,
            7.5,
            "Upper-back volume.",
            prescription_type="strength",
            equipment="machine or bench + dumbbells",
            modality="supported pull",
            fatigue_cost="medium",
            combat_transfer="high",
        ),
        make_exercise(
            "Goblet Squat",
            "squat",
            "accessory",
            3,
            8,
            12,
            0,
            6.5,
            "Light lower-body work.",
            prescription_type="strength",
            equipment="dumbbell or kettlebell",
            modality="free weight",
            fatigue_cost="low",
            combat_transfer="medium",
        ),
        make_exercise(
            "Back Extension",
            "posterior_chain",
            "accessory",
            3,
            10,
            15,
            0,
            7.0,
            "Posterior-chain support.",
            prescription_type="bodyweight",
            equipment="back extension bench",
            modality="bodyweight or loaded",
            fatigue_cost="medium",
            combat_transfer="high",
        ),
        make_exercise(
            "Lateral Raise",
            "shoulder_accessory",
            "accessory",
            2,
            12,
            20,
            0,
            7.0,
            "Shoulder accessory.",
            prescription_type="strength",
            equipment="dumbbells or cable",
            modality="isolation",
            fatigue_cost="low",
            combat_transfer="low",
        ),
    ]

    exercises.extend(accessory_rotation(completed_count + 3, workout_modifier))
    return trim_for_time(exercises, time_available)


def red_day_workout(time_available: int, workout_modifier: str = "normal") -> list[dict[str, Any]]:
    exercises = [
        make_exercise(
            "Incline Walk",
            "conditioning",
            "cardio",
            1,
            10,
            20,
            0,
            4.0,
            "Easy pace. Nasal breathing if possible.",
            prescription_type="cardio",
            equipment="treadmill",
            modality="cyclical cardio",
            fatigue_cost="low",
            combat_transfer="medium",
            duration_minutes=15,
            heart_rate_target="Zone 2 or nasal breathing",
            intensity_target="easy",
        ),
        make_exercise(
            "Mobility Flow",
            "mobility",
            "mobility",
            1,
            5,
            10,
            0,
            3.0,
            "Move smoothly. Do not force range.",
            prescription_type="mobility",
            equipment="bodyweight",
            modality="flow",
            fatigue_cost="low",
            combat_transfer="medium",
            duration_minutes=8,
            intensity_target="smooth and controlled",
        ),
        make_exercise(
            "Hip Airplane",
            "mobility",
            "mobility",
            2,
            5,
            8,
            0,
            4.0,
            "Balance and hip control.",
            prescription_type="mobility",
            equipment="bodyweight",
            modality="mobility",
            fatigue_cost="low",
            combat_transfer="medium",
            intensity_target="controlled range",
            side="each side",
        ),
        make_exercise(
            "Back Extension",
            "posterior_chain",
            "accessory",
            2,
            10,
            15,
            0,
            5.0,
            "Very easy blood-flow work.",
            prescription_type="bodyweight",
            equipment="back extension bench",
            modality="bodyweight",
            fatigue_cost="low",
            combat_transfer="high",
        ),
        make_exercise(
            "Dead Bug",
            "core",
            "recovery_accessory",
            2,
            8,
            12,
            0,
            4.0,
            "Controlled breathing and bracing.",
            prescription_type="mobility",
            equipment="floor",
            modality="bodyweight",
            fatigue_cost="low",
            combat_transfer="medium",
            intensity_target="controlled breathing",
        ),
        make_exercise(
            "Couch Stretch",
            "stretch",
            "stretch",
            2,
            45,
            60,
            0,
            3.0,
            "Open hips and quads. Keep breathing relaxed.",
            prescription_type="stretch",
            equipment="bench or wall",
            modality="static stretch",
            fatigue_cost="low",
            combat_transfer="medium",
            hold_seconds=60,
            side="each side",
            intensity_target="easy-moderate",
        ),
        make_exercise(
            "Neck Isometrics",
            "neck",
            "recovery_accessory",
            2,
            10,
            20,
            0,
            4.0,
            "Light neck work.",
            prescription_type="mobility",
            equipment="bodyweight or hands",
            modality="isometric",
            fatigue_cost="low",
            combat_transfer="high",
            intensity_target="easy controlled pressure",
        ),
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
