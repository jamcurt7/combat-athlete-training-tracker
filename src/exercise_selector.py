from typing import Any

from src.database import read_table, get_personalization_settings
from src.exercise_catalog import get_exercise_catalog


VALUE_SCORE = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


FOCUS_TAGS = {
    "Full body": ["strength", "lower", "upper", "grappling", "core"],
    "Lower emphasis": ["lower", "single_leg", "posterior_chain", "hips"],
    "Upper emphasis": ["upper", "grip", "press", "pull", "shoulders", "upper_back"],
    "Posterior chain / grappling": ["posterior_chain", "grappling", "grip", "core", "neck", "hips"],
    "Accessory / pump": ["arms", "forearms", "shoulders", "accessory", "grip", "core", "pump", "glutes"],
    "Recovery / mobility": ["recovery", "mobility", "stretch", "cardio", "CARs", "PAILs", "RAILs"],
    "Deload / Accessory Full Body": ["recovery", "mobility", "light", "core", "grip"],
}


READINESS_METHOD_BONUS = {
    "Green": {
        "submax_strength": 8,
        "dynamic_effort": 7,
        "overcoming_isometric": 5,
        "repeated_effort": 4,
        "gpp": 3,
        "skill_conditioning": 2,
        "mobility_control": 1,
        "recovery": 0,
        "movement_prep": 2,
    },
    "Yellow": {
        "submax_strength": 5,
        "repeated_effort": 5,
        "overcoming_isometric": 3,
        "dynamic_effort": 3,
        "gpp": 3,
        "skill_conditioning": 4,
        "mobility_control": 4,
        "recovery": 3,
        "movement_prep": 3,
    },
    "Orange": {
        "submax_strength": -2,
        "repeated_effort": 4,
        "overcoming_isometric": 1,
        "dynamic_effort": 0,
        "gpp": 3,
        "skill_conditioning": 5,
        "mobility_control": 6,
        "recovery": 6,
        "movement_prep": 5,
    },
    "Red": {
        "submax_strength": -12,
        "repeated_effort": -2,
        "overcoming_isometric": -8,
        "dynamic_effort": -8,
        "gpp": 0,
        "skill_conditioning": 4,
        "mobility_control": 9,
        "recovery": 10,
        "movement_prep": 7,
    },
}


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_list(values: list[Any]) -> list[str]:
    return [normalize_text(value) for value in values if normalize_text(value)]


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
        return max(0, fatigue_score - 1) * 6

    return fatigue_score * 9


def joint_stress_penalty(joint_stress: str, readiness_category: str) -> int:
    stress_score = VALUE_SCORE.get(str(joint_stress).lower(), 2)

    if readiness_category == "Green":
        return 0

    if readiness_category == "Yellow":
        return max(0, stress_score - 2) * 2

    if readiness_category == "Orange":
        return stress_score * 2

    return stress_score * 4


def method_bonus(exercise: dict[str, Any], readiness_category: str) -> float:
    method_tag = str(exercise.get("method_tag", ""))
    return READINESS_METHOD_BONUS.get(readiness_category, {}).get(method_tag, 0)


def modifier_bonus(exercise: dict[str, Any], workout_modifier: str) -> float:
    category = exercise.get("exercise_category", "")
    method_tag = exercise.get("method_tag", "")
    modality = exercise.get("modality", "")
    prescription_type = exercise.get("prescription_type", "")
    session_slot = exercise.get("session_slot", "")

    score = 0.0

    if workout_modifier == "focus":
        if category in {"main_lift", "secondary_lift"}:
            score += 6
        if method_tag in {"submax_strength", "overcoming_isometric", "repeated_effort"}:
            score += 4
        if prescription_type in {"stretch", "mobility"} and session_slot != "movement_prep":
            score -= 2

    elif workout_modifier == "fun":
        if category in {"accessory", "gpp", "mobility", "cardio", "stretch"}:
            score += 6
        if modality in {
            "machine",
            "flow",
            "loaded carry",
            "bodyweight grip",
            "footwork cardio",
            "technical cardio",
            "ground mobility",
            "mobility circuit",
        }:
            score += 4

    elif workout_modifier == "chaos":
        if category in {"gpp", "mobility", "accessory", "stretch", "cardio"}:
            score += 8
        if modality in {
            "loaded carry",
            "flow",
            "single-leg",
            "isometric",
            "locomotion",
            "ballistic",
            "PAILs/RAILs",
            "technical cardio",
            "ground mobility",
            "mobility circuit",
        }:
            score += 6

    return score


