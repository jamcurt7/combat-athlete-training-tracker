import streamlit as st

from src.database import (
    init_db,
    read_table,
    delete_workout,
    delete_checkin,
    get_active_user_id,
    get_user_by_id,
)
from src.ui import page_header


st.set_page_config(page_title="Workout History", page_icon="📋", layout="wide")

init_db()

active_user_id = get_active_user_id()
active_user = get_user_by_id(active_user_id)
active_name = active_user["display_name"] if active_user else "User"

page_header(
    "Workout History",
    f"Review saved workouts, planned exercises, completed sets, check-ins, and progression state for {active_name}.",
)

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
    st.subheader(f"Workout Sessions — {active_name}")

    sessions = read_table("workout_sessions")

    if sessions.empty:
        st.info("No workout sessions saved yet for this profile.")
    else:
        st.dataframe(
            sessions.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tabs[1]:
    st.subheader(f"Completed Sets — {active_name}")

    sets = read_table("completed_sets")

    if sets.empty:
        st.info("No completed sets logged yet for this profile.")
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
    st.subheader(f"Planned Exercises — {active_name}")

    planned = read_table("planned_exercises")

    if planned.empty:
        st.info("No planned exercises saved yet for this profile.")
    else:
        st.dataframe(
            planned.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tabs[3]:
    st.subheader(f"Daily Check-Ins — {active_name}")

    checkins = read_table("daily_checkins")

    if checkins.empty:
        st.info("No daily check-ins saved yet for this profile.")
    else:
        st.dataframe(
            checkins.sort_values("id", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with tabs[4]:
    st.subheader(f"Progression State — {active_name}")

    progression = read_table("progression_state")

    if progression.empty:
        st.info("No progression state available yet for this profile.")
    else:
        st.dataframe(
            progression,
            use_container_width=True,
            hide_index=True,
        )

with tabs[5]:
    st.subheader(f"Cleanup Tools — {active_name}")

    st.warning(
        "Use this if you accidentally generated test workouts or check-ins. "
        "Deleting a workout also deletes its planned exercises and completed sets for the active profile."
    )

    sessions = read_table("workout_sessions")
    checkins = read_table("daily_checkins")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Delete Workout")

        if sessions.empty:
            st.info("No workouts to delete for this profile.")
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
                st.success(f"Workout {selected_workout_id} deleted for {active_name}.")
                st.rerun()

    with col2:
        st.markdown("### Delete Check-In")

        if checkins.empty:
            st.info("No check-ins to delete for this profile.")
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
                st.success(f"Check-in {selected_checkin_id} deleted for {active_name}.")
                st.rerun()
