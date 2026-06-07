import streamlit as st

from src.database import (
    init_db,
    read_table,
    get_setting,
    get_users,
    set_active_user,
    get_active_user_id,
    get_user_by_id,
)
from src.seed_data import seed_all
from src.analytics import (
    calculate_summary_metrics,
    calculate_readiness_summary,
    calculate_bodyweight_trend,
)
from src.charts import plot_readiness_trend, plot_bodyweight
from src.ui import (
    inject_global_styles,
    home_banner,
    command_card,
    mini_stat,
    mission_card,
    app_storage_warning,
)


st.set_page_config(
    page_title="Home",
    page_icon="🥋",
    layout="wide",
)

inject_global_styles()
init_db()


def profile_selector() -> None:
    users = get_users()

    if users.empty:
        st.error("No user profiles found. Go to Settings after the app loads and create a profile.")
        return

    current_user_id = get_active_user_id()
    user_ids = users["id"].astype(int).tolist()

    if current_user_id not in user_ids:
        current_user_id = user_ids[0]

    current_index = user_ids.index(current_user_id)

    display_options = [
        f"{row['display_name'] or row['name']}"
        for _, row in users.iterrows()
    ]

    selected_display = st.selectbox(
        "Who is using the app?",
        options=display_options,
        index=current_index,
        key="home_profile_selector",
    )

    selected_row = users.iloc[display_options.index(selected_display)]
    selected_user_id = int(selected_row["id"])
    selected_name = str(selected_row["display_name"] or selected_row["name"])

    set_active_user(selected_user_id, selected_name)

    st.success(f"Active profile: {selected_name}")


profile_selector()

active_user_id = get_active_user_id()
active_user = get_user_by_id(active_user_id)
active_name = active_user["display_name"] if active_user else "User"

if st.session_state.get("seeded_user_id") != active_user_id:
    seed_all()
    st.session_state["seeded_user_id"] = active_user_id

home_banner()

current_bodyweight = float(get_setting("current_bodyweight", 218))
goal_bodyweight = float(get_setting("goal_bodyweight", 200))
primary_goal = get_setting(
    "primary_goal",
    "Cut while maintaining strength and improving conditioning",
)
selected_template_key = get_setting("selected_template_key", "balanced")

remaining = round(current_bodyweight - goal_bodyweight, 1)

st.subheader(f"{active_name}'s Command Center")

c1, c2, c3, c4 = st.columns(4)

with c1:
    mini_stat("Current", f"{current_bodyweight} lb")

with c2:
    mini_stat("Goal", f"{goal_bodyweight} lb")

with c3:
    mini_stat("Remaining", f"{remaining} lb")

with c4:
    mini_stat("Lift Days", "M / W / S")

mission_card(primary_goal, selected_template_key)

st.divider()

st.subheader("Primary Actions")

a1, a2, a3 = st.columns(3)

with a1:
    command_card(
        title="Start Workout",
        description="Run the daily check-in, generate today’s adaptive workout, and log completed sets.",
        page="pages/1_Start_Workout.py",
        icon_file="strength.svg",
        button_label="Start Today’s Workout",
    )

with a2:
    command_card(
        title="Analytics",
        description="Review readiness, bodyweight, strength, volume, and RPE trends.",
        page="pages/3_Analytics.py",
        icon_file="analytics.svg",
        button_label="View Analytics",
    )

with a3:
    command_card(
        title="Export Center",
        description="Download your data as Excel, CSV, and PNG charts for backup and long-term review.",
        page="pages/4_Export_Center.py",
        icon_file="export.svg",
        button_label="Download Data",
    )

st.subheader("Secondary Tools")

b1, b2, b3 = st.columns(3)

with b1:
    command_card(
        title="Workout History",
        description="Inspect saved workouts, check-ins, planned exercises, completed sets, and progression state.",
        page="pages/2_Workout_History.py",
        icon_file="readiness.svg",
        button_label="Open History",
    )

with b2:
    command_card(
        title="Program Templates",
        description="Choose the generator’s bias: strength, posterior chain, upper grip, accessories, or recovery.",
        page="pages/6_Program_Templates.py",
        icon_file="templates.svg",
        button_label="Choose Template",
    )

with b3:
    command_card(
        title="Settings",
        description="Edit bodyweight goals, training loads, exercise defaults, users, and database tools.",
        page="pages/5_Settings.py",
        icon_file="settings.svg",
        button_label="Open Settings",
    )

st.divider()

metrics = calculate_summary_metrics()

st.subheader("Training Snapshot")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Check-Ins", metrics.get("checkins_logged", 0))

with m2:
    st.metric("Workouts", metrics.get("workouts_generated", 0))

with m3:
    st.metric("Sets Logged", metrics.get("completed_sets_logged", 0))

with m4:
    st.metric("Avg Readiness", metrics.get("avg_readiness", 0))

st.divider()

st.subheader("Recent Trends")

trend_col1, trend_col2 = st.columns(2)

with trend_col1:
    readiness = calculate_readiness_summary()

    if readiness.empty:
        st.info("No readiness data yet. Complete a daily check-in to populate this chart.")
    else:
        fig = plot_readiness_trend(readiness)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

with trend_col2:
    bodyweight = calculate_bodyweight_trend()

    if bodyweight.empty:
        st.info("No bodyweight data yet. Enter bodyweight during check-ins to populate this chart.")
    else:
        fig = plot_bodyweight(bodyweight)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

st.divider()

app_storage_warning()

with st.expander("Database status for active profile"):
    try:
        checkins = read_table("daily_checkins")
        workouts = read_table("workout_sessions")
        completed_sets = read_table("completed_sets")
        exercises = read_table("exercise_library")
        progression = read_table("progression_state")

        status_data = [
            {"table": "daily_checkins", "rows": len(checkins)},
            {"table": "workout_sessions", "rows": len(workouts)},
            {"table": "completed_sets", "rows": len(completed_sets)},
            {"table": "exercise_library", "rows": len(exercises)},
            {"table": "progression_state", "rows": len(progression)},
        ]

        st.dataframe(status_data, use_container_width=True, hide_index=True)

        st.subheader("Current Main Lift Progression")
        st.dataframe(progression, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Database check failed: {e}")
