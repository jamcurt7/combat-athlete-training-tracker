from datetime import date

import pandas as pd
import streamlit as st

from src.database import (
    init_db,
    insert_checkin,
    insert_workout_session,
    insert_planned_exercise,
)
from src.readiness_engine import calculate_readiness_score
from src.workout_generator import generate_workout


st.set_page_config(page_title="Start Workout", page_icon="🏋️", layout="wide")

init_db()

st.title("Start Workout")

st.write(
    """
    Complete the daily check-in first. The app will use this to decide whether today should be
    a push day, normal day, light/accessory day, or recovery day.
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

    st.success("Check-in saved and workout generated.")

if "latest_checkin" in st.session_state and "latest_workout" in st.session_state:
    checkin = st.session_state["latest_checkin"]
    workout = st.session_state["latest_workout"]
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

    for index, exercise in enumerate(workout["exercises"], start=1):
        with st.expander(f"{index}. {exercise['exercise_name']}"):
            st.write(f"**Movement Pattern:** {exercise['movement_pattern']}")
            st.write(f"**Category:** {exercise['exercise_category']}")
            st.write(
                f"**Prescription:** {exercise['planned_sets']} sets x "
                f"{exercise['planned_reps_min']}-{exercise['planned_reps_max']} reps"
            )

            if exercise["planned_weight"] and exercise["planned_weight"] > 0:
                st.write(f"**Suggested Weight:** {exercise['planned_weight']} lb")
            else:
                st.write("**Suggested Weight:** Choose based on target RPE")

            st.write(f"**Target RPE:** {exercise['target_rpe']}")
            st.write(f"**Notes:** {exercise['notes']}")

    st.warning(
        "Set logging is coming in the next step. For now, the app saves the generated workout as the plan."
    )

with st.expander("Latest check-in data"):
    if "latest_checkin" in st.session_state:
        st.json(st.session_state["latest_checkin"])
    else:
        st.write("No check-in submitted yet.")