def equipment_matches_preference(exercise: dict[str, Any], preferred_equipment: list[str]) -> bool:
    if not preferred_equipment:
        return False

    equipment_text = normalize_text(exercise.get("equipment", ""))
    modality_text = normalize_text(exercise.get("modality", ""))
    name_text = normalize_text(exercise.get("exercise_name", ""))

    combined = " ".join([equipment_text, modality_text, name_text])

    for equipment in normalize_list(preferred_equipment):
        if equipment in combined:
            return True

    return False


def exercise_matches_mobility_priority(exercise: dict[str, Any], mobility_priorities: list[str]) -> bool:
    if not mobility_priorities:
        return False

    body_region = normalize_text(exercise.get("body_region", ""))
    mobility_style = normalize_text(exercise.get("mobility_style", ""))
    name = normalize_text(exercise.get("exercise_name", ""))
    tags = " ".join(normalize_list(exercise.get("tags", [])))

    combined = " ".join([body_region, mobility_style, name, tags])

    for priority in normalize_list(mobility_priorities):
        if priority in combined:
            return True

        if priority == "t-spine" and "thoracic" in combined:
            return True

        if priority == "thoracic" and "t-spine" in combined:
            return True

    return False


def cardio_preference_bonus(exercise: dict[str, Any], cardio_preference: str) -> float:
    preference = normalize_text(cardio_preference)
    prescription_type = normalize_text(exercise.get("prescription_type", ""))
    modality = normalize_text(exercise.get("modality", ""))
    name = normalize_text(exercise.get("exercise_name", ""))
    session_slot = normalize_text(exercise.get("session_slot", ""))

    if prescription_type not in {"cardio", "cardio_skill", "conditioning"} and "cardio" not in session_slot:
        return 0.0

    combined = " ".join([modality, name, session_slot])

    technical_terms = ["technical", "shadow", "boxing", "muay", "footwork", "jump rope", "stance", "defensive"]
    machine_terms = ["bike", "rower", "treadmill", "incline", "machine", "erg"]
    low_impact_terms = ["bike", "walk", "incline", "zone2", "zone 2", "sled"]

    score = 0.0

    if preference == "technical combat":
        if any(term in combined for term in technical_terms):
            score += 14
        if any(term in combined for term in machine_terms):
            score -= 4

    elif preference == "machine":
        if any(term in combined for term in machine_terms):
            score += 12
        if any(term in combined for term in technical_terms):
            score -= 5

    elif preference == "low impact":
        if any(term in combined for term in low_impact_terms):
            score += 10
        if "jump rope" in combined:
            score -= 6

    elif preference == "mixed":
        if any(term in combined for term in technical_terms):
            score += 4
        if any(term in combined for term in machine_terms):
            score += 4

    return score


def strength_method_preference_bonus(exercise: dict[str, Any], strength_method_preference: str) -> float:
    preference = normalize_text(strength_method_preference)
    method_tag = normalize_text(exercise.get("method_tag", ""))
    category = normalize_text(exercise.get("exercise_category", ""))
    prescription_type = normalize_text(exercise.get("prescription_type", ""))

    if category not in {"main_lift", "secondary_lift", "accessory", "gpp"} and prescription_type != "strength":
        return 0.0

    if preference == "standard strength":
        if method_tag == "submax_strength":
            return 9
        if method_tag in {"dynamic_effort", "overcoming_isometric"}:
            return -4

    if preference == "conjugate-inspired":
        if method_tag in {"dynamic_effort", "overcoming_isometric", "repeated_effort"}:
            return 9
        if method_tag == "submax_strength":
            return 2

    if preference == "isometrics":
        if method_tag in {"overcoming_isometric", "yielding_isometric"}:
            return 14
        if method_tag == "dynamic_effort":
            return -5

    if preference == "repeated effort":
        if method_tag == "repeated_effort":
            return 12
        if method_tag in {"overcoming_isometric", "dynamic_effort"}:
            return -2

    return 0.0


