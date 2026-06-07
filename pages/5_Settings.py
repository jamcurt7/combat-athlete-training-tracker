import streamlit as st

from src.database import (
    init_db,
    read_table,
    get_setting,
    set_setting,
    reset_database,
    upsert_progression_state,
    get_personalization_settings,
    save_personalization_settings,
)
from src.seed_data import seed_all
from src.exercise_catalog import get_exercise_catalog
from src.ui import page_header, app_storage_warning


st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

init_db()

page_header(
    "Settings",
    "Edit your goals, training loads, personalization, and app data.",
)

app_storage_warning()


def get_catalog_exercise_names() -> list[str]:
    try:
        catalog = get_exercise_catalog()
        names = sorted({exercise.get("exercise_name", "") for exercise in catalog if exercise.get("exercise_name")})
        return names
    except Exception:
        return []


def clean_existing_selection(existing: list[str], options: list[str]) -> list[str]:
    option_set = set(options)
    return [item for item in existing if item in option_set]


tabs = st.tabs(
    [
        "Bodyweight & Goals",
        "Training Loads",
        "Personalization",
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
    st.subheader("Personalization")

    st.write(
        """
        These settings give the workout generator a long-term personality.
        The daily check-in still controls readiness and intensity, but these settings influence exercise selection,
        fatigue limits, mobility targets, cardio style, and training method bias.
        """
    )

    personalization = get_personalization_settings()

    equipment_options = [
        "barbell",
        "dumbbells",
        "kettlebell",
        "trap bar",
        "landmine",
        "cable",
        "machine",
        "bodyweight",
        "pull-up bar",
        "rings",
        "bands",
        "sled",
        "bike",
        "rower",
        "treadmill",
        "jump rope",
        "foam roller",
        "lacrosse ball",
    ]

    mobility_options = [
        "hips",
        "t-spine",
        "thoracic",
        "shoulders",
        "ankles",
        "neck",
        "adductors",
        "hamstrings",
        "upper back",
        "wrists",
        "breathing",
    ]

    exercise_names = get_catalog_exercise_names()

    with st.form("personalization_settings_form"):
        preferred_equipment = st.multiselect(
            "Preferred equipment",
            options=equipment_options,
            default=[item for item in personalization["preferred_equipment"] if item in equipment_options],
            help="The selector gives a small bonus to exercises that use this equipment.",
        )

        mobility_priorities = st.multiselect(
            "Mobility priorities",
            options=mobility_options,
            default=[item for item in personalization["mobility_priorities"] if item in mobility_options],
            help="Mobility and stretching selections will bias these regions.",
        )

        cardio_preference = st.selectbox(
            "Cardio preference",
            options=[
                "Mixed",
                "Technical combat",
                "Machine",
                "Low impact",
                "App decides",
            ],
            index=[
                "Mixed",
                "Technical combat",
                "Machine",
                "Low impact",
                "App decides",
            ].index(personalization.get("cardio_preference", "Mixed"))
            if personalization.get("cardio_preference", "Mixed")
            in ["Mixed", "Technical combat", "Machine", "Low impact", "App decides"]
            else 0,
            help="Technical combat biases shadow boxing, footwork, jump rope, and Muay Thai-style cardio.",
        )

        strength_method_preference = st.selectbox(
            "Strength method preference",
            options=[
                "App decides",
                "Standard strength",
                "Conjugate-inspired",
                "Isometrics",
                "Repeated effort",
            ],
            index=[
                "App decides",
                "Standard strength",
                "Conjugate-inspired",
                "Isometrics",
                "Repeated effort",
            ].index(personalization.get("strength_method_preference", "App decides"))
            if personalization.get("strength_method_preference", "App decides")
            in ["App decides", "Standard strength", "Conjugate-inspired", "Isometrics", "Repeated effort"]
            else 0,
            help="This does not force bad choices; it nudges the algorithm when readiness allows.",
        )

        exercise_variety_preference = st.selectbox(
            "Exercise variety preference",
            options=[
                "Balanced",
                "Higher variety",
                "Repeat proven exercises",
            ],
            index=[
                "Balanced",
                "Higher variety",
                "Repeat proven exercises",
            ].index(personalization.get("exercise_variety_preference", "Balanced"))
            if personalization.get("exercise_variety_preference", "Balanced")
            in ["Balanced", "Higher variety", "Repeat proven exercises"]
            else 0,
            help="Higher variety increases the penalty for exercises used recently.",
        )

        max_session_fatigue_preference = st.slider(
            "Max session fatigue preference",
            min_value=0,
            max_value=40,
            value=int(personalization.get("max_session_fatigue_preference", 0)),
            step=1,
            help="Set to 0 to let the app decide. Otherwise, this caps the session fatigue budget.",
        )

        avoided_exercises = st.multiselect(
            "Avoided exercises",
            options=exercise_names,
            default=clean_existing_selection(personalization["avoided_exercises"], exercise_names),
            help="The selector will strongly avoid these unless no other option exists.",
        )

        favorite_exercises = st.multiselect(
            "Favorite exercises",
            options=exercise_names,
            default=clean_existing_selection(personalization["favorite_exercises"], exercise_names),
            help="The selector gives these a bonus when they fit the slot.",
        )

        save_personalization = st.form_submit_button(
            "Save Personalization Settings",
            use_container_width=True,
        )

    if save_personalization:
        save_personalization_settings(
            {
                "preferred_equipment": preferred_equipment,
                "mobility_priorities": mobility_priorities,
                "cardio_preference": cardio_preference,
                "strength_method_preference": strength_method_preference,
                "exercise_variety_preference": exercise_variety_preference,
                "max_session_fatigue_preference": max_session_fatigue_preference,
                "avoided_exercises": avoided_exercises,
                "favorite_exercises": favorite_exercises,
            }
        )

        st.success("Personalization settings saved.")

    st.divider()

    st.subheader("Current Personalization Summary")

    latest = get_personalization_settings()

    p1, p2, p3 = st.columns(3)

    with p1:
        st.metric("Cardio Bias", latest["cardio_preference"])
        st.metric("Strength Bias", latest["strength_method_preference"])

    with p2:
        st.metric("Variety", latest["exercise_variety_preference"])
        fatigue_cap = latest["max_session_fatigue_preference"]
        st.metric("Fatigue Cap", "App decides" if fatigue_cap == 0 else fatigue_cap)

    with p3:
        st.metric("Avoided Exercises", len(latest["avoided_exercises"]))
        st.metric("Favorites", len(latest["favorite_exercises"]))

    with st.expander("View raw personalization settings"):
        st.json(latest)

with tabs[3]:
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
            "Exercise editing will come later. For now, this shows the database exercise library. "
            "The newer generator also uses the structured catalog in src/exercise_catalog.py."
        )

with tabs[4]:
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
