import streamlit as st

from src.database import init_db
from src.analytics import (
    calculate_summary_metrics,
    calculate_readiness_summary,
    calculate_bodyweight_trend,
    calculate_estimated_1rm_trend,
    calculate_weekly_volume,
    calculate_average_rpe_by_exercise,
    calculate_exercise_summary,
)
from src.charts import (
    plot_readiness_trend,
    plot_energy_sleep_soreness,
    plot_bodyweight,
    plot_estimated_1rm,
    plot_weekly_volume,
    plot_average_rpe,
)


st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")

init_db()

st.title("Analytics")

st.write("View readiness, bodyweight, strength, volume, and RPE trends.")

metrics = calculate_summary_metrics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Check-Ins", metrics.get("checkins_logged", 0))

with col2:
    st.metric("Workouts", metrics.get("workouts_generated", 0))

with col3:
    st.metric("Completed Sets", metrics.get("completed_sets_logged", 0))

with col4:
    st.metric("Avg Readiness", metrics.get("avg_readiness", 0))

st.divider()

tabs = st.tabs(
    [
        "Readiness",
        "Bodyweight",
        "Strength",
        "Volume",
        "RPE",
        "Exercise Summary",
    ]
)

with tabs[0]:
    st.subheader("Readiness Trends")

    readiness = calculate_readiness_summary()

    if readiness.empty:
        st.info("No readiness data yet. Complete daily check-ins first.")
    else:
        fig = plot_readiness_trend(readiness)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        fig2 = plot_energy_sleep_soreness(readiness)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)

        with st.expander("Readiness Table"):
            st.dataframe(readiness, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Bodyweight Trend")

    bodyweight = calculate_bodyweight_trend()

    if bodyweight.empty:
        st.info("No bodyweight data yet.")
    else:
        fig = plot_bodyweight(bodyweight)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(bodyweight, use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Estimated 1RM Trend")

    e1rm = calculate_estimated_1rm_trend()

    if e1rm.empty:
        st.info("No estimated 1RM data yet. Log completed sets with weight and reps first.")
    else:
        selected_exercises = st.multiselect(
            "Choose exercises",
            sorted(e1rm["exercise_name"].dropna().unique().tolist()),
            default=sorted(e1rm["exercise_name"].dropna().unique().tolist()),
        )

        filtered = e1rm[e1rm["exercise_name"].isin(selected_exercises)]

        fig = plot_estimated_1rm(filtered)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(filtered, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Weekly Volume")

    weekly_volume = calculate_weekly_volume()

    if weekly_volume.empty:
        st.info("No weekly volume data yet.")
    else:
        fig = plot_weekly_volume(weekly_volume)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(weekly_volume, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Average RPE by Exercise")

    avg_rpe = calculate_average_rpe_by_exercise()

    if avg_rpe.empty:
        st.info("No RPE data yet.")
    else:
        fig = plot_average_rpe(avg_rpe)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(avg_rpe, use_container_width=True, hide_index=True)

with tabs[5]:
    st.subheader("Exercise Summary")

    exercise_summary = calculate_exercise_summary()

    if exercise_summary.empty:
        st.info("No exercise summary yet.")
    else:
        st.dataframe(exercise_summary, use_container_width=True, hide_index=True)