def personalization_bonus(
    exercise: dict[str, Any],
    personalization: dict[str, Any],
) -> float:
    score = 0.0

    name = str(exercise.get("exercise_name", ""))
    avoided = set(personalization.get("avoided_exercises", []))
    favorites = set(personalization.get("favorite_exercises", []))
    preferred_equipment = personalization.get("preferred_equipment", [])
    mobility_priorities = personalization.get("mobility_priorities", [])
    cardio_preference = personalization.get("cardio_preference", "Mixed")
    strength_method_preference = personalization.get("strength_method_preference", "App decides")

    prescription_type = normalize_text(exercise.get("prescription_type", ""))

    if name in avoided:
        score -= 1000

    if name in favorites:
        score += 14

    if equipment_matches_preference(exercise, preferred_equipment):
        score += 6

    if prescription_type in {"mobility", "stretch"}:
        if exercise_matches_mobility_priority(exercise, mobility_priorities):
            score += 12
        elif mobility_priorities:
            score -= 2

    score += cardio_preference_bonus(exercise, cardio_preference)
    score += strength_method_preference_bonus(exercise, strength_method_preference)

    return score


def recent_history_penalty(
    exercise_name: str,
    recent_counts: dict[str, int],
    personalization: dict[str, Any],
) -> float:
    recent_count = recent_counts.get(exercise_name, 0)
    variety_preference = personalization.get("exercise_variety_preference", "Balanced")

    if variety_preference == "Higher variety":
        return min(recent_count * 8, 35)

    if variety_preference == "Repeat proven exercises":
        return min(recent_count * 2, 10)

    return min(recent_count * 5, 25)


def score_exercise(
    exercise: dict[str, Any],
    desired_pattern: str,
    readiness_category: str,
    focus: str,
    workout_modifier: str,
    recent_counts: dict[str, int],
    avoid_names: set[str],
    desired_session_slot: str | None = None,
    desired_method_tag: str | None = None,
    personalization: dict[str, Any] | None = None,
) -> float:
    score = 0.0
    personalization = personalization or get_personalization_settings()

    name = exercise.get("exercise_name", "")
    movement_pattern = exercise.get("movement_pattern", "")
    category = exercise.get("exercise_category", "")
    tags = exercise.get("tags", [])
    session_slot = exercise.get("session_slot", "")
    method_tag = exercise.get("method_tag", "")
    prescription_type = exercise.get("prescription_type", "")

    if name in avoid_names:
        score -= 35

    if desired_session_slot:
        if session_slot == desired_session_slot:
            score += 45
        elif desired_session_slot in tags:
            score += 20

    if desired_method_tag:
        if method_tag == desired_method_tag:
            score += 25
        elif desired_method_tag in tags:
            score += 10

    if movement_pattern == desired_pattern:
        score += 30
    elif desired_pattern in tags:
        score += 18
    elif desired_pattern == session_slot:
        score += 22

    focus_tags = FOCUS_TAGS.get(focus, [])

    for tag in tags:
        if tag in focus_tags:
            score += 5

    combat_transfer = VALUE_SCORE.get(str(exercise.get("combat_transfer", "medium")).lower(), 2)
    technical_transfer = VALUE_SCORE.get(str(exercise.get("technical_transfer", "medium")).lower(), 2)

    score += combat_transfer * 4
    score += technical_transfer * 3
    score += method_bonus(exercise, readiness_category)
    score += modifier_bonus(exercise, workout_modifier)
    score += personalization_bonus(exercise, personalization)

    score -= fatigue_penalty_for_readiness(exercise.get("fatigue_cost", "medium"), readiness_category)
    score -= joint_stress_penalty(exercise.get("joint_stress", "medium"), readiness_category)
    score -= recent_history_penalty(str(name), recent_counts, personalization)

    fatigue_points = int(exercise.get("fatigue_points", 3))

    if readiness_category == "Green":
        if 4 <= fatigue_points <= 8:
            score += 3

    elif readiness_category == "Yellow":
        if 2 <= fatigue_points <= 6:
            score += 4
        if fatigue_points >= 8:
            score -= 4

    elif readiness_category == "Orange":
        if fatigue_points <= 4:
            score += 6
        if fatigue_points >= 7:
            score -= 8

    else:
        if fatigue_points <= 2:
            score += 10
        if prescription_type in {"mobility", "stretch", "cardio", "cardio_skill"}:
            score += 12
        if category in {"main_lift", "secondary_lift"}:
            score -= 30
        if method_tag == "overcoming_isometric":
            score -= 20

    return score


