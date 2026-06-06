import streamlit as st

from src.database import (
    init_db,
    read_table,
    delete_workout,
    delete_checkin,
)


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
        "Cleanup Tools",
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

with tabs[5]:
    st.subheader("Cleanup Tools")

    st.warning(
        "Use this if you accidentally generated test workouts or check-ins. Deleting a workout also deletes its planned exercises and completed sets."
    )

    sessions = read_table("workout_sessions")
    checkins = read_table("daily_checkins")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Delete Workout")

        if sessions.empty:
            st.info("No workouts to delete.")
        else:
            workout_options = sessions.sort_values("id", ascending=False).copy()
            workout_options["label"] = workout_options.apply(
                lambda row: f"ID {row['id']} — {row['date']} — {row['workout_type']} — {row['focus']}",
                axis=1,
            )

            selected_workout_label = st.selectbox(
                "Choose workout to delete",
                workout_options["label"].tolist(),
            )

            selected_workout_id = int(
                workout_options[workout_options["label"] == selected_workout_label]["id"].iloc[0]
            )

            confirm_delete_workout = st.checkbox("Confirm workout deletion")

            if st.button(
                "Delete Selected Workout",
                disabled=not confirm_delete_workout,
                use_container_width=True,
            ):
                delete_workout(selected_workout_id)
                st.success(f"Workout {selected_workout_id} deleted.")
                st.rerun()

    with col2:
        st.markdown("### Delete Check-In")

        if checkins.empty:
            st.info("No check-ins to delete.")
        else:
            checkin_options = checkins.sort_values("id", ascending=False).copy()
            checkin_options["label"] = checkin_options.apply(
                lambda row: f"ID {row['id']} — {row['date']} — {row['readiness_category']} — {row['readiness_score']}/10",
                axis=1,
            )

            selected_checkin_label = st.selectbox(
                "Choose check-in to delete",
                checkin_options["label"].tolist(),
            )

            selected_checkin_id = int(
                checkin_options[checkin_options["label"] == selected_checkin_label]["id"].iloc[0]
            )

            confirm_delete_checkin = st.checkbox("Confirm check-in deletion")

            if st.button(
                "Delete Selected Check-In",
                disabled=not confirm_delete_checkin,
                use_container_width=True,
            ):
                delete_checkin(selected_checkin_id)
                st.success(f"Check-in {selected_checkin_id} deleted.")
                st.rerun()
