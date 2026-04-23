"""Retail health insurance policy module.

Extract: reuses the existing 26-metric structured extractor unchanged.
Render: deterministic 0-100 score + strengths / weaknesses / red_flags lists.
No LLM is called at render time."""

from loguru import logger

from insurance_rag.structured_extractor import extract_structured_metrics


DOCUMENT_TYPE = "retail_policy"

_GRADE_POINTS = {"good": 100, "moderate": 60, "bad": 20}

_METRIC_LABELS = {
    "claim_settlement_ratio": "Claim settlement ratio",
    "incurred_claim_ratio": "Incurred claim ratio",
    "cashless_hospital_network": "Cashless hospital network",
    "sum_insured": "Sum insured",
    "restoration_benefit": "Restoration benefit",
    "cumulative_bonus": "No-claim / cumulative bonus",
    "max_ncb_limit": "Maximum NCB cap",
    "room_rent_limit": "Room rent limit",
    "co_payment": "Co-payment",
    "disease_sub_limits": "Disease sub-limits",
    "pre_existing_disease_waiting": "Pre-existing disease waiting period",
    "specific_disease_waiting": "Specific disease waiting period",
    "pre_hospitalisation": "Pre-hospitalisation coverage",
    "post_hospitalisation": "Post-hospitalisation coverage",
    "day_care_procedures": "Day care procedures",
    "modern_treatments": "Modern treatments",
    "consumables_coverage": "Consumables coverage",
    "organ_donor_cover": "Organ donor cover",
    "ambulance_cover": "Ambulance cover",
    "ayush_treatment": "AYUSH treatment",
    "opd_benefits": "OPD benefits",
    "preventive_health_checkups": "Preventive health checkups",
    "teleconsultation": "Teleconsultation",
    "wellness_rewards": "Wellness rewards",
    "maternity_benefits": "Maternity benefits",
    "home_healthcare": "Home healthcare",
}


async def extract(pages: list[str], user_id: str, pdf_name: str) -> dict:
    """Populate the retail 26-metric structured block for this policy."""
    return await extract_structured_metrics(pages, user_id, pdf_name)


def render(structured: dict) -> dict:
    """Deterministically score the retail policy and categorize its metrics.

    Returns {score, grade, strengths, weaknesses, red_flags, scored_metric_count,
    total_metric_count}."""
    strengths: list[str] = []
    weaknesses: list[str] = []
    red_flags: list[str] = []
    total_points = 0
    scored = 0

    for key, label in _METRIC_LABELS.items():
        entry = structured.get(key) if isinstance(structured, dict) else None
        if not isinstance(entry, dict):
            continue
        benchmark = entry.get("benchmark")
        value = entry.get("value")
        if benchmark not in _GRADE_POINTS:
            continue

        total_points += _GRADE_POINTS[benchmark]
        scored += 1

        line = f"{label}: {_format_value(value)}"
        if benchmark == "good":
            strengths.append(line)
        elif benchmark == "moderate":
            weaknesses.append(line)
        elif benchmark == "bad":
            red_flags.append(line)

    score = round(total_points / scored) if scored else 0
    grade = _grade_for(score) if scored else "N/A"

    logger.info(
        f"Retail render: score={score}/{grade}, scored={scored}/{len(_METRIC_LABELS)}, "
        f"strengths={len(strengths)}, weaknesses={len(weaknesses)}, red_flags={len(red_flags)}"
    )

    return {
        "score": score,
        "grade": grade,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "red_flags": red_flags,
        "scored_metric_count": scored,
        "total_metric_count": len(_METRIC_LABELS),
    }


def _format_value(value) -> str:
    if value is None:
        return "not specified"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return str(value)


def _grade_for(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"
