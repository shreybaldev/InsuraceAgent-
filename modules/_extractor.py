"""Shared extraction helper for schema-based document-type modules.

Each non-retail module populates a fixed JSON schema via a prompt that inlines
the schema and the extracted page text. This helper wraps the common shape:
format prompt, call GPT-4o-mini with json_object, parse, persist, return."""

import json

from loguru import logger

from insurance_rag.config import get_db, get_openai_client
from insurance_rag.db import (
    _ensure_policy,
    update_structured_content_data,
    update_structured_content_status,
)
from insurance_rag.schemas import schema_as_prompt_block


async def run_schema_extraction(
    pages: list[str],
    user_id: str,
    pdf_name: str,
    doc_type: str,
    prompt_template: str,
) -> dict:
    """Render the schema into `prompt_template`, run vision-text extraction via
    GPT-4o-mini, persist the result as the policy's structured_content, and
    return it."""
    db = get_db()
    client = get_openai_client()

    await _ensure_policy(db, user_id, pdf_name)
    await update_structured_content_status(db, user_id, pdf_name, "in_progress")

    document_content = "\n\n".join(
        f"--- Page {i + 1} ---\n{content}" for i, content in enumerate(pages)
    )
    prompt = prompt_template.format(
        schema=schema_as_prompt_block(doc_type),
        document_content=document_content,
    )

    logger.info(
        f"Running schema extraction for doc_type={doc_type}, user={user_id}, "
        f"file={pdf_name}, pages={len(pages)}"
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=4096,
        )
        data = json.loads(response.choices[0].message.content)
        await update_structured_content_data(db, user_id, pdf_name, data)
        await update_structured_content_status(db, user_id, pdf_name, "completed")
        logger.info(f"Schema extraction completed for doc_type={doc_type}, file={pdf_name}")
        return data
    except Exception as e:
        logger.error(f"Schema extraction failed for doc_type={doc_type}, file={pdf_name}: {e}")
        await update_structured_content_status(db, user_id, pdf_name, "failed")
        raise
