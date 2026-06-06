from datetime import date
from typing import Any

import pandas as pd

from src.database import (
    get_progression_state,
    get_completed_workout_count,
    get_setting,
)


# ------------------------------------------------------------
# Basic helpers
# ------------------------------------------------------------

def get_day_name() -> str:
    return date.today().strftime("%A")


def is_deload_day() -> bool:
    completed_count = get_completed_workout_count()

    if completed_count == 0:
        return False

    return completed_count % 4 == 0


def safe_float(value: Any, default: float = 0) -> float:
    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default

        if pd.isna(value):
            return default

        return int(value)
    except (TypeError, ValueError):
        return default


def round_to_nearest_5(weight: float) -> float:
    if weight <= 0:
        return 0

    return round(weight / 5) * 5


def round_to_nearest_25(weight: float) -> float:
    if weight <= 0:
        return 0

    return round(weight / 2.5) * 2.5


def normalize_key_text(value: str) -> str:
    return (
        value.lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )


# ------------------------------------------------------------
# Exercise classification
# ------------------------------------------------------------

def is_weighted_bodyweight_exercise(exercise_name: str) -> bool:
    exercise_lower = exercise_name.lower()

    weighted_bodyweight_terms = [
        "weighted pull",
        "weighted chin",
        "weighted dip",
    ]

    return any(term in exercise_lower for term in weighted_bodyweight_terms)


def is_bodyweight_exercise(exercise_name: str) -> bool:
    exercise_lower = exercise_name.lower()

    bodyweight_terms = [
        "pull-up",
        "pull up",
        "chin-up",
        "chin up",
        "push-up",
        "push up",
        "dip",
        "plank",
        "dead bug",
        "hip airplane",
        "mobility flow",
        "incline walk",
        "neck isometric",
    ]

    return any(term in exercise_lower for term in bodyweight_terms)


def is_small_increment_exercise(exercise_name: str) -> bool:
    exercise_lower = exercise_name.lower()

    small_increment_terms = [
        "weighted pull",
        "weighted chin",
        "weighted dip",
        "lateral raise",
        "curl",
        "pressdown",
        "wrist",
    ]

    return any(term in exercise_lower for term in small_increment_terms)


# ------------------------------------------------------------
# Max / progression safety helpers
# ------------------------------------------------------------

def get_progression_row(exercise_name: str) -> pd.Series | None:
    progression = get_progression_state()

    if progression.empty:
        return None

    if "exercise_name" not in progression.columns:
        return None

    exact_match = progression[progression["exercise_name"] == exercise_name]

    if not exact_match.empty:
        return exact_match.iloc[0]

    normalized_target = normalize_key_text(exercise_name)

    for _, row in progression.iterrows():
        row_name = str(row.get("exercise_name", ""))
        if normalize_key_text(row_name) == normalized_target:
            return row

    return None


def get_progression_load(exercise_name: str, default_load: float = 0) -> float:
    row = get_progression_row(exercise_name)

    if row is None:
        return default_load

    value = row.get("next_recommended_load", default_load)

    if pd.isna(value):
        return default_load

    return safe_float(value, default_load)


def get_known_max_from_progression(exercise_name: str) -> float | None:
    row = get_progression_row(exercise_name)

    if row is None:
        return None

    possible_max_columns = [
        "max_load",
        "max_weight",
        "one_rep_max",
        "estimated_1rm",
        "estimated_max",
        "training_max",
        "current_max",
        "max",
    ]

    for column in possible_max_columns:
        if column in row.index:
            value = safe_float(row.get(column), 0)
            if value > 0:
                return value

    return None


def get_known_max_from_settings(exercise_name: str) -> float | None:
    normalized = normalize_key_text(exercise_name)

    possible_setting_keys = [
        f"{normalized}_max",
        f"{normalized}_1rm",
        f"{normalized}_one_rep_max",
        f"{normalized}_estimated_1rm",
        f"{normalized}_training_max",
        f"max_{normalized}",
        f"one_rep_max_{normalized}",
        f"estimated_1rm_{normalized}",
        f"training_max_{normalized}",
        f"{exercise_name}_max",
        f"{exercise_name}_1rm",
        f"max_{exercise_name}",
    ]

    for key in possible_setting_keys:
        value = get_setting(key, None)
        numeric_value = safe_float(value, 0)

        if numeric_value > 0:
            return numeric_value

    return None


