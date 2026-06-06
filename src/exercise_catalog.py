from typing import Any


def exercise(
    name: str,
    movement_pattern: str,
    exercise_category: str,
    prescription_type: str,
    equipment: str,
    modality: str,
    fatigue_cost: str,
    combat_transfer: str,
    difficulty: str,
    joint_stress: str,
    default_sets: int,
    reps_min: int,
    reps_max: int,
    target_rpe: float,
    notes: str,
    tags: list[str] | None = None,
    duration_minutes: int | None = None,
    hold_seconds: int | None = None,
    distance: str = "",
    heart_rate_target: str = "",
    intensity_target: str = "",
    side: str = "",
) -> dict[str, Any]:
    return {
        "exercise_name": name,
        "movement_pattern": movement_pattern,
        "exercise_category": exercise_category,
        "prescription_type": prescription_type,
        "equipment": equipment,
        "modality": modality,
        "fatigue_cost": fatigue_cost,
        "combat_transfer": combat_transfer,
        "difficulty": difficulty,
        "joint_stress": joint_stress,
        "planned_sets": default_sets,
        "planned_reps_min": reps_min,
        "planned_reps_max": reps_max,
        "planned_weight": 0,
        "target_rpe": target_rpe,
        "notes": notes,
        "tags": tags or [],
        "duration_minutes": duration_minutes,
        "hold_seconds": hold_seconds,
        "distance": distance,
        "heart_rate_target": heart_rate_target,
        "intensity_target": intensity_target,
        "side": side,
    }


