import streamlit as st

from src.database import init_db
from src.ui import inject_global_styles


st.set_page_config(
    page_title="Home",
    page_icon="🥊",
    layout="wide",
)

inject_global_styles()
init_db()


def inject_home_clickable_card_styles():
    st.markdown(
        """
        <style>
        .home-hero {
            background: linear-gradient(135deg, #160025 0%, #2b0052 55%, #050008 100%);
            border: 1px solid rgba(0, 245, 255, 0.25);
            border-radius: 28px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 0 32px rgba(0, 245, 255, 0.08);
        }

        .home-hero-title {
            color: white;
            font-size: 2.2rem;
            font-weight: 900;
            margin-bottom: 0.5rem;
        }

        .home-hero-subtitle {
            color: rgba(255, 255, 255, 0.72);
            font-size: 1.05rem;
            max-width: 760px;
            line-height: 1.55;
        }

        .section-title {
            color: white;
            font-size: 1.65rem;
            font-weight: 900;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }

        a.app-card {
            display: block;
            text-decoration: none !important;
            background: linear-gradient(135deg, rgba(36, 10, 72, 0.92), rgba(8, 18, 36, 0.92));
            border: 1px solid rgba(0, 245, 255, 0.18);
            border-radius: 24px;
            padding: 1.45rem;
            min-height: 245px;
            color: white !important;
            transition: all 0.18s ease;
            box-shadow: 0 0 18px rgba(0, 245, 255, 0.04);
        }

        a.app-card:hover {
            transform: translateY(-3px);
            border-color: rgba(0, 245, 255, 0.55);
            box-shadow: 0 0 28px rgba(0, 245, 255, 0.16);
            background: linear-gradient(135deg, rgba(48, 12, 96, 0.98), rgba(9, 27, 48, 0.98));
        }

        .app-card-icon {
            width: 58px;
            height: 58px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 18px;
            background: rgba(0, 0, 0, 0.16);
            font-size: 1.75rem;
            margin-bottom: 1.7rem;
        }

        .app-card-title {
            color: white;
            font-size: 1.45rem;
            font-weight: 900;
            margin-bottom: 0.75rem;
        }

        .app-card-description {
            color: rgba(255, 255, 255, 0.68);
            font-size: 0.98rem;
            line-height: 1.55;
        }

        .mini-link-label {
            color: rgba(255, 255, 255, 0.86);
            font-weight: 800;
            margin-top: 0.65rem;
            font-size: 0.92rem;
        }

        @media (max-width: 768px) {
            .home-hero {
                padding: 1.2rem;
            }

            .home-hero-title {
                font-size: 1.55rem;
            }

            a.app-card {
                min-height: 205px;
                padding: 1.1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def clickable_card(title, description, icon, href):
    st.markdown(
        f"""
        <a class="app-card" href="{href}" target="_self">
            <div class="app-card-icon">{icon}</div>
            <div class="app-card-title">{title}</div>
            <div class="app-card-description">{description}</div>
            <div class="mini-link-label">Open →</div>
        </a>
        """,
        unsafe_allow_html=True,
    )


inject_home_clickable_card_styles()

st.markdown(
    """
    <div class="home-hero">
        <div class="home-hero-title">Combat Athlete Training Tracker</div>
        <div class="home-hero-subtitle">
            Adaptive strength, readiness, and workout tracking for BJJ, Muay Thai, and athletic performance.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Primary Actions</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    clickable_card(
        title="Start Workout",
        description="Run the daily check-in, generate today’s adaptive workout, and log completed sets.",
        icon="🏋️",
        href="./Start_Workout",
    )

with col2:
    clickable_card(
        title="Analytics",
        description="Review readiness, bodyweight, strength, volume, and RPE trends.",
        icon="📊",
        href="./Analytics",
    )

with col3:
    clickable_card(
        title="Export Center",
        description="Download your data as Excel, CSV, and PNG charts for backup and long-term review.",
        icon="⬇️",
        href="./Export_Center",
    )

st.markdown('<div class="section-title">Secondary Tools</div>', unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    clickable_card(
        title="Workout History",
        description="Review past sessions, completed sets, notes, and workout progression.",
        icon="📜",
        href="./Workout_History",
    )

with col5:
    clickable_card(
        title="Program Templates",
        description="Review and adjust training templates that bias workout generation.",
        icon="🧩",
        href="./Program_Templates",
    )

with col6:
    clickable_card(
        title="Settings",
        description="Update bodyweight, maxes, template preferences, and app configuration.",
        icon="⚙️",
        href="./Settings",
    )
