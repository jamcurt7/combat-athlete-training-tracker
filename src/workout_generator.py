from datetime import date
from typing import Any

import pandas as pd

from src.database import (
    get_progression_state,
    get_completed_workout_count,
    get_setting,
)
from src.exercise_selector import select_exercise


MAX_LIFTS = {
    "Trap Bar Deadlift": 375,
    "Bench Press": 245,
    "Squat": 365,
    "Weighted Pull-Up": 45,
    "Weighted Chin-Up": 45,
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
    session_type = checkin.get("session_type", "Main Workout")
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

    slot_plan = build_slot_plan(
        checkin=checkin,
        focus=focus,
        readiness_category=readiness_category,
        goal_today=goal_today,
        workout_modifier=workout_modifier,
        template_key=template_key,
        deload=deload,
        session_type=session_type,
    )

    fatigue_budget = get_fatigue_budget(
        readiness_category=readiness_category,
        goal_today=goal_today,
        time_available=time_available,
        combat_later_today=bool(checkin.get("combat_later_today", False)),
        hard_sparring_last_24h=bool(checkin.get("hard_sparring_last_24h", False)),
        deload=deload,
        workout_modifier=workout_modifier,
        session_type=session_type,
    )

    exercises = build_workout_from_slots(
        slot_plan=slot_plan,
        readiness_category=readiness_category,
        focus=focus,
        workout_modifier=workout_modifier,
        fatigue_budget=fatigue_budget,
        time_available=time_available,
    )

    exercises = finalize_selected_exercises(
        exercises=exercises,
        readiness_category=readiness_category,
        workout_modifier=workout_modifier,
        session_type=session_type,
    )

    workout_type = determine_workout_type(
        readiness_category=readiness_category,
        focus=focus,
        goal_today=goal_today,
        deload=deload,
        template_key=template_key,
        session_type=session_type,
        exercises=exercises,
    )

    reason = build_generation_reason(
        readiness_category=readiness_category,
        focus=focus,
        goal_today=goal_today,
        workout_modifier=workout_modifier,
        fatigue_budget=fatigue_budget,
        checkin=checkin,
        deload=deload,
        exercises=exercises,
        session_type=session_type,
    )

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
        "session_type": session_type,
        "fatigue_budget": fatigue_budget,
        "estimated_fatigue": sum(int(exercise.get("fatigue_points", 3)) for exercise in exercises),
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


def get_fatigue_budget(
    readiness_category: str,
    goal_today: str,
    time_available: int,
    combat_later_today: bool,
    hard_sparring_last_24h: bool,
    deload: bool,
    workout_modifier: str,
    session_type: str,
) -> int:
    if session_type == "Post-Workout Stretch / Mobility":
        return 10 if time_available <= 30 else 14

    if session_type == "Mobility & Stretch Only":
        return 12 if time_available <= 30 else 16

    if session_type == "Technical Cardio / Footwork":
        return 12 if time_available <= 30 else 18

    if readiness_category == "Green":
        budget = 30
    elif readiness_category == "Yellow":
        budget = 23
    elif readiness_category == "Orange":
        budget = 15
    else:
        budget = 10

    if goal_today == "push":
        budget += 4
    elif goal_today == "maintain":
        budget -= 2
    elif goal_today == "recovery":
        budget -= 5

    if time_available <= 30:
        budget -= 6
    elif time_available <= 45:
        budget -= 2
    elif time_available >= 75:
        budget += 5

    if combat_later_today:
        budget -= 5

    if hard_sparring_last_24h:
        budget -= 4

    if deload:
        budget -= 7

    if workout_modifier == "focus":
        budget -= 3
    elif workout_modifier == "fun":
        budget += 2
    elif workout_modifier == "chaos":
        budget += 1

    return max(6, budget)


def slot(
    name: str,
    desired_pattern: str,
    session_slot: str,
    method_tag: str | None = None,
    allowed_categories: list[str] | None = None,
    allowed_types: list[str] | None = None,
    required: bool = False,
    priority: int = 5,
) -> dict[str, Any]:
    return {
        "name": name,
        "desired_pattern": desired_pattern,
        "session_slot": session_slot,
        "method_tag": method_tag,
        "allowed_categories": allowed_categories,
        "allowed_types": allowed_types,
        "required": required,
        "priority": priority,
    }


def build_slot_plan(
    checkin: dict[str, Any],
    focus: str,
    readiness_category: str,
    goal_today: str,
    workout_modifier: str,
    template_key: str,
    deload: bool,
    session_type: str,
) -> list[dict[str, Any]]:
    soreness = int(checkin.get("soreness", 5))
    combat_later_today = bool(checkin.get("combat_later_today", False))
    combat_last_24h = bool(checkin.get("combat_last_24h", False))
    hard_sparring_last_24h = bool(checkin.get("hard_sparring_last_24h", False))

    if session_type == "Post-Workout Stretch / Mobility":
        return post_workout_mobility_slot_plan(workout_modifier)

    if session_type == "Mobility & Stretch Only":
        return recovery_slot_plan(workout_modifier)

    if session_type == "Technical Cardio / Footwork":
        return technical_cardio_slot_plan(workout_modifier)

    if template_key == "recovery" or readiness_category == "Red" or goal_today == "recovery":
        return recovery_slot_plan(workout_modifier)

    if deload:
        return deload_slot_plan(focus, workout_modifier)

    if readiness_category == "Orange" or soreness >= 8 or hard_sparring_last_24h:
        return light_slot_plan(
            focus=focus,
            workout_modifier=workout_modifier,
            combat_later_today=combat_later_today,
            combat_last_24h=combat_last_24h,
        )

    if template_key == "accessory" or focus == "Accessory / pump":
        return accessory_slot_plan(workout_modifier)

    if focus == "Lower emphasis":
        return lower_strength_slot_plan(
            readiness_category=readiness_category,
            goal_today=goal_today,
            workout_modifier=workout_modifier,
            combat_later_today=combat_later_today,
        )

    if focus == "Upper emphasis":
        return upper_strength_slot_plan(
            readiness_category=readiness_category,
            goal_today=goal_today,
            workout_modifier=workout_modifier,
            combat_later_today=combat_later_today,
        )

    if focus == "Posterior chain / grappling":
        return grappling_strength_slot_plan(
            readiness_category=readiness_category,
            goal_today=goal_today,
            workout_modifier=workout_modifier,
            combat_later_today=combat_later_today,
        )

    return full_body_slot_plan(
        readiness_category=readiness_category,
        goal_today=goal_today,
        workout_modifier=workout_modifier,
        combat_later_today=combat_later_today,
    )


def full_body_slot_plan(
    readiness_category: str,
    goal_today: str,
    workout_modifier: str,
    combat_later_today: bool,
) -> list[dict[str, Any]]:
    use_isometric = readiness_category == "Yellow" or combat_later_today
    use_dynamic = readiness_category == "Green" and goal_today == "push" and not combat_later_today

    plan = [
        slot("Movement Prep", "mobility", "movement_prep", "movement_prep", ["mobility"], required=True, priority=1),
    ]

    if use_dynamic:
        plan.append(slot("Dynamic Effort", "hinge", "dynamic_effort", "dynamic_effort", ["gpp"], priority=2))

    if use_isometric:
        plan.append(slot("Strength Exposure", "hinge", "lower_isometric_strength", "overcoming_isometric", ["secondary_lift"], required=True, priority=2))
    else:
        plan.append(slot("Main Strength", "hinge", "main_strength", "submax_strength", ["main_lift"], required=True, priority=2))

    plan.extend(
        [
            slot("Upper Strength", "horizontal_push", "main_strength", "submax_strength", ["main_lift", "secondary_lift"], required=True, priority=3),
            slot("Upper Back", "vertical_pull", "upper_back_accessory", "repeated_effort", ["main_lift", "secondary_lift", "accessory"], required=True, priority=4),
            slot("Single-Leg / Lower Accessory", "single_leg", "single_leg_strength", "repeated_effort", ["accessory"], priority=5),
            slot("Grip / GPP", "carry_grip", "grip_gpp", "gpp", ["gpp"], priority=6),
            slot("Core", "core", "core_anti_rotation", "repeated_effort", ["accessory", "recovery_accessory"], priority=7),
            slot("Mobility Finish", "mobility", "hip_controlled_mobility", "mobility_control", ["mobility"], priority=8),
        ]
    )

    if workout_modifier in {"fun", "chaos"}:
        plan.append(slot("Technical Cardio", "conditioning", "technical_cardio", "skill_conditioning", ["cardio"], priority=9))

    return plan


def lower_strength_slot_plan(
    readiness_category: str,
    goal_today: str,
    workout_modifier: str,
    combat_later_today: bool,
) -> list[dict[str, Any]]:
    use_isometric = combat_later_today or readiness_category == "Yellow"
    use_dynamic = readiness_category == "Green" and goal_today == "push" and not combat_later_today

    plan = [
        slot("Movement Prep", "mobility", "movement_prep", "movement_prep", ["mobility"], required=True, priority=1),
    ]

    if use_dynamic:
        plan.append(slot("Dynamic Lower", "hinge", "dynamic_effort", "dynamic_effort", ["gpp"], priority=2))

    if use_isometric:
        plan.append(slot("Lower Isometric Strength", "single_leg", "lower_isometric_strength", "overcoming_isometric", ["secondary_lift"], required=True, priority=2))
    else:
        plan.append(slot("Main Squat Strength", "squat", "main_strength", "submax_strength", ["main_lift"], required=True, priority=2))

    plan.extend(
        [
            slot("Posterior Chain", "hinge", "posterior_chain_accessory", "repeated_effort", ["secondary_lift", "accessory"], required=True, priority=3),
            slot("Single-Leg Strength", "single_leg", "single_leg_strength", "repeated_effort", ["accessory"], priority=4),
            slot("Hip Accessory", "hip_accessory", "hip_accessory", "repeated_effort", ["accessory"], priority=5),
            slot("Core Brace", "core", "trunk_strength", "repeated_effort", ["accessory"], priority=6),
            slot("Hip Mobility", "mobility", "hip_controlled_mobility", "mobility_control", ["mobility"], priority=7),
            slot("Static Hip Stretch", "stretch", "static_hip_stretch", "recovery", ["stretch"], priority=8),
        ]
    )

    if workout_modifier in {"fun", "chaos"}:
        plan.append(slot("Loaded GPP", "conditioning", "gpp_conditioning", "gpp", ["gpp", "cardio"], priority=9))

    return plan


def upper_strength_slot_plan(
    readiness_category: str,
    goal_today: str,
    workout_modifier: str,
    combat_later_today: bool,
) -> list[dict[str, Any]]:
    use_isometric = combat_later_today or readiness_category == "Yellow"

    plan = [
        slot("Movement Prep", "mobility", "movement_prep", "movement_prep", ["mobility"], required=True, priority=1),
    ]

    if use_isometric:
        plan.append(slot("Upper Isometric Strength", "horizontal_push", "upper_isometric_strength", "overcoming_isometric", ["secondary_lift", "accessory"], required=True, priority=2))
    else:
        plan.append(slot("Main Press Strength", "horizontal_push", "main_strength", "submax_strength", ["main_lift"], required=True, priority=2))

    plan.extend(
        [
            slot("Main Pull Strength", "vertical_pull", "main_strength", "submax_strength", ["main_lift", "accessory"], required=True, priority=3),
            slot("Upper Back", "horizontal_pull", "upper_back_accessory", "repeated_effort", ["secondary_lift", "accessory"], priority=4),
            slot("Shoulder Accessory", "shoulder_accessory", "shoulder_accessory", "repeated_effort", ["accessory"], priority=5),
            slot("Arm / Grip Accessory", "forearm_grip", "arm_grip_accessory", "repeated_effort", ["accessory"], priority=6),
            slot("Core Anti-Rotation", "core", "core_anti_rotation", "repeated_effort", ["accessory"], priority=7),
            slot("Shoulder Mobility", "mobility", "shoulder_controlled_mobility", "mobility_control", ["mobility", "stretch"], priority=8),
        ]
    )

    if workout_modifier in {"fun", "chaos"}:
        plan.append(slot("Technical Cardio", "conditioning", "technical_cardio", "skill_conditioning", ["cardio"], priority=9))

    return plan


def grappling_strength_slot_plan(
    readiness_category: str,
    goal_today: str,
    workout_modifier: str,
    combat_later_today: bool,
) -> list[dict[str, Any]]:
    use_isometric = readiness_category == "Yellow" or combat_later_today
    use_dynamic = readiness_category == "Green" and goal_today == "push" and not combat_later_today

    plan = [
        slot("Grappling Movement Prep", "mobility", "movement_prep", "movement_prep", ["mobility"], required=True, priority=1),
    ]

    if use_dynamic:
        plan.append(slot("Dynamic Hinge", "hinge", "dynamic_effort", "dynamic_effort", ["gpp"], priority=2))

    if use_isometric:
        plan.append(slot("Isometric Pull / Hinge", "horizontal_pull", "upper_isometric_strength", "overcoming_isometric", ["secondary_lift", "accessory"], required=True, priority=2))
    else:
        plan.append(slot("Main Hinge Strength", "hinge", "main_strength", "submax_strength", ["main_lift"], required=True, priority=2))

    plan.extend(
        [
            slot("Main Pull", "vertical_pull", "main_strength", "submax_strength", ["main_lift", "accessory"], required=True, priority=3),
            slot("Posterior Chain", "posterior_chain", "posterior_chain_accessory", "repeated_effort", ["secondary_lift", "accessory"], priority=4),
            slot("Upper Back", "horizontal_pull", "upper_back_accessory", "repeated_effort", ["secondary_lift", "accessory"], priority=5),
            slot("Grip / Carry", "carry_grip", "grip_gpp", "gpp", ["gpp"], priority=6),
            slot("Neck Prep", "neck", "neck_prep", "yielding_isometric", ["recovery_accessory"], priority=7),
            slot("Core Anti-Rotation", "core", "core_anti_rotation", "repeated_effort", ["accessory"], priority=8),
            slot("Hip Mobility", "mobility", "hip_controlled_mobility", "mobility_control", ["mobility"], priority=9),
        ]
    )

    if workout_modifier in {"fun", "chaos"}:
        plan.append(slot("Technical Cardio", "conditioning", "technical_cardio", "skill_conditioning", ["cardio"], priority=10))

    return plan


def accessory_slot_plan(workout_modifier: str) -> list[dict[str, Any]]:
    plan = [
        slot("Movement Prep", "mobility", "movement_prep", "movement_prep", ["mobility"], required=True, priority=1),
        slot("Upper Back", "horizontal_pull", "upper_back_accessory", "repeated_effort", ["secondary_lift", "accessory"], required=True, priority=2),
        slot("Posterior Chain", "posterior_chain", "posterior_chain_accessory", "repeated_effort", ["accessory"], required=True, priority=3),
        slot("Shoulders", "shoulder_accessory", "shoulder_accessory", "repeated_effort", ["accessory"], priority=4),
        slot("Arms / Grip", "forearm_grip", "arm_grip_accessory", "repeated_effort", ["accessory"], priority=5),
        slot("Core", "core", "trunk_strength", "repeated_effort", ["accessory"], priority=6),
        slot("Grip GPP", "carry_grip", "grip_gpp", "gpp", ["gpp"], priority=7),
        slot("Hip Accessory", "hip_accessory", "hip_accessory", "repeated_effort", ["accessory"], priority=8),
        slot("Mobility Finish", "mobility", "upper_body_mobility", "recovery", ["mobility", "stretch"], priority=9),
    ]

    if workout_modifier in {"fun", "chaos"}:
        plan.append(slot("Technical Cardio", "conditioning", "technical_cardio", "skill_conditioning", ["cardio"], priority=10))

    return plan


def light_slot_plan(
    focus: str,
    workout_modifier: str,
    combat_later_today: bool,
    combat_last_24h: bool,
) -> list[dict[str, Any]]:
    return [
        slot("Movement Prep", "mobility", "movement_prep", "movement_prep", ["mobility"], required=True, priority=1),
        slot("Technical Cardio", "conditioning", "technical_cardio", "skill_conditioning", ["cardio"], required=True, priority=2),
        slot("Upper Back", "horizontal_pull", "upper_back_accessory", "repeated_effort", ["accessory", "secondary_lift"], priority=3),
        slot("Posterior Chain Blood Flow", "posterior_chain", "posterior_chain_blood_flow", "repeated_effort", ["accessory"], priority=4),
        slot("Core Breathing", "core", "core_breathing", "recovery", ["recovery_accessory"], priority=5),
        slot("Neck Prep", "neck", "neck_prep", "yielding_isometric", ["recovery_accessory"], priority=6),
        slot("Hip Mobility", "mobility", "hip_controlled_mobility", "mobility_control", ["mobility"], priority=7),
        slot("T-Spine Mobility", "mobility", "t_spine_mobility", "mobility_control", ["mobility"], priority=8),
    ]


def deload_slot_plan(focus: str, workout_modifier: str) -> list[dict[str, Any]]:
    return [
        slot("Movement Prep", "mobility", "movement_prep", "movement_prep", ["mobility"], required=True, priority=1),
        slot("Low-Fatigue Strength", "horizontal_pull", "upper_back_accessory", "repeated_effort", ["accessory", "secondary_lift"], required=True, priority=2),
        slot("Posterior Chain Blood Flow", "posterior_chain", "posterior_chain_blood_flow", "repeated_effort", ["accessory"], priority=3),
        slot("Grip / Carry", "carry_grip", "grip_gpp", "gpp", ["gpp"], priority=4),
        slot("Core Breathing", "core", "core_breathing", "recovery", ["recovery_accessory"], priority=5),
        slot("Hip Mobility", "mobility", "hip_controlled_mobility", "mobility_control", ["mobility"], priority=6),
        slot("T-Spine Mobility", "mobility", "t_spine_mobility", "mobility_control", ["mobility"], priority=7),
        slot("Static Stretch", "stretch", "static_hip_stretch", "recovery", ["stretch"], priority=8),
    ]


def recovery_slot_plan(workout_modifier: str) -> list[dict[str, Any]]:
    plan = [
        slot("Easy Cardio", "conditioning", "zone2_cardio", "recovery", ["cardio"], required=True, priority=1),
        slot("Hip Mobility", "mobility", "hip_controlled_mobility", "mobility_control", ["mobility"], required=True, priority=2),
        slot("T-Spine Mobility", "mobility", "t_spine_mobility", "mobility_control", ["mobility"], priority=3),
        slot("Shoulder Mobility", "mobility", "shoulder_controlled_mobility", "mobility_control", ["mobility", "stretch"], priority=4),
        slot("Core Breathing", "core", "core_breathing", "recovery", ["recovery_accessory"], priority=5),
        slot("Neck Prep", "neck", "neck_prep", "yielding_isometric", ["recovery_accessory"], priority=6),
        slot("Upper Body Mobility", "stretch", "upper_body_mobility", "recovery", ["mobility", "stretch"], priority=7),
        slot("Static Hip Stretch", "stretch", "static_hip_stretch", "recovery", ["stretch"], priority=8),
        slot("Positional Breathing", "mobility", "positional_breathing", "recovery", ["mobility"], priority=9),
    ]

    if workout_modifier in {"fun", "chaos"}:
        plan.insert(1, slot("Technical Cardio", "conditioning", "technical_cardio", "skill_conditioning", ["cardio"], priority=2))

    if workout_modifier == "focus":
        return [item for item in plan if item["priority"] <= 6]

    return plan


def post_workout_mobility_slot_plan(workout_modifier: str) -> list[dict[str, Any]]:
    return [
        slot("Downshift Breathing", "mobility", "positional_breathing", "recovery", ["mobility"], required=True, priority=1),
        slot("Hip Reset", "mobility", "hip_controlled_mobility", "mobility_control", ["mobility"], required=True, priority=2),
        slot("T-Spine Reset", "mobility", "t_spine_mobility", "mobility_control", ["mobility"], required=True, priority=3),
        slot("Upper Body Mobility", "stretch", "upper_body_mobility", "recovery", ["mobility", "stretch"], priority=4),
        slot("Static Hip Stretch", "stretch", "static_hip_stretch", "recovery", ["stretch"], priority=5),
        slot("Shoulder Mobility", "mobility", "shoulder_controlled_mobility", "mobility_control", ["mobility", "stretch"], priority=6),
        slot("Neck Prep", "neck", "neck_prep", "yielding_isometric", ["recovery_accessory"], priority=7),
    ]


def technical_cardio_slot_plan(workout_modifier: str) -> list[dict[str, Any]]:
    return [
        slot("Technical Cardio", "conditioning", "technical_cardio", "skill_conditioning", ["cardio"], required=True, priority=1),
        slot("Footwork Cardio", "conditioning", "technical_cardio", "skill_conditioning", ["cardio"], priority=2),
        slot("Hip Mobility", "mobility", "hip_controlled_mobility", "mobility_control", ["mobility"], priority=3),
        slot("T-Spine Mobility", "mobility", "t_spine_mobility", "mobility_control", ["mobility"], priority=4),
        slot("Core Breathing", "core", "core_breathing", "recovery", ["recovery_accessory"], priority=5),
        slot("Static Stretch", "stretch", "static_hip_stretch", "recovery", ["stretch"], priority=6),
    ]


def build_workout_from_slots(
    slot_plan: list[dict[str, Any]],
    readiness_category: str,
    focus: str,
    workout_modifier: str,
    fatigue_budget: int,
    time_available: int,
) -> list[dict[str, Any]]:
    selected = []
    avoid_names = set()
    current_fatigue = 0

    sorted_slots = sorted(slot_plan, key=lambda item: item["priority"])

    for item in sorted_slots:
        exercise = select_exercise(
            desired_pattern=item["desired_pattern"],
            readiness_category=readiness_category,
            focus=focus,
            workout_modifier=workout_modifier,
            allowed_categories=item.get("allowed_categories"),
            allowed_prescription_types=item.get("allowed_types"),
            avoid_names=avoid_names,
            desired_session_slot=item.get("session_slot"),
            desired_method_tag=item.get("method_tag"),
        )

        exercise_fatigue = int(exercise.get("fatigue_points", 3))
        would_exceed_budget = current_fatigue + exercise_fatigue > fatigue_budget

        if item.get("required", False) or not would_exceed_budget:
            selected.append(add_slot_metadata(exercise, item))
            avoid_names.add(exercise["exercise_name"])
            current_fatigue += exercise_fatigue

    return trim_by_time_and_fatigue(selected, time_available)


def add_slot_metadata(exercise: dict[str, Any], slot_item: dict[str, Any]) -> dict[str, Any]:
    updated = exercise.copy()
    updated["selected_for_slot"] = slot_item["name"]
    return updated


def finalize_selected_exercises(
    exercises: list[dict[str, Any]],
    readiness_category: str,
    workout_modifier: str,
    session_type: str,
) -> list[dict[str, Any]]:
    return [
        apply_training_prescription(exercise, readiness_category, workout_modifier, session_type)
        for exercise in exercises
    ]


def apply_training_prescription(
    exercise: dict[str, Any],
    readiness_category: str,
    workout_modifier: str,
    session_type: str,
) -> dict[str, Any]:
    updated = exercise.copy()

    name = updated["exercise_name"]
    category = updated["exercise_category"]
    prescription_type = updated["prescription_type"]
    method_tag = updated.get("method_tag", "")

    if session_type in {"Post-Workout Stretch / Mobility", "Mobility & Stretch Only"}:
        if prescription_type in {"mobility", "stretch"}:
            updated["target_rpe"] = min(float(updated.get("target_rpe", 4.0)), 4.5)
        return updated

    if category == "main_lift":
        fallback = DEFAULT_TRAINING_LOADS.get(name, 0)
        updated["planned_weight"] = safe_main_lift_load(name, readiness_category, fallback)

        if readiness_category == "Green":
            updated["planned_sets"] = 4 if workout_modifier != "focus" else 3
            updated["target_rpe"] = 8.0
        elif readiness_category == "Yellow":
            updated["planned_sets"] = 3
            updated["target_rpe"] = 7.5
        else:
            updated["planned_sets"] = 2
            updated["target_rpe"] = 6.5

    elif method_tag == "overcoming_isometric":
        if readiness_category == "Green":
            updated["planned_sets"] = 4
            updated["target_rpe"] = 8.5
            updated["hold_seconds"] = 5
        elif readiness_category == "Yellow":
            updated["planned_sets"] = 3
            updated["target_rpe"] = 8.0
            updated["hold_seconds"] = 5
        else:
            updated["planned_sets"] = 2
            updated["target_rpe"] = 6.5
            updated["hold_seconds"] = 4

    elif category == "secondary_lift":
        if readiness_category == "Green":
            updated["planned_sets"] = 3
            updated["target_rpe"] = max(float(updated.get("target_rpe", 7.5)), 7.5)
        elif readiness_category == "Yellow":
            updated["planned_sets"] = 3
            updated["target_rpe"] = min(float(updated.get("target_rpe", 7.0)), 7.5)
        else:
            updated["planned_sets"] = 2
            updated["target_rpe"] = min(float(updated.get("target_rpe", 6.5)), 6.5)

    elif category in {"accessory", "gpp"}:
        if workout_modifier == "focus":
            updated["planned_sets"] = max(1, min(int(updated.get("planned_sets", 2)), 2))
        elif workout_modifier == "fun":
            updated["planned_sets"] = min(int(updated.get("planned_sets", 3)) + 1, 4)

    elif prescription_type in {"mobility", "stretch", "cardio", "cardio_skill"}:
        updated["target_rpe"] = min(float(updated.get("target_rpe", 5.0)), 5.5)

    if prescription_type == "cardio_skill" and readiness_category in {"Orange", "Red"}:
        updated["target_rpe"] = min(float(updated.get("target_rpe", 5.0)), 5.0)
        updated["intensity_target"] = "RPE 4-5, technical quality only"

    if workout_modifier == "chaos" and category in {"accessory", "gpp", "mobility", "cardio"}:
        updated["notes"] = updated.get("notes", "") + " Chaos mode: keep it safe, but make the variation interesting."

    return updated


def determine_workout_type(
    readiness_category: str,
    focus: str,
    goal_today: str,
    deload: bool,
    template_key: str,
    session_type: str,
    exercises: list[dict[str, Any]],
) -> str:
    if session_type != "Main Workout":
        return session_type

    method_tags = {exercise.get("method_tag", "") for exercise in exercises}

    if deload:
        return "Deload / Low-Fatigue Full Body"

    if readiness_category == "Red" or goal_today == "recovery" or template_key == "recovery":
        return "Recovery / Mobility"

    if "overcoming_isometric" in method_tags:
        return "Isometric Strength / Combat Support"

    if "dynamic_effort" in method_tags:
        return "Dynamic Effort / Athletic Strength"

    if focus == "Accessory / pump":
        return "Accessory / Armor Building"

    if readiness_category == "Orange":
        return "Light / Technical Support"

    return "Full-Body Strength"


def build_generation_reason(
    readiness_category: str,
    focus: str,
    goal_today: str,
    workout_modifier: str,
    fatigue_budget: int,
    checkin: dict[str, Any],
    deload: bool,
    exercises: list[dict[str, Any]],
    session_type: str,
) -> str:
    estimated_fatigue = sum(int(exercise.get("fatigue_points", 3)) for exercise in exercises)

    reason = (
        f"The app built this {session_type.lower()} using a fatigue budget of {fatigue_budget} "
        f"and selected {estimated_fatigue} estimated fatigue points. "
    )

    reason += f"Readiness is {readiness_category}, focus is {focus}, and goal today is {goal_today}. "

    if session_type == "Post-Workout Stretch / Mobility":
        reason += "Because this is a second session, the app biased downregulation, mobility, breathing, and low-fatigue tissue work. "
    elif session_type == "Technical Cardio / Footwork":
        reason += "The app biased light combat-skill cardio instead of machine-only conditioning. "

    if deload:
        reason += "Deload logic is active, so the app reduced heavy strength exposure. "

    if checkin.get("combat_later_today"):
        reason += "Because combat training is later today, the app biased lower-fatigue and technical work. "

    if checkin.get("hard_sparring_last_24h"):
        reason += "Because hard sparring/rolling happened recently, the app reduced high-fatigue selections. "

    if workout_modifier == "focus":
        reason += "Focus mode kept the session tighter and more direct."
    elif workout_modifier == "fun":
        reason += "Fun mode allowed more variety and technical-cardio options."
    elif workout_modifier == "chaos":
        reason += "Chaos mode biased unusual but still safe options."
    else:
        reason += "Normal mode balanced strength, combat support, and recovery."

    return reason


def is_low_fatigue_exercise(exercise: dict[str, Any]) -> bool:
    prescription_type = exercise.get("prescription_type", "strength")
    fatigue_points = int(exercise.get("fatigue_points", 3))
    target_rpe = float(exercise.get("target_rpe", 7.0))

    if fatigue_points <= 2:
        return True

    if prescription_type in {"mobility", "stretch", "cardio", "cardio_skill"} and target_rpe <= 5.5:
        return True

    return False


def trim_by_time_and_fatigue(
    exercises: list[dict[str, Any]],
    time_available: int,
) -> list[dict[str, Any]]:
    if not exercises:
        return exercises

    low_fatigue_count = sum(1 for exercise in exercises if is_low_fatigue_exercise(exercise))
    low_fatigue_ratio = low_fatigue_count / len(exercises)

    if low_fatigue_ratio >= 0.75:
        if time_available <= 30:
            return exercises[:5]
        if time_available <= 45:
            return exercises[:7]
        if time_available <= 60:
            return exercises[:9]
        return exercises[:10]

    if low_fatigue_ratio >= 0.50:
        if time_available <= 30:
            return exercises[:4]
        if time_available <= 45:
            return exercises[:6]
        if time_available <= 60:
            return exercises[:8]
        return exercises[:9]

    if time_available <= 30:
        return exercises[:4]

    if time_available <= 45:
        return exercises[:5]

    if time_available <= 60:
        return exercises[:6]

    return exercises[:7]
