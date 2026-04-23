import json

from loguru import logger

from insurance_rag.config import get_db, get_openai_client
from insurance_rag.db import update_structured_content_status, update_structured_content_data
from insurance_rag.prompts import STRUCTURED_EXTRACTION_PROMPT


async def extract_structured_metrics(all_content: list[str], user_id: str, pdf_name: str) -> dict:
    """Extract structured insurance metrics (e.g. sum insured, waiting periods) from page content using GPT-4o-mini.

    Returns the parsed metrics dict (also persisted to Mongo)."""
    db = get_db()
    client = get_openai_client()

    await update_structured_content_status(db, user_id, pdf_name, "in_progress")

    logger.info(f"Starting structured extraction for user {user_id}, file {pdf_name}, {len(all_content)} page(s) of content")

    document_content = "\n\n".join(
        f"--- Page {i + 1} ---\n{content}" for i, content in enumerate(all_content)
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": STRUCTURED_EXTRACTION_PROMPT.format(
                        document_content=document_content
                    ),
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=4096,
        )

        metrics_data = json.loads(response.choices[0].message.content)

        await update_structured_content_data(db, user_id, pdf_name, metrics_data)
        await update_structured_content_status(db, user_id, pdf_name, "completed")

        logger.info(f"Structured extraction completed for user {user_id}, file {pdf_name}")

        return metrics_data

    except Exception as e:
        logger.error(f"Structured extraction failed for user {user_id}, file {pdf_name}: {e}")
        await update_structured_content_status(db, user_id, pdf_name, "failed")
        raise
