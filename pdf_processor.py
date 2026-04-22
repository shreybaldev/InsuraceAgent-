import base64
import os

import fitz
from loguru import logger

from insurance_rag.config import get_db, get_openai_client
from insurance_rag.db import update_content_status, update_content_data, update_total_pages, append_page_data, _ensure_policy
from insurance_rag.prompts import PAGE_EXTRACTION_PROMPT


async def extract_pages_from_pdf(pdf_path: str, user_id: str) -> list[str]:
    """Extract text content from each page of a PDF using GPT-4o-mini vision and store results in the database."""
    pdf_name = os.path.basename(pdf_path)
    db = get_db()
    client = get_openai_client()

    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)

        await _ensure_policy(db, user_id, pdf_name)
        await update_content_data(db, user_id, pdf_name, [])
        await update_content_status(db, user_id, pdf_name, "in_progress")
        await update_total_pages(db, user_id, pdf_name, total_pages)

        all_content = []

        logger.info(f"Starting page extraction for user {user_id}, file {pdf_name}, {total_pages} page(s)")

        for page_num in range(total_pages):
            try:
                page = doc[page_num]
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": PAGE_EXTRACTION_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=4096,
                )

                content = response.choices[0].message.content.strip()
                all_content.append(content)

                page = {"page_number": page_num + 1, "text": content}
                try:
                    await append_page_data(db, user_id, pdf_name, page)
                except Exception as db_err:
                    logger.error(f"Failed to store page {page_num + 1}/{total_pages} to DB for user {user_id}, file {pdf_name}: {db_err}")

                logger.info(f"Extracted and stored page {page_num + 1}/{total_pages} for user {user_id}, file {pdf_name}")

            except Exception as e:
                logger.error(f"Error extracting page {page_num + 1}/{total_pages} for user {user_id}, file {pdf_name}: {e}")
                error_text = f"[Error extracting page {page_num + 1}]"
                all_content.append(error_text)

                error_page = {"page_number": page_num + 1, "text": error_text}
                try:
                    await append_page_data(db, user_id, pdf_name, error_page)
                except Exception as db_err:
                    logger.error(f"Failed to store error page {page_num + 1}/{total_pages} to DB for user {user_id}, file {pdf_name}: {db_err}")

    await update_content_status(db, user_id, pdf_name, "completed")

    logger.info(f"Page extraction completed for user {user_id}, file {pdf_name}: {total_pages} page(s)")
    return all_content