def get_known_max_load(exercise_name: str) -> float | None:
    max_from_progression = get_known_max_from_progression(exercise_name)

    if max_from_progression and max_from_progression > 0:
        return max_from_progression

    max_from_settings = get_known_max_from_settings(exercise_name)

    if max_from_settings and max_from_settings > 0:
        return max_from_settings

    return None


def get_default_safety_max(exercise_name: str) -> float | None:
    """
    Conservative fallback caps.

    These are only used if the app cannot find a user-entered max in settings
    or progression state. They prevent obviously absurd defaults while still
    allowing the user's stored progression data to drive normal behavior.
    """

    defaults = {
        "bench press": 245,
        "squat": 425,
        "trap bar deadlift": 475,
        "weighted pull-up": 45,
        "weighted chin-up": 45,
    }

    exercise_lower = exercise_name.lower().strip()

    return defaults.get(exercise_lower)


def clamp_suggested_load(
    exercise_name: str,
    suggested_load: float,
    readiness_category: str,
) -> float:
    """
    Prevents unsafe or impossible suggested loads.

    Standard weighted lifts:
    - Do not suggest above known max.

    Weighted bodyweight lifts:
    - Treat the number as added weight only.
    - Do not add bodyweight.
    - Do not suggest above added-weight max.
    """

    suggested_load = safe_float(suggested_load, 0)

    if suggested_load <= 0:
        return 0

    known_max = get_known_max_load(exercise_name)

    if known_max is None:
        known_max = get_default_safety_max(exercise_name)

    if known_max is not None and known_max > 0:
        suggested_load = min(suggested_load, known_max)

    if is_weighted_bodyweight_exercise(exercise_name):
        suggested_load = max(0, suggested_load)

    if is_small_increment_exercise(exercise_name):
        suggested_load = round_to_nearest_25(suggested_load)
    else:
        suggested_load = round_to_nearest_5(suggested_load)

    return suggested_load


def adjust_load(base_load: float, readiness_category: str, exercise_name: str = "") -> float:
    base_load = safe_float(base_load, 0)

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

    adjusted = base_load * multiplier

    adjusted = clamp_suggested_load(
        exercise_name=exercise_name,
        suggested_load=adjusted,
        readiness_category=readiness_category,
    )

    return adjusted


# ------------------------------------------------------------
# Workout mode / bias helpers
# ------------------------------------------------------------

def normalize_template_key(value: str | None) -> str:
    if not value:
        return "balanced"

    value = normalize_key_text(value)

    bias_map = {
        "mixed": "balanced",
        "strength": "strength",
        "hypertrophy": "accessory",
        "grappling_transfer": "upper_grip",
        "striking_transfer": "posterior_chain",
        "conditioning": "conditioning",
        "mobility_recovery": "recovery",
        "mobility__recovery": "recovery",
        "recovery": "recovery",
        "balanced": "balanced",
        "posterior_chain": "posterior_chain",
        "upper_grip": "upper_grip",
        "lower_strength": "lower_strength",
        "accessory": "accessory",
    }

    return bias_map.get(value, value)


def get_template_key_from_checkin(checkin: dict[str, Any]) -> str:
    if checkin.get("template_key"):
        return normalize_template_key(str(checkin.get("template_key")))

    if checkin.get("training_bias"):
        return normalize_template_key(str(checkin.get("training_bias")))

    stored_template = get_setting("selected_template_key", "balanced")

    return normalize_template_key(str(stored_template))


def get_workout_mode(checkin: dict[str, Any]) -> str:
    workout_mode = str(checkin.get("workout_mode", "Focused")).strip().title()

    if workout_mode not in {"Focused", "Fun", "Chaos"}:
        return "Focused"

    return workout_mode


def apply_workout_mode_to_reason(reason: str, workout_mode: str, readiness_category: str) -> str:
    if workout_mode == "Focused":
        return reason + " Focused mode selected: exercise choices prioritize progression and consistency."

    if workout_mode == "Fun":
        return reason + " Fun mode selected: the app added slightly more variety while keeping the session productive."

    if workout_mode == "Chaos":
        if readiness_category in {"Orange", "Red"}:
            return (
                reason
                + " Chaos mode was selected, but readiness is reduced, so novelty is limited and intensity remains conservative."
            )

        return (
            reason
            + " Chaos mode selected: the app adds more novelty while keeping loading constrained by readiness."
        )

    return reason


