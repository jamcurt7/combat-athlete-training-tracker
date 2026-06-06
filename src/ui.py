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

        .home-hero {
            border-radius: 30px;
            overflow: hidden;
            border: 1px solid rgba(0,245,212,0.18);
            box-shadow: 0 22px 60px rgba(0,0,0,0.35);
            margin-bottom: 1.25rem;
        }

        .clickable-card-link {
            text-decoration: none !important;
            color: inherit !important;
            display: block;
        }

        .command-card {
            background:
                radial-gradient(circle at top right, rgba(0,245,212,0.10), transparent 35%),
                linear-gradient(135deg, rgba(33,17,56,0.98), rgba(9,5,15,0.98));
            border: 1px solid rgba(0,245,212,0.14);
            border-radius: 24px;
            padding: 1.35rem;
            min-height: 250px;
            box-shadow: 0 14px 38px rgba(0,0,0,0.22);
            margin-bottom: 0.75rem;
            cursor: pointer;
        }

        .command-card:hover {
            border-color: rgba(0,245,212,0.72);
            box-shadow: 0 18px 48px rgba(0,245,212,0.08);
            transform: translateY(-2px);
            transition: all 0.15s ease-in-out;
        }

        .command-card h3 {
            margin-top: 1.4rem;
            margin-bottom: 0.8rem;
            color: #F8FAFC;
            font-size: 1.55rem;
        }

        .command-card p {
            color: rgba(216,180,254,0.86);
            font-size: 1.02rem;
            line-height: 1.65;
        }

        .command-card-footer {
            color: #00F5D4;
            font-weight: 900;
            margin-top: 1.1rem;
            font-size: 0.92rem;
            letter-spacing: 0.02em;
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

        .exercise-card-mobility,
        .exercise-card-stretch {
            border-left-color: #38BDF8;
        }

        .exercise-card-cardio,
        .exercise-card-conditioning {
            border-left-color: #FB7185;
        }

        .prescription-chip {
            display: inline-block;
            padding: 0.32rem 0.58rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            background: rgba(0,245,212,0.10);
            border: 1px solid rgba(0,245,212,0.26);
            color: #5FFFEA;
            margin-bottom: 0.45rem;
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

        .action-panel {
            background: linear-gradient(135deg, rgba(22,11,46,0.92), rgba(9,5,15,0.98));
            border: 1px solid rgba(0,245,212,0.14);
            border-radius: 20px;
            padding: 1rem;
            margin: 0.75rem 0 1rem 0;
        }

        .metadata-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.45rem;
            margin-bottom: 0.65rem;
        }

        .metadata-pill {
            background: rgba(255,255,255,0.045);
            border: 1px solid rgba(255,255,255,0.08);
            color: rgba(248,250,252,0.86);
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
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

            .command-card h3 {
                font-size: 1.3rem;
            }

            .exercise-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
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


def route_for_page(page: str) -> str:
    route_map = {
        "pages/1_Start_Workout.py": "/Start_Workout",
        "pages/2_Workout_History.py": "/Workout_History",
        "pages/3_Analytics.py": "/Analytics",
        "pages/4_Export_Center.py": "/Export_Center",
        "pages/5_Settings.py": "/Settings",
        "pages/6_Program_Templates.py": "/Program_Templates",
        "Home.py": "/",
    }
    return route_map.get(page, "/")


def command_card(
    title: str,
    description: str,
    page: str,
    icon_file: str,
    button_label: str,
) -> None:
    icon_html = asset_img_html(icon_file, title, "54px")
    route = route_for_page(page)

    st.markdown(
        f"""
        <a href="{route}" target="_self" class="clickable-card-link">
            <div class="command-card">
                {icon_html}
                <h3>{title}</h3>
                <p>{description}</p>
                <div class="command-card-footer">{button_label} →</div>
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )


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


def step_navigation(active_step: int) -> None:
    step_defs = [
        (1, "Check-In"),
        (2, "Workout"),
        (3, "Log Sets"),
        (4, "Complete"),
    ]

    cols = st.columns(4)

    for col, (step_num, label) in zip(cols, step_defs):
        disabled = False

        if step_num in {2, 3} and "latest_workout" not in st.session_state:
            disabled = True

        if step_num == 4 and not st.session_state.get("workout_saved", False):
            disabled = True

        button_label = f"Step {step_num}: {label}"

        if step_num == active_step:
            button_label = f"✓ {button_label}"

        with col:
            if st.button(
                button_label,
                use_container_width=True,
                disabled=disabled or step_num == active_step,
                key=f"step_nav_{step_num}",
            ):
                st.session_state["workout_flow_step"] = step_num
                st.rerun()


def get_prescription_type(exercise: dict) -> str:
    explicit_type = exercise.get("prescription_type")

    if explicit_type:
        return str(explicit_type)

    category = str(exercise.get("exercise_category", "")).lower()
    movement = str(exercise.get("movement_pattern", "")).lower()
    name = str(exercise.get("exercise_name", "")).lower()

    if "stretch" in category or "stretch" in movement or "stretch" in name:
        return "stretch"

    if "mobility" in category or "mobility" in movement or "mobility" in name:
        return "mobility"

    if "conditioning" in category or "cardio" in category or "conditioning" in movement:
        return "cardio"

    if "carry" in movement or "carry" in name:
        return "carry"

    if exercise.get("planned_weight", 0) and float(exercise.get("planned_weight", 0)) > 0:
        return "strength"

    if "pull-up" in name or "chin-up" in name or "push-up" in name:
        return "bodyweight"

    return "strength"


def prescription_label(prescription_type: str) -> str:
    label_map = {
        "strength": "Strength",
        "bodyweight": "Bodyweight",
        "carry": "Carry / Grip",
        "mobility": "Mobility",
        "stretch": "Stretch",
        "cardio": "Cardio",
        "conditioning": "Conditioning",
        "recovery": "Recovery",
    }

    return label_map.get(prescription_type, prescription_type.title())


def get_exercise_stat_blocks(exercise: dict) -> list[tuple[str, str]]:
    prescription_type = get_prescription_type(exercise)

    sets = exercise.get("planned_sets", 1)
    reps_min = exercise.get("planned_reps_min", 0)
    reps_max = exercise.get("planned_reps_max", 0)
    planned_weight = float(exercise.get("planned_weight") or 0)
    target_rpe = exercise.get("target_rpe", "")
    duration = exercise.get("duration_minutes")
    hold_seconds = exercise.get("hold_seconds")
    distance = exercise.get("distance")
    heart_rate_target = exercise.get("heart_rate_target")
    intensity_target = exercise.get("intensity_target")

    if prescription_type == "cardio":
        return [
            ("Duration", f"{duration or reps_min}-{duration or reps_max} min"),
            ("Target", heart_rate_target or intensity_target or f"RPE {target_rpe}"),
            ("Mode", exercise.get("movement_pattern", "cardio")),
            ("Effort", f"RPE {target_rpe}"),
        ]

    if prescription_type == "conditioning":
        return [
            ("Rounds", str(sets)),
            ("Work", f"{reps_min}-{reps_max}"),
            ("Target", intensity_target or f"RPE {target_rpe}"),
            ("Effort", f"RPE {target_rpe}"),
        ]

    if prescription_type == "mobility":
        return [
            ("Rounds", str(sets)),
            ("Time/Reps", f"{reps_min}-{reps_max}"),
            ("Intensity", intensity_target or "Easy"),
            ("RPE", str(target_rpe)),
        ]

    if prescription_type == "stretch":
        return [
            ("Rounds", str(sets)),
            ("Hold", f"{hold_seconds or reps_min}-{hold_seconds or reps_max} sec"),
            ("Side", exercise.get("side", "each side")),
            ("Intensity", intensity_target or "Easy-moderate"),
        ]

    if prescription_type == "carry":
        load_text = f"{planned_weight} lb" if planned_weight > 0 else "Choose load"
        return [
            ("Sets", str(sets)),
            ("Distance/Time", distance or f"{reps_min}-{reps_max} sec"),
            ("Load", load_text),
            ("RPE", str(target_rpe)),
        ]

    if prescription_type == "bodyweight":
        return [
            ("Sets", str(sets)),
            ("Reps", f"{reps_min}-{reps_max}"),
            ("Load", "Bodyweight"),
            ("RPE", str(target_rpe)),
        ]

    load_text = f"{planned_weight} lb" if planned_weight > 0 else "RPE-based"

    return [
        ("Sets", str(sets)),
        ("Reps", f"{reps_min}-{reps_max}"),
        ("Load", load_text),
        ("RPE", str(target_rpe)),
    ]


def get_metadata_pills(exercise: dict) -> list[str]:
    pills = []

    for key in [
        "equipment",
        "modality",
        "fatigue_cost",
        "combat_transfer",
    ]:
        value = exercise.get(key)
        if value:
            label = key.replace("_", " ").title()
            pills.append(f"{label}: {value}")

    return pills


def compact_exercise_card(exercise: dict, index: int) -> None:
    category = exercise.get("exercise_category", "accessory")
    safe_category = str(category).replace(" ", "_")
    prescription_type = get_prescription_type(exercise)
    stats = get_exercise_stat_blocks(exercise)
    metadata_pills = get_metadata_pills(exercise)

    stats_html = "".join(
        [
            f"""
<div class="mini-stat">
    <div class="mini-stat-label">{label}</div>
    <div class="mini-stat-value">{value}</div>
</div>
"""
            for label, value in stats
        ]
    )

    if metadata_pills:
        metadata_html = (
            "<div class='metadata-row'>"
            + "".join([f"<span class='metadata-pill'>{pill}</span>" for pill in metadata_pills])
            + "</div>"
        )
    else:
        metadata_html = ""

    html = f"""
<div class="exercise-card exercise-card-{safe_category}">
    <span class="prescription-chip">{prescription_label(prescription_type)}</span>
    <div class="small-label">{exercise.get('movement_pattern', 'movement')} · {exercise.get('exercise_category', 'exercise')}</div>
    <h3>{index}. {exercise.get('exercise_name', 'Exercise')}</h3>

    <div class="exercise-grid" style="display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.6rem; margin: 0.75rem 0;">
        {stats_html}
    </div>

    {metadata_html}

    <p class="muted-text">{exercise.get('notes', '')}</p>
</div>
"""

    st.markdown(html, unsafe_allow_html=True)


def action_panel_start() -> None:
    st.markdown('<div class="action-panel">', unsafe_allow_html=True)


def action_panel_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def app_storage_warning() -> None:
    st.warning(
        "This app uses local SQLite storage. On Streamlit Community Cloud, use the Export Center regularly as a backup."
    )


def nav_card(title: str, description: str, page: str, icon: str) -> None:
    icon_file_map = {
        "🏋️": "strength.svg",
        "📊": "analytics.svg",
        "📥": "export.svg",
        "📋": "readiness.svg",
        "🧠": "templates.svg",
        "⚙️": "settings.svg",
    }

    icon_file = icon_file_map.get(icon, "strength.svg")

    command_card(
        title=title,
        description=description,
        page=page,
        icon_file=icon_file,
        button_label=f"Open {title}",
    )
