import pandas as pd
import streamlit as st

from src.database import init_db, read_table, get_setting
from src.seed_data import seed_all
from src.analytics import (
    calculate_summary_metrics,
    calculate_readiness_summary,
    calculate_bodyweight_trend,
)
from src.charts import plot_readiness_trend, plot_bodyweight
from src.ui import app_storage_warning


st.set_page_config(
    page_title="Combat Athlete Training Tracker",
    page_icon="🥋",
    layout="wide",
)

init_db()

if "seeded" not in st.session_state:
    seed_all()
    st.session_state.seeded = True

st.title("Combat Athlete Training Tracker")

st.subheader("Adaptive strength training for BJJ, Muay Thai, and cutting.")

app_storage_warning()

current_bodyweight = float(get_setting("current_bodyweight", 218))
goal_bodyweight = float(get_setting("goal_bodyweight", 200))
primary_goal = get_setting(
    "primary_goal",
    "Cut while maintaining strength and improving conditioning",
)
selected_template_key = get_setting("selected_template_key", "balanced")

st.divider()

st.subheader("Current Goal")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current Bodyweight", f"{current_bodyweight} lb")

with col2:
    st.metric("Goal Bodyweight", f"{goal_bodyweight} lb")

with col3:
    remaining = round(current_bodyweight - goal_bodyweight, 1)
    st.metric("Remaining", f"{remaining} lb")

with col4:
    st.metric("Lifting Days", "Mon / Wed / Sat")

st.write(f"**Primary goal:** {primary_goal}")
st.write(f"**Current template bias:** {selected_template_key}")

st.divider()

st.subheader("Quick Navigation")

col_a, col_b, col_c, col_d, col_e = st.columns(5)

with col_a:
    st.page_link("pages/1_Start_Workout.py", label="Start Workout", icon="🏋️")

with col_b:
    st.page_link("pages/2_Workout_History.py", label="Workout History", icon="📋")

with col_c:
    st.page_link("pages/3_Analytics.py", label="Analytics", icon="📊")

with col_d:
    st.page_link("pages/4_Export_Center.py", label="Export Data", icon="📥")

with col_e:
    st.page_link("pages/6_Program_Templates.py", label="Templates", icon="🧠")
st.divider()

metrics = calculate_summary_metrics()

st.subheader("Training Database Snapshot")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Check-Ins", metrics.get("checkins_logged", 0))

with m2:
    st.metric("Workouts Generated", metrics.get("workouts_generated", 0))

with m3:
    st.metric("Completed Sets", metrics.get("completed_sets_logged", 0))

with m4:
    st.metric("Avg Readiness", metrics.get("avg_readiness", 0))

st.divider()

st.subheader("Recent Trends")

trend_col1, trend_col2 = st.columns(2)

with trend_col1:
    readiness = calculate_readiness_summary()

    if readiness.empty:
        st.info("No readiness data yet.")
    else:
        fig = plot_readiness_trend(readiness)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

with trend_col2:
    bodyweight = calculate_bodyweight_trend()

    if bodyweight.empty:
        st.info("No bodyweight data yet.")
    else:
        fig = plot_bodyweight(bodyweight)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

st.divider()

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
