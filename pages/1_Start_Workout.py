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
from src.exercise_selector import substitute_exercise
from src.ui import (
    inject_global_styles,
    page_header,
    readiness_panel,
    compact_exercise_card,
    step_navigation,
)


st.set_page_config(page_title="Start Workout", page_icon="🏋️", layout="wide")

inject_global_styles()
init_db()


def clear_active_workout() -> None:
    keys_to_clear = [
        "latest_checkin",
        "latest_checkin_id",
        "latest_workout",
        "latest_workout_id",
        "latest_readiness_explanation",
        "workout_saved",
        "progression_updates",
        "completed_set_keys",
        "workout_flow_step",
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def initialize_set_state(
    exercise_index: int,
    set_number: int,
    default_weight: float,
    default_reps: int,
    default_rpe: float,
) -> tuple[str, str, str]:
    weight_key = f"active_weight_{exercise_index}_{set_number}"
    reps_key = f"active_reps_{exercise_index}_{set_number}"
    rpe_key = f"active_rpe_{exercise_index}_{set_number}"

    if weight_key not in st.session_state:
        st.session_state[weight_key] = float(default_weight)

    if reps_key not in st.session_state:
        st.session_state[reps_key] = int(default_reps)

    if rpe_key not in st.session_state:
        st.session_state[rpe_key] = float(default_rpe)

    return weight_key, reps_key, rpe_key


def copy_previous_set(exercise_index: int, set_number: int) -> None:
    if set_number <= 1:
        return

    prev_weight_key = f"active_weight_{exercise_index}_{set_number - 1}"
    prev_reps_key = f"active_reps_{exercise_index}_{set_number - 1}"
    prev_rpe_key = f"active_rpe_{exercise_index}_{set_number - 1}"

    weight_key = f"active_weight_{exercise_index}_{set_number}"
    reps_key = f"active_reps_{exercise_index}_{set_number}"
    rpe_key = f"active_rpe_{exercise_index}_{set_number}"

    st.session_state[weight_key] = st.session_state.get(prev_weight_key, st.session_state.get(weight_key, 0.0))
    st.session_state[reps_key] = st.session_state.get(prev_reps_key, st.session_state.get(reps_key, 0))
    st.session_state[rpe_key] = st.session_state.get(prev_rpe_key, st.session_state.get(rpe_key, 7.0))


def adjust_weight(key: str, amount: float) -> None:
    st.session_state[key] = max(0.0, float(st.session_state.get(key, 0.0)) + amount)


def adjust_reps(key: str, amount: int) -> None:
    st.session_state[key] = max(0, int(st.session_state.get(key, 0)) + amount)


def adjust_rpe(key: str, amount: float) -> None:
    st.session_state[key] = min(10.0, max(0.0, float(st.session_state.get(key, 7.0)) + amount))


def clear_set_state_for_exercise(exercise_index: int) -> None:
    keys_to_delete = []

    for key in st.session_state.keys():
        if key.startswith(f"active_weight_{exercise_index}_"):
            keys_to_delete.append(key)
        if key.startswith(f"active_reps_{exercise_index}_"):
            keys_to_delete.append(key)
        if key.startswith(f"active_rpe_{exercise_index}_"):
            keys_to_delete.append(key)
        if key.startswith(f"notes_{exercise_index}_"):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]


def replace_exercise(exercise_index: int, substitution_type: str) -> None:
    workout = st.session_state["latest_workout"]
    checkin = st.session_state["latest_checkin"]

    current_exercise = workout["exercises"][exercise_index - 1]

    replacement = substitute_exercise(
        current_exercise=current_exercise,
        substitution_type=substitution_type,
        readiness_category=checkin["readiness_category"],
        focus=workout["focus"],
        workout_modifier=workout.get("workout_modifier", "normal"),
        current_workout_exercises=workout["exercises"],
    )

    workout["exercises"][exercise_index - 1] = replacement
    st.session_state["latest_workout"] = workout
    clear_set_state_for_exercise(exercise_index)


if "workout_flow_step" not in st.session_state:
    st.session_state["workout_flow_step"] = 1

