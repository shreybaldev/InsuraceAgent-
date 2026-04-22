import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from loguru import logger
from pydantic import BaseModel

from insurance_rag.config import init_clients, close_clients, get_db
from insurance_rag.db import ensure_indexes
from insurance_rag.qa import answer_question


LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))


def _configure_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"), format=fmt)
    logger.add(
        LOG_DIR / "insurance_rag.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        enqueue=True,
    )


class QARequest(BaseModel):
    query: str
    user_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    mongo_uri = os.environ["MONGO_URI"]
    openai_api_key = os.environ["OPENAI_API_KEY"]
    logger.info(f"Starting insurance_rag service; mongo={_redact_uri(mongo_uri)}, openai_key=***{openai_api_key[-4:]}")
    init_clients(mongo_uri, openai_api_key)
    await ensure_indexes(get_db())
    logger.info("insurance_rag service ready; listening for requests")
    try:
        yield
    finally:
        logger.info("Shutting down insurance_rag service")
        close_clients()
        logger.info("insurance_rag service stopped")


def _redact_uri(uri: str) -> str:
    """Return a version of a mongo URI safe for logs (password masked)."""
    if "@" in uri and "://" in uri:
        scheme, rest = uri.split("://", 1)
        creds, host = rest.split("@", 1)
        if ":" in creds:
            user = creds.split(":", 1)[0]
            return f"{scheme}://{user}:***@{host}"
    return uri


app = FastAPI(title="insurance_rag", lifespan=lifespan)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = uuid.uuid4().hex[:8]
    start = time.perf_counter()
    with logger.contextualize(request_id=request_id):
        logger.info(f"[{request_id}] --> {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(f"[{request_id}] !! {request.method} {request.url.path} raised after {elapsed_ms:.1f}ms")
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(f"[{request_id}] <-- {request.method} {request.url.path} {response.status_code} in {elapsed_ms:.1f}ms")
        return response


async def require_bearer(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        logger.warning("Rejected request: missing or malformed Authorization header")
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        logger.warning("Rejected request: empty bearer token")
        raise HTTPException(status_code=401, detail="Empty bearer token")
    expected = os.getenv("API_TOKEN")
    if expected and token != expected:
        logger.warning("Rejected request: bearer token did not match configured API_TOKEN")
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    return token


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/cr/portfolio-query/insurance-qa")
async def insurance_qa(body: QARequest, _=Depends(require_bearer)):
    logger.info(f"QA request received user_id={body.user_id} query_len={len(body.query)}")
    result = await answer_question(user_id=body.user_id, query=body.query)
    logger.info(
        f"QA response user_id={body.user_id} source_pages={result.get('source_pages')} "
        f"answer_len={len(result.get('answer') or '')}"
    )
    return result
