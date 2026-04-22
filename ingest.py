"""Ingest a local PDF into MongoDB for a given user_id, bypassing the askmyfi
documents API. Useful for development and for serving the QA endpoint
without running the full fetch pipeline."""

import argparse
import asyncio
import os

from loguru import logger

from insurance_rag.config import init_clients, close_clients, get_db
from insurance_rag.db import ensure_indexes
from insurance_rag.pdf_processor import extract_pages_from_pdf
from insurance_rag.structured_extractor import extract_structured_metrics


async def ingest_pdf(pdf_path: str, user_id: str):
    await ensure_indexes(get_db())
    pdf_name = os.path.basename(pdf_path)
    pages = await extract_pages_from_pdf(pdf_path, user_id)
    await extract_structured_metrics(pages, user_id, pdf_name)
    logger.info(f"Ingestion complete for {pdf_name} (user {user_id})")


def main():
    parser = argparse.ArgumentParser(description="Ingest a local PDF for a user")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--user-id", required=True, help="User ID to associate the policy with")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        raise SystemExit(f"PDF not found: {args.pdf}")

    init_clients(os.environ["MONGO_URI"], os.environ["OPENAI_API_KEY"])
    try:
        asyncio.run(ingest_pdf(args.pdf, args.user_id))
    finally:
        close_clients()


if __name__ == "__main__":
    main()