page_header(
    "Start Workout",
    "Check in, generate today’s adaptive workout, then log your completed sets.",
)

active_step = st.session_state["workout_flow_step"]
step_navigation(active_step)

default_bodyweight = float(get_setting("current_bodyweight", 218))

if active_step == 1:
    st.subheader("Daily Check-In")

    st.write(
        "Answer honestly. The app uses this to decide whether today should be a push, normal, light, or recovery session."
    )

    if "latest_workout" in st.session_state:
        st.info("You already have an active generated workout. Save it or clear it before generating a new one.")

        if st.button("Clear Active Workout", use_container_width=True):
            clear_active_workout()
            st.rerun()

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

        st.markdown("### Training Intent")

        col3, col4 = st.columns(2)

        with col3:
            motivation = st.slider("Motivation to train", 1, 10, 6)

            protein_on_track = st.selectbox(
                "Protein on track yesterday?",
                ["yes", "unsure", "no"],
                index=1,
            )

            training_focus_today = st.selectbox(
                "Training focus today",
                [
                    "Let app decide",
                    "Full body",
                    "Lower emphasis",
                    "Upper emphasis",
                    "Posterior chain / grappling",
                    "Accessory / pump",
                    "Recovery / mobility",
                ],
                index=0,
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

            fun_workout = st.checkbox("Fun workout")
            focus_workout = st.checkbox("Focus workout")
            chaos_workout = st.checkbox("Chaos workout")

        st.markdown("### Combat Training Context")

        col5, col6, col7 = st.columns(3)

        with col5:
            combat_last_24h = st.checkbox("BJJ/Muay Thai in last 24 hours?")

        with col6:
            hard_sparring_last_24h = st.checkbox("Hard sparring or hard rolling in last 24 hours?")

        with col7:
            combat_later_today = st.checkbox("BJJ/Muay Thai later today?")

        submitted = st.form_submit_button("Generate Workout", use_container_width=True)

    if submitted:
        if focus_workout and chaos_workout:
            st.warning("Focus workout and Chaos workout conflict. The app will prioritize Focus workout.")

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
            "training_focus_today": training_focus_today,
            "fun_workout": fun_workout,
            "focus_workout": focus_workout,
            "chaos_workout": chaos_workout,
        }

        readiness_score, readiness_category, explanation = calculate_readiness_score(checkin)

        checkin["readiness_score"] = readiness_score
        checkin["readiness_category"] = readiness_category

        checkin_id = insert_checkin(checkin)

        workout = generate_workout(checkin)

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

        for exercise_item in workout["exercises"]:
            insert_planned_exercise(workout_id, exercise_item)

        st.session_state["latest_checkin"] = checkin
        st.session_state["latest_checkin_id"] = checkin_id
        st.session_state["latest_workout"] = workout
        st.session_state["latest_workout_id"] = workout_id
        st.session_state["latest_readiness_explanation"] = explanation
        st.session_state["workout_saved"] = False
        st.session_state["progression_updates"] = []
        st.session_state["completed_set_keys"] = set()
        st.session_state["workout_flow_step"] = 2

        st.rerun()

