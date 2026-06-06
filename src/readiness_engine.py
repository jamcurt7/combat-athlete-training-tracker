from typing import Any


def calculate_readiness_score(checkin: dict[str, Any]) -> tuple[float, str, str]:
    """
    Calculate readiness score and category from daily check-in answers.

    Score is on a rough 1-10 scale.
    """

    energy = float(checkin.get("energy", 5))
    sleep_quality = float(checkin.get("sleep_quality", 5))
    mood = float(checkin.get("mood", 5))
    motivation = float(checkin.get("motivation", 5))
    stress = float(checkin.get("stress", 5))
    soreness = float(checkin.get("soreness", 5))
    hydration = float(checkin.get("hydration", 5))
    hours_slept = float(checkin.get("hours_slept", 7))

    combat_last_24h = bool(checkin.get("combat_last_24h", False))
    hard_sparring_last_24h = bool(checkin.get("hard_sparring_last_24h", False))
    combat_later_today = bool(checkin.get("combat_later_today", False))

    protein_on_track = str(checkin.get("protein_on_track", "unsure")).lower()
    goal_today = str(checkin.get("goal_today", "normal")).lower()

    # Positive readiness inputs
    score = 0.0
    score += energy * 0.25
    score += sleep_quality * 0.18
    score += mood * 0.10
    score += motivation * 0.15
    score += hydration * 0.10

    # Lower soreness and lower stress are better, so invert them.
    score += (10 - soreness) * 0.15
    score += (10 - stress) * 0.07

    # Hours slept modifier
    if hours_slept < 5:
        score -= 1.0
    elif hours_slept < 6:
        score -= 0.5
    elif hours_slept >= 8:
        score += 0.3

    # Combat sport fatigue modifiers
    if combat_last_24h:
        score -= 0.5

    if hard_sparring_last_24h:
        score -= 1.0

    if combat_later_today:
        score -= 0.4

    # Nutrition modifier
    if protein_on_track == "yes":
        score += 0.2
    elif protein_on_track == "no":
        score -= 0.4

    # User intent modifier
    if goal_today == "push":
        score += 0.4
    elif goal_today == "maintain":
        score -= 0.2
    elif goal_today == "recovery":
        score -= 1.0

    # Clamp score between 1 and 10
    score = max(1.0, min(10.0, round(score, 2)))

    if score >= 7.5:
        category = "Green"
    elif score >= 5.5:
        category = "Yellow"
    elif score >= 3.5:
        category = "Orange"
    else:
        category = "Red"

    explanation = build_readiness_explanation(
        score=score,
        category=category,
        soreness=soreness,
        stress=stress,
        hours_slept=hours_slept,
        combat_last_24h=combat_last_24h,
        hard_sparring_last_24h=hard_sparring_last_24h,
        combat_later_today=combat_later_today,
        goal_today=goal_today,
    )

    return score, category, explanation


def build_readiness_explanation(
    score: float,
    category: str,
    soreness: float,
    stress: float,
    hours_slept: float,
    combat_last_24h: bool,
    hard_sparring_last_24h: bool,
    combat_later_today: bool,
    goal_today: str,
) -> str:
    reasons = []

    if category == "Green":
        reasons.append("Readiness is high enough to push strength or volume slightly.")
    elif category == "Yellow":
        reasons.append("Readiness supports a normal productive training day.")
    elif category == "Orange":
        reasons.append("Readiness is reduced, so the workout should be lighter and more accessory-focused.")
    else:
        reasons.append("Readiness is low, so the workout should focus on recovery, mobility, and easy work.")

    if soreness >= 7:
        reasons.append("Soreness is high, so volume should be reduced.")
    elif soreness >= 5:
        reasons.append("Soreness is moderate, so the app should avoid excessive volume.")

    if stress >= 7:
        reasons.append("Stress is high, which can reduce recovery capacity.")

    if hours_slept < 6:
        reasons.append("Sleep was low, so intensity should be capped.")

    if combat_last_24h:
        reasons.append("Recent BJJ/Muay Thai adds fatigue.")

    if hard_sparring_last_24h:
        reasons.append("Hard sparring or hard rolling in the last 24 hours is a major fatigue signal.")

    if combat_later_today:
        reasons.append("Combat training later today means the lift should not drain you.")

    if goal_today == "recovery":
        reasons.append("You selected recovery as today's goal.")
    elif goal_today == "push":
        reasons.append("You selected push as today's goal, but the app still respects readiness.")

    return " ".join(reasons)
