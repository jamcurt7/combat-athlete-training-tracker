from datetime import date

import pandas as pd
import streamlit as st

from src.database import (
    init_db,
    insert_checkin,
    insert_workout_session,
    insert_planned_exercise,
    insert_completed_set,
    mark_workout_completed,
    get_setting,
)
from src.readiness_engine import calculate_readiness_score
from src.workout_generator import generate_workout
from src.progression_engine import update_progression_from_workout
from src.ui import (
    inject_global_styles,
    page_header,
    readiness_panel,
    compact_exercise_card,
    flow_indicator,
)


st.set_page_config(page_title="Start Workout", page_icon="🏋️", layout="wide")

inject_global_styles()
init_db()


# ------------------------------------------------------------
# Local UI helpers for this page
# ------------------------------------------------------------

def inject_start_workout_styles():
    st.markdown(
        """
        <style>
        .workout-flow-card {
            background: linear-gradient(135deg, rgba(18, 0, 31, 0.96), rgba(43, 0, 82, 0.88));
            border: 1px solid rgba(0, 245, 255, 0.22);
            border-radius: 22px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 0 22px rgba(0, 245, 255, 0.08);
        }

        .workout-flow-title {
            color: white;
            font-size: 1.2rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }

        .workout-flow-subtitle {
            color: rgba(255, 255, 255, 0.68);
            font-size: 0.9rem;
            margin-bottom: 0;
        }

        .exercise-log-card {
            background: rgba(8, 0, 14, 0.94);
            border: 1px solid rgba(0, 245, 255, 0.18);
            border-radius: 20px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .exercise-log-title {
            color: white;
            font-size: 1.1rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .exercise-log-meta {
            color: rgba(255, 255, 255, 0.62);
            font-size: 0.85rem;
            margin-bottom: 0.8rem;
        }

        .completed-set-pill {
            display: inline-block;
            background: rgba(0, 245, 255, 0.14);
            border: 1px solid rgba(0, 245, 255, 0.35);
            color: #00f5ff;
            border-radius: 999px;
            padding: 0.25rem 0.65rem;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .pending-set-pill {
            display: inline-block;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: rgba(255, 255, 255, 0.75);
            border-radius: 999px;
            padding: 0.25rem 0.65rem;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        div[data-testid="stButton"] button {
            min-height: 42px;
            border-radius: 12px;
            font-weight: 700;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 0.6rem;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.85rem;
                padding-right: 0.85rem;
                padding-top: 1rem;
            }

            .exercise-log-card {
                padding: 0.85rem;
            }

            .workout-flow-card {
                padding: 0.85rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def workout_flow_card(title, subtitle):
    st.markdown(
        f"""
        <div class="workout-flow-card">
            <div class="workout-flow-title">{title}</div>
            <p class="workout-flow-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_exercise_key(exercise_name, exercise_index):
    clean_name = (
        exercise_name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
    )
    return f"exercise_{exercise_index}_{clean_name}"


def is_weighted_bodyweight_exercise(exercise_name):
    exercise_lower = exercise_name.lower()

    weighted_bodyweight_terms = [
        "weighted pull",
        "weighted chin",
        "weighted dip",
    ]

    return any(term in exercise_lower for term in weighted_bodyweight_terms)


def format_weight_for_display(exercise_name, weight):
    try:
        weight = float(weight)
    except (TypeError, ValueError):
        return "0 lb"

    if is_weighted_bodyweight_exercise(exercise_name):
        return f"+{weight:g} lb"

    return f"{weight:g} lb"


def initialize_set_state(exercise, exercise_index, set_number):
    exercise_name = exercise["exercise_name"]
    base_key = normalize_exercise_key(exercise_name, exercise_index)
    set_key = f"{base_key}_set_{set_number}"

    weight_key = f"{set_key}_weight"
    reps_key = f"{set_key}_reps"
    rpe_key = f"{set_key}_rpe"
    notes_key = f"{set_key}_notes"
    completed_key = f"{set_key}_completed"

    planned_weight = exercise.get("planned_weight", 0) or 0
    planned_reps = exercise.get("planned_reps_min", 0) or 0
    target_rpe = exercise.get("target_rpe", 7) or 7

    if weight_key not in st.session_state:
        st.session_state[weight_key] = float(planned_weight)

    if reps_key not in st.session_state:
        st.session_state[reps_key] = int(planned_reps)

    if rpe_key not in st.session_state:
        st.session_state[rpe_key] = float(target_rpe)

    if notes_key not in st.session_state:
        st.session_state[notes_key] = ""

    if completed_key not in st.session_state:
        st.session_state[completed_key] = False

    return {
        "set_key": set_key,
        "weight_key": weight_key,
        "reps_key": reps_key,
        "rpe_key": rpe_key,
        "notes_key": notes_key,
        "completed_key": completed_key,
    }


def clear_active_workout_state():
    keys_to_clear = []

    for key in st.session_state.keys():
        if key.startswith("exercise_"):
            keys_to_clear.append(key)

        if key in [
            "latest_checkin",
            "latest_checkin_id",
            "latest_workout",
            "latest_workout_id",
            "latest_readiness_explanation",
            "workout_saved",
            "progression_updates",
            "workout_focus_ready",
            "workout_generation_ready",
        ]:
            keys_to_clear.append(key)

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def set_adjustment_button(label, key, state_key, amount, minimum=None, maximum=None):
    if st.button(label, key=key, use_container_width=True):
        new_value = st.session_state[state_key] + amount

        if minimum is not None:
            new_value = max(minimum, new_value)

        if maximum is not None:
            new_value = min(maximum, new_value)

        st.session_state[state_key] = new_value
        st.rerun()


def quick_set_logger(exercise, exercise_index, set_number):
    exercise_name = exercise["exercise_name"]
    keys = initialize_set_state(exercise, exercise_index, set_number)

    weight_key = keys["weight_key"]
    reps_key = keys["reps_key"]
    rpe_key = keys["rpe_key"]
    notes_key = keys["notes_key"]
    completed_key = keys["completed_key"]
    set_key = keys["set_key"]

    st.markdown("---")

    if st.session_state[completed_key]:
        st.markdown(
            f'<span class="completed-set-pill">Set {set_number} completed</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<span class="pending-set-pill">Set {set_number} pending</span>',
            unsafe_allow_html=True,
        )

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)

    with metric_col_1:
        st.metric(
            "Weight",
            format_weight_for_display(exercise_name, st.session_state[weight_key]),
        )

    with metric_col_2:
        st.metric("Reps", int(st.session_state[reps_key]))

    with metric_col_3:
        st.metric("RPE", f"{st.session_state[rpe_key]:g}")

    weight_col_1, weight_col_2, weight_col_3, weight_col_4 = st.columns(4)

    with weight_col_1:
        set_adjustment_button(
            "-10",
            f"{set_key}_weight_minus_10",
            weight_key,
            -10,
            minimum=0,
        )

    with weight_col_2:
        set_adjustment_button(
            "-5",
            f"{set_key}_weight_minus_5",
            weight_key,
            -5,
            minimum=0,
        )

    with weight_col_3:
        set_adjustment_button(
            "+5",
            f"{set_key}_weight_plus_5",
            weight_key,
            5,
            minimum=0,
        )

    with weight_col_4:
        set_adjustment_button(
            "+10",
            f"{set_key}_weight_plus_10",
            weight_key,
            10,
            minimum=0,
        )

    reps_col_1, reps_col_2, rpe_col_1, rpe_col_2 = st.columns(4)

    with reps_col_1:
        set_adjustment_button(
            "Reps -1",
            f"{set_key}_reps_minus_1",
            reps_key,
            -1,
            minimum=0,
        )

    with reps_col_2:
        set_adjustment_button(
            "Reps +1",
            f"{set_key}_reps_plus_1",
            reps_key,
            1,
            minimum=0,
        )

    with rpe_col_1:
        set_adjustment_button(
            "RPE -0.5",
            f"{set_key}_rpe_minus",
            rpe_key,
            -0.5,
            minimum=0,
            maximum=10,
        )

    with rpe_col_2:
        set_adjustment_button(
            "RPE +0.5",
            f"{set_key}_rpe_plus",
            rpe_key,
            0.5,
            minimum=0,
            maximum=10,
        )

    with st.expander("Optional exact entry / notes", expanded=False):
        exact_col_1, exact_col_2, exact_col_3 = st.columns(3)

        with exact_col_1:
            exact_weight = st.number_input(
                "Exact weight",
                min_value=0.0,
                max_value=1000.0,
                value=float(st.session_state[weight_key]),
                step=2.5,
                key=f"{set_key}_exact_weight_input",
            )

            if st.button("Use exact weight", key=f"{set_key}_use_exact_weight", use_container_width=True):
                st.session_state[weight_key] = float(exact_weight)
                st.rerun()

        with exact_col_2:
            exact_reps = st.number_input(
                "Exact reps",
                min_value=0,
                max_value=100,
                value=int(st.session_state[reps_key]),
                step=1,
                key=f"{set_key}_exact_reps_input",
            )

            if st.button("Use exact reps", key=f"{set_key}_use_exact_reps", use_container_width=True):
                st.session_state[reps_key] = int(exact_reps)
                st.rerun()

        with exact_col_3:
            exact_rpe = st.number_input(
                "Exact RPE",
                min_value=0.0,
                max_value=10.0,
                value=float(st.session_state[rpe_key]),
                step=0.5,
                key=f"{set_key}_exact_rpe_input",
            )

            if st.button("Use exact RPE", key=f"{set_key}_use_exact_rpe", use_container_width=True):
                st.session_state[rpe_key] = float(exact_rpe)
                st.rerun()

        st.text_input(
            "Set notes",
            key=notes_key,
            placeholder="Optional: pain, grip, form note, shortened rest, etc.",
        )

    if st.session_state[completed_key]:
        if st.button("Undo Completed Set", key=f"{set_key}_undo_complete", use_container_width=True):
            st.session_state[completed_key] = False
            st.rerun()
    else:
        if st.button("Complete Set", key=f"{set_key}_complete", type="primary", use_container_width=True):
            st.session_state[completed_key] = True
            st.rerun()

    return {
        "exercise_name": exercise_name,
        "set_number": set_number,
        "weight": st.session_state[weight_key],
        "reps": st.session_state[reps_key],
        "rpe": st.session_state[rpe_key],
        "notes": st.session_state[notes_key],
        "completed": st.session_state[completed_key],
    }