# ------------------------------------------------------------
# Exercise creation helpers
# ------------------------------------------------------------

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
    safe_weight = safe_float(weight, 0)

    safe_weight = clamp_suggested_load(
        exercise_name=exercise_name,
        suggested_load=safe_weight,
        readiness_category="Green",
    )

    return {
        "exercise_name": exercise_name,
        "movement_pattern": movement_pattern,
        "exercise_category": exercise_category,
        "planned_sets": safe_int(sets, 0),
        "planned_reps_min": safe_int(reps_min, 0),
        "planned_reps_max": safe_int(reps_max, 0),
        "planned_weight": safe_weight,
        "target_rpe": safe_float(target_rpe, 7),
        "notes": notes,
    }


def make_loaded_exercise(
    exercise_name: str,
    movement_pattern: str,
    exercise_category: str,
    sets: int,
    reps_min: int,
    reps_max: int,
    weight: float,
    target_rpe: float,
    notes: str,
    readiness_category: str,
) -> dict[str, Any]:
    safe_weight = clamp_suggested_load(
        exercise_name=exercise_name,
        suggested_load=weight,
        readiness_category=readiness_category,
    )

    return {
        "exercise_name": exercise_name,
        "movement_pattern": movement_pattern,
        "exercise_category": exercise_category,
        "planned_sets": safe_int(sets, 0),
        "planned_reps_min": safe_int(reps_min, 0),
        "planned_reps_max": safe_int(reps_max, 0),
        "planned_weight": safe_weight,
        "target_rpe": safe_float(target_rpe, 7),
        "notes": notes,
    }


# ------------------------------------------------------------
# Exercise rotation helpers
# ------------------------------------------------------------