elif active_step == 2:
    if "latest_checkin" not in st.session_state or "latest_workout" not in st.session_state:
        st.info("Complete the Daily Check-In first to generate a workout.")
        if st.button("Go to Check-In", use_container_width=True):
            st.session_state["workout_flow_step"] = 1
            st.rerun()
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

        st.info(workout["generation_reason"])

        st.caption(
            f"Template bias: {workout.get('template_key', 'balanced')} | "
            f"Modifier: {workout.get('workout_modifier', 'normal')}"
        )

        st.divider()

        st.subheader("Workout Plan")

        for index, exercise_item in enumerate(workout["exercises"], start=1):
            compact_exercise_card(exercise_item, index)

            sub_col1, sub_col2, sub_col3 = st.columns(3)

            with sub_col1:
                if st.button("Modality Substitute", key=f"modality_sub_{index}", use_container_width=True):
                    replace_exercise(index, "modality")
                    st.rerun()

            with sub_col2:
                if st.button("Full Substitute", key=f"full_sub_{index}", use_container_width=True):
                    replace_exercise(index, "full")
                    st.rerun()

            with sub_col3:
                if st.button("Log This Exercise", key=f"log_exercise_{index}", use_container_width=True):
                    st.session_state["workout_flow_step"] = 3
                    st.rerun()

            st.divider()

        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("Start Logging Sets", use_container_width=True):
                st.session_state["workout_flow_step"] = 3
                st.rerun()

        with action_col2:
            if st.button("Back to Check-In", use_container_width=True):
                st.session_state["workout_flow_step"] = 1
                st.rerun()

        with st.expander("Table View"):
            workout_df = pd.DataFrame(workout["exercises"])

            display_columns = [
                "exercise_name",
                "movement_pattern",
                "exercise_category",
                "prescription_type",
                "planned_sets",
                "planned_reps_min",
                "planned_reps_max",
                "planned_weight",
                "target_rpe",
                "equipment",
                "modality",
                "notes",
            ]

            existing_columns = [column for column in display_columns if column in workout_df.columns]

            st.dataframe(
                workout_df[existing_columns],
                use_container_width=True,
                hide_index=True,
            )

