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
    readiness_badge,
    compact_exercise_card,
)


st.set_page_config(page_title="Start Workout", page_icon="🏋️", layout="wide")

inject_global_styles()
init_db()

page_header(
    "Start Workout",
    "Check in, generate today's adaptive workout, then log your completed sets.",
)

default_bodyweight = float(get_setting("current_bodyweight", 218))

checkin_tab, workout_tab, log_tab = st.tabs(
    [
        "1. Daily Check-In",
        "2. Generated Workout",
        "3. Log Sets",
    ]
)

with checkin_tab:
    st.subheader("Daily Check-In")

    st.write(
        "Keep this honest. The app uses these answers to decide whether today should be a push, normal, light, or recovery session."
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

        submitted = st.form_submit_button("Generate Workout", use_container_width=True)

    if submitted:
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

        for exercise in workout["exercises"]:
            insert_planned_exercise(workout_id, exercise)

        st.session_state["latest_checkin"] = checkin
        st.session_state["latest_checkin_id"] = checkin_id
        st.session_state["latest_workout"] = workout
        st.session_state["latest_workout_id"] = workout_id
        st.session_state["latest_readiness_explanation"] = explanation
        st.session_state["workout_saved"] = False
        st.session_state["progression_updates"] = []

        st.success("Check-in saved and workout generated. Open the Generated Workout tab next.")

with workout_tab:
    if "latest_checkin" not in st.session_state or "latest_workout" not in st.session_state:
        st.info("Complete the Daily Check-In first to generate a workout.")
    else:
        checkin = st.session_state["latest_checkin"]
        workout = st.session_state["latest_workout"]
        explanation = st.session_state["latest_readiness_explanation"]

        st.subheader("Today's Readiness")
        readiness_badge(checkin["readiness_category"], checkin["readiness_score"])

        st.write(explanation)

        if workout.get("deload"):
            st.warning("Scheduled deload logic is active for this workout.")

        st.divider()

        st.subheader("Workout Overview")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.metric("Workout Type", workout["workout_type"])

        with col_b:
            st.metric("Focus", workout["focus"])

        with col_c:
            st.metric("Duration", f"{workout['estimated_duration']} min")

        st.info(workout["generation_reason"])

        if "template_key" in workout:
            st.caption(f"Template bias: {workout['template_key']}")

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

            st.dataframe(
                workout_df[display_columns],
                use_container_width=True,
                hide_index=True,
            )

with log_tab:
    if "latest_checkin" not in st.session_state or "latest_workout" not in st.session_state:
        st.info("Generate a workout first before logging sets.")
    else:
        checkin = st.session_state["latest_checkin"]
        workout = st.session_state["latest_workout"]
        workout_id = st.session_state["latest_workout_id"]
        readiness_category = checkin["readiness_category"]

        st.subheader("Log Completed Sets")

        st.write(
            "Enter what you actually completed. For bodyweight or accessory movements, leave weight at 0 if you do not want to track load."
        )

        with st.form("set_logging_form"):
            all_set_entries = []

            for exercise_index, exercise in enumerate(workout["exercises"], start=1):
                with st.expander(
                    f"{exercise_index}. {exercise['exercise_name']} — "
                    f"{exercise['planned_sets']} x {exercise['planned_reps_min']}-{exercise['planned_reps_max']}",
                    expanded=exercise_index <= 2,
                ):
                    st.caption(
                        f"Target RPE {exercise['target_rpe']} · {exercise['movement_pattern']} · {exercise['exercise_category']}"
                    )

                    if exercise["planned_weight"] and exercise["planned_weight"] > 0:
                        default_weight = float(exercise["planned_weight"])
                    else:
                        default_weight = 0.0

                    planned_sets = int(exercise["planned_sets"])

                    for set_number in range(1, planned_sets + 1):
                        st.markdown(f"**Set {set_number}**")

                        col_w, col_r, col_rpe = st.columns(3)

                        with col_w:
                            weight = st.number_input(
                                "Weight",
                                min_value=0.0,
                                max_value=1000.0,
                                value=default_weight,
                                step=2.5,
                                key=f"weight_{exercise_index}_{set_number}",
                            )

                        with col_r:
                            reps = st.number_input(
                                "Reps",
                                min_value=0,
                                max_value=100,
                                value=int(exercise["planned_reps_min"]),
                                step=1,
                                key=f"reps_{exercise_index}_{set_number}",
                            )

                        with col_rpe:
                            rpe = st.number_input(
                                "RPE",
                                min_value=0.0,
                                max_value=10.0,
                                value=float(exercise["target_rpe"]),
                                step=0.5,
                                key=f"rpe_{exercise_index}_{set_number}",
                            )

                        notes = st.text_input(
                            "Notes",
                            value="",
                            key=f"notes_{exercise_index}_{set_number}",
                        )

                        all_set_entries.append(
                            {
                                "exercise_name": exercise["exercise_name"],
                                "set_number": set_number,
                                "weight": weight,
                                "reps": reps,
                                "rpe": rpe,
                                "notes": notes,
                            }
                        )

            st.divider()

            session_rpe = st.slider("Overall workout difficulty / session RPE", 1, 10, 7)

            workout_notes = st.text_area(
                "Workout notes",
                placeholder="Example: Felt strong, grip was tired, shortened accessories, etc.",
            )

            save_workout = st.form_submit_button("Save Completed Workout", use_container_width=True)

        if save_workout:
            saved_sets = 0

            for set_entry in all_set_entries:
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

            st.success(f"Workout saved. Completed sets saved: {saved_sets}")

        if st.session_state.get("workout_saved"):
            st.divider()
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