def choose_vertical_pull(
    index_seed: int,
    readiness_category: str,
    prefer_weighted: bool = False,
    workout_mode: str = "Focused",
) -> dict[str, Any]:
    weighted_pullup_load = adjust_load(
        get_progression_load("Weighted Pull-Up", 25),
        readiness_category,
        "Weighted Pull-Up",
    )

    weighted_chinup_load = adjust_load(
        get_progression_load("Weighted Chin-Up", 20),
        readiness_category,
        "Weighted Chin-Up",
    )

    if readiness_category in {"Orange", "Red"}:
        options = [
            make_exercise("Pull-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 7.0, "Bodyweight pulling. Leave reps in reserve."),
            make_exercise("Chin-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 7.0, "Bodyweight pulling with more biceps emphasis."),
            make_exercise("Lat Pulldown", "vertical_pull", "accessory", 3, 8, 12, 0, 7.0, "Controlled vertical pull with lower joint cost."),
        ]

        return options[index_seed % len(options)]

    if prefer_weighted:
        options = [
            make_loaded_exercise("Weighted Pull-Up", "vertical_pull", "main_lift", 4, 3, 6, weighted_pullup_load, 8.0, "Added weight only. Clean reps.", readiness_category),
            make_loaded_exercise("Weighted Chin-Up", "vertical_pull", "main_lift", 4, 3, 6, weighted_chinup_load, 8.0, "Added weight only. Strong supinated pulling.", readiness_category),
            make_exercise("Pull-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 8.0, "Bodyweight pulling volume."),
            make_exercise("Chin-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 8.0, "Bodyweight chin-up volume."),
        ]
    else:
        options = [
            make_exercise("Pull-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 8.0, "Bodyweight pulling volume."),
            make_exercise("Chin-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 8.0, "Bodyweight pulling with biceps emphasis."),
            make_loaded_exercise("Weighted Pull-Up", "vertical_pull", "main_lift", 3, 3, 6, weighted_pullup_load, 7.5, "Added weight only. Stop before form breaks.", readiness_category),
            make_loaded_exercise("Weighted Chin-Up", "vertical_pull", "main_lift", 3, 3, 6, weighted_chinup_load, 7.5, "Added weight only. Clean reps.", readiness_category),
        ]

    if workout_mode == "Chaos" and readiness_category in {"Green", "Yellow"}:
        options.append(
            make_exercise("Neutral-Grip Pull-Up", "vertical_pull", "accessory", 3, 5, 10, 0, 8.0, "Neutral grip variation for variety.")
        )

    return options[index_seed % len(options)]


def choose_horizontal_pull(index_seed: int, workout_mode: str = "Focused") -> dict[str, Any]:
    options = [
        make_exercise("Chest-Supported Row", "horizontal_pull", "secondary_lift", 3, 8, 12, 0, 8.0, "Upper-back strength with low low-back fatigue."),
        make_exercise("DB Row", "horizontal_pull", "accessory", 3, 8, 12, 0, 8.0, "One-arm row for grappling strength."),
        make_exercise("Cable Row", "horizontal_pull", "accessory", 3, 8, 12, 0, 7.5, "Controlled upper-back volume."),
    ]

    if workout_mode == "Chaos":
        options.append(
            make_exercise("Seal Row", "horizontal_pull", "secondary_lift", 3, 8, 12, 0, 8.0, "Strict row variation for variety.")
        )

    return options[index_seed % len(options)]


def accessory_rotation(index_seed: int, workout_mode: str = "Focused") -> list[dict[str, Any]]:
    rotations = [
        [
            make_exercise("Farmer Carry", "carry_grip", "gpp", 3, 30, 60, 0, 7.5, "Grip, trunk, and posture."),
            make_exercise("GHR Sit-Up", "core", "accessory", 2, 8, 12, 0, 7.0, "Core strength."),
            make_exercise("Neck Isometrics", "neck", "recovery_accessory", 2, 10, 20, 0, 5.0, "Controlled neck work."),
        ],
        [
            make_exercise("Suitcase Carry", "carry_grip", "gpp", 3, 30, 60, 0, 7.0, "Anti-lateral flexion and grip."),
            make_exercise("Hanging Knee Raise", "core", "accessory", 2, 8, 12, 0, 7.0, "Abs and hip flexor control."),
            make_exercise("Reverse Wrist Curl", "forearm_grip", "accessory", 2, 12, 20, 0, 7.0, "Forearm balance."),
        ],
        [
            make_exercise("Back Extension", "posterior_chain", "accessory", 3, 10, 15, 0, 7.0, "Posterior-chain volume."),
            make_exercise("Plank", "core", "accessory", 2, 30, 60, 0, 7.0, "Trunk stiffness."),
            make_exercise("Hammer Curl", "forearm_grip", "accessory", 2, 10, 15, 0, 7.5, "Arm and grip support."),
        ],
        [
            make_exercise("Hip Airplane", "mobility", "recovery", 2, 5, 8, 0, 4.0, "Hip control and balance."),
            make_exercise("Dead Bug", "core", "recovery_accessory", 2, 8, 12, 0, 5.0, "Breathing and bracing."),
            make_exercise("Wrist Curl", "forearm_grip", "accessory", 2, 12, 20, 0, 7.0, "Forearm support."),
        ],
    ]

    selected = rotations[index_seed % len(rotations)]

    if workout_mode == "Fun":
        selected = selected + [
            make_exercise("Sled Push", "conditioning", "gpp", 3, 20, 40, 0, 7.5, "Fun conditioning finisher if equipment is available.")
        ]

    if workout_mode == "Chaos":
        selected = selected + [
            make_exercise("Bear Crawl", "locomotion", "gpp", 2, 20, 40, 0, 7.0, "Controlled chaos: trunk, shoulders, and conditioning.")
        ]

    return selected


# ------------------------------------------------------------
# Main workout generation
# ------------------------------------------------------------

def generate_workout(checkin: dict[str, Any]) -> dict[str, Any]:
    readiness_category = checkin.get("readiness_category", "Yellow")
    time_available = safe_int(checkin.get("time_available", 60), 60)
    goal_today = checkin.get("goal_today", "normal")
    day_name = get_day_name()
    deload = is_deload_day()
    template_key = get_template_key_from_checkin(checkin)
    workout_mode = get_workout_mode(checkin)
    training_bias = checkin.get("training_bias", template_key)

    focus = determine_focus(
        day_name=day_name,
        readiness_category=readiness_category,
        goal_today=goal_today,
        soreness=safe_int(checkin.get("soreness", 5), 5),
        combat_later_today=bool(checkin.get("combat_later_today", False)),
        deload=deload,
        template_key=template_key,
        workout_mode=workout_mode,
    )

    if template_key == "recovery":
        exercises = red_day_workout(time_available, workout_mode)
        workout_type = "Recovery / Mobility"
        reason = "Recovery bias selected. The app generated a low-fatigue mobility and recovery session."

    elif template_key == "accessory" and readiness_category in {"Yellow", "Orange", "Red"}:
        exercises = accessory_day_workout(time_available, workout_mode)
        workout_type = "Accessory / Hypertrophy Support"
        reason = "Accessory bias selected. The app generated lower-fatigue isolation, grip, core, and mobility work."

    elif template_key == "conditioning" and readiness_category in {"Green", "Yellow"}:
        exercises = conditioning_day_workout(time_available, readiness_category, workout_mode)
        workout_type = "Conditioning / GPP"
        reason = "Conditioning bias selected. The app generated a GPP-focused session."

    elif deload and readiness_category in {"Green", "Yellow"}:
        workout_type = "Deload / Light Full Body"
        reason = (
            "Scheduled conservative deload. The app reduced intensity and volume to protect recovery "
            "while keeping movement quality high."
        )
        exercises = orange_day_workout(
            focus=focus,
            time_available=time_available,
            deload=True,
            template_key=template_key,
            workout_mode=workout_mode,
        )

    elif readiness_category == "Green":
        exercises = green_day_workout(focus, time_available, template_key, workout_mode)
        workout_type = "Full-Body Strength"
        reason = "High readiness. The app generated a productive full-body strength session."

    elif readiness_category == "Yellow":
        exercises = yellow_day_workout(focus, time_available, template_key, workout_mode)
        workout_type = "Full-Body Strength"
        reason = "Moderate readiness. The app generated a normal full-body session."

    elif readiness_category == "Orange":
        exercises = orange_day_workout(
            focus=focus,
            time_available=time_available,
            template_key=template_key,
            workout_mode=workout_mode,
        )
        workout_type = "Light / Accessory"
        reason = "Reduced readiness. The app lowered intensity and shifted toward accessories."

    else:
        exercises = red_day_workout(time_available, workout_mode)
        workout_type = "Recovery"
        reason = "Low readiness. The app generated a recovery-focused session."

    reason = apply_workout_mode_to_reason(reason, workout_mode, readiness_category)

    return {
        "date": date.today().isoformat(),
        "workout_type": workout_type,
        "focus": focus,
        "readiness_category": readiness_category,
        "estimated_duration": time_available,
        "generation_reason": reason,
        "deload": deload,
        "template_key": template_key,
        "training_bias": training_bias,
        "workout_mode": workout_mode,
        "exercises": exercises,
    }


def determine_focus(
    day_name: str,
    readiness_category: str,
    goal_today: str,
    soreness: int,
    combat_later_today: bool,
    deload: bool,
    template_key: str,
    workout_mode: str = "Focused",
) -> str:
    if template_key == "posterior_chain":
        return "Posterior Chain / Grappling Strength"

    if template_key == "upper_grip":
        return "Upper Strength + Grip"

    if template_key == "lower_strength":
        return "Lower Strength"

    if template_key == "strength":
        return "Strength Emphasis Full Body"

    if template_key == "accessory":
        return "Accessory / Hypertrophy Support"

    if template_key == "conditioning":
        return "Conditioning / GPP"

    if template_key == "recovery":
        return "Recovery / Mobility"

    if deload:
        return "Deload / Accessory Full Body"

    if readiness_category == "Red" or goal_today == "recovery":
        return "Recovery"

    if readiness_category == "Orange" or soreness >= 7:
        return "Accessory / Light Full Body"

    if combat_later_today:
        return "Upper / Accessory Emphasis"

    if workout_mode == "Fun":
        return "Fun Full Body / Athletic Variety"

    if workout_mode == "Chaos" and readiness_category in {"Green", "Yellow"}:
        return "Chaos Full Body / Novelty GPP"

    if day_name == "Monday":
        return "Lower Emphasis Full Body"

    if day_name == "Wednesday":
        return "Upper Emphasis Full Body"

    if day_name == "Saturday":
        return "Full Body / Posterior Chain Emphasis"

    return "Full Body"


# ------------------------------------------------------------
# Workout templates
# ------------------------------------------------------------

def green_day_workout(
    focus: str,
    time_available: int,
    template_key: str,
    workout_mode: str = "Focused",
) -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()

    trap_load = adjust_load(get_progression_load("Trap Bar Deadlift", 300), "Green", "Trap Bar Deadlift")
    bench_load = adjust_load(get_progression_load("Bench Press", 195), "Green", "Bench Press")
    squat_load = adjust_load(get_progression_load("Squat", 275), "Green", "Squat")

    vertical_pull = choose_vertical_pull(
        index_seed=completed_count,
        readiness_category="Green",
        prefer_weighted=True,
        workout_mode=workout_mode,
    )

    horizontal_pull = choose_horizontal_pull(completed_count, workout_mode)

    if template_key == "posterior_chain":
        exercises = [
            make_loaded_exercise("Trap Bar Deadlift", "hinge", "main_lift", 4, 3, 5, trap_load, 8.0, "Main posterior-chain strength.", "Green"),
            vertical_pull,
            make_exercise("Romanian Deadlift", "hinge", "secondary_lift", 3, 6, 10, 0, 7.5, "Hamstrings and trunk."),
            horizontal_pull,
        ]

    elif template_key == "upper_grip":
        exercises = [
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 4, 4, 6, bench_load, 8.0, "Main press.", "Green"),
            vertical_pull,
            horizontal_pull,
            make_exercise("Landmine Press", "vertical_push", "secondary_lift", 3, 6, 10, 0, 7.5, "Athletic pressing."),
        ]

    elif template_key == "lower_strength":
        exercises = [
            make_loaded_exercise("Squat", "squat", "main_lift", 4, 4, 6, squat_load, 8.0, "Main squat pattern.", "Green"),
            make_loaded_exercise("Trap Bar Deadlift", "hinge", "main_lift", 3, 3, 5, trap_load, 8.0, "Main hinge pattern.", "Green"),
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Keep pressing maintained.", "Green"),
            make_exercise("Step-Up", "single_leg", "accessory", 3, 8, 12, 0, 7.5, "Single-leg strength."),
        ]

    elif template_key == "strength":
        exercises = [
            make_loaded_exercise("Squat", "squat", "main_lift", 3, 3, 5, squat_load, 8.0, "Primary strength squat pattern.", "Green"),
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 3, 5, bench_load, 8.0, "Primary strength press.", "Green"),
            vertical_pull,
            make_loaded_exercise("Trap Bar Deadlift", "hinge", "main_lift", 2, 3, 5, trap_load, 7.5, "Secondary hinge strength.", "Green"),
        ]

    elif "Lower" in focus:
        exercises = [
            make_loaded_exercise("Trap Bar Deadlift", "hinge", "main_lift", 4, 3, 5, trap_load, 8.0, "Strong but smooth. Leave 1-2 reps in reserve.", "Green"),
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 8.0, "Do not grind reps.", "Green"),
            vertical_pull,
            make_exercise("Split Squat", "single_leg", "accessory", 3, 8, 12, 0, 7.5, "Single-leg strength."),
        ]

    elif "Upper" in focus:
        exercises = [
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 4, 4, 6, bench_load, 8.0, "Main upper-body strength work.", "Green"),
            vertical_pull,
            make_loaded_exercise("Squat", "squat", "main_lift", 3, 4, 6, squat_load, 7.5, "Moderate lower work, no grinders.", "Green"),
            horizontal_pull,
        ]

    else:
        exercises = [
            make_loaded_exercise("Squat", "squat", "main_lift", 3, 4, 6, squat_load, 8.0, "Main lower-body strength work.", "Green"),
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 8.0, "Main press.", "Green"),
            vertical_pull,
            make_exercise("Romanian Deadlift", "hinge", "secondary_lift", 3, 6, 10, 0, 7.5, "Posterior-chain accessory."),
        ]

    exercises.extend(accessory_rotation(completed_count, workout_mode))

    return trim_for_time(exercises, time_available)


def yellow_day_workout(
    focus: str,
    time_available: int,
    template_key: str,
    workout_mode: str = "Focused",
) -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()

    trap_load = adjust_load(get_progression_load("Trap Bar Deadlift", 300), "Yellow", "Trap Bar Deadlift")
    bench_load = adjust_load(get_progression_load("Bench Press", 195), "Yellow", "Bench Press")
    squat_load = adjust_load(get_progression_load("Squat", 275), "Yellow", "Squat")

    vertical_pull = choose_vertical_pull(
        index_seed=completed_count + 1,
        readiness_category="Yellow",
        prefer_weighted=template_key in {"upper_grip", "strength"},
        workout_mode=workout_mode,
    )

    horizontal_pull = choose_horizontal_pull(completed_count + 1, workout_mode)

    if template_key == "posterior_chain":
        exercises = [
            make_loaded_exercise("Trap Bar Deadlift", "hinge", "main_lift", 3, 3, 5, trap_load, 7.5, "Main hinge work.", "Yellow"),
            vertical_pull,
            make_exercise("Back Extension", "posterior_chain", "accessory", 3, 10, 15, 0, 7.0, "Posterior-chain support."),
            horizontal_pull,
        ]

    elif template_key == "upper_grip":
        exercises = [
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Main press.", "Yellow"),
            vertical_pull,
            horizontal_pull,
            make_exercise("Hammer Curl", "forearm_grip", "accessory", 3, 10, 15, 0, 7.5, "Grip and arm support."),
        ]

    elif template_key == "lower_strength":
        exercises = [
            make_loaded_exercise("Squat", "squat", "main_lift", 3, 4, 6, squat_load, 7.5, "Main squat work.", "Yellow"),
            make_loaded_exercise("Trap Bar Deadlift", "hinge", "main_lift", 3, 3, 5, trap_load, 7.5, "Main hinge work.", "Yellow"),
            make_exercise("Step-Up", "single_leg", "accessory", 2, 8, 12, 0, 7.0, "Single-leg support."),
            make_exercise("Dead Bug", "core", "recovery_accessory", 2, 8, 12, 0, 5.0, "Core control."),
        ]

    elif template_key == "strength":
        exercises = [
            make_loaded_exercise("Squat", "squat", "main_lift", 3, 4, 6, squat_load, 7.5, "Controlled strength work.", "Yellow"),
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Controlled pressing.", "Yellow"),
            vertical_pull,
            make_exercise("Back Extension", "posterior_chain", "accessory", 2, 10, 15, 0, 7.0, "Posterior-chain support."),
        ]

    elif "Lower" in focus:
        exercises = [
            make_loaded_exercise("Trap Bar Deadlift", "hinge", "main_lift", 3, 3, 5, trap_load, 7.5, "Productive but conservative.", "Yellow"),
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Smooth reps.", "Yellow"),
            vertical_pull,
            make_exercise("Step-Up", "single_leg", "accessory", 2, 8, 12, 0, 7.0, "Moderate single-leg work."),
        ]

    elif "Upper" in focus:
        exercises = [
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Main upper-body work.", "Yellow"),
            vertical_pull,
            make_exercise("Goblet Squat", "squat", "accessory", 3, 8, 12, 0, 7.0, "Light lower-body volume."),
            horizontal_pull,
        ]

    else:
        exercises = [
            make_loaded_exercise("Squat", "squat", "main_lift", 3, 4, 6, squat_load, 7.5, "Controlled lower-body strength.", "Yellow"),
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 3, 4, 6, bench_load, 7.5, "Controlled pressing.", "Yellow"),
            vertical_pull,
            make_exercise("Back Extension", "posterior_chain", "accessory", 2, 10, 15, 0, 7.0, "Posterior-chain accessory."),
        ]

    exercises.extend(accessory_rotation(completed_count + 1, workout_mode))

    return trim_for_time(exercises, time_available)


