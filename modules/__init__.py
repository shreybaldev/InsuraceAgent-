"""Per-document-type analysis modules. Each module exposes:
    - async extract(pages, user_id, pdf_name) -> dict   # schema-shaped structured output
    - render(structured) -> dict                         # plain-English JTBD output

Dispatch through MODULES[doc_type]."""

from insurance_rag.modules import (
    brochure,
    group_policy,
    policy_wording,
    rejection_letter,
    retail_policy,
)


MODULES = {
    "retail_policy": retail_policy,
    "policy_wording": policy_wording,
    "brochure": brochure,
    "group_policy": group_policy,
    "rejection_letter": rejection_letter,
}
