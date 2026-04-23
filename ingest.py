"""Ingest a local PDF into MongoDB for a given user_id.

Flow:
  1. Vision-extract pages (PyMuPDF + GPT-4o-mini).
  2. Classify the document type (retail_policy, policy_wording, brochure,
     group_policy, rejection_letter) — unless --force-type is given.
  3. Dispatch to the matching module's extract() to populate the type-specific
     schema in MongoDB.
  4. Render the extracted structured data into a plain-English JTBD output,
     persist it, and print it to stdout."""

import argparse
import asyncio
import json
import os
import sys

from loguru import logger

from insurance_rag.classifier import (
    VALID_TYPES,
    ClassificationError,
    classify_document,
)
from insurance_rag.config import close_clients, get_db, init_clients
from insurance_rag.db import (
    ensure_indexes,
    update_document_type,
    update_rendered_output_data,
    update_rendered_output_status,
)
from insurance_rag.modules import MODULES
from insurance_rag.pdf_processor import extract_pages_from_pdf


async def ingest_pdf(pdf_path: str, user_id: str, force_type: str | None = None) -> dict:
    await ensure_indexes(get_db())
    pdf_name = os.path.basename(pdf_path)

    pages = await extract_pages_from_pdf(pdf_path, user_id)
    if not pages:
        raise SystemExit("Vision extraction returned no pages.")

    if force_type:
        if force_type not in VALID_TYPES:
            raise SystemExit(f"--force-type '{force_type}' is not one of {sorted(VALID_TYPES)}")
        doc_type = force_type
        logger.info(f"Skipping classification; forcing document_type={doc_type}")
    else:
        classification = await classify_document(pages)
        doc_type = classification["document_type"]

    db = get_db()
    await update_document_type(db, user_id, pdf_name, doc_type)
    await update_rendered_output_status(db, user_id, pdf_name, "in_progress")

    module = MODULES[doc_type]
    structured = await module.extract(pages, user_id, pdf_name)
    rendered = module.render(structured)

    await update_rendered_output_data(db, user_id, pdf_name, rendered)
    await update_rendered_output_status(db, user_id, pdf_name, "completed")

    logger.info(f"Ingestion complete: doc_type={doc_type}, file={pdf_name}, user={user_id}")

    return {"document_type": doc_type, "result": rendered}


def main():
    parser = argparse.ArgumentParser(description="Ingest a local PDF for a user")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--user-id", required=True, help="User ID to associate the policy with")
    parser.add_argument(
        "--force-type",
        default=None,
        choices=sorted(VALID_TYPES),
        help="Skip classification and force this document type (for testing)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        raise SystemExit(f"PDF not found: {args.pdf}")

    init_clients(os.environ["MONGO_URI"], os.environ["OPENAI_API_KEY"])
    try:
        try:
            result = asyncio.run(ingest_pdf(args.pdf, args.user_id, args.force_type))
        except ClassificationError as e:
            logger.error(f"Classification failed: {e}")
            sys.exit(2)
        print(json.dumps(result, indent=2, default=str))
    finally:
        close_clients()


if __name__ == "__main__":
    main()
