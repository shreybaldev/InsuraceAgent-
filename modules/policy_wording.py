"""Policy wording module — "what's in and out without reading 40 pages".

Extract: populates the policy_wordings schema.
Render: 4-section plain-English breakdown — covered, excluded, claim reducers,
claim mechanics."""

from insurance_rag.modules._extractor import run_schema_extraction
from insurance_rag.prompts import POLICY_WORDING_EXTRACTION_PROMPT


DOCUMENT_TYPE = "policy_wording"


async def extract(pages: list[str], user_id: str, pdf_name: str) -> dict:
    return await run_schema_extraction(
        pages, user_id, pdf_name, DOCUMENT_TYPE, POLICY_WORDING_EXTRACTION_PROMPT
    )


def render(structured: dict) -> dict:
    meta = structured.get("policy_meta") or {}
    coverage = structured.get("coverage") or {}
    add_ons = structured.get("add_ons_active") or {}
    exclusions = structured.get("exclusions") or {}
    claim_mechanics = structured.get("claim_mechanics") or {}
    escalation = structured.get("escalation") or {}

    active_add_ons = [name for name, val in add_ons.items() if val]

    covered = {
        "sum_insured": coverage.get("sum_insured"),
        "policy_structure": coverage.get("policy_structure"),
        "room_rent": coverage.get("room_rent"),
        "pre_hospitalisation_days": coverage.get("pre_hospitalisation_days"),
        "post_hospitalisation_days": coverage.get("post_hospitalisation_days"),
        "day_care": coverage.get("day_care"),
        "domiciliary": coverage.get("domiciliary"),
        "ayush": coverage.get("ayush"),
        "ambulance": coverage.get("ambulance"),
        "donor_expenses": coverage.get("donor_expenses"),
        "restoration": coverage.get("restoration"),
        "loyalty_bonus": coverage.get("loyalty_bonus"),
        "technological_treatments": coverage.get("technological_treatments"),
        "active_add_ons": active_add_ons,
    }

    excluded = {
        "waiting_periods": exclusions.get("waiting_periods"),
        "permanent_exclusions": exclusions.get("permanent"),
        "permanent_exceptions": exclusions.get("permanent_exceptions"),
        "domiciliary_excluded_conditions": exclusions.get("domiciliary_excluded_conditions"),
        "non_payable_items": exclusions.get("non_payable_items"),
        "non_payable_unlockable_via": exclusions.get("non_payable_unlockable_via"),
        "policy_void_triggers": exclusions.get("policy_void_triggers"),
    }

    claim_reducers = exclusions.get("claim_reducers") or {}

    return {
        "plan": {
            "insurer": meta.get("insurer"),
            "product_name": meta.get("product_name"),
            "uin": meta.get("uin"),
            "policy_type": meta.get("policy_type"),
            "zone": meta.get("zone"),
        },
        "covered": covered,
        "excluded": excluded,
        "claim_reducers": claim_reducers,
        "claim_mechanics": claim_mechanics,
        "escalation": escalation,
    }
