import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from loguru import logger
from pydantic import BaseModel

from insurance_rag.config import init_clients, close_clients, get_db
from insurance_rag.db import ensure_indexes
from insurance_rag.qa import answer_question


class QARequest(BaseModel):
    query: str
    user_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_uri = os.environ["MONGO_URI"]
    openai_api_key = os.environ["OPENAI_API_KEY"]
    init_clients(mongo_uri, openai_api_key)
    await ensure_indexes(get_db())
    logger.info("insurance_rag service ready")
    try:
        yield
    finally:
        close_clients()


app = FastAPI(title="insurance_rag", lifespan=lifespan)


async def require_bearer(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")
    expected = os.getenv("API_TOKEN")
    if expected and token != expected:
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    return token


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/cr/portfolio-query/insurance-qa")
async def insurance_qa(body: QARequest, _=Depends(require_bearer)):
    return await answer_question(user_id=body.user_id, query=body.query)
