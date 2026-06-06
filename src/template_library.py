from typing import Dict, List


def get_training_templates() -> List[Dict]:
    return [
        {
            "name": "Balanced Combat Athlete",
            "key": "balanced",
            "description": "General full-body strength with pulling, posterior chain, carries, abs, grip, and mobility.",
            "best_for": "Default training when you want balanced strength while cutting.",
            "influences": [
                "Full-body lifting",
                "Main lift + secondary lift",
                "Posterior chain",
                "Grip/carries",
                "Core",
            ],
        },
        {
            "name": "Posterior Chain / Grappling Strength",
            "key": "posterior_chain",
            "description": "Hinge, back, hamstrings, trunk, carries, and grip emphasis for grappling strength.",
            "best_for": "Days where you want strength that transfers to wrestling/BJJ positions.",
            "influences": [
                "Trap bar deadlift",
                "Romanian deadlift",
                "Back extensions",
                "Rows",
                "Carries",
                "Neck/core",
            ],
        },
        {
            "name": "Upper Strength + Grip",
            "key": "upper_grip",
            "description": "Pressing, pulling, upper back, forearms, weighted pull-ups, and grip-focused accessories.",
            "best_for": "Days before or after lower-body fatigue, or when you want upper-body emphasis.",
            "influences": [
                "Bench press",
                "Weighted pull-ups",
                "Rows",
                "Landmine press",
                "Forearms",
                "Grip",
            ],
        },
        {
            "name": "Lower Strength",
            "key": "lower_strength",
            "description": "Squat/hinge-focused full-body work with controlled volume.",
            "best_for": "High-readiness days where lower-body strength is the priority.",
            "influences": [
                "Trap bar deadlift",
                "Squat",
                "Single-leg work",
                "Posterior chain",
                "Core",
            ],
        },
        {
            "name": "Accessory / Hypertrophy Support",
            "key": "accessory",
            "description": "Isolation, arms, shoulders, forearms, abs, neck, grip, and light movement work.",
            "best_for": "Lower-readiness days, cutting phases, or when you want to train without heavy fatigue.",
            "influences": [
                "Lateral raises",
                "Hammer curls",
                "Triceps",
                "Forearms",
                "Abs",
                "Neck",
                "Mobility",
            ],
        },
        {
            "name": "Recovery / Mobility",
            "key": "recovery",
            "description": "Easy conditioning, mobility, trunk control, neck isometrics, and light posterior-chain blood flow.",
            "best_for": "Low-energy days, high soreness, or days around hard BJJ/Muay Thai.",
            "influences": [
                "Incline walk",
                "Bike",
                "Mobility flow",
                "Hip airplanes",
                "Dead bugs",
                "Light neck work",
            ],
        },
    ]


def get_template_by_key(key: str) -> Dict:
    templates = get_training_templates()

    for template in templates:
        if template["key"] == key:
            return template

    return templates[0]