elif active_step == 3:
    if "latest_checkin" not in st.session_state or "latest_workout" not in st.session_state:
        st.info("Generate a workout first before logging sets.")
        if st.button("Go to Check-In", use_container_width=True):
            st.session_state["workout_flow_step"] = 1
            st.rerun()
    else:
        checkin = st.session_state["latest_checkin"]
        workout = st.session_state["latest_workout"]
        workout_id = st.session_state["latest_workout_id"]
        readiness_category = checkin["readiness_category"]

        if "completed_set_keys" not in st.session_state:
            st.session_state["completed_set_keys"] = set()

        st.subheader("Log Completed Sets")

        st.write(
            "Use the buttons to adjust quickly. Tap Complete Set after each finished set."
        )

        total_planned_sets = sum(int(exercise_item["planned_sets"]) for exercise_item in workout["exercises"])
        completed_count = len(st.session_state["completed_set_keys"])

        st.progress(
            completed_count / total_planned_sets if total_planned_sets > 0 else 0,
            text=f"{completed_count} of {total_planned_sets} planned sets completed",
        )

        for exercise_index, exercise_item in enumerate(workout["exercises"], start=1):
            exercise_sets = int(exercise_item["planned_sets"])
            exercise_completed = len(
                [
                    key
                    for key in st.session_state["completed_set_keys"]
                    if key.startswith(f"{exercise_index}_")
                ]
            )

            expanded_default = exercise_completed < exercise_sets and exercise_index <= 2

            with st.expander(
                f"{exercise_index}. {exercise_item['exercise_name']} — "
                f"{exercise_completed}/{exercise_sets} sets complete",
                expanded=expanded_default,
            ):
                st.caption(
                    f"Target RPE {exercise_item['target_rpe']} · {exercise_item['movement_pattern']} · {exercise_item['exercise_category']}"
                )

                default_weight = float(exercise_item["planned_weight"] or 0)
                default_reps = int(exercise_item["planned_reps_min"])
                default_rpe = float(exercise_item["target_rpe"])
                planned_sets = int(exercise_item["planned_sets"])

                for set_number in range(1, planned_sets + 1):
                    set_key = f"{exercise_index}_{set_number}_{exercise_item['exercise_name']}"

                    st.markdown(f"### Set {set_number}")

                    weight_key, reps_key, rpe_key = initialize_set_state(
                        exercise_index,
                        set_number,
                        default_weight,
                        default_reps,
                        default_rpe,
                    )

                    if set_key in st.session_state["completed_set_keys"]:
                        st.success(
                            f"Completed: {st.session_state[weight_key]} lb x "
                            f"{st.session_state[reps_key]} @ RPE {st.session_state[rpe_key]}"
                        )
                        continue

                    button_cols = st.columns(6)

                    with button_cols[0]:
                        if st.button("+5 lb", key=f"plus5_{set_key}"):
                            adjust_weight(weight_key, 5)
                            st.rerun()

                    with button_cols[1]:
                        if st.button("-5 lb", key=f"minus5_{set_key}"):
                            adjust_weight(weight_key, -5)
                            st.rerun()

                    with button_cols[2]:
                        if st.button("+1 rep", key=f"plusrep_{set_key}"):
                            adjust_reps(reps_key, 1)
                            st.rerun()

                    with button_cols[3]:
                        if st.button("-1 rep", key=f"minusrep_{set_key}"):
                            adjust_reps(reps_key, -1)
                            st.rerun()

                    with button_cols[4]:
                        if st.button("Easy", key=f"easy_{set_key}"):
                            adjust_rpe(rpe_key, -0.5)
                            st.rerun()

                    with button_cols[5]:
                        if st.button("Hard", key=f"hard_{set_key}"):
                            adjust_rpe(rpe_key, 0.5)
                            st.rerun()

                    if set_number > 1:
                        if st.button("Same as previous set", key=f"same_prev_{set_key}", use_container_width=True):
                            copy_previous_set(exercise_index, set_number)
                            st.rerun()

                    input_cols = st.columns(3)

                    with input_cols[0]:
                        st.number_input(
                            "Weight",
                            min_value=0.0,
                            max_value=1000.0,
                            step=2.5,
                            key=weight_key,
                        )

                    with input_cols[1]:
                        st.number_input(
                            "Reps",
                            min_value=0,
                            max_value=100,
                            step=1,
                            key=reps_key,
                        )

                    with input_cols[2]:
                        st.number_input(
                            "RPE",
                            min_value=0.0,
                            max_value=10.0,
                            step=0.5,
                            key=rpe_key,
                        )

                    notes = st.text_input(
                        "Set notes",
                        value="",
                        key=f"notes_{set_key}",
                    )

                    complete_col1, complete_col2 = st.columns(2)

                    with complete_col1:
                        if st.button("Complete Set", key=f"complete_{set_key}", use_container_width=True):
                            set_data = {
                                "exercise_name": exercise_item["exercise_name"],
                                "set_number": set_number,
                                "weight": float(st.session_state[weight_key]),
                                "reps": int(st.session_state[reps_key]),
                                "rpe": float(st.session_state[rpe_key]),
                                "notes": notes,
                            }

                            if int(set_data["reps"]) > 0:
                                insert_completed_set(workout_id, set_data)
                                st.session_state["completed_set_keys"].add(set_key)
                                st.success("Set saved.")
                                st.rerun()
                            else:
                                st.warning("Reps must be greater than 0 to complete a set.")

                    with complete_col2:
                        if st.button("Skip Set", key=f"skip_{set_key}", use_container_width=True):
                            st.session_state["completed_set_keys"].add(set_key)
                            st.rerun()

                    st.divider()

        st.divider()

        st.subheader("Finish Workout")

        session_rpe = st.slider("Overall workout difficulty / session RPE", 1, 10, 7)

        workout_notes = st.text_area(
            "Workout notes",
            placeholder="Example: Felt strong, grip was tired, shortened accessories, etc.",
        )

        finish_col1, finish_col2 = st.columns(2)

        with finish_col1:
            if st.button("Save and Finish Workout", use_container_width=True):
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
                st.session_state["workout_flow_step"] = 4
                st.rerun()

        with finish_col2:
            if st.button("Clear Without Marking Complete", use_container_width=True):
                clear_active_workout()
                st.rerun()

elif active_step == 4:
    st.success("Workout saved and completed.")

    updates = st.session_state.get("progression_updates", [])

    if updates:
        st.subheader("Progression Update")
        updates_df = pd.DataFrame(updates)
        st.dataframe(updates_df, use_container_width=True, hide_index=True)

        for update in updates:
            st.write(f"**{update['exercise_name']}**: {update['decision']}")
    else:
        st.info("No main lift progression updates were made.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start New Workout", use_container_width=True):
            clear_active_workout()
            st.session_state["workout_flow_step"] = 1
            st.rerun()

    with col2:
        st.page_link("pages/2_Workout_History.py", label="View Workout History")