def orange_day_workout(
    focus: str,
    time_available: int,
    deload: bool = False,
    template_key: str = "balanced",
    workout_mode: str = "Focused",
) -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()

    trap_load = adjust_load(get_progression_load("Trap Bar Deadlift", 300), "Orange", "Trap Bar Deadlift")
    bench_load = adjust_load(get_progression_load("Bench Press", 195), "Orange", "Bench Press")

    rpe_cap = 6.0 if deload else 6.5

    vertical_pull = choose_vertical_pull(
        index_seed=completed_count + 2,
        readiness_category="Orange",
        prefer_weighted=False,
        workout_mode=workout_mode,
    )

    horizontal_pull = choose_horizontal_pull(completed_count + 2, workout_mode)

    if template_key == "upper_grip":
        exercises = [
            make_loaded_exercise("Bench Press", "horizontal_push", "main_lift", 2, 4, 6, bench_load, rpe_cap, "Easy technique pressing.", "Orange"),
            horizontal_pull,
            make_exercise("Landmine Press", "vertical_push", "secondary_lift", 2, 6, 10, 0, 7.0, "Moderate pressing."),
            make_exercise("Hammer Curl", "forearm_grip", "accessory", 2, 10, 15, 0, 7.0, "Grip and arm work."),
        ]
    else:
        exercises = [
            make_loaded_exercise("Trap Bar Deadlift", "hinge", "main_lift", 2, 3, 5, trap_load, rpe_cap, "Technique work. Keep it easy.", "Orange"),
            make_exercise("Landmine Press", "vertical_push", "secondary_lift", 3, 6, 10, 0, 7.0, "Moderate pressing without grinding."),
            horizontal_pull,
            make_exercise("Goblet Squat", "squat", "accessory", 2, 8, 12, 0, 6.5, "Light lower-body work."),
        ]

    if workout_mode in {"Fun", "Chaos"}:
        exercises.append(vertical_pull)

    exercises.extend(accessory_rotation(completed_count + 2, workout_mode))

    return trim_for_time(exercises, time_available)


