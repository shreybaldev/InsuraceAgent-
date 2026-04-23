"""Group policy module — employee-focused view of employer-sponsored cover.

Extract: populates the group_policy schema.
Render: what you're covered for, your family definition, waivers you get, and
a prominent GOTCHAS block that surfaces the schema's pre-computed critical_flags
as human-readable warnings."""

from insurance_rag.modules._extractor import run_schema_extraction
from insurance_rag.prompts import GROUP_POLICY_EXTRACTION_PROMPT


DOCUMENT_TYPE = "group_policy"


_CRITICAL_FLAG_MESSAGES = {
    "coverage_ends_on_termination": "Your coverage ends the day you leave the company — you lose protection immediately, with no continuation.",
    "no_portability_to_personal_retail_on_exit": "On exit you cannot carry your waiting-period credits into a personal retail policy — portability is not offered.",
    "copay_10pct_all_claims_real_oop": "A 10% co-payment applies to every claim. You will always pay at least 10% of any bill out of pocket.",
    "modern_treatments_50pct_copay_significant_exposure": "Modern treatments (robotic surgery, stem cell, oral chemo, etc.) carry a 50% co-payment — significant out-of-pocket exposure for high-cost procedures.",
    "corporate_floater_not_for_maternity": "The corporate floater sum insured cannot be used for maternity claims — maternity is ring-fenced to its own sub-limit.",
    "parents_one_set_only": "You can cover only one set of parents — either your own parents OR parents-in-law, not both.",
    "ayush_govt_hospital_only": "AYUSH treatments are covered only at government or accredited AYUSH hospitals — private clinics won't qualify.",
    "reimbursement_intimation_within_24hrs_of_admission": "Claim intimation is required within 24 hours of hospital admission. Missing this window can lead to partial or full denial.",
}


async def extract(pages: list[str], user_id: str, pdf_name: str) -> dict:
    return await run_schema_extraction(
        pages, user_id, pdf_name, DOCUMENT_TYPE, GROUP_POLICY_EXTRACTION_PROMPT
    )


def render(structured: dict) -> dict:
    meta = structured.get("_meta") or {}
    coverage = structured.get("coverage") or {}
    family = structured.get("family_definition") or {}
    waiting = structured.get("waiting_periods") or {}
    copay = structured.get("copayment") or {}
    critical_flags = structured.get("critical_flags") or {}
    exclusions = structured.get("key_exclusions") or {}
    claim_mechanics = structured.get("claim_mechanics") or {}
    escalation = structured.get("escalation") or {}

    gotchas = [
        {"flag": flag, "warning": _CRITICAL_FLAG_MESSAGES.get(flag, flag)}
        for flag, active in critical_flags.items()
        if active
    ]

    return {
        "plan": {
            "policyholder": meta.get("policyholder"),
            "insurer": meta.get("insurer"),
            "product_name": meta.get("product_name"),
            "policy_number": meta.get("policy_number"),
            "policy_type": meta.get("policy_type"),
            "period_start": meta.get("period_start"),
            "period_end": meta.get("period_end"),
            "total_insured": meta.get("total_insured"),
        },
        "what_you_are_covered_for": {
            "sum_insured_graded_INR": coverage.get("sum_insured_graded_INR"),
            "corporate_floater_INR": coverage.get("corporate_floater_INR"),
            "corporate_floater_per_family_sublimit_INR": coverage.get("corporate_floater_per_family_sublimit_INR"),
            "room_rent": coverage.get("room_rent"),
            "pre_hospitalisation_days": coverage.get("pre_hospitalisation_days"),
            "post_hospitalisation_days": coverage.get("post_hospitalisation_days"),
            "day_care": coverage.get("day_care"),
            "ayush": coverage.get("ayush"),
            "ambulance": coverage.get("ambulance"),
            "donor_expenses": coverage.get("donor_expenses"),
            "maternity": coverage.get("maternity"),
            "baby_day_one_cover": coverage.get("baby_day_one_cover"),
            "psychiatric_mental_disorder_limit_INR": coverage.get("psychiatric_mental_disorder_limit_INR"),
            "hospital_cash": coverage.get("hospital_cash"),
            "nursing_allowance": coverage.get("nursing_allowance"),
            "family_transport_benefit_INR": coverage.get("family_transport_benefit_INR"),
            "covid19": coverage.get("covid19"),
            "terrorism": coverage.get("terrorism"),
        },
        "your_family_definition": family,
        "waivers_you_get": waiting,
        "copayments": copay,
        "gotchas": gotchas,
        "key_exclusions": exclusions,
        "claim_mechanics": claim_mechanics,
        "escalation": escalation,
    }
