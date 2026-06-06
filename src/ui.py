from pathlib import Path
import base64

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1220px;
        }

        section[data-testid="stSidebar"] {
            background: #050308;
            border-right: 1px solid rgba(0,245,212,0.12);
        }

        div.stButton > button,
        div.stDownloadButton > button {
            width: 100%;
            border-radius: 14px;
            min-height: 3rem;
            font-weight: 800;
            border: 1px solid rgba(0,245,212,0.40);
            background: linear-gradient(135deg, #160B2E, #09050F);
            color: #F8FAFC;
        }

        div.stButton > button:hover,
        div.stDownloadButton > button:hover {
            border-color: rgba(0,245,212,0.95);
            color: #00F5D4;
            transform: translateY(-1px);
            transition: all 0.15s ease-in-out;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(124,58,237,0.16), rgba(9,5,15,0.45));
            border: 1px solid rgba(0,245,212,0.12);
            padding: 1rem;
            border-radius: 18px;
            min-height: 112px;
        }

        button[data-baseweb="tab"] {
            font-weight: 800;
        }

        .home-hero {
            border-radius: 30px;
            overflow: hidden;
            border: 1px solid rgba(0,245,212,0.18);
            box-shadow: 0 22px 60px rgba(0,0,0,0.35);
            margin-bottom: 1.25rem;
        }

        .command-card {
            background:
                radial-gradient(circle at top right, rgba(0,245,212,0.10), transparent 35%),
                linear-gradient(135deg, rgba(33,17,56,0.98), rgba(9,5,15,0.98));
            border: 1px solid rgba(0,245,212,0.14);
            border-radius: 24px;
            padding: 1.25rem;
            min-height: 190px;
            box-shadow: 0 14px 38px rgba(0,0,0,0.22);
            margin-bottom: 0.65rem;
        }

        .command-card:hover {
            border-color: rgba(0,245,212,0.55);
            box-shadow: 0 18px 48px rgba(0,245,212,0.06);
            transform: translateY(-1px);
            transition: all 0.15s ease-in-out;
        }

        .command-card h3 {
            margin-top: 0.65rem;
            margin-bottom: 0.35rem;
        }

        .mission-card {
            background:
                linear-gradient(135deg, rgba(22,11,46,0.92), rgba(9,5,15,0.98));
            border: 1px solid rgba(0,245,212,0.16);
            border-radius: 22px;
            padding: 1.1rem 1.25rem;
            margin-bottom: 1rem;
        }

        .readiness-panel {
            background:
                radial-gradient(circle at top right, rgba(0,245,212,0.16), transparent 38%),
                linear-gradient(135deg, rgba(33,17,56,0.98), rgba(9,5,15,0.98));
            border: 1px solid rgba(0,245,212,0.22);
            border-radius: 24px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 14px 38px rgba(0,0,0,0.22);
        }

        .exercise-card {
            background: linear-gradient(180deg, rgba(33,17,56,0.82), rgba(9,5,15,0.72));
            border: 1px solid rgba(255,255,255,0.085);
            border-left: 7px solid #00F5D4;
            border-radius: 18px;
            padding: 1.05rem 1.15rem;
            margin-bottom: 0.9rem;
        }

        .exercise-card-main_lift {
            border-left-color: #00F5D4;
            box-shadow: inset 0 0 0 1px rgba(0,245,212,0.06);
        }

        .exercise-card-secondary_lift {
            border-left-color: #7C3AED;
        }

        .exercise-card-accessory {
            border-left-color: #F59E0B;
        }

        .exercise-card-gpp {
            border-left-color: #A78BFA;
        }

        .exercise-card-recovery,
        .exercise-card-recovery_accessory {
            border-left-color: #94A3B8;
        }

        .small-label {
            color: rgba(216,180,254,0.82);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            font-weight: 900;
            margin-bottom: 0.2rem;
        }

        .muted-text {
            color: rgba(216,180,254,0.86);
            font-size: 0.96rem;
        }

        .mini-stat {
            background: rgba(0,0,0,0.22);
            border: 1px solid rgba(0,245,212,0.10);
            border-radius: 14px;
            padding: 0.75rem;
            text-align: center;
        }

        .mini-stat-label {
            color: rgba(216,180,254,0.78);
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .mini-stat-value {
            color: #F8FAFC;
            font-size: 1.25rem;
            font-weight: 900;
        }

        .green-badge,
        .yellow-badge,
        .orange-badge,
        .red-badge,
        .neutral-badge {
            padding: 0.52rem 0.8rem;
            border-radius: 999px;
            font-weight: 900;
            display: inline-block;
            letter-spacing: 0.02em;
            margin-bottom: 0.35rem;
        }

        .green-badge {
            background: rgba(0,245,212,0.14);
            border: 1px solid rgba(0,245,212,0.44);
            color: #5FFFEA;
        }

        .yellow-badge {
            background: rgba(124,58,237,0.20);
            border: 1px solid rgba(124,58,237,0.48);
            color: #D8B4FE;
        }

        .orange-badge {
            background: rgba(245,158,11,0.16);
            border: 1px solid rgba(245,158,11,0.42);
            color: #FCD34D;
        }

        .red-badge {
            background: rgba(239,68,68,0.16);
            border: 1px solid rgba(239,68,68,0.42);
            color: #FCA5A5;
        }

        .neutral-badge {
            background: rgba(148,163,184,0.14);
            border: 1px solid rgba(148,163,184,0.34);
            color: #CBD5E1;
        }

        .flow-step {
            background: rgba(33,17,56,0.55);
            border: 1px solid rgba(0,245,212,0.11);
            border-radius: 16px;
            padding: 0.85rem;
            text-align: center;
            font-weight: 800;
            margin-bottom: 1rem;
        }

        .flow-active {
            border-color: rgba(0,245,212,0.62);
            background: rgba(0,245,212,0.10);
            color: #00F5D4;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 0.85rem;
                padding-right: 0.85rem;
            }

            .command-card {
                min-height: auto;
                padding: 1rem;
            }

            .exercise-card {
                padding: 0.95rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def asset_to_base64(filename: str) -> str:
    path = ASSETS_DIR / filename
    if not path.exists():
        return ""
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def asset_img_html(filename: str, alt: str = "", width: str = "64px") -> str:
    encoded = asset_to_base64(filename)
    if not encoded:
        return ""
    return f'<img src="data:image/svg+xml;base64,{encoded}" alt="{alt}" style="width:{width}; height:auto;">'


def banner_html() -> str:
    encoded = asset_to_base64("banner.svg")
    if not encoded:
        return "<h1>Combat Athlete Training Tracker</h1>"
    return f"""
    <div class="home-hero">
        <img src="data:image/svg+xml;base64,{encoded}" style="width:100%; display:block;">
    </div>
    """


def home_banner() -> None:
    inject_global_styles()
    st.markdown(banner_html(), unsafe_allow_html=True)


def page_header(title: str, subtitle: str | None = None) -> None:
    inject_global_styles()
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<div class='muted-text'>{subtitle}</div>", unsafe_allow_html=True)
    st.divider()


def readiness_badge(category: str, score: float | int | None = None) -> None:
    label = category or "Unknown"
    text = f"{label} Day — {score}/10" if score is not None else f"{label} Day"

    class_name = {
        "Green": "green-badge",
        "Yellow": "yellow-badge",
        "Orange": "orange-badge",
        "Red": "red-badge",
    }.get(label, "neutral-badge")

    st.markdown(f"<span class='{class_name}'>{text}</span>", unsafe_allow_html=True)


def readiness_panel(
    category: str,
    score: float,
    explanation: str,
    workout_type: str = "",
    focus: str = "",
) -> None:
    st.markdown('<div class="readiness-panel">', unsafe_allow_html=True)

    readiness_badge(category, score)

    st.markdown("### Today’s Readiness")
    if workout_type:
        st.write(f"**Recommended mode:** {workout_type}")
    if focus:
        st.write(f"**Training focus:** {focus}")
    st.markdown(f"<div class='muted-text'>{explanation}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def command_card(
    title: str,
    description: str,
    page: str,
    icon_file: str,
    button_label: str,
) -> None:
    icon_html = asset_img_html(icon_file, title, "50px")

    st.markdown(
        f"""
        <div class="command-card">
            {icon_html}
            <h3>{title}</h3>
            <p class="muted-text">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.page_link(page, label=button_label)


def mini_stat(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="mini-stat">
            <div class="mini-stat-label">{label}</div>
            <div class="mini-stat-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mission_card(primary_goal: str, training_bias: str) -> None:
    st.markdown(
        f"""
        <div class="mission-card">
            <div class="small-label">Current Mission</div>
            <p><b>Primary goal:</b> {primary_goal}</p>
            <p><b>Training bias:</b> {training_bias}</p>
            <p><b>Combat training:</b> Tuesday / Thursday / Friday / Sunday</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def flow_indicator(active_step: int) -> None:
    labels = ["Check-In", "Workout", "Log Sets", "Complete"]
    cols = st.columns(4)

    for idx, col in enumerate(cols, start=1):
        class_name = "flow-step flow-active" if idx == active_step else "flow-step"
        with col:
            st.markdown(
                f"<div class='{class_name}'>Step {idx}<br>{labels[idx-1]}</div>",
                unsafe_allow_html=True,
            )


def compact_exercise_card(exercise: dict, index: int) -> None:
    category = exercise.get("exercise_category", "accessory")
    safe_category = str(category).replace(" ", "_")

    load_text = (
        f"{exercise['planned_weight']} lb"
        if exercise["planned_weight"] and exercise["planned_weight"] > 0
        else "RPE-based"
    )

    st.markdown(
        f"""
        <div class="exercise-card exercise-card-{safe_category}">
            <div class="small-label">{exercise['movement_pattern']} · {exercise['exercise_category']}</div>
            <h3>{index}. {exercise['exercise_name']}</h3>
            <div style="display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.6rem; margin: 0.75rem 0;">
                <div class="mini-stat">
                    <div class="mini-stat-label">Sets</div>
                    <div class="mini-stat-value">{exercise['planned_sets']}</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-label">Reps</div>
                    <div class="mini-stat-value">{exercise['planned_reps_min']}-{exercise['planned_reps_max']}</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-label">Load</div>
                    <div class="mini-stat-value">{load_text}</div>
                </div>
                <div class="mini-stat">
                    <div class="mini-stat-label">RPE</div>
                    <div class="mini-stat-value">{exercise['target_rpe']}</div>
                </div>
            </div>
            <p class="muted-text">{exercise['notes']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def app_storage_warning() -> None:
    st.warning(
        "This app uses local SQLite storage. On Streamlit Community Cloud, use the Export Center regularly as a backup."
    )
