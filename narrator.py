"""Warm-tone narrator that turns a module's structured rendered output into a
natural-language paragraph suitable for the reader of the document.

Uses GPT-4o-mini with a per-document-type JTBD framing so each narrative
answers the question the reader actually cares about for that document type."""

import json

from loguru import logger

from insurance_rag.config import get_openai_client
from insurance_rag.prompts import JTBD_FRAMINGS, NARRATION_PROMPT


_DOC_TYPE_LABELS = {
    "retail_policy": "Your retail health insurance policy",
    "policy_wording": "A policy wordings (terms and conditions) document",
    "brochure": "A health insurance brochure",
    "group_policy": "Your employer-sponsored group health cover",
    "rejection_letter": "A claim rejection letter",
}


async def narrate(doc_type: str, rendered: dict) -> str:
    """Generate a warm, 2-4 paragraph narrative summary of `rendered` for the given doc_type."""
    if doc_type not in JTBD_FRAMINGS:
        raise ValueError(f"No JTBD framing configured for doc_type={doc_type!r}")

    client = get_openai_client()
    prompt = NARRATION_PROMPT.format(
        doc_type=_DOC_TYPE_LABELS.get(doc_type, doc_type),
        jtbd_framing=JTBD_FRAMINGS[doc_type],
        rendered_json=json.dumps(rendered, indent=2, default=str),
    )

    logger.info(f"Narrating rendered output for doc_type={doc_type}")

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
        temperature=0.4,
    )

    narrative = response.choices[0].message.content.strip()
    logger.info(f"Narrative generated for doc_type={doc_type}, length={len(narrative)} chars")
    return narrative