def render_exercise_log_card(exercise, exercise_index):
    exercise_name = exercise["exercise_name"]
    planned_sets = int(exercise.get("planned_sets", 0) or 0)
    reps_min = exercise.get("planned_reps_min", 0)
    reps_max = exercise.get("planned_reps_max", 0)
    planned_weight = exercise.get("planned_weight", 0) or 0
    target_rpe = exercise.get("target_rpe", 7)
    movement_pattern = exercise.get("movement_pattern", "Movement")
    exercise_category = exercise.get("exercise_category", "Training")

    st.markdown(
        f"""
        <div class="exercise-log-card">
            <div class="exercise-log-title">{exercise_index}. {exercise_name}</div>
            <div class="exercise-log-meta">
                Target: {planned_sets} sets x {reps_min}-{reps_max} reps · 
                {format_weight_for_display(exercise_name, planned_weight)} · 
                RPE {target_rpe} · {movement_pattern} · {exercise_category}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    action_col_1, action_col_2, action_col_3 = st.columns(3)

    with action_col_1:
        if st.button("Full Replacement", key=f"full_replace_{exercise_index}", use_container_width=True):
            st.info("Exercise replacement is coming next. This button is now reserved for a full exercise swap.")

    with action_col_2:
        if st.button("Change Modality", key=f"modality_replace_{exercise_index}", use_container_width=True):
            st.info("Modality replacement is coming next. Example: squat to hack squat, pull-up to pulldown.")

    with action_col_3:
        if st.button("Skip Exercise", key=f"skip_exercise_{exercise_index}", use_container_width=True):
            skip_key = f"exercise_{exercise_index}_skipped"
            st.session_state[skip_key] = True
            st.warning(f"{exercise_name} marked as skipped for this session.")

    skip_key = f"exercise_{exercise_index}_skipped"

    if st.session_state.get(skip_key):
        st.warning("This exercise is currently marked as skipped. No sets from it will be saved.")
        if st.button("Undo Skip", key=f"undo_skip_{exercise_index}", use_container_width=True):
            st.session_state[skip_key] = False
            st.rerun()
        return []

    completed_entries = []

    for set_number in range(1, planned_sets + 1):
        set_entry = quick_set_logger(exercise, exercise_index, set_number)
        completed_entries.append(set_entry)

    return completed_entries


def collect_completed_set_entries(workout):
    completed_sets = []

    for exercise_index, exercise in enumerate(workout["exercises"], start=1):
        skip_key = f"exercise_{exercise_index}_skipped"

        if st.session_state.get(skip_key):
            continue

        planned_sets = int(exercise.get("planned_sets", 0) or 0)

        for set_number in range(1, planned_sets + 1):
            keys = initialize_set_state(exercise, exercise_index, set_number)

            if st.session_state.get(keys["completed_key"]):
                completed_sets.append(
                    {
                        "exercise_name": exercise["exercise_name"],
                        "set_number": set_number,
                        "weight": st.session_state[keys["weight_key"]],
                        "reps": st.session_state[keys["reps_key"]],
                        "rpe": st.session_state[keys["rpe_key"]],
                        "notes": st.session_state[keys["notes_key"]],
                    }
                )

    return completed_sets


# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------

inject_start_workout_styles()

page_header(
    "Start Workout",
    "Check in, choose today’s training intent, generate the workout, then log sets fast.",
)

default_bodyweight = float(get_setting("current_bodyweight", 218))

checkin_tab, workout_tab, log_tab = st.tabs(
    [
        "1. Daily Check-In",
        "2. Generated Workout",
        "3. Log Sets",
    ]
)


# ------------------------------------------------------------
# Tab 1: Daily Check-In + Workout Focus
# ------------------------------------------------------------

with checkin_tab:
    flow_indicator(active_step=1)

    workout_flow_card(
        "Daily Check-In",
        "First, tell the app how ready you are. Then choose the style and bias for today’s workout.",
    )

    with st.form("daily_checkin_form"):
        st.markdown("### Body & Recovery")

        col1, col2 = st.columns(2)

        with col1:
            bodyweight = st.number_input(
                "Bodyweight today",
                min_value=0.0,
                max_value=500.0,
                value=default_bodyweight,
                step=0.2,
            )

            hours_slept = st.number_input(
                "Hours slept",
                min_value=0.0,
                max_value=14.0,
                value=7.0,
                step=0.5,
            )

            sleep_quality = st.slider("Sleep quality", 1, 10, 7)
            energy = st.slider("Energy", 1, 10, 6)

        with col2:
            soreness = st.slider("Soreness", 1, 10, 5)
            hydration = st.slider("Hydration", 1, 10, 6)
            mood = st.slider("Mood", 1, 10, 6)
            stress = st.slider("Stress", 1, 10, 5)

        st.markdown("### Training Mindset")

        col3, col4 = st.columns(2)

        with col3:
            motivation = st.slider("Motivation to train", 1, 10, 6)

            protein_on_track = st.selectbox(
                "Protein on track yesterday?",
                ["yes", "unsure", "no"],
                index=1,
            )

        with col4:
            time_available = st.selectbox(
                "Time available today",
                [30, 45, 60, 75],
                index=2,
                help="Choose the closest option in minutes.",
            )

            goal_today = st.selectbox(
                "Goal for today",
                ["push", "normal", "maintain", "recovery"],
                index=1,
            )

        st.markdown("### Combat Training Context")

        col5, col6, col7 = st.columns(3)

        with col5:
            combat_last_24h = st.checkbox("BJJ/Muay Thai in last 24 hours?")

        with col6:
            hard_sparring_last_24h = st.checkbox("Hard sparring or hard rolling in last 24 hours?")

        with col7:
            combat_later_today = st.checkbox("BJJ/Muay Thai later today?")

        submitted_checkin = st.form_submit_button("Save Check-In", use_container_width=True)

    if submitted_checkin:
        checkin = {
            "date": date.today().isoformat(),
            "bodyweight": bodyweight if bodyweight > 0 else None,
            "hours_slept": hours_slept,
            "sleep_quality": sleep_quality,
            "energy": energy,
            "mood": mood,
            "motivation": motivation,
            "stress": stress,
            "soreness": soreness,
            "combat_last_24h": combat_last_24h,
            "hard_sparring_last_24h": hard_sparring_last_24h,
            "combat_later_today": combat_later_today,
            "hydration": hydration,
            "protein_on_track": protein_on_track,
            "time_available": time_available,
            "goal_today": goal_today,
        }

        readiness_score, readiness_category, explanation = calculate_readiness_score(checkin)

        checkin["readiness_score"] = readiness_score
        checkin["readiness_category"] = readiness_category

        checkin_id = insert_checkin(checkin)

        st.session_state["latest_checkin"] = checkin
        st.session_state["latest_checkin_id"] = checkin_id
        st.session_state["latest_readiness_explanation"] = explanation
        st.session_state["workout_focus_ready"] = True

        if "latest_workout" in st.session_state:
            del st.session_state["latest_workout"]

        if "latest_workout_id" in st.session_state:
            del st.session_state["latest_workout_id"]

        st.success("Check-in saved. Choose your workout focus below.")

    if st.session_state.get("workout_focus_ready") and "latest_checkin" in st.session_state:
        st.divider()

        checkin = st.session_state["latest_checkin"]
        explanation = st.session_state["latest_readiness_explanation"]

        readiness_panel(
            category=checkin["readiness_category"],
            score=checkin["readiness_score"],
            explanation=explanation,
            workout_type="Not generated yet",
            focus="Choose below",
        )

        st.markdown("### Workout Focus")

        workout_mode = st.radio(
            "Workout mode",
            options=["Focused", "Fun", "Chaos"],
            index=0,
            horizontal=True,
            help=(
                "Focused = structured progression. "
                "Fun = more variety. "
                "Chaos = novelty, but still controlled by readiness."
            ),
        )

        training_bias = st.selectbox(
            "Training bias today",
            [
                "Mixed",
                "Strength",
                "Hypertrophy",
                "Grappling Transfer",
                "Striking Transfer",
                "Conditioning",
                "Mobility / Recovery",
            ],
            index=0,
            help="This gives the workout generator a directional bias for today.",
        )

        st.caption(
            "Readiness still controls intensity. Chaos or Fun mode should not override a low-readiness day."
        )

        if st.button("Generate Workout", type="primary", use_container_width=True):
            checkin["workout_mode"] = workout_mode
            checkin["training_bias"] = training_bias
            checkin["template_key"] = training_bias.lower().replace(" ", "_").replace("/", "").replace("__", "_")

            workout = generate_workout(checkin)

            workout["workout_mode"] = workout_mode
            workout["training_bias"] = training_bias

            workout_id = insert_workout_session(
                {
                    "date": workout["date"],
                    "workout_type": workout["workout_type"],
                    "focus": workout["focus"],
                    "readiness_category": workout["readiness_category"],
                    "estimated_duration": workout["estimated_duration"],
                    "generation_reason": workout["generation_reason"],
                    "completed": 0,
                    "session_rpe": None,
                    "notes": "",
                }
            )

            for exercise in workout["exercises"]:
                insert_planned_exercise(workout_id, exercise)

            st.session_state["latest_checkin"] = checkin
            st.session_state["latest_workout"] = workout
            st.session_state["latest_workout_id"] = workout_id
            st.session_state["workout_saved"] = False
            st.session_state["progression_updates"] = []

            st.success("Workout generated. Open the Generated Workout tab next.")


# ------------------------------------------------------------
# Tab 2: Generated Workout
# ------------------------------------------------------------

with workout_tab:
    flow_indicator(active_step=2)

    if "latest_checkin" not in st.session_state:
        st.info("Complete the Daily Check-In first.")
    elif "latest_workout" not in st.session_state:
        st.info("Your check-in is saved. Go back to Daily Check-In and generate the workout.")
    else:
        checkin = st.session_state["latest_checkin"]
        workout = st.session_state["latest_workout"]
        explanation = st.session_state["latest_readiness_explanation"]

        readiness_panel(
            category=checkin["readiness_category"],
            score=checkin["readiness_score"],
            explanation=explanation,
            workout_type=workout["workout_type"],
            focus=workout["focus"],
        )

        if workout.get("deload"):
            st.warning("Scheduled deload logic is active for this workout.")

        st.subheader("Workout Overview")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric("Workout Type", workout["workout_type"])

        with col_b:
            st.metric("Focus", workout["focus"])

        with col_c:
            st.metric("Duration", f"{workout['estimated_duration']} min")

        mode_col, bias_col = st.columns(2)

        with mode_col:
            st.metric("Mode", workout.get("workout_mode", checkin.get("workout_mode", "Focused")))

        with bias_col:
            st.metric("Training Bias", workout.get("training_bias", checkin.get("training_bias", "Mixed")))

        st.info(workout["generation_reason"])

        if "template_key" in workout:
            st.caption(f"Template bias: {workout['template_key']}")
        elif "template_key" in checkin:
            st.caption(f"Template bias: {checkin['template_key']}")

        st.divider()

        st.subheader("Workout Plan")

        for index, exercise in enumerate(workout["exercises"], start=1):
            compact_exercise_card(exercise, index)

        with st.expander("Table View"):
            workout_df = pd.DataFrame(workout["exercises"])

            display_columns = [
                "exercise_name",
                "planned_sets",
                "planned_reps_min",
                "planned_reps_max",
                "planned_weight",
                "target_rpe",
                "notes",
            ]

            available_columns = [
                column for column in display_columns if column in workout_df.columns
            ]

            st.dataframe(
                workout_df[available_columns],
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        if st.button("Go to Log Sets", type="primary", use_container_width=True):
            st.info("Open the Log Sets tab above to start tracking your sets.")


# ------------------------------------------------------------
# Tab 3: Fast Set Logging
# ------------------------------------------------------------

with log_tab:
    flow_indicator(active_step=3)

    if "latest_checkin" not in st.session_state:
        st.info("Complete the Daily Check-In first.")
    elif "latest_workout" not in st.session_state:
        st.info("Generate a workout before logging sets.")
    else:
        checkin = st.session_state["latest_checkin"]
        workout = st.session_state["latest_workout"]
        workout_id = st.session_state["latest_workout_id"]
        readiness_category = checkin["readiness_category"]

        st.subheader("Fast Set Logging")

        st.write(
            "Use the buttons during the workout. Complete only the sets you actually perform. "
            "Skipped exercises and unfinished sets will not be saved."
        )

        all_visible_set_entries = []

        for exercise_index, exercise in enumerate(workout["exercises"], start=1):
            with st.container():
                set_entries = render_exercise_log_card(exercise, exercise_index)
                all_visible_set_entries.extend(set_entries)

        completed_set_entries = collect_completed_set_entries(workout)

        st.divider()

        completed_count = len(completed_set_entries)
        total_planned_sets = sum(
            int(exercise.get("planned_sets", 0) or 0)
            for exercise in workout["exercises"]
        )

        progress_value = 0

        if total_planned_sets > 0:
            progress_value = completed_count / total_planned_sets

        st.progress(progress_value)

        progress_col_1, progress_col_2 = st.columns(2)

        with progress_col_1:
            st.metric("Completed Sets", completed_count)

        with progress_col_2:
            st.metric("Planned Sets", total_planned_sets)

        st.markdown("### Finish Workout")

        session_rpe = st.slider(
            "Overall workout difficulty / session RPE",
            1,
            10,
            7,
            key="session_rpe_fast_logger",
        )

        workout_notes = st.text_area(
            "Workout notes",
            placeholder="Example: Felt strong, grip was tired, shortened accessories, etc.",
            key="workout_notes_fast_logger",
        )

        save_col_1, save_col_2 = st.columns(2)

        with save_col_1:
            if st.button("Complete Workout", type="primary", use_container_width=True):
                completed_set_entries = collect_completed_set_entries(workout)

                if not completed_set_entries:
                    st.warning("No completed sets were marked. Complete at least one set before saving.")
                else:
                    saved_sets = 0

                    for set_entry in completed_set_entries:
                        if int(set_entry["reps"]) > 0:
                            insert_completed_set(workout_id, set_entry)
                            saved_sets += 1

                    mark_workout_completed(
                        workout_id=workout_id,
                        session_rpe=float(session_rpe),
                        notes=workout_notes,
                    )

                    progression_updates = update_progression_from_workout(
                        workout_id=workout_id,
                        readiness_category=readiness_category,
                    )

                    st.session_state["workout_saved"] = True
                    st.session_state["progression_updates"] = progression_updates
                    st.session_state["last_saved_set_count"] = saved_sets

                    st.success(f"Workout saved. Completed sets saved: {saved_sets}")

        with save_col_2:
            if st.button("Clear Active Workout", use_container_width=True):
                clear_active_workout_state()
                st.success("Active workout cleared.")
                st.rerun()

        if st.session_state.get("workout_saved"):
            flow_indicator(active_step=4)

            st.subheader("Progression Update")

            updates = st.session_state.get("progression_updates", [])

            if updates:
                updates_df = pd.DataFrame(updates)
                st.dataframe(updates_df, use_container_width=True, hide_index=True)

                for update in updates:
                    st.write(f"**{update['exercise_name']}**: {update['decision']}")
            else:
                st.info(
                    "No main lift progression updates were made. This can happen on recovery/light days or if no main lifts were logged."
                )

            if st.button("Done — Clear Workout From View", type="primary", use_container_width=True):
                clear_active_workout_state()
                st.rerun()
