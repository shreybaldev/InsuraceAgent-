import os
import shutil

from loguru import logger

from insurance_rag.config import get_db
from insurance_rag.db import ensure_indexes, _ensure_policy
from insurance_rag.document_fetcher import fetch_user_documents, download_pdf
from insurance_rag.pdf_processor import extract_pages_from_pdf
from insurance_rag.structured_extractor import extract_structured_metrics


async def process_user_documents(user_id: str, auth_token: str) -> dict:
    """
    Full pipeline: fetch user documents from the API, download PDFs,
    extract page content, and run structured metrics extraction.

    Returns a summary of processed documents.
    """
    db = get_db()
    await ensure_indexes(db)

    documents = await fetch_user_documents(user_id, auth_token)

    # Filter to only PDF documents
    pdf_docs = [
        doc for doc in documents
        if doc.get("contentType") == "application/pdf" and doc.get("signedUrl")
    ]

    if not pdf_docs:
        logger.warning(f"No PDF documents found for user {user_id}")
        return {
            "user_id": user_id,
            "total_documents": len(documents),
            "pdfs_processed": 0,
            "results": [],
        }

    # TODO: Process only the first PDF for now; remove slicing to process all
    pdf_docs = pdf_docs[:1]

    logger.info(f"Processing {len(pdf_docs)} PDF(s) for user {user_id}")

    results = []
    for doc in pdf_docs:
        file_name = doc["fileName"]
        signed_url = doc["signedUrl"]
        tmp_path = None

        try:
            # Download the PDF
            tmp_path = await download_pdf(signed_url, file_name)

            # Extract page content via vision
            all_content = await extract_pages_from_pdf(tmp_path, user_id)

            # Extract structured metrics
            await extract_structured_metrics(all_content, user_id, file_name)

            results.append({
                "fileName": file_name,
                "insuranceType": doc.get("insuranceType"),
                "status": "completed",
                "pages_extracted": len(all_content),
            })
            logger.info(f"Successfully processed {file_name} for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to process {file_name} for user {user_id}: {e}")
            results.append({
                "fileName": file_name,
                "insuranceType": doc.get("insuranceType"),
                "status": "failed",
                "error": str(e),
            })

        finally:
            # Clean up temp file
            if tmp_path:
                try:
                    shutil.rmtree(os.path.dirname(tmp_path), ignore_errors=True)
                except Exception:
                    pass

    return {
        "user_id": user_id,
        "total_documents": len(documents),
        "pdfs_processed": len(pdf_docs),
        "results": results,
    }
