"""Claim rejection letter module.

Extract: populates the claim_rejection schema from the letter content.
Render: what-happened + can-you-appeal + 4-step escalation, all sourced
directly from the schema's already-extracted fields (minimal synthesis)."""

from insurance_rag.modules._extractor import run_schema_extraction
from insurance_rag.prompts import REJECTION_LETTER_EXTRACTION_PROMPT


DOCUMENT_TYPE = "rejection_letter"


async def extract(pages: list[str], user_id: str, pdf_name: str) -> dict:
    return await run_schema_extraction(
        pages, user_id, pdf_name, DOCUMENT_TYPE, REJECTION_LETTER_EXTRACTION_PROMPT
    )


def render(structured: dict) -> dict:
    claim_identity = structured.get("claim_identity") or {}
    details = structured.get("rejection_details") or {}
    flags = structured.get("appeal_flags") or {}
    escalation = structured.get("escalation_path") or {}

    what_happened = {
        "claim_number": claim_identity.get("claim_number"),
        "policy_number": claim_identity.get("policy_number"),
        "patient": claim_identity.get("patient_name"),
        "treatment_or_test": details.get("treatment_or_test_in_question"),
        "rejection_type": details.get("rejection_type"),
        "reason": details.get("reason_summary"),
        "clause_cited": details.get("clause_cited"),
        "amount_rejected": details.get("amount_rejected"),
        "insurer_observation": details.get("insurer_observation"),
        "date_of_rejection": claim_identity.get("date_of_rejection"),
    }

    can_you_appeal = {
        "is_appeal_possible": flags.get("is_appeal_possible"),
        "appeal_strength": flags.get("appeal_strength"),
        "anomaly_flag": flags.get("anomaly_flag"),
        "deadline_flag": flags.get("deadline_flag"),
        "cross_doc_flag": flags.get("cross_doc_flag"),
    }

    next_steps = [
        {
            "step": 1,
            "title": "Contact the insurer's internal team",
            "contact": (escalation.get("step_1_internal") or {}).get("contact"),
            "email": (escalation.get("step_1_internal") or {}).get("email"),
            "response_sla_days": (escalation.get("step_1_internal") or {}).get("response_sla_days"),
        },
        {
            "step": 2,
            "title": "Escalate to the Grievance Officer",
            "contact": (escalation.get("step_2_grievance_officer") or {}).get("contact"),
            "email": (escalation.get("step_2_grievance_officer") or {}).get("email"),
        },
        {
            "step": 3,
            "title": "File with the Insurance Ombudsman",
            "applicable_office": (escalation.get("step_3_ombudsman") or {}).get("applicable_office"),
            "email": (escalation.get("step_3_ombudsman") or {}).get("email"),
            "cio_portal": (escalation.get("step_3_ombudsman") or {}).get("cio_portal"),
        },
        {
            "step": 4,
            "title": "Raise with IRDAI",
            "portal": (escalation.get("step_4_irdai") or {}).get("portal"),
            "toll_free": (escalation.get("step_4_irdai") or {}).get("toll_free"),
        },
    ]

    return {
        "what_happened": what_happened,
        "can_you_appeal": can_you_appeal,
        "next_steps": next_steps,
        "customer_care": escalation.get("customer_care"),
    }