EXERCISE_CATALOG = [
    # Main lifts
    exercise("Trap Bar Deadlift", "hinge", "main_lift", "strength", "trap bar", "free weight", "high", "high", "high", "medium", 3, 3, 5, 8.0, "Main hinge strength. Smooth reps only.", ["posterior_chain", "grappling", "strength"]),
    exercise("Bench Press", "horizontal_push", "main_lift", "strength", "barbell", "free weight", "medium", "medium", "medium", "medium", 3, 4, 6, 8.0, "Main press. Do not grind reps.", ["upper", "strength", "press"]),
    exercise("Squat", "squat", "main_lift", "strength", "barbell", "free weight", "high", "high", "high", "high", 3, 4, 6, 8.0, "Main squat pattern. Keep positions clean.", ["lower", "strength"]),
    exercise("Weighted Pull-Up", "vertical_pull", "main_lift", "strength", "pull-up bar", "weighted bodyweight", "high", "high", "high", "medium", 3, 3, 6, 8.0, "Added weight only. Prioritize clean reps.", ["upper", "grip", "grappling", "pull"]),
    exercise("Weighted Chin-Up", "vertical_pull", "main_lift", "strength", "pull-up bar", "weighted bodyweight", "high", "high", "high", "medium", 3, 3, 6, 8.0, "Added weight only. Chin-up variation for pulling strength.", ["upper", "grip", "grappling", "pull"]),

    # Squat pattern substitutions
    exercise("Hack Squat", "squat", "secondary_lift", "strength", "machine", "machine", "medium", "medium", "medium", "medium", 3, 8, 12, 7.5, "Squat pattern with more external stability.", ["lower", "modality_swap"]),
    exercise("Leg Press", "squat", "secondary_lift", "strength", "machine", "machine", "medium", "medium", "low", "medium", 3, 10, 15, 7.5, "Lower-body volume with less bracing demand.", ["lower", "modality_swap"]),
    exercise("Zercher Squat", "squat", "secondary_lift", "strength", "barbell", "free weight", "high", "high", "high", "medium", 3, 5, 8, 7.5, "Squat variation with trunk and upper-back demand.", ["lower", "grappling", "modality_swap"]),
    exercise("Front Squat", "squat", "secondary_lift", "strength", "barbell", "free weight", "high", "medium", "high", "medium", 3, 4, 8, 7.5, "Upright squat variation. Keep it technical.", ["lower", "modality_swap"]),
    exercise("Goblet Squat", "squat", "accessory", "strength", "dumbbell or kettlebell", "free weight", "low", "medium", "low", "low", 3, 8, 12, 6.5, "Light squat pattern. Good for lower-readiness days.", ["lower", "light"]),

    # Hinge / posterior chain
    exercise("Romanian Deadlift", "hinge", "secondary_lift", "strength", "barbell or dumbbells", "free weight", "medium", "high", "medium", "medium", 3, 6, 10, 7.5, "Hamstrings, glutes, and trunk tension.", ["posterior_chain", "grappling"]),
    exercise("Barbell Hip Thrust", "hinge", "secondary_lift", "strength", "barbell", "free weight", "medium", "medium", "medium", "low", 3, 8, 12, 7.5, "Glute strength without as much spinal fatigue.", ["posterior_chain", "modality_swap"]),
    exercise("Kettlebell Swing", "hinge", "gpp", "conditioning", "kettlebell", "ballistic", "medium", "high", "medium", "medium", 4, 10, 20, 7.0, "Explosive hinge conditioning. Keep reps crisp.", ["posterior_chain", "athletic", "conditioning"]),
    exercise("Back Extension", "posterior_chain", "accessory", "bodyweight", "back extension bench", "bodyweight or loaded", "medium", "high", "medium", "low", 3, 10, 15, 7.0, "Posterior-chain support and low-back endurance.", ["posterior_chain", "grappling"]),
    exercise("Reverse Hyper", "posterior_chain", "accessory", "strength", "reverse hyper machine", "machine", "low", "medium", "low", "low", 3, 12, 20, 6.5, "Posterior-chain blood flow and low-back support.", ["posterior_chain", "recovery"]),
    exercise("Hamstring Curl", "posterior_chain", "accessory", "strength", "machine", "machine", "low", "medium", "low", "low", 3, 10, 15, 7.0, "Hamstring isolation with low systemic fatigue.", ["posterior_chain", "accessory"]),

    # Upper push
    exercise("DB Bench Press", "horizontal_push", "secondary_lift", "strength", "dumbbells", "free weight", "medium", "medium", "medium", "low", 3, 8, 12, 7.5, "Pressing volume with more freedom than barbell bench.", ["upper", "press", "modality_swap"]),
    exercise("Incline DB Bench", "horizontal_push", "secondary_lift", "strength", "dumbbells", "free weight", "medium", "medium", "medium", "low", 3, 8, 12, 7.5, "Incline pressing for upper chest and shoulders.", ["upper", "press"]),
    exercise("Push-Up", "horizontal_push", "accessory", "bodyweight", "floor", "bodyweight", "low", "medium", "low", "low", 3, 10, 20, 7.0, "Bodyweight pressing volume.", ["upper", "press", "light"]),
    exercise("Landmine Press", "vertical_push", "secondary_lift", "strength", "landmine", "free weight", "medium", "medium", "medium", "low", 3, 6, 10, 7.5, "Athletic pressing without excessive shoulder stress.", ["upper", "press", "athletic"]),
    exercise("DB Shoulder Press", "vertical_push", "secondary_lift", "strength", "dumbbells", "free weight", "medium", "medium", "medium", "medium", 3, 8, 12, 7.5, "Vertical pressing volume.", ["upper", "press"]),
    exercise("Lateral Raise", "shoulder_accessory", "accessory", "strength", "dumbbells or cable", "isolation", "low", "low", "low", "low", 3, 12, 20, 7.0, "Shoulder accessory for delts.", ["shoulders", "accessory", "pump"]),
    exercise("Face Pull", "shoulder_accessory", "accessory", "strength", "cable or band", "cable", "low", "medium", "low", "low", 3, 12, 20, 6.5, "Rear delt and shoulder health.", ["shoulders", "upper_back", "recovery"]),

    # Upper pull
    exercise("Chest-Supported Row", "horizontal_pull", "secondary_lift", "strength", "machine or bench + dumbbells", "supported pull", "medium", "high", "medium", "low", 3, 8, 12, 8.0, "Upper-back strength without taxing the low back.", ["upper", "grappling", "posture"]),
    exercise("DB Row", "horizontal_pull", "accessory", "strength", "dumbbell", "free weight", "medium", "high", "medium", "low", 3, 8, 12, 8.0, "Rowing volume for lats and upper back.", ["upper", "grappling"]),
    exercise("Cable Row", "horizontal_pull", "accessory", "strength", "cable machine", "machine", "low", "medium", "low", "low", 3, 10, 15, 7.0, "Low-fatigue rowing volume.", ["upper", "modality_swap"]),
    exercise("Seal Row", "horizontal_pull", "secondary_lift", "strength", "bench + barbell/dumbbells", "supported pull", "medium", "high", "medium", "low", 3, 8, 12, 7.5, "Strict upper-back row.", ["upper", "grappling"]),
    exercise("Pull-Up", "vertical_pull", "accessory", "bodyweight", "pull-up bar", "bodyweight", "medium", "high", "medium", "medium", 3, 5, 10, 8.0, "Bodyweight pulling volume.", ["upper", "grip", "grappling"]),
    exercise("Chin-Up", "vertical_pull", "accessory", "bodyweight", "pull-up bar", "bodyweight", "medium", "high", "medium", "medium", 3, 5, 10, 8.0, "Bodyweight pulling with more biceps involvement.", ["upper", "grip", "grappling"]),
    exercise("Neutral-Grip Pull-Up", "vertical_pull", "accessory", "bodyweight", "pull-up bar", "bodyweight", "medium", "high", "medium", "low", 3, 5, 10, 7.5, "Joint-friendly vertical pull variation.", ["upper", "grip", "grappling"]),
    exercise("Lat Pulldown", "vertical_pull", "accessory", "strength", "cable machine", "machine", "low", "medium", "low", "low", 3, 8, 12, 7.0, "Vertical pull substitution when pull-ups are not ideal.", ["upper", "modality_swap"]),

    # Single-leg / lower accessories
    exercise("Step-Up", "single_leg", "accessory", "strength", "box + dumbbells optional", "single-leg", "medium", "medium", "medium", "low", 2, 8, 12, 7.0, "Single-leg strength and balance.", ["lower", "single_leg"]),
    exercise("Split Squat", "single_leg", "accessory", "strength", "dumbbells optional", "single-leg", "medium", "medium", "medium", "medium", 3, 8, 12, 7.5, "Single-leg strength with trunk control.", ["lower", "single_leg"]),
    exercise("Reverse Lunge", "single_leg", "accessory", "strength", "dumbbells optional", "single-leg", "medium", "medium", "medium", "low", 3, 8, 12, 7.0, "Single-leg work with controlled fatigue.", ["lower", "single_leg"]),
    exercise("Cossack Squat", "single_leg", "accessory", "mobility", "bodyweight or kettlebell", "mobility strength", "low", "medium", "medium", "low", 2, 5, 8, 5.0, "Lateral hip mobility and leg strength.", ["hips", "mobility", "single_leg"], side="each side", intensity_target="controlled range"),

    # Carries / grip
    exercise("Farmer Carry", "carry_grip", "gpp", "carry", "dumbbells or kettlebells", "loaded carry", "medium", "high", "medium", "low", 3, 30, 60, 7.5, "Grip, trunk, and posture.", ["grip", "gpp", "grappling"], distance="30-60 sec"),
    exercise("Suitcase Carry", "carry_grip", "gpp", "carry", "dumbbell or kettlebell", "loaded carry", "medium", "high", "medium", "low", 3, 30, 60, 7.0, "Anti-lateral flexion and grip.", ["grip", "core", "gpp"], distance="30-60 sec each side", side="each side"),
    exercise("Front Rack Carry", "carry_grip", "gpp", "carry", "kettlebells or dumbbells", "loaded carry", "medium", "high", "medium", "medium", 3, 20, 45, 7.5, "Upper-back, trunk, and breathing under load.", ["grip", "core", "grappling"], distance="20-45 sec"),
    exercise("Dead Hang", "carry_grip", "gpp", "carry", "pull-up bar", "bodyweight grip", "low", "high", "low", "low", 3, 20, 45, 7.0, "Grip endurance and shoulder decompression.", ["grip", "shoulders", "grappling"], distance="20-45 sec"),
    exercise("Plate Pinch Hold", "carry_grip", "gpp", "carry", "plates", "grip hold", "low", "high", "low", "low", 3, 20, 40, 7.0, "Pinch grip endurance.", ["grip", "forearms"], distance="20-40 sec"),

    # Arms / forearms
    exercise("Hammer Curl", "forearm_grip", "accessory", "strength", "dumbbells", "isolation", "low", "medium", "low", "low", 2, 10, 15, 7.5, "Arm and grip support.", ["grip", "arms", "pump"]),
    exercise("Reverse Curl", "forearm_grip", "accessory", "strength", "barbell or dumbbells", "isolation", "low", "medium", "low", "low", 2, 10, 15, 7.0, "Brachialis and forearm strength.", ["grip", "arms", "forearms"]),
    exercise("Reverse Wrist Curl", "forearm_grip", "accessory", "strength", "dumbbell or barbell", "isolation", "low", "medium", "low", "low", 2, 12, 20, 7.0, "Forearm balance.", ["grip", "forearms"]),
    exercise("Wrist Curl", "forearm_grip", "accessory", "strength", "dumbbell or barbell", "isolation", "low", "medium", "low", "low", 2, 12, 20, 7.0, "Forearm support.", ["grip", "forearms"]),
    exercise("Triceps Pressdown", "arm_accessory", "accessory", "strength", "cable", "isolation", "low", "low", "low", "low", 3, 10, 15, 7.0, "Triceps accessory volume.", ["arms", "pump"]),

    # Core / trunk
    exercise("GHR Sit-Up", "core", "accessory", "bodyweight", "GHR bench", "bodyweight", "medium", "medium", "medium", "medium", 2, 8, 12, 7.0, "Core strength.", ["core", "trunk"]),
    exercise("Hanging Knee Raise", "core", "accessory", "bodyweight", "pull-up bar", "bodyweight", "medium", "medium", "medium", "low", 2, 8, 12, 7.0, "Abs and hip flexor control.", ["core", "grip"]),
    exercise("Ab Wheel", "core", "accessory", "bodyweight", "ab wheel", "bodyweight", "medium", "medium", "medium", "medium", 3, 6, 12, 7.5, "Anti-extension core strength.", ["core", "brace"]),
    exercise("Pallof Press", "core", "accessory", "strength", "cable or band", "anti-rotation", "low", "high", "low", "low", 3, 8, 12, 6.5, "Anti-rotation trunk work.", ["core", "grappling"]),
    exercise("Side Plank", "core", "accessory", "mobility", "floor", "isometric", "low", "medium", "low", "low", 2, 20, 45, 6.0, "Lateral trunk endurance.", ["core", "brace"], hold_seconds=30, side="each side", intensity_target="strong brace"),
    exercise("Plank", "core", "accessory", "mobility", "floor", "isometric", "low", "medium", "low", "low", 2, 30, 60, 7.0, "Trunk stiffness. Time is in seconds.", ["core", "brace"], hold_seconds=45, intensity_target="strong brace"),
    exercise("Dead Bug", "core", "recovery_accessory", "mobility", "floor", "bodyweight", "low", "medium", "low", "low", 2, 8, 12, 5.0, "Breathing and bracing.", ["core", "recovery"], intensity_target="controlled breathing"),
    exercise("Bear Crawl", "core", "gpp", "conditioning", "floor", "locomotion", "medium", "high", "medium", "low", 3, 20, 40, 7.0, "Trunk, shoulders, and coordination.", ["core", "gpp", "grappling"], distance="20-40 sec"),

    # Neck / mobility / stretch
    exercise("Neck Isometrics", "neck", "recovery_accessory", "mobility", "bodyweight or hands", "isometric", "low", "high", "low", "low", 2, 10, 20, 5.0, "Controlled neck work. Do not strain.", ["neck", "grappling"], intensity_target="easy controlled pressure"),
    exercise("Hip Airplane", "mobility", "mobility", "mobility", "bodyweight", "mobility", "low", "medium", "medium", "low", 2, 5, 8, 4.0, "Hip control and balance.", ["hips", "mobility"], side="each side", intensity_target="controlled range"),
    exercise("World's Greatest Stretch", "mobility", "mobility", "mobility", "bodyweight", "flow", "low", "medium", "low", "low", 2, 4, 6, 4.0, "Full-body hip, t-spine, and hamstring mobility.", ["mobility", "hips"], side="each side", intensity_target="smooth controlled range"),
    exercise("90/90 Hip Switch", "mobility", "mobility", "mobility", "floor", "mobility", "low", "medium", "low", "low", 2, 6, 10, 4.0, "Hip rotation control.", ["hips", "mobility"], intensity_target="controlled range"),
    exercise("Adductor Rockback", "mobility", "mobility", "mobility", "floor", "mobility", "low", "high", "low", "low", 2, 8, 12, 4.0, "Adductor mobility for grappling positions.", ["hips", "mobility", "grappling"], side="each side"),
    exercise("Thoracic Rotation", "mobility", "mobility", "mobility", "floor", "mobility", "low", "medium", "low", "low", 2, 6, 10, 3.5, "T-spine rotation and breathing.", ["mobility", "upper_back"], side="each side"),
    exercise("Scap CARs", "mobility", "mobility", "mobility", "bodyweight", "mobility", "low", "medium", "low", "low", 2, 5, 8, 3.5, "Shoulder blade control.", ["shoulders", "mobility"]),
    exercise("Mobility Flow", "mobility", "mobility", "mobility", "bodyweight", "flow", "low", "medium", "low", "low", 1, 5, 10, 3.0, "Move smoothly. Do not force range.", ["mobility", "recovery"], duration_minutes=8, intensity_target="smooth and controlled"),

    # Static stretches
    exercise("Couch Stretch", "stretch", "stretch", "stretch", "bench or wall", "static stretch", "low", "medium", "low", "low", 2, 45, 60, 3.0, "Open hips and quads. Keep breathing relaxed.", ["hips", "stretch"], hold_seconds=60, side="each side", intensity_target="easy-moderate"),
    exercise("Lat Stretch", "stretch", "stretch", "stretch", "bench or rack", "static stretch", "low", "medium", "low", "low", 2, 30, 45, 3.0, "Open lats and shoulders after pulling.", ["shoulders", "stretch"], hold_seconds=45, side="each side", intensity_target="easy"),
    exercise("Pigeon Stretch", "stretch", "stretch", "stretch", "floor", "static stretch", "low", "medium", "low", "low", 2, 45, 60, 3.0, "Hip external rotation stretch.", ["hips", "stretch"], hold_seconds=60, side="each side", intensity_target="easy-moderate"),
    exercise("Hamstring Floss", "stretch", "stretch", "mobility", "floor or band", "dynamic stretch", "low", "medium", "low", "low", 2, 8, 12, 3.0, "Dynamic hamstring mobility.", ["hamstrings", "stretch"], side="each side", intensity_target="easy"),
    exercise("Pec Doorway Stretch", "stretch", "stretch", "stretch", "doorway", "static stretch", "low", "medium", "low", "low", 2, 30, 45, 3.0, "Open chest and anterior shoulder.", ["shoulders", "stretch"], hold_seconds=45, side="each side", intensity_target="easy"),

    # Cardio / conditioning
    exercise("Incline Walk", "conditioning", "cardio", "cardio", "treadmill", "cyclical cardio", "low", "medium", "low", "low", 1, 10, 20, 4.0, "Easy pace. Nasal breathing if possible.", ["cardio", "recovery"], duration_minutes=15, heart_rate_target="Zone 2 or nasal breathing", intensity_target="easy"),
    exercise("Bike", "conditioning", "cardio", "cardio", "bike", "cyclical cardio", "low", "medium", "low", "low", 1, 8, 12, 5.0, "Easy conditioning. Keep it smooth.", ["cardio", "recovery"], duration_minutes=10, heart_rate_target="Zone 2 or nasal breathing", intensity_target="easy-moderate"),
    exercise("Row Erg", "conditioning", "cardio", "cardio", "rower", "cyclical cardio", "medium", "medium", "medium", "low", 1, 6, 10, 6.0, "Moderate conditioning. Avoid turning it into a death set.", ["cardio", "conditioning"], duration_minutes=8, heart_rate_target="Zone 2-3", intensity_target="moderate"),
    exercise("Assault Bike Intervals", "conditioning", "cardio", "conditioning", "assault bike", "intervals", "medium", "high", "medium", "low", 6, 20, 40, 7.0, "Short intervals. Hard but not reckless.", ["cardio", "conditioning", "combat"], heart_rate_target="Hard intervals, full recovery", intensity_target="RPE 7"),
    exercise("Jump Rope", "conditioning", "cardio", "conditioning", "jump rope", "footwork cardio", "medium", "high", "medium", "medium", 5, 60, 120, 6.5, "Footwork and rhythm conditioning.", ["cardio", "footwork", "combat"], duration_minutes=10, intensity_target="smooth rhythm"),
    exercise("Sled Push", "conditioning", "gpp", "conditioning", "sled", "loaded conditioning", "medium", "high", "medium", "low", 6, 15, 30, 7.0, "Leg drive and conditioning with low eccentric damage.", ["conditioning", "lower", "gpp"], distance="15-30 yd"),
]


def get_exercise_catalog() -> list[dict[str, Any]]:
    return [exercise.copy() for exercise in EXERCISE_CATALOG]
