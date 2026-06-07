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

        .mission-card,
        .logic-card,
        .summary-card {
            background:
                radial-gradient(circle at top right, rgba(0,245,212,0.08), transparent 34%),
                linear-gradient(135deg, rgba(22,11,46,0.92), rgba(9,5,15,0.98));
            border: 1px solid rgba(0,245,212,0.16);
            border-radius: 22px;
            padding: 1.1rem 1.25rem;
            margin-bottom: 1rem;
        }

        .logic-card h4,
        .summary-card h4 {
            margin-top: 0;
            color: #F8FAFC;
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

        .exercise-shell {
            background: linear-gradient(180deg, rgba(33,17,56,0.82), rgba(9,5,15,0.72));
            border-top: 1px solid rgba(255,255,255,0.085);
            border-right: 1px solid rgba(255,255,255,0.085);
            border-bottom: 1px solid rgba(255,255,255,0.085);
            border-radius: 18px;
            padding: 1.05rem 1.15rem;
            margin-bottom: 0.45rem;
        }

        .how-to-shell {
            background: linear-gradient(135deg, rgba(0,245,212,0.045), rgba(124,58,237,0.06));
            border: 1px solid rgba(0,245,212,0.12);
            border-radius: 16px;
            padding: 0.85rem 1rem;
            margin-top: 0.35rem;
            margin-bottom: 0.9rem;
        }

        .prescription-chip,
        .tech-chip,
        .logic-chip {
            display: inline-block;
            padding: 0.32rem 0.58rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
            margin-right: 0.35rem;
        }

        .prescription-chip {
            background: rgba(0,245,212,0.10);
            border: 1px solid rgba(0,245,212,0.26);
            color: #5FFFEA;
        }

        .tech-chip {
            background: rgba(245,158,11,0.12);
            border: 1px solid rgba(245,158,11,0.32);
            color: #FCD34D;
        }

        .logic-chip {
            background: rgba(124,58,237,0.16);
            border: 1px solid rgba(124,58,237,0.35);
            color: #D8B4FE;
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

        .logic-line {
            color: rgba(248,250,252,0.88);
            font-size: 0.95rem;
            line-height: 1.55;
            margin-bottom: 0.3rem;
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

        .how-to-section-title {
            color: #00F5D4;
            font-weight: 900;
            font-size: 0.88rem;
            margin-top: 0.6rem;
            margin-bottom: 0.2rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .how-to-text {
            color: rgba(248,250,252,0.88);
            font-size: 0.95rem;
            line-height: 1.55;
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

            .exercise-shell {
                padding: 0.95rem;
            }

            .command-card h3 {
                font-size: 1.3rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def clean_label(value: str | int | float | None) -> str:
    if value in [None, ""]:
        return "—"
    return str(value).replace("_", " ").title()


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

    if "isometric" in name:
        return "isometric"

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
        "cardio_skill": "Technical Cardio",
        "conditioning": "Conditioning",
        "recovery": "Recovery",
        "isometric": "Isometric",
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

    if prescription_type in {"cardio", "cardio_skill"}:
        duration_text = f"{duration} min" if duration else f"{reps_min}-{reps_max} min"
        return [
            ("Duration", duration_text),
            ("Target", heart_rate_target or intensity_target or f"RPE {target_rpe}"),
            ("Mode", str(exercise.get("modality") or exercise.get("movement_pattern") or "cardio")),
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
        if hold_seconds:
            time_text = f"{hold_seconds} sec"
        elif duration:
            time_text = f"{duration} min"
        else:
            time_text = f"{reps_min}-{reps_max}"

        return [
            ("Rounds", str(sets)),
            ("Time/Reps", time_text),
            ("Intensity", intensity_target or "Easy"),
            ("RPE", str(target_rpe)),
        ]

    if prescription_type == "stretch":
        hold_text = f"{hold_seconds} sec" if hold_seconds else f"{reps_min}-{reps_max} sec"
        return [
            ("Rounds", str(sets)),
            ("Hold", hold_text),
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

    if prescription_type == "isometric":
        hold_text = f"{hold_seconds} sec" if hold_seconds else f"{reps_min}-{reps_max} sec"
        return [
            ("Sets", str(sets)),
            ("Hold", hold_text),
            ("Intent", exercise.get("intensity_target", f"RPE {target_rpe}")),
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
        "selected_for_slot",
        "method_tag",
        "session_slot",
        "fatigue_points",
        "combat_transfer",
        "technical_transfer",
    ]:
        value = exercise.get(key)
        if value not in [None, ""]:
            label = key.replace("_", " ").title()
            pills.append(f"{label}: {clean_label(value)}")

    return pills


def exercise_needs_how_to(exercise: dict) -> bool:
    name = str(exercise.get("exercise_name", "")).lower()
    method_tag = str(exercise.get("method_tag", "")).lower()
    mobility_style = str(exercise.get("mobility_style", "")).lower()
    modality = str(exercise.get("modality", "")).lower()
    prescription_type = str(exercise.get("prescription_type", "")).lower()
    session_slot = str(exercise.get("session_slot", "")).lower()

    common = {
        "bench press",
        "squat",
        "trap bar deadlift",
        "weighted pull-up",
        "weighted chin-up",
        "pull-up",
        "chin-up",
        "neutral-grip pull-up",
        "db row",
        "chest-supported row",
        "lat pulldown",
        "db bench press",
        "incline db bench",
        "landmine press",
        "db shoulder press",
        "push-up",
        "goblet squat",
        "step-up",
        "split squat",
        "reverse lunge",
        "romanian deadlift",
        "back extension",
        "hammer curl",
        "triceps pressdown",
        "lateral raise",
        "face pull",
        "bike",
        "incline walk",
    }

    if name in common:
        return False

    keywords = [
        "car",
        "cars",
        "pails",
        "rails",
        "overcoming",
        "isometric",
        "mobility circuit",
        "technical",
        "footwork",
        "shadow boxing",
        "muay thai",
        "defensive movement",
        "combat base",
        "open guard",
        "deep squat breathing",
        "positional breathing",
        "foam roll",
        "band-assisted",
        "t-spine",
        "thoracic",
        "adductor",
        "90/90",
        "hip airplane",
        "cossack",
        "sled",
        "bear crawl",
        "neck",
        "pigeon",
    ]

    combined = " ".join([name, method_tag, mobility_style, modality, prescription_type, session_slot])

    if any(keyword in combined for keyword in keywords):
        return True

    if prescription_type in {"mobility", "stretch", "cardio_skill", "isometric"}:
        return True

    if method_tag in {"mobility_control", "movement_prep", "overcoming_isometric", "yielding_isometric", "skill_conditioning"}:
        return True

    return False


def build_how_to_content(exercise: dict) -> dict[str, list[str]]:
    name = str(exercise.get("exercise_name", "Exercise"))
    name_lower = name.lower()
    method_tag = str(exercise.get("method_tag", "")).lower()
    mobility_style = str(exercise.get("mobility_style", "")).lower()
    modality = str(exercise.get("modality", "")).lower()
    prescription_type = str(exercise.get("prescription_type", "")).lower()
    coaching_cues = str(exercise.get("coaching_cues", "")).strip()
    notes = str(exercise.get("notes", "")).strip()

    setup = []
    execution = []
    avoid = []

    if "pails" in name_lower or "rails" in name_lower or "pails" in mobility_style or "rails" in mobility_style:
        setup = [
            "Get into the listed stretch or end-range position gently.",
            "Spend the first part of the hold breathing and settling into a pain-free range.",
            "Use a conservative range. This should feel controlled, not forced.",
        ]
        execution = [
            "PAILs: gradually push the stretched tissue into the floor, wall, band, or imagined barrier.",
            "Ramp effort slowly. Do not jump straight to max tension.",
            "RAILs: switch intent and use the opposite-side tissue to actively pull deeper into the new range.",
            "After the contraction, breathe and own the new range for a few seconds before exiting.",
        ]
        avoid = [
            "Do not chase pain, numbness, pinching, or sharp sensation.",
            "Do not use maximal effort the first time you try it.",
            "Do not collapse posture just to move farther.",
        ]

    elif "car" in name_lower or "cars" in name_lower or "cars" in mobility_style:
        setup = [
            "Set your body in a stable position so only the target joint is moving.",
            "Brace lightly and keep the rest of your body quiet.",
            "Use the biggest pain-free circle you can control.",
        ]
        execution = [
            "Move slowly through the full circle.",
            "Try to explore the edges of your usable range without compensating.",
            "Perform the prescribed reps in both directions if the exercise allows it.",
        ]
        avoid = [
            "Do not rush the circle.",
            "Do not twist your trunk, shrug, or shift your hips to fake more range.",
            "Avoid painful pinching or grinding.",
        ]

    elif "overcoming" in name_lower or method_tag == "overcoming_isometric":
        setup = [
            "Set up against an immovable object, pins, straps, wall, or fixed implement.",
            "Find a strong joint angle where you can create force safely.",
            "Brace before you start pushing or pulling.",
        ]
        execution = [
            "Ramp force quickly but smoothly into the immovable object.",
            "Hold hard for the prescribed seconds.",
            "Rest fully between efforts so each rep has high intent.",
        ]
        avoid = [
            "Do not jerk into the contraction.",
            "Do not let your position change during the hold.",
            "Avoid maximal intent if you feel beat up, under-recovered, or unsure of the setup.",
        ]

    elif method_tag == "yielding_isometric" or "isometric" in name_lower:
        setup = [
            "Get into the listed position and establish clean alignment.",
            "Brace lightly and make sure the position is pain-free.",
            "Choose a position you can hold without shaking apart immediately.",
        ]
        execution = [
            "Hold the position for the prescribed time.",
            "Breathe behind the brace rather than holding your breath the whole time.",
            "Keep tension steady and controlled.",
        ]
        avoid = [
            "Do not compensate by arching, shrugging, twisting, or collapsing.",
            "Do not turn a low-intensity recovery drill into a max-effort strain.",
        ]

    elif "shadow boxing" in name_lower:
        setup = [
            "Use open space and start in stance.",
            "Keep intensity light enough that your technique stays clean.",
            "Pick one focus: stance, jab, defense, rhythm, exits, or balance.",
        ]
        execution = [
            "Move in rounds. Keep your guard honest and return to stance after combinations.",
            "Throw smooth punches and add slips, rolls, pivots, or exits.",
            "Breathe rhythmically and stay relaxed.",
        ]
        avoid = [
            "Do not turn this into hard sparring with the air.",
            "Do not throw wild power shots or lose your feet.",
            "Avoid sloppy fatigue reps.",
        ]

    elif "muay thai" in name_lower or "footwork" in name_lower or "defensive movement" in name_lower:
        setup = [
            "Start in stance with enough space to move safely.",
            "Choose a light technical theme: step-outs, pivots, checks, teeps, angle exits, or stance recovery.",
            "Keep the work smooth and repeatable.",
        ]
        execution = [
            "Move in relaxed rounds at the prescribed RPE.",
            "Reset stance after every movement.",
            "Keep your eyes up, base under you, and breathing under control.",
        ]
        avoid = [
            "Do not cross your feet or rush the drill.",
            "Do not turn technical cardio into a conditioning test unless the app prescribed that.",
            "Avoid sloppy kicks or pivots on sticky flooring.",
        ]

    elif "mobility circuit" in modality or "combat base" in name_lower or "open guard" in name_lower:
        setup = [
            "Clear enough floor space to move between positions.",
            "Move slowly at first and treat each position like skill practice.",
            "Stay within controllable range.",
        ]
        execution = [
            "Flow through the listed positions with control.",
            "Pause briefly in tight positions and breathe.",
            "Prioritize smooth transitions over speed.",
        ]
        avoid = [
            "Do not force end ranges.",
            "Do not bounce through tight joints.",
            "Do not let the drill become random movement with no control.",
        ]

    elif "foam roll" in name_lower:
        setup = [
            "Place the target tissue on the roller or ball with mild to moderate pressure.",
            "Support your body so you can control the pressure.",
            "Start with slow breathing.",
        ]
        execution = [
            "Move slowly over the target area.",
            "Pause on tight spots and breathe for a few seconds.",
            "If prescribed, add small joint movements while staying relaxed.",
        ]
        avoid = [
            "Do not grind aggressively.",
            "Do not roll directly on sharp pain, joints, or irritated tissue.",
            "Do not hold your breath.",
        ]

    elif "band-assisted" in name_lower:
        setup = [
            "Anchor the band securely.",
            "Create gentle traction, not a violent pull.",
            "Position your body so the band helps you find a stretch without joint irritation.",
        ]
        execution = [
            "Ease into the stretch and breathe slowly.",
            "Adjust distance from the anchor to change intensity.",
            "Hold the prescribed time with relaxed control.",
        ]
        avoid = [
            "Do not let the band yank the joint.",
            "Avoid numbness, tingling, pinching, or sharp pain.",
            "Do not force range just because the band allows it.",
        ]

    elif "neck" in name_lower:
        setup = [
            "Use a comfortable position and start with very low pressure.",
            "Keep jaw relaxed and shoulders down.",
            "Move or press only through pain-free range.",
        ]
        execution = [
            "Apply gentle controlled pressure in the prescribed direction.",
            "Build intensity gradually.",
            "Keep the neck long and avoid aggressive strain.",
        ]
        avoid = [
            "Do not crank the neck.",
            "Do not use maximal effort on recovery days.",
            "Stop if you feel dizziness, nerve symptoms, sharp pain, or headache pressure.",
        ]

    elif "sled" in name_lower:
        setup = [
            "Load the sled conservatively enough that speed and posture stay clean.",
            "Set your torso angle and brace before driving.",
            "Use a clear lane.",
        ]
        execution = [
            "Drive through the floor with powerful steps.",
            "Keep the torso angle consistent.",
            "Stop each rep before your mechanics fall apart.",
        ]
        avoid = [
            "Do not let the hips shoot up and posture collapse.",
            "Do not turn every sled session into a max-effort conditioning test.",
        ]

    elif "bear crawl" in name_lower:
        setup = [
            "Start on hands and feet with knees hovering close to the floor.",
            "Brace lightly and keep the back flat.",
            "Move in open floor space.",
        ]
        execution = [
            "Move opposite hand and foot together.",
            "Keep hips low and steps quiet.",
            "Use the prescribed time or distance.",
        ]
        avoid = [
            "Do not let hips hike up.",
            "Do not rush so much that coordination breaks down.",
            "Stop if wrists or shoulders feel irritated.",
        ]

    elif prescription_type in {"mobility", "stretch"}:
        setup = [
            "Get into the listed position gradually.",
            "Find a range that feels useful but not painful.",
            "Breathe slowly before increasing intensity.",
        ]
        execution = [
            "Follow the prescribed time, reps, or rounds.",
            "Move with control and own the range.",
            "Keep the target area doing the work instead of compensating elsewhere.",
        ]
        avoid = [
            "Do not force painful range.",
            "Do not bounce aggressively.",
            "Do not sacrifice position just to go farther.",
        ]

    elif prescription_type == "cardio_skill":
        setup = [
            "Use enough space to move safely.",
            "Pick a technical theme and keep the intensity controlled.",
            "Start relaxed and build rhythm.",
        ]
        execution = [
            "Work for the prescribed rounds or duration.",
            "Prioritize stance, balance, rhythm, and clean mechanics.",
            "Keep breathing under control.",
        ]
        avoid = [
            "Do not turn technical work into sloppy conditioning.",
            "Do not chase speed at the expense of position.",
        ]

    else:
        setup = [
            "Set up the exercise according to the listed equipment and prescription.",
            "Use a conservative first set if the movement is unfamiliar.",
        ]
        execution = [
            "Follow the prescribed sets, reps, time, or RPE.",
            "Prioritize clean technique over load or speed.",
        ]
        avoid = [
            "Do not push through sharp pain.",
            "Do not increase intensity until the movement feels controlled.",
        ]

    if coaching_cues:
        execution.append(coaching_cues)

    if notes:
        setup.append(notes)

    return {
        "Setup": setup,
        "Execution": execution,
        "Avoid": avoid,
    }


def render_how_to_expander(exercise: dict, index: int) -> None:
    if not exercise_needs_how_to(exercise):
        return

    content = build_how_to_content(exercise)
    exercise_name = exercise.get("exercise_name", "Exercise")

    with st.expander(f"How to do this: {exercise_name}", expanded=False):
        st.markdown('<div class="how-to-shell">', unsafe_allow_html=True)

        for section_title, bullets in content.items():
            st.markdown(
                f"<div class='how-to-section-title'>{section_title}</div>",
                unsafe_allow_html=True,
            )
            for bullet in bullets:
                st.markdown(f"<div class='how-to-text'>• {bullet}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


def compact_exercise_card(exercise: dict, index: int) -> None:
    category = exercise.get("exercise_category", "accessory")
    prescription_type = get_prescription_type(exercise)
    stats = get_exercise_stat_blocks(exercise)
    metadata_pills = get_metadata_pills(exercise)

    category_label = str(category).replace("_", " ").title()
    prescription = prescription_label(prescription_type)

    border_color_map = {
        "main_lift": "#00F5D4",
        "secondary_lift": "#7C3AED",
        "accessory": "#F59E0B",
        "gpp": "#A78BFA",
        "recovery": "#94A3B8",
        "recovery_accessory": "#94A3B8",
        "mobility": "#38BDF8",
        "stretch": "#38BDF8",
        "cardio": "#FB7185",
        "conditioning": "#FB7185",
    }

    border_color = border_color_map.get(str(category), "#00F5D4")
    technical_chip = "<span class='tech-chip'>How-To Available</span>" if exercise_needs_how_to(exercise) else ""
    method_chip = f"<span class='logic-chip'>{clean_label(exercise.get('method_tag'))}</span>" if exercise.get("method_tag") else ""

    st.markdown(
        f"""
        <div class="exercise-shell" style="border-left: 7px solid {border_color};">
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <span class="prescription-chip">{prescription}</span>
        {method_chip}
        {technical_chip}
        <div class="small-label">{clean_label(exercise.get("movement_pattern", "movement"))} · {category_label}</div>
        <h3>{index}. {exercise.get("exercise_name", "Exercise")}</h3>
        """,
        unsafe_allow_html=True,
    )

    stat_cols = st.columns(4)

    for idx, (label, value) in enumerate(stats):
        with stat_cols[idx % 4]:
            st.metric(label, value)

    if metadata_pills:
        st.caption(" · ".join(metadata_pills))

    notes = exercise.get("notes", "")
    if notes:
        st.write(notes)

    st.markdown("</div>", unsafe_allow_html=True)

    render_how_to_expander(exercise, index)


def workout_intelligence_summary(workout: dict, checkin: dict) -> None:
    exercises = workout.get("exercises", [])
    method_tags = [exercise.get("method_tag", "") for exercise in exercises if exercise.get("method_tag")]
    session_slots = [exercise.get("selected_for_slot", exercise.get("session_slot", "")) for exercise in exercises]
    estimated_fatigue = workout.get("estimated_fatigue", sum(int(exercise.get("fatigue_points", 3)) for exercise in exercises))
    fatigue_budget = workout.get("fatigue_budget", "—")

    primary_methods = []
    for method in method_tags:
        pretty = clean_label(method)
        if pretty not in primary_methods:
            primary_methods.append(pretty)

    primary_slots = []
    for slot_name in session_slots:
        pretty = clean_label(slot_name)
        if pretty and pretty != "—" and pretty not in primary_slots:
            primary_slots.append(pretty)

    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
    st.markdown("<h4>Workout Intelligence Summary</h4>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Session", workout.get("session_type", "Main Workout"))

    with col2:
        st.metric("Fatigue", f"{estimated_fatigue} / {fatigue_budget}")

    with col3:
        st.metric("Readiness", workout.get("readiness_category", checkin.get("readiness_category", "—")))

    with col4:
        st.metric("Modifier", clean_label(workout.get("workout_modifier", "normal")))

    if primary_methods:
        st.markdown(
            f"<div class='logic-line'><b>Primary methods:</b> {', '.join(primary_methods[:5])}</div>",
            unsafe_allow_html=True,
        )

    if primary_slots:
        st.markdown(
            f"<div class='logic-line'><b>Session priorities:</b> {', '.join(primary_slots[:7])}</div>",
            unsafe_allow_html=True,
        )

    if workout.get("generation_reason"):
        st.markdown(
            f"<div class='logic-line'><b>Coach logic:</b> {workout.get('generation_reason')}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def workout_training_logic_expander(workout: dict, checkin: dict) -> None:
    exercises = workout.get("exercises", [])

    with st.expander("Show training logic", expanded=False):
        st.markdown('<div class="logic-card">', unsafe_allow_html=True)
        st.markdown("<h4>How this workout was built</h4>", unsafe_allow_html=True)

        st.markdown(
            f"<div class='logic-line'><b>Session type:</b> {workout.get('session_type', 'Main Workout')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='logic-line'><b>Training focus:</b> {workout.get('focus', '—')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='logic-line'><b>Readiness category:</b> {workout.get('readiness_category', checkin.get('readiness_category', '—'))}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='logic-line'><b>Goal today:</b> {checkin.get('goal_today', '—')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='logic-line'><b>Combat context:</b> Last 24h = {checkin.get('combat_last_24h', False)}, hard sparring = {checkin.get('hard_sparring_last_24h', False)}, later today = {checkin.get('combat_later_today', False)}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='logic-line'><b>Fatigue budget:</b> {workout.get('estimated_fatigue', '—')} used out of {workout.get('fatigue_budget', '—')}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='how-to-section-title'>Exercise Slot Map</div>", unsafe_allow_html=True)

        for index, exercise in enumerate(exercises, start=1):
            slot_name = exercise.get("selected_for_slot", exercise.get("session_slot", "—"))
            method = exercise.get("method_tag", "—")
            fatigue = exercise.get("fatigue_points", "—")
            reason = exercise.get("selection_reason", "")

            st.markdown(
                f"<div class='logic-line'><b>{index}. {exercise.get('exercise_name', 'Exercise')}</b> — "
                f"{clean_label(slot_name)} · {clean_label(method)} · Fatigue {fatigue}</div>",
                unsafe_allow_html=True,
            )

            if reason:
                st.markdown(
                    f"<div class='muted-text'>{reason}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)


def exercise_intelligence_panel(exercise: dict) -> None:
    selected_for = exercise.get("selected_for_slot")
    method = exercise.get("method_tag")
    slot_name = exercise.get("session_slot")
    fatigue = exercise.get("fatigue_points")
    combat_transfer = exercise.get("combat_transfer")
    technical_transfer = exercise.get("technical_transfer")
    reason = exercise.get("selection_reason")

    with st.expander("Why this exercise?", expanded=False):
        st.markdown('<div class="logic-card">', unsafe_allow_html=True)

        if selected_for:
            st.markdown(
                f"<div class='logic-line'><b>Selected for:</b> {clean_label(selected_for)}</div>",
                unsafe_allow_html=True,
            )

        if method:
            st.markdown(
                f"<div class='logic-line'><b>Training method:</b> {clean_label(method)}</div>",
                unsafe_allow_html=True,
            )

        if slot_name:
            st.markdown(
                f"<div class='logic-line'><b>Session slot:</b> {clean_label(slot_name)}</div>",
                unsafe_allow_html=True,
            )

        if fatigue not in [None, ""]:
            st.markdown(
                f"<div class='logic-line'><b>Fatigue points:</b> {fatigue}</div>",
                unsafe_allow_html=True,
            )

        if combat_transfer:
            st.markdown(
                f"<div class='logic-line'><b>Combat transfer:</b> {clean_label(combat_transfer)}</div>",
                unsafe_allow_html=True,
            )

        if technical_transfer:
            st.markdown(
                f"<div class='logic-line'><b>Technical transfer:</b> {clean_label(technical_transfer)}</div>",
                unsafe_allow_html=True,
            )

        if reason:
            st.markdown(
                f"<div class='logic-line'><b>Reason:</b> {reason}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


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
