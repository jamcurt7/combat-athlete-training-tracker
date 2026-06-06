import streamlit as st

from src.database import init_db, read_table, get_setting
from src.seed_data import seed_all
from src.analytics import (
    calculate_summary_metrics,
    calculate_readiness_summary,
    calculate_bodyweight_trend,
)
from src.charts import plot_readiness_trend, plot_bodyweight
from src.ui import (
    inject_global_styles,
    page_header,
    app_storage_warning,
    nav_card,
)


st.set_page_config(
    page_title="Combat Athlete Training Tracker",
    page_icon="🥋",
    layout="wide",
)

inject_global_styles()
init_db()

if "seeded" not in st.session_state:
    seed_all()
    st.session_state.seeded = True

page_header(
    "Combat Athlete Training Tracker",
    "Adaptive strength training for BJJ, Muay Thai, cutting, and long-term performance tracking.",
)

current_bodyweight = float(get_setting("current_bodyweight", 218))
goal_bodyweight = float(get_setting("goal_bodyweight", 200))
primary_goal = get_setting(
    "primary_goal",
    "Cut while maintaining strength and improving conditioning",
)
selected_template_key = get_setting("selected_template_key", "balanced")

st.subheader("Current Mission")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current", f"{current_bodyweight} lb")

with col2:
    st.metric("Goal", f"{goal_bodyweight} lb")

with col3:
    remaining = round(current_bodyweight - goal_bodyweight, 1)
    st.metric("Remaining", f"{remaining} lb")

with col4:
    st.metric("Lift Days", "Mon / Wed / Sat")

with st.container(border=True):
    st.write(f"**Primary goal:** {primary_goal}")
    st.write(f"**Current training bias:** {selected_template_key}")
    st.write("**Combat training:** Tuesday / Thursday / Friday / Sunday")

st.divider()

st.subheader("Start Here")

nav1, nav2, nav3 = st.columns(3)

with nav1:
    nav_card(
        title="Start Workout",
        description="Run the daily check-in, generate today's workout, and log completed sets.",
        page="pages/1_Start_Workout.py",
        icon="🏋️",
    )

with nav2:
    nav_card(
        title="Analytics",
        description="Review readiness, bodyweight, strength, volume, and RPE trends.",
        page="pages/3_Analytics.py",
        icon="📊",
    )

with nav3:
    nav_card(
        title="Export Center",
        description="Download your data as Excel, CSV, and PNG charts.",
        page="pages/4_Export_Center.py",
        icon="📥",
    )

nav4, nav5, nav6 = st.columns(3)

with nav4:
    nav_card(
        title="Workout History",
        description="Inspect saved workouts, check-ins, planned exercises, and progression state.",
        page="pages/2_Workout_History.py",
        icon="📋",
    )

with nav5:
    nav_card(
        title="Program Templates",
        description="Choose whether the generator biases strength, posterior chain, upper grip, accessories, or recovery.",
        page="pages/6_Program_Templates.py",
        icon="🧠",
    )

with nav6:
    nav_card(
        title="Settings",
        description="Edit bodyweight goals, training loads, and database tools.",
        page="pages/5_Settings.py",
        icon="⚙️",
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

with st.expander("Database status"):
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
