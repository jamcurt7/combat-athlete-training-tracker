import streamlit as st

from src.database import init_db, read_table


st.set_page_config(
    page_title="Combat Athlete Training Tracker",
    page_icon="🥋",
    layout="wide",
)

init_db()

st.title("Combat Athlete Training Tracker")

st.subheader("Adaptive strength training for BJJ, Muay Thai, and cutting.")

st.write(
    """
    This app helps track daily readiness, generate adaptive full-body workouts,
    log sets/reps/weight/RPE, and export long-term progress data.
    """
)

st.success("Database initialized successfully.")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Current Bodyweight", "218 lb")

with col2:
    st.metric("Goal Bodyweight", "200 lb")

with col3:
    st.metric("Lifting Days", "Mon / Wed / Sat")

st.divider()

st.subheader("Quick Navigation")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.page_link("pages/1_Start_Workout.py", label="Start Workout", icon="🏋️")

with col_b:
    st.page_link("pages/3_Analytics.py", label="View Analytics", icon="📊")

with col_c:
    st.page_link("pages/4_Export_Center.py", label="Export Data", icon="📥")

st.divider()

with st.expander("Database status"):
    try:
        checkins = read_table("daily_checkins")
        workouts = read_table("workout_sessions")
        completed_sets = read_table("completed_sets")

        st.write(f"Daily check-ins saved: {len(checkins)}")
        st.write(f"Workout sessions saved: {len(workouts)}")
        st.write(f"Completed sets saved: {len(completed_sets)}")
    except Exception as e:
        st.error(f"Database check failed: {e}")