def accessory_day_workout(
    time_available: int,
    workout_mode: str = "Focused",
) -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()

    horizontal_pull = choose_horizontal_pull(completed_count + 3, workout_mode)

    exercises = [
        make_exercise("Landmine Press", "vertical_push", "secondary_lift", 3, 8, 12, 0, 7.0, "Athletic pressing without heavy fatigue."),
        horizontal_pull,
        make_exercise("Goblet Squat", "squat", "accessory", 3, 8, 12, 0, 6.5, "Light lower-body work."),
        make_exercise("Back Extension", "posterior_chain", "accessory", 3, 10, 15, 0, 7.0, "Posterior-chain support."),
        make_exercise("Lateral Raise", "shoulder_accessory", "accessory", 2, 12, 20, 0, 7.0, "Shoulder accessory."),
        make_exercise("Triceps Pressdown", "arm_accessory", "accessory", 2, 10, 15, 0, 7.0, "Arm accessory."),
    ]

    exercises.extend(accessory_rotation(completed_count + 3, workout_mode))

    return trim_for_time(exercises, time_available)


def conditioning_day_workout(
    time_available: int,
    readiness_category: str,
    workout_mode: str = "Focused",
) -> list[dict[str, Any]]:
    completed_count = get_completed_workout_count()

    if readiness_category == "Green":
        target_rpe = 7.5
    else:
        target_rpe = 6.5

    exercises = [
        make_exercise("Sled Push", "conditioning", "gpp", 4, 20, 40, 0, target_rpe, "Powerful but controlled pushes."),
        make_exercise("Farmer Carry", "carry_grip", "gpp", 4, 30, 60, 0, target_rpe, "Grip and trunk conditioning."),
        make_exercise("Assault Bike Intervals", "conditioning", "gpp", 6, 10, 30, 0, target_rpe, "Short hard intervals. Stop before sloppy output."),
        make_exercise("Dead Bug", "core", "recovery_accessory", 2, 8, 12, 0, 5.0, "Core reset."),
    ]

    if workout_mode == "Chaos":
        exercises.append(
            make_exercise("Bear Crawl", "locomotion", "gpp", 3, 20, 40, 0, 7.0, "Novel but controlled full-body conditioning.")
        )

    exercises.extend(accessory_rotation(completed_count + 4, workout_mode))

    return trim_for_time(exercises, time_available)


