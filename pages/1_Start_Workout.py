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
)
from src.readiness_engine import calculate_readiness_score
from src.workout_generator import generate_workout
from src.progression_engine import update_progression_from_workout


st.set_page_config(page_title="Start Workout", page_icon="🏋️", layout="wide")

init_db()

st.title("Start Workout")

st.write(
    """
    Complete the daily check-in first. The app will generate today's workout, then let you
    log your sets, reps, weight, and RPE.
    """
)

st.divider()

with st.form("daily_checkin_form"):
    st.subheader("Daily Check-In")

    col1, col2 = st.columns(2)

    with col1:
        bodyweight = st.number_input(
            "Bodyweight today, optional",
            min_value=0.0,
            max_value=500.0,
            value=218.0,
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
        mood = st.slider("Mood", 1, 10, 6)
        motivation = st.slider("Motivation to train", 1, 10, 6)

    with col2:
        stress = st.slider("Stress", 1, 10, 5)
        soreness = st.slider("Soreness", 1, 10, 5)
        hydration = st.slider("Hydration", 1, 10, 6)

        protein_on_track = st.selectbox(
            "Protein on track yesterday?",
            ["yes", "unsure", "no"],
            index=1,
        )

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

    st.subheader("Combat Training Context")

    col3, col4, col5 = st.columns(3)

    with col3:
        combat_last_24h = st.checkbox("BJJ/Muay Thai in last 24 hours?")

    with col4:
        hard_sparring_last_24h = st.checkbox("Hard sparring or hard rolling in last 24 hours?")

    with col5:
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

    st.success("Check-in saved and workout generated.")


if "latest_checkin" in st.session_state and "latest_workout" in st.session_state:
    checkin = st.session_state["latest_checkin"]
    workout = st.session_state["latest_workout"]
    workout_id = st.session_state["latest_workout_id"]
    explanation = st.session_state["latest_readiness_explanation"]

    st.divider()

    st.subheader("Today's Readiness")

    readiness_category = checkin["readiness_category"]
    readiness_score = checkin["readiness_score"]

    if readiness_category == "Green":
        st.success(f"Green Day — Readiness Score: {readiness_score}/10")
    elif readiness_category == "Yellow":
        st.info(f"Yellow Day — Readiness Score: {readiness_score}/10")
    elif readiness_category == "Orange":
        st.warning(f"Orange Day — Readiness Score: {readiness_score}/10")
    else:
        st.error(f"Red Day — Readiness Score: {readiness_score}/10")

    st.write(explanation)

    st.divider()

    st.subheader("Generated Workout")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.metric("Workout Type", workout["workout_type"])

    with col_b:
        st.metric("Focus", workout["focus"])

    with col_c:
        st.metric("Estimated Duration", f"{workout['estimated_duration']} min")

    st.info(workout["generation_reason"])

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

    st.divider()

    st.subheader("Log Completed Sets")

    st.write(
        """
        Enter what you actually completed. For bodyweight or accessory movements,
        leave weight at 0 if you do not want to track load.
        """
    )

    with st.form("set_logging_form"):
        all_set_entries = []

        for exercise_index, exercise in enumerate(workout["exercises"], start=1):
            st.markdown(f"### {exercise_index}. {exercise['exercise_name']}")

            st.caption(
                f"Target: {exercise['planned_sets']} sets x "
                f"{exercise['planned_reps_min']}-{exercise['planned_reps_max']} reps "
                f"@ RPE {exercise['target_rpe']}"
            )

            if exercise["planned_weight"] and exercise["planned_weight"] > 0:
                default_weight = float(exercise["planned_weight"])
            else:
                default_weight = 0.0

            planned_sets = int(exercise["planned_sets"])

            for set_number in range(1, planned_sets + 1):
                col_w, col_r, col_rpe, col_notes = st.columns([1, 1, 1, 2])

                with col_w:
                    weight = st.number_input(
                        f"Weight set {set_number}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=default_weight,
                        step=2.5,
                        key=f"weight_{exercise_index}_{set_number}",
                    )

                with col_r:
                    reps = st.number_input(
                        f"Reps set {set_number}",
                        min_value=0,
                        max_value=100,
                        value=int(exercise["planned_reps_min"]),
                        step=1,
                        key=f"reps_{exercise_index}_{set_number}",
                    )

                with col_rpe:
                    rpe = st.number_input(
                        f"RPE set {set_number}",
                        min_value=0.0,
                        max_value=10.0,
                        value=float(exercise["target_rpe"]),
                        step=0.5,
                        key=f"rpe_{exercise_index}_{set_number}",
                    )

                with col_notes:
                    notes = st.text_input(
                        f"Notes set {set_number}",
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


with st.expander("Latest check-in data"):
    if "latest_checkin" in st.session_state:
        st.json(st.session_state["latest_checkin"])
    else:
        st.write("No check-in submitted yet.")
