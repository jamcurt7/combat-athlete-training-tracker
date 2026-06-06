import streamlit as st

from src.database import (
    init_db,
    read_table,
    get_setting,
    set_setting,
    reset_database,
    upsert_progression_state,
)
from src.seed_data import seed_all
from src.ui import page_header, app_storage_warning


st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

init_db()

page_header(
    "Settings",
    "Edit your goals, training loads, and app data.",
)

app_storage_warning()

tabs = st.tabs(
    [
        "Bodyweight & Goals",
        "Training Loads",
        "Exercise Library",
        "Database Tools",
    ]
)

with tabs[0]:
    st.subheader("Bodyweight & Goal Settings")

    current_bodyweight = float(get_setting("current_bodyweight", 218))
    goal_bodyweight = float(get_setting("goal_bodyweight", 200))
    primary_goal = get_setting(
        "primary_goal",
        "Cut while maintaining strength and improving conditioning",
    )

    with st.form("goal_settings_form"):
        new_current_bodyweight = st.number_input(
            "Current bodyweight",
            min_value=0.0,
            max_value=500.0,
            value=current_bodyweight,
            step=0.2,
        )

        new_goal_bodyweight = st.number_input(
            "Goal bodyweight",
            min_value=0.0,
            max_value=500.0,
            value=goal_bodyweight,
            step=0.2,
        )

        new_primary_goal = st.text_area(
            "Primary goal",
            value=primary_goal,
        )

        save_goal_settings = st.form_submit_button(
            "Save Goal Settings",
            use_container_width=True,
        )

    if save_goal_settings:
        set_setting("current_bodyweight", new_current_bodyweight)
        set_setting("goal_bodyweight", new_goal_bodyweight)
        set_setting("primary_goal", new_primary_goal)

        st.success("Goal settings saved.")

    st.divider()

    st.subheader("Current App Defaults")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Current Bodyweight", f"{get_setting('current_bodyweight', 218)} lb")

    with col2:
        st.metric("Goal Bodyweight", f"{get_setting('goal_bodyweight', 200)} lb")

    with col3:
        weight_to_lose = float(get_setting("current_bodyweight", 218)) - float(
            get_setting("goal_bodyweight", 200)
        )
        st.metric("Remaining Cut", f"{round(weight_to_lose, 1)} lb")

with tabs[1]:
    st.subheader("Training Loads")

    st.write(
        """
        These are the current training loads used by the workout generator.
        Keep these conservative. The progression engine will increase them slowly.
        """
    )

    progression = read_table("progression_state")

    if progression.empty:
        st.info("No progression data found. Use the seed button in Database Tools.")
    else:
        edited_progression = st.data_editor(
            progression,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "exercise_name": st.column_config.TextColumn(disabled=True),
                "movement_pattern": st.column_config.TextColumn(disabled=True),
                "exercise_category": st.column_config.TextColumn(disabled=True),
                "current_training_load": st.column_config.NumberColumn(
                    "Current Training Load",
                    min_value=0.0,
                    step=2.5,
                ),
                "target_sets": st.column_config.NumberColumn(
                    "Target Sets",
                    min_value=1,
                    step=1,
                ),
                "target_reps_min": st.column_config.NumberColumn(
                    "Min Reps",
                    min_value=1,
                    step=1,
                ),
                "target_reps_max": st.column_config.NumberColumn(
                    "Max Reps",
                    min_value=1,
                    step=1,
                ),
                "next_recommended_load": st.column_config.NumberColumn(
                    "Next Recommended Load",
                    min_value=0.0,
                    step=2.5,
                ),
            },
        )

        if st.button("Save Training Load Changes", use_container_width=True):
            for _, row in edited_progression.iterrows():
                upsert_progression_state(row.to_dict())

            st.success("Training loads saved.")

with tabs[2]:
    st.subheader("Exercise Library")

    exercises = read_table("exercise_library")

    if exercises.empty:
        st.info("No exercises found. Use the seed button in Database Tools.")
    else:
        st.dataframe(
            exercises.sort_values(["exercise_category", "exercise_name"]),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Exercise editing will come later. For now, this shows what the workout generator can pull from."
        )

with tabs[3]:
    st.subheader("Database Tools")

    st.warning(
        "Be careful here. Resetting the database deletes your saved check-ins, workouts, sets, and progression data."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Reseed Default Data", use_container_width=True):
            seed_all()
            st.success("Default settings, exercises, and progression state reseeded.")

    with col2:
        confirm_reset = st.checkbox("I understand reset deletes my app data.")

        if st.button("Reset Database", use_container_width=True, disabled=not confirm_reset):
            reset_database()
            seed_all()
            st.success("Database reset and default data reseeded.")

    st.divider()

    st.subheader("Raw Table Counts")

    table_names = [
        "settings",
        "exercise_library",
        "daily_checkins",
        "workout_sessions",
        "planned_exercises",
        "completed_sets",
        "progression_state",
    ]

    counts = []

    for table in table_names:
        try:
            df = read_table(table)
            counts.append({"table": table, "rows": len(df)})
        except Exception as e:
            counts.append({"table": table, "rows": f"Error: {e}"})

    st.dataframe(counts, use_container_width=True, hide_index=True)