def red_day_workout(
    time_available: int,
    workout_mode: str = "Focused",
) -> list[dict[str, Any]]:
    exercises = [
        make_exercise("Incline Walk", "conditioning", "recovery", 1, 10, 20, 0, 4.0, "Easy pace. Nasal breathing if possible."),
        make_exercise("Mobility Flow", "mobility", "recovery", 1, 5, 10, 0, 3.0, "Move smoothly. Do not force range."),
        make_exercise("Hip Airplane", "mobility", "recovery", 2, 5, 8, 0, 4.0, "Balance and hip control."),
        make_exercise("Back Extension", "posterior_chain", "accessory", 2, 10, 15, 0, 5.0, "Very easy blood-flow work."),
        make_exercise("Dead Bug", "core", "recovery_accessory", 2, 8, 12, 0, 4.0, "Controlled breathing and bracing."),
        make_exercise("Neck Isometrics", "neck", "recovery_accessory", 2, 10, 20, 0, 4.0, "Light neck work."),
        make_exercise("Reverse Wrist Curl", "forearm_grip", "accessory", 2, 12, 20, 0, 5.0, "Light forearm work."),
    ]

    if workout_mode == "Fun":
        exercises.append(
            make_exercise("Easy Shadowboxing", "skill_movement", "recovery", 1, 3, 5, 0, 4.0, "Light movement only. No intensity.")
        )

    return trim_for_time(exercises, time_available)


def trim_for_time(exercises: list[dict[str, Any]], time_available: int) -> list[dict[str, Any]]:
    if time_available <= 30:
        return exercises[:4]

    if time_available <= 45:
        return exercises[:5]

    if time_available <= 60:
        return exercises[:6]

    return exercises
