import streamlit as st


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        /* Main layout */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }

        /* Make buttons more mobile friendly */
        div.stButton > button {
            width: 100%;
            border-radius: 12px;
            min-height: 3rem;
            font-weight: 700;
        }

        div.stDownloadButton > button {
            width: 100%;
            border-radius: 12px;
            min-height: 3rem;
            font-weight: 700;
        }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 1rem;
            border-radius: 16px;
        }

        /* Better tabs */
        button[data-baseweb="tab"] {
            font-weight: 700;
        }

        /* Better expanders */
        details {
            border-radius: 12px !important;
        }

        /* Custom cards */
        .hero-card {
            background: linear-gradient(135deg, rgba(60, 60, 70, 0.35), rgba(20, 20, 25, 0.65));
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 22px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        .section-card {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.075);
            border-radius: 18px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }

        .exercise-card {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.85rem;
        }

        .muted-text {
            color: rgba(250, 250, 250, 0.68);
            font-size: 0.95rem;
        }

        .small-label {
            color: rgba(250, 250, 250, 0.60);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }

        .big-title {
            font-size: 2.4rem;
            font-weight: 900;
            margin-bottom: 0.25rem;
            line-height: 1.05;
        }

        .subtle-divider {
            margin-top: 1.2rem;
            margin-bottom: 1.2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        .green-badge {
            background: rgba(35, 160, 90, 0.18);
            border: 1px solid rgba(35, 160, 90, 0.35);
            color: #73e6a2;
            padding: 0.5rem 0.75rem;
            border-radius: 999px;
            font-weight: 800;
            display: inline-block;
        }

        .yellow-badge {
            background: rgba(60, 130, 220, 0.18);
            border: 1px solid rgba(60, 130, 220, 0.35);
            color: #93c5fd;
            padding: 0.5rem 0.75rem;
            border-radius: 999px;
            font-weight: 800;
            display: inline-block;
        }

        .orange-badge {
            background: rgba(245, 160, 40, 0.18);
            border: 1px solid rgba(245, 160, 40, 0.35);
            color: #fbbf24;
            padding: 0.5rem 0.75rem;
            border-radius: 999px;
            font-weight: 800;
            display: inline-block;
        }

        .red-badge {
            background: rgba(220, 60, 60, 0.18);
            border: 1px solid rgba(220, 60, 60, 0.35);
            color: #f87171;
            padding: 0.5rem 0.75rem;
            border-radius: 999px;
            font-weight: 800;
            display: inline-block;
        }

        /* Mobile cleanup */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .big-title {
                font-size: 1.8rem;
            }

            .hero-card {
                padding: 1rem;
                border-radius: 18px;
            }

            .section-card {
                padding: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str | None = None) -> None:
    inject_global_styles()

    st.markdown(
        f"""
        <div class="hero-card">
            <div class="big-title">{title}</div>
            {f'<div class="muted-text">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<div class='muted-text'>{subtitle}</div>", unsafe_allow_html=True)


def card_start() -> None:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)


def card_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def readiness_badge(category: str, score: float | int | None = None) -> None:
    label = category or "Unknown"

    if score is not None:
        text = f"{label} Day — {score}/10"
    else:
        text = f"{label} Day"

    class_name = {
        "Green": "green-badge",
        "Yellow": "yellow-badge",
        "Orange": "orange-badge",
        "Red": "red-badge",
    }.get(label, "yellow-badge")

    st.markdown(
        f"<span class='{class_name}'>{text}</span>",
        unsafe_allow_html=True,
    )


def workout_type_badge(text: str) -> None:
    st.markdown(
        f"<span class='yellow-badge'>{text}</span>",
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.info(message)


def app_storage_warning() -> None:
    st.warning(
        "This app uses local SQLite storage. On Streamlit Community Cloud, use the Export Center regularly as a backup."
    )


def nav_card(title: str, description: str, page: str, icon: str) -> None:
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.write(description)
        st.page_link(page, label=f"Open {title}", icon=icon)


def exercise_card(exercise: dict, index: int) -> None:
    with st.container(border=True):
        st.markdown(f"### {index}. {exercise['exercise_name']}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Sets", exercise["planned_sets"])

        with col2:
            st.metric("Reps", f"{exercise['planned_reps_min']}-{exercise['planned_reps_max']}")

        with col3:
            if exercise["planned_weight"] and exercise["planned_weight"] > 0:
                st.metric("Load", f"{exercise['planned_weight']} lb")
            else:
                st.metric("Load", "RPE")

        with col4:
            st.metric("RPE", exercise["target_rpe"])

        st.caption(f"{exercise['movement_pattern']} • {exercise['exercise_category']}")
        st.write(exercise["notes"])


def compact_exercise_card(exercise: dict, index: int) -> None:
    load_text = (
        f"{exercise['planned_weight']} lb"
        if exercise["planned_weight"] and exercise["planned_weight"] > 0
        else "RPE-based"
    )

    st.markdown(
        f"""
        <div class="exercise-card">
            <div class="small-label">{exercise['movement_pattern']} • {exercise['exercise_category']}</div>
            <h3>{index}. {exercise['exercise_name']}</h3>
            <p>
                <b>{exercise['planned_sets']}</b> sets × 
                <b>{exercise['planned_reps_min']}-{exercise['planned_reps_max']}</b> reps · 
                <b>{load_text}</b> · 
                Target RPE <b>{exercise['target_rpe']}</b>
            </p>
            <p class="muted-text">{exercise['notes']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
