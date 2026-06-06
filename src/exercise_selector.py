from typing import Any

from src.database import read_table
from src.exercise_catalog import get_exercise_catalog


VALUE_SCORE = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


FOCUS_TAGS = {
    "Full body": ["strength", "lower", "upper", "grappling"],
    "Lower emphasis": ["lower", "single_leg", "posterior_chain"],
    "Upper emphasis": ["upper", "grip", "press", "pull"],
    "Posterior chain / grappling": ["posterior_chain", "grappling", "grip", "core"],
    "Accessory / pump": ["arms", "forearms", "shoulders", "accessory", "grip", "core", "pump"],
    "Recovery / mobility": ["recovery", "mobility", "stretch", "cardio"],
    "Deload / Accessory Full Body": ["recovery", "mobility", "light"],
}


def get_recent_exercise_counts(limit: int = 5) -> dict[str, int]:
    try:
        sets = read_table("completed_sets")
    except Exception:
        return {}

    if sets.empty or "exercise_name" not in sets.columns:
        return {}

    recent = sets.tail(100)
    counts = recent["exercise_name"].value_counts().to_dict()
    return {str(name): int(count) for name, count in counts.items()}


def fatigue_penalty_for_readiness(fatigue_cost: str, readiness_category: str) -> int:
    fatigue_score = VALUE_SCORE.get(str(fatigue_cost).lower(), 2)

    if readiness_category == "Green":
        return 0

    if readiness_category == "Yellow":
        return max(0, fatigue_score - 2) * 3

    if readiness_category == "Orange":
        return max(0, fatigue_score - 1) * 5

    return fatigue_score * 8


def joint_stress_penalty(joint_stress: str, readiness_category: str) -> int:
    stress_score = VALUE_SCORE.get(str(joint_stress).lower(), 2)

    if readiness_category in {"Green", "Yellow"}:
        return 0

    return stress_score * 2


def score_exercise(
    exercise: dict[str, Any],
    desired_pattern: str,
    readiness_category: str,
    focus: str,
    workout_modifier: str,
    recent_counts: dict[str, int],
    avoid_names: set[str],
) -> float:
    score = 0.0

    name = exercise["exercise_name"]
    movement_pattern = exercise["movement_pattern"]
    category = exercise["exercise_category"]
    tags = exercise.get("tags", [])

    if name in avoid_names:
        score -= 25

    if movement_pattern == desired_pattern:
        score += 30
    elif desired_pattern in tags:
        score += 18

    focus_tags = FOCUS_TAGS.get(focus, [])

    for tag in tags:
        if tag in focus_tags:
            score += 5

    combat_transfer = VALUE_SCORE.get(str(exercise.get("combat_transfer", "medium")).lower(), 2)
    score += combat_transfer * 4

    if workout_modifier == "focus":
        if category in {"main_lift", "secondary_lift"}:
            score += 6
        if str(exercise.get("fatigue_cost", "medium")).lower() == "low":
            score -= 2

    if workout_modifier == "fun":
        if category in {"accessory", "gpp", "mobility", "cardio", "stretch"}:
            score += 6
        if exercise.get("modality") in {"machine", "flow", "loaded carry", "bodyweight grip", "footwork cardio"}:
            score += 3

    if workout_modifier == "chaos":
        if category in {"gpp", "mobility", "accessory", "stretch"}:
            score += 8
        if exercise.get("modality") in {"loaded carry", "flow", "single-leg", "isometric", "locomotion", "ballistic"}:
            score += 5

    score -= fatigue_penalty_for_readiness(exercise.get("fatigue_cost", "medium"), readiness_category)
    score -= joint_stress_penalty(exercise.get("joint_stress", "medium"), readiness_category)

    recent_count = recent_counts.get(name, 0)
    score -= min(recent_count * 4, 20)

    if readiness_category == "Red":
        if exercise["prescription_type"] in {"mobility", "stretch", "cardio"}:
            score += 20
        if exercise["exercise_category"] in {"main_lift", "secondary_lift"}:
            score -= 30

    if readiness_category == "Orange":
        if exercise.get("fatigue_cost") == "low":
            score += 8
        if exercise["exercise_category"] == "main_lift":
            score -= 8

    return score


def select_exercise(
    desired_pattern: str,
    readiness_category: str,
    focus: str,
    workout_modifier: str = "normal",
    allowed_categories: list[str] | None = None,
    allowed_prescription_types: list[str] | None = None,
    avoid_names: set[str] | None = None,
) -> dict[str, Any]:
    catalog = get_exercise_catalog()
    recent_counts = get_recent_exercise_counts()
    avoid = avoid_names or set()

    candidates = []

    for exercise in catalog:
        if allowed_categories and exercise["exercise_category"] not in allowed_categories:
            continue

        if allowed_prescription_types and exercise["prescription_type"] not in allowed_prescription_types:
            continue

        if exercise["movement_pattern"] != desired_pattern and desired_pattern not in exercise.get("tags", []):
            continue

        candidates.append(exercise)

    if not candidates:
        candidates = [
            exercise
            for exercise in catalog
            if not allowed_categories or exercise["exercise_category"] in allowed_categories
        ]

    if not candidates:
        candidates = catalog

    scored = []

    for exercise in candidates:
        score = score_exercise(
            exercise=exercise,
            desired_pattern=desired_pattern,
            readiness_category=readiness_category,
            focus=focus,
            workout_modifier=workout_modifier,
            recent_counts=recent_counts,
            avoid_names=avoid,
        )
        scored.append((score, exercise))

    scored.sort(key=lambda item: item[0], reverse=True)

    return scored[0][1].copy()


