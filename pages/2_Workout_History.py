import streamlit as st

from src.database import init_db, read_table


st.set_page_config(page_title="Workout History", page_icon="📋", layout="wide")

init_db()

st.title("Workout History")

st.write("Review saved workouts, planned exercises, completed sets, check-ins, and progression state.")

tabs = st.tabs(
    [
        "Workout Sessions",
        "Completed Sets",
        "Planned Exercises",
        "Daily Check-Ins",
        "Progression State",
    ]
)

with tabs[0]:
    st.subheader("Workout Sessions")

    sessions = read_table("workout_sessions")

    if sessions.empty:
        st.info("No workout sessions saved yet.")
    else:
        st.dataframe(
            sessions.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tabs[1]:
    st.subheader("Completed Sets")

    sets = read_table("completed_sets")

    if sets.empty:
        st.info("No completed sets logged yet.")
    else:
        exercise_options = ["All"] + sorted(sets["exercise_name"].dropna().unique().tolist())
        selected_exercise = st.selectbox("Filter by exercise", exercise_options)

        filtered_sets = sets.copy()

        if selected_exercise != "All":
            filtered_sets = filtered_sets[filtered_sets["exercise_name"] == selected_exercise]

        st.dataframe(
            filtered_sets.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tabs[2]:
    st.subheader("Planned Exercises")

    planned = read_table("planned_exercises")

    if planned.empty:
        st.info("No planned exercises saved yet.")
    else:
        st.dataframe(
            planned.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tabs[3]:
    st.subheader("Daily Check-Ins")

    checkins = read_table("daily_checkins")

    if checkins.empty:
        st.info("No daily check-ins saved yet.")
    else:
        st.dataframe(
            checkins.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tabs[4]:
    st.subheader("Progression State")

    progression = read_table("progression_state")

    if progression.empty:
        st.info("No progression state available yet.")
    else:
        st.dataframe(
            progression,
            use_container_width=True,
            hide_index=True,
        )
