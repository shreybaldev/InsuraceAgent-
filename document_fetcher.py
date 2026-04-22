import os
import tempfile

import httpx
from loguru import logger


FETCH_ENDPOINT = "/cr/insure/admin/documents/fetch"


async def fetch_user_documents(user_id: str, auth_token: str) -> list[dict]:
    """Fetch document metadata (including signed URLs) for a user from the insurance API."""
    api_base_url = os.getenv("API_BASE_URL", "https://api.askmyfi.dev")
    url = f"{api_base_url}{FETCH_ENDPOINT}"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            json={"userId": int(user_id)},
        )
        response.raise_for_status()

    data = response.json()
    documents = data.get("payload", {}).get("data") or []
    logger.info(f"Fetched {len(documents)} documents for user {user_id}")
    return documents


async def download_pdf(signed_url: str, file_name: str) -> str:
    """Download a PDF from a signed URL to a temp file. Returns the temp file path."""
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.get(signed_url)
        response.raise_for_status()

    tmp_dir = tempfile.mkdtemp(prefix="insurance_pdf_")
    file_path = os.path.join(tmp_dir, file_name)

    with open(file_path, "wb") as f:
        f.write(response.content)

    logger.info(f"Downloaded {file_name} ({len(response.content)} bytes)")
    return file_path
