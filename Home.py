from src.charts import plot_readiness_trend, plot_bodyweight
from src.ui import (
    inject_global_styles,
    page_header,
    home_banner,
    command_card,
    mini_stat,
    mission_card,
    app_storage_warning,
    nav_card,
)


st.set_page_config(
    page_title="Combat Athlete Training Tracker",
    page_title="Home",
    page_icon="🥋",
    layout="wide",
)
@@ -29,10 +31,7 @@
    seed_all()
    st.session_state.seeded = True

page_header(
    "Combat Athlete Training Tracker",
    "Adaptive strength training for BJJ, Muay Thai, cutting, and long-term performance tracking.",
)
home_banner()

current_bodyweight = float(get_setting("current_bodyweight", 218))
goal_bodyweight = float(get_setting("goal_bodyweight", 200))
@@ -42,82 +41,88 @@
)
selected_template_key = get_setting("selected_template_key", "balanced")

st.subheader("Current Mission")
remaining = round(current_bodyweight - goal_bodyweight, 1)

st.subheader("Command Center")

col1, col2, col3, col4 = st.columns(4)
c1, c2, c3, c4 = st.columns(4)

with col1:
    st.metric("Current", f"{current_bodyweight} lb")
with c1:
    mini_stat("Current", f"{current_bodyweight} lb")

with col2:
    st.metric("Goal", f"{goal_bodyweight} lb")
with c2:
    mini_stat("Goal", f"{goal_bodyweight} lb")

with col3:
    remaining = round(current_bodyweight - goal_bodyweight, 1)
    st.metric("Remaining", f"{remaining} lb")
with c3:
    mini_stat("Remaining", f"{remaining} lb")

with col4:
    st.metric("Lift Days", "Mon / Wed / Sat")
with c4:
    mini_stat("Lift Days", "M / W / S")

with st.container(border=True):
    st.write(f"**Primary goal:** {primary_goal}")
    st.write(f"**Current training bias:** {selected_template_key}")
    st.write("**Combat training:** Tuesday / Thursday / Friday / Sunday")
mission_card(primary_goal, selected_template_key)

st.divider()

st.subheader("Start Here")
st.subheader("Primary Actions")

nav1, nav2, nav3 = st.columns(3)
a1, a2, a3 = st.columns(3)

with nav1:
    nav_card(
with a1:
    command_card(
        title="Start Workout",
        description="Run the daily check-in, generate today's workout, and log completed sets.",
        description="Run the daily check-in, generate today’s adaptive workout, and log completed sets.",
        page="pages/1_Start_Workout.py",
        icon="🏋️",
        icon_file="strength.svg",
        button_label="Start Today’s Workout",
    )

with nav2:
    nav_card(
with a2:
    command_card(
        title="Analytics",
        description="Review readiness, bodyweight, strength, volume, and RPE trends.",
        page="pages/3_Analytics.py",
        icon="📊",
        icon_file="analytics.svg",
        button_label="View Analytics",
    )

with nav3:
    nav_card(
with a3:
    command_card(
        title="Export Center",
        description="Download your data as Excel, CSV, and PNG charts.",
        description="Download your data as Excel, CSV, and PNG charts for backup and long-term review.",
        page="pages/4_Export_Center.py",
        icon="📥",
        icon_file="export.svg",
        button_label="Download Data",
    )

nav4, nav5, nav6 = st.columns(3)
st.subheader("Secondary Tools")

b1, b2, b3 = st.columns(3)

with nav4:
    nav_card(
with b1:
    command_card(
        title="Workout History",
        description="Inspect saved workouts, check-ins, planned exercises, and progression state.",
        description="Inspect saved workouts, check-ins, planned exercises, completed sets, and progression state.",
        page="pages/2_Workout_History.py",
        icon="📋",
        icon_file="readiness.svg",
        button_label="Open History",
    )

with nav5:
    nav_card(
with b2:
    command_card(
        title="Program Templates",
        description="Choose whether the generator biases strength, posterior chain, upper grip, accessories, or recovery.",
        description="Choose the generator’s bias: strength, posterior chain, upper grip, accessories, or recovery.",
        page="pages/6_Program_Templates.py",
        icon="🧠",
        icon_file="templates.svg",
        button_label="Choose Template",
    )

with nav6:
    nav_card(
with b3:
    command_card(
        title="Settings",
        description="Edit bodyweight goals, training loads, and database tools.",
        description="Edit bodyweight goals, training loads, exercise defaults, and database tools.",
        page="pages/5_Settings.py",
        icon="⚙️",
        icon_file="settings.svg",
        button_label="Open Settings",
    )

st.divider()