def select_exercise(
    desired_pattern: str,
    readiness_category: str,
    focus: str,
    workout_modifier: str = "normal",
    allowed_categories: list[str] | None = None,
    allowed_prescription_types: list[str] | None = None,
    avoid_names: set[str] | None = None,
    desired_session_slot: str | None = None,
    desired_method_tag: str | None = None,
) -> dict[str, Any]:
    catalog = get_exercise_catalog()
    recent_counts = get_recent_exercise_counts()
    personalization = get_personalization_settings()

    avoid = avoid_names or set()
    user_avoided = set(personalization.get("avoided_exercises", []))
    combined_avoid = set(avoid).union(user_avoided)

    candidates = []

    for exercise in catalog:
        if exercise.get("exercise_name") in user_avoided:
            continue

        if allowed_categories and exercise.get("exercise_category") not in allowed_categories:
            continue

        if allowed_prescription_types and exercise.get("prescription_type") not in allowed_prescription_types:
            continue

        tags = exercise.get("tags", [])

        pattern_match = (
            exercise.get("movement_pattern") == desired_pattern
            or desired_pattern in tags
            or desired_pattern == exercise.get("session_slot")
        )

        slot_match = True
        if desired_session_slot:
            slot_match = (
                exercise.get("session_slot") == desired_session_slot
                or desired_session_slot in tags
            )

        method_match = True
        if desired_method_tag:
            method_match = (
                exercise.get("method_tag") == desired_method_tag
                or desired_method_tag in tags
            )

        if desired_session_slot or desired_method_tag:
            if not slot_match and not method_match:
                continue
        elif not pattern_match:
            continue

        candidates.append(exercise)

    if not candidates and desired_session_slot:
        candidates = [
            exercise
            for exercise in catalog
            if exercise.get("session_slot") == desired_session_slot
            and exercise.get("exercise_name") not in user_avoided
        ]

    if not candidates:
        candidates = [
            exercise
            for exercise in catalog
            if (not allowed_categories or exercise.get("exercise_category") in allowed_categories)
            and exercise.get("exercise_name") not in user_avoided
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
            avoid_names=combined_avoid,
            desired_session_slot=desired_session_slot,
            desired_method_tag=desired_method_tag,
            personalization=personalization,
        )
        scored.append((score, exercise))

    scored.sort(key=lambda item: item[0], reverse=True)

    selected = scored[0][1].copy()
    selected["selection_score"] = round(scored[0][0], 2)
    selected["selection_reason"] = build_selection_reason(
        selected,
        readiness_category,
        focus,
        desired_session_slot,
        desired_method_tag,
        personalization,
    )

    return selected


