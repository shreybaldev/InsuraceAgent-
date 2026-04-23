"""Brochure module — pre-purchase summary for the "should I buy this?" JTBD.

Extract: populates the brochure schema.
Render: 6-section plain-English summary of the plan's pitch surface."""

from insurance_rag.modules._extractor import run_schema_extraction
from insurance_rag.prompts import BROCHURE_EXTRACTION_PROMPT


DOCUMENT_TYPE = "brochure"


async def extract(pages: list[str], user_id: str, pdf_name: str) -> dict:
    return await run_schema_extraction(
        pages, user_id, pdf_name, DOCUMENT_TYPE, BROCHURE_EXTRACTION_PROMPT
    )


def render(structured: dict) -> dict:
    meta = structured.get("_meta") or {}
    coverage = structured.get("coverage") or {}
    waiting = structured.get("waiting_periods") or {}
    exclusions = structured.get("key_exclusions") or {}
    cost = structured.get("cost_and_rewards") or {}
    eligibility = structured.get("eligibility") or {}
    optional = structured.get("key_optional_covers") or {}
    contact = structured.get("claim_contact") or {}

    active_optionals = [name for name, val in optional.items() if val]

    return {
        "plan": {
            "insurer": meta.get("insurer"),
            "product_name": meta.get("product_name"),
            "uin": meta.get("uin"),
        },
        "core_coverage": {
            "sum_insured_options": coverage.get("sum_insured_options"),
            "room_rent": coverage.get("room_rent_entitlement"),
            "room_rent_proportionate_deduction": coverage.get("room_rent_proportionate_deduction"),
            "pre_hospitalisation_days": coverage.get("pre_hospitalisation_days"),
            "post_hospitalisation_days": coverage.get("post_hospitalisation_days"),
            "restoration": coverage.get("restoration"),
            "cumulative_bonus": coverage.get("cumulative_bonus"),
            "day_care": coverage.get("day_care"),
            "domiciliary": coverage.get("domiciliary"),
            "ayush": coverage.get("ayush"),
            "ambulance_modes": coverage.get("ambulance_modes"),
            "donor_expenses": coverage.get("donor_expenses"),
            "advance_technology": coverage.get("advance_technology"),
        },
        "waiting_periods": waiting,
        "key_exclusions": exclusions,
        "cost_and_rewards": cost,
        "eligibility": eligibility,
        "key_optional_covers": {
            "available": active_optionals,
            "detail": optional,
        },
        "claim_contact": contact,
    }