def select_multiple_exercises(
    desired_patterns: list[str],
    readiness_category: str,
    focus: str,
    workout_modifier: str = "normal",
    allowed_categories_by_pattern: dict[str, list[str]] | None = None,
    allowed_types_by_pattern: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    selected = []
    avoid_names = set()

    for pattern in desired_patterns:
        allowed_categories = None
        allowed_types = None

        if allowed_categories_by_pattern:
            allowed_categories = allowed_categories_by_pattern.get(pattern)

        if allowed_types_by_pattern:
            allowed_types = allowed_types_by_pattern.get(pattern)

        exercise = select_exercise(
            desired_pattern=pattern,
            readiness_category=readiness_category,
            focus=focus,
            workout_modifier=workout_modifier,
            allowed_categories=allowed_categories,
            allowed_prescription_types=allowed_types,
            avoid_names=avoid_names,
        )

        selected.append(exercise)
        avoid_names.add(exercise["exercise_name"])

    return selected


def apply_overrides(exercise: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    updated = exercise.copy()

    for key, value in overrides.items():
        updated[key] = value

    return updated


def substitute_exercise(
    current_exercise: dict[str, Any],
    substitution_type: str,
    readiness_category: str,
    focus: str,
    workout_modifier: str,
    current_workout_exercises: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    substitution_type:
    - modality: same movement pattern, different equipment/modality if possible
    - full: different movement pattern/category if possible
    """
    catalog = get_exercise_catalog()
    recent_counts = get_recent_exercise_counts()

    current_name = current_exercise.get("exercise_name", "")
    current_pattern = current_exercise.get("movement_pattern", "")
    current_modality = current_exercise.get("modality", "")
    current_category = current_exercise.get("exercise_category", "")
    current_prescription_type = current_exercise.get("prescription_type", "strength")

    avoid_names = {current_name}
    avoid_names.update([exercise.get("exercise_name", "") for exercise in current_workout_exercises])

    candidates = []

    for exercise in catalog:
        if exercise["exercise_name"] in avoid_names:
            continue

        if substitution_type == "modality":
            if exercise["movement_pattern"] != current_pattern:
                continue

            # Prefer a true modality/equipment change.
            if exercise.get("modality") == current_modality and exercise.get("equipment") == current_exercise.get("equipment"):
                continue

            # Keep the same broad category when possible.
            if current_category == "main_lift" and exercise["exercise_category"] not in {"main_lift", "secondary_lift"}:
                continue

        elif substitution_type == "full":
            if exercise["movement_pattern"] == current_pattern:
                continue

            # Avoid replacing a strength movement with pure stretching unless current movement is recovery-style.
            if current_prescription_type == "strength" and exercise["prescription_type"] in {"stretch", "mobility", "cardio"}:
                continue

        else:
            continue

        candidates.append(exercise)

    if not candidates:
        candidates = [
            exercise
            for exercise in catalog
            if exercise["exercise_name"] != current_name
        ]

    scored = []

    desired_pattern = current_pattern if substitution_type == "modality" else exercise_goal_from_current(current_exercise)

    for exercise in candidates:
        score = score_exercise(
            exercise=exercise,
            desired_pattern=desired_pattern,
            readiness_category=readiness_category,
            focus=focus,
            workout_modifier=workout_modifier,
            recent_counts=recent_counts,
            avoid_names=avoid_names,
        )

        if substitution_type == "modality":
            if exercise.get("modality") != current_modality:
                score += 12
            if exercise.get("equipment") != current_exercise.get("equipment"):
                score += 8

        if substitution_type == "full":
            if exercise["movement_pattern"] != current_pattern:
                score += 12
            if exercise["exercise_category"] == current_category:
                score += 4

        scored.append((score, exercise))

    scored.sort(key=lambda item: item[0], reverse=True)

    replacement = scored[0][1].copy()

    replacement["planned_sets"] = current_exercise.get("planned_sets", replacement.get("planned_sets", 3))
    replacement["target_rpe"] = min(
        float(current_exercise.get("target_rpe", replacement.get("target_rpe", 7.0))),
        float(replacement.get("target_rpe", 7.0)),
    )

    replacement["notes"] = (
        replacement.get("notes", "")
        + f" Substituted for {current_name} using {substitution_type} substitution."
    )

    return replacement


def exercise_goal_from_current(current_exercise: dict[str, Any]) -> str:
    category = current_exercise.get("exercise_category", "")
    pattern = current_exercise.get("movement_pattern", "")

    if category == "main_lift":
        if pattern in {"squat", "hinge"}:
            return "horizontal_push"
        if pattern in {"horizontal_push", "vertical_push"}:
            return "vertical_pull"
        return "squat"

    if pattern in {"mobility", "stretch"}:
        return "conditioning"

    if pattern in {"conditioning"}:
        return "mobility"

    if pattern in {"core"}:
        return "carry_grip"

    return "core"