def select_multiple_exercises(
    desired_patterns: list[str],
    readiness_category: str,
    focus: str,
    workout_modifier: str = "normal",
    allowed_categories_by_pattern: dict[str, list[str]] | None = None,
    allowed_types_by_pattern: dict[str, list[str]] | None = None,
    session_slots_by_pattern: dict[str, str] | None = None,
    method_tags_by_pattern: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    selected = []
    avoid_names = set()

    for pattern in desired_patterns:
        exercise = select_exercise(
            desired_pattern=pattern,
            readiness_category=readiness_category,
            focus=focus,
            workout_modifier=workout_modifier,
            allowed_categories=(allowed_categories_by_pattern or {}).get(pattern),
            allowed_prescription_types=(allowed_types_by_pattern or {}).get(pattern),
            avoid_names=avoid_names,
            desired_session_slot=(session_slots_by_pattern or {}).get(pattern),
            desired_method_tag=(method_tags_by_pattern or {}).get(pattern),
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
    catalog = get_exercise_catalog()
    recent_counts = get_recent_exercise_counts()
    personalization = get_personalization_settings()

    current_name = current_exercise.get("exercise_name", "")
    current_pattern = current_exercise.get("movement_pattern", "")
    current_modality = current_exercise.get("modality", "")
    current_equipment = current_exercise.get("equipment", "")
    current_category = current_exercise.get("exercise_category", "")
    current_prescription_type = current_exercise.get("prescription_type", "strength")
    current_slot = current_exercise.get("session_slot", "")
    current_group = current_exercise.get("substitution_group", "")
    current_modality_group = current_exercise.get("modality_group", "")

    user_avoided = set(personalization.get("avoided_exercises", []))

    avoid_names = {current_name}
    avoid_names.update([exercise.get("exercise_name", "") for exercise in current_workout_exercises])
    avoid_names.update(user_avoided)

    candidates = []

    for exercise in catalog:
        if exercise["exercise_name"] in avoid_names:
            continue

        if substitution_type == "modality":
            same_group = (
                exercise.get("substitution_group") == current_group
                or exercise.get("movement_pattern") == current_pattern
                or exercise.get("session_slot") == current_slot
            )

            if not same_group:
                continue

            changed_modality = (
                exercise.get("modality") != current_modality
                or exercise.get("equipment") != current_equipment
                or exercise.get("modality_group") != current_modality_group
            )

            if not changed_modality:
                continue

            if current_category == "main_lift" and exercise["exercise_category"] not in {"main_lift", "secondary_lift"}:
                continue

            if current_prescription_type == "strength" and exercise["prescription_type"] in {"stretch", "mobility", "cardio", "cardio_skill"}:
                continue

        elif substitution_type == "full":
            same_exact_pattern = exercise["movement_pattern"] == current_pattern
            same_exact_group = exercise.get("substitution_group") == current_group

            if same_exact_pattern and same_exact_group:
                continue

            if current_prescription_type == "strength" and exercise["prescription_type"] in {"stretch", "mobility", "cardio", "cardio_skill"}:
                continue

            if current_prescription_type in {"mobility", "stretch"} and exercise["prescription_type"] == "strength":
                continue

        else:
            continue

        candidates.append(exercise)

    if not candidates:
        candidates = [
            exercise
            for exercise in catalog
            if exercise["exercise_name"] != current_name
            and exercise["exercise_name"] not in user_avoided
        ]

    if not candidates:
        candidates = [
            exercise
            for exercise in catalog
            if exercise["exercise_name"] != current_name
        ]

    scored = []

    desired_pattern = current_pattern if substitution_type == "modality" else exercise_goal_from_current(current_exercise)
    desired_slot = current_slot

    for exercise in candidates:
        score = score_exercise(
            exercise=exercise,
            desired_pattern=desired_pattern,
            readiness_category=readiness_category,
            focus=focus,
            workout_modifier=workout_modifier,
            recent_counts=recent_counts,
            avoid_names=avoid_names,
            desired_session_slot=desired_slot,
            desired_method_tag=None,
            personalization=personalization,
        )

        if substitution_type == "modality":
            if exercise.get("modality") != current_modality:
                score += 12
            if exercise.get("equipment") != current_equipment:
                score += 8
            if exercise.get("substitution_group") == current_group:
                score += 10

        if substitution_type == "full":
            if exercise["movement_pattern"] != current_pattern:
                score += 12
            if exercise.get("session_slot") == current_slot:
                score += 10
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

    replacement["selection_score"] = round(scored[0][0], 2)
    replacement["selection_reason"] = build_selection_reason(
        replacement,
        readiness_category,
        focus,
        replacement.get("session_slot"),
        replacement.get("method_tag"),
        personalization,
    )

    return replacement


def exercise_goal_from_current(current_exercise: dict[str, Any]) -> str:
    category = current_exercise.get("exercise_category", "")
    pattern = current_exercise.get("movement_pattern", "")
    prescription_type = current_exercise.get("prescription_type", "")

    if category == "main_lift":
        if pattern in {"squat", "hinge", "single_leg"}:
            return "horizontal_push"
        if pattern in {"horizontal_push", "vertical_push"}:
            return "vertical_pull"
        return "squat"

    if prescription_type in {"mobility", "stretch"}:
        return "conditioning"

    if pattern == "conditioning":
        return "mobility"

    if pattern == "core":
        return "carry_grip"

    if pattern in {"carry_grip", "forearm_grip"}:
        return "core"

    return "core"


def build_selection_reason(
    exercise: dict[str, Any],
    readiness_category: str,
    focus: str,
    desired_session_slot: str | None,
    desired_method_tag: str | None,
    personalization: dict[str, Any] | None = None,
) -> str:
    personalization = personalization or get_personalization_settings()
    reasons = []

    name = exercise.get("exercise_name", "")
    session_slot = exercise.get("session_slot", "")
    method_tag = exercise.get("method_tag", "")
    fatigue_points = int(exercise.get("fatigue_points", 3))
    combat_transfer = exercise.get("combat_transfer", "")
    technical_transfer = exercise.get("technical_transfer", "")
    prescription_type = normalize_text(exercise.get("prescription_type", ""))

    favorites = set(personalization.get("favorite_exercises", []))

    if desired_session_slot and session_slot == desired_session_slot:
        reasons.append(f"matched the {desired_session_slot.replace('_', ' ')} slot")

    if desired_method_tag and method_tag == desired_method_tag:
        reasons.append(f"matched the {desired_method_tag.replace('_', ' ')} method")

    if name in favorites:
        reasons.append("it is one of your favorite exercises")

    if equipment_matches_preference(exercise, personalization.get("preferred_equipment", [])):
        reasons.append("it uses preferred equipment")

    if prescription_type in {"mobility", "stretch"} and exercise_matches_mobility_priority(
        exercise,
        personalization.get("mobility_priorities", []),
    ):
        reasons.append("it matches your mobility priorities")

    cardio_pref = personalization.get("cardio_preference", "Mixed")
    if cardio_preference_bonus(exercise, cardio_pref) >= 8:
        reasons.append(f"it fits your {str(cardio_pref).lower()} cardio preference")

    strength_pref = personalization.get("strength_method_preference", "App decides")
    if strength_method_preference_bonus(exercise, strength_pref) >= 8:
        reasons.append(f"it fits your {str(strength_pref).lower()} strength preference")

    if combat_transfer == "high":
        reasons.append("high combat transfer")

    if technical_transfer == "high":
        reasons.append("high technical transfer")

    if readiness_category in {"Orange", "Red"} and fatigue_points <= 3:
        reasons.append("low fatigue for today’s readiness")

    if readiness_category in {"Green", "Yellow"} and method_tag in {"submax_strength", "dynamic_effort", "overcoming_isometric"}:
        reasons.append("appropriate strength stimulus for readiness")

    if focus and any(tag in exercise.get("tags", []) for tag in FOCUS_TAGS.get(focus, [])):
        reasons.append(f"fits {focus.lower()} focus")

    if not reasons:
        reasons.append("best available match based on readiness, focus, preferences, and recent exercise history")

    return "Selected because it " + ", ".join(reasons) + "."
