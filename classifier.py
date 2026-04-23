"""Classifies an insurance document into one of five types so the ingest
pipeline can route to the correct extraction module.

Runs on the already-vision-extracted page text (not the raw PDF) — classification
is a coarse routing task and the first few pages contain enough signal."""

import json

from loguru import logger

from insurance_rag.config import get_openai_client
from insurance_rag.prompts import CLASSIFICATION_PROMPT


VALID_TYPES = {"retail_policy", "policy_wording", "brochure", "group_policy", "rejection_letter"}
CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.7
_CLASSIFICATION_PAGES = 3


class ClassificationError(Exception):
    """Raised when the classifier can't confidently identify the document type."""


async def classify_document(pages: list[str]) -> dict:
    """Return {"document_type": ..., "confidence": ..., "reasoning": ...} for the document.

    Raises ClassificationError on invalid type or confidence below threshold."""
    if not pages:
        raise ClassificationError("No pages to classify")

    client = get_openai_client()
    window = pages[:_CLASSIFICATION_PAGES]
    document_content = "\n\n".join(
        f"--- Page {i + 1} ---\n{content}" for i, content in enumerate(window)
    )

    logger.info(f"Classifying document using first {len(window)} page(s) of content")

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": CLASSIFICATION_PROMPT.format(document_content=document_content)}
        ],
        response_format={"type": "json_object"},
        max_tokens=256,
    )

    try:
        parsed = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        raise ClassificationError(f"Classifier returned non-JSON: {e}")

    doc_type = parsed.get("type")
    confidence = parsed.get("confidence")
    reasoning = parsed.get("reasoning", "")

    if doc_type not in VALID_TYPES:
        raise ClassificationError(f"Classifier returned unknown type '{doc_type}'")
    if not isinstance(confidence, (int, float)):
        raise ClassificationError(f"Classifier returned non-numeric confidence: {confidence!r}")

    logger.info(f"Classified as '{doc_type}' with confidence {confidence:.2f}: {reasoning}")

    if confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD:
        raise ClassificationError(
            f"Confidence {confidence:.2f} below threshold {CLASSIFICATION_CONFIDENCE_THRESHOLD} "
            f"(classifier saw: {reasoning}). Use --force-type to override."
        )

    return {"document_type": doc_type, "confidence": float(confidence), "reasoning": reasoning}
