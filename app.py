import streamlit as st

st.set_page_config(
    page_title="Combat Athlete Training Tracker",
    page_icon="🥋",
    layout="wide",
)

st.title("Combat Athlete Training Tracker")

st.subheader("Adaptive strength training for BJJ, Muay Thai, and cutting.")

st.write(
    """
    This app will help track daily readiness, generate adaptive full-body workouts,
    log sets/reps/weight/RPE, and export long-term progress data.
    """
)

st.info("Build status: foundation setup complete.")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Current Bodyweight", "218 lb")

with col2:
    st.metric("Goal Bodyweight", "200 lb")

with col3:
    st.metric("Lifting Days", "Mon / Wed / Sat")

st.divider()

st.page_link("pages/1_Start_Workout.py", label="Start Workout", icon="🏋️")
st.page_link("pages/3_Analytics.py", label="View Analytics", icon="📊")
st.page_link("pages/4_Export_Center.py", label="Export Data", icon="📥")
