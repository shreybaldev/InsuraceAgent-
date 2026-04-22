import os
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from openai import AsyncOpenAI

_mongo_client: AsyncIOMotorClient = None
_openai_client: AsyncOpenAI = None


def resolve_secret(secret_id: str) -> str:
    """Try env var first, fall back to GCP Secrets Manager."""
    value = os.getenv(secret_id)
    if value:
        return value
    from mcs_google_cloud import GoogleSecretsManager, SecretAccessBody
    secrets_manager = GoogleSecretsManager(project_id=os.environ["PROJECT_ID"])
    return secrets_manager.access_secret(SecretAccessBody(secret_id=secret_id))


def init_clients(mongo_uri: str, openai_api_key: str):
    """Initialize MongoDB and OpenAI clients with the provided credentials."""
    global _mongo_client, _openai_client
    _mongo_client = AsyncIOMotorClient(mongo_uri)
    _openai_client = AsyncOpenAI(api_key=openai_api_key)
    logger.info("Initialized MongoDB and OpenAI async clients")


def get_db():
    """Return the MongoDB database instance. Raises RuntimeError if the client is not initialized."""
    if _mongo_client is None:
        raise RuntimeError("MongoDB client is not initialized. Ensure init_clients() was called successfully during startup.")
    db_name = os.getenv("MONGO_DB_NAME", "insurance")
    return _mongo_client[db_name]


def get_openai_client() -> AsyncOpenAI:
    """Return the OpenAI async client. Raises RuntimeError if the client is not initialized."""
    if _openai_client is None:
        raise RuntimeError("OpenAI client is not initialized. Ensure init_clients() was called successfully during startup.")
    return _openai_client


def close_clients():
    """Close the MongoDB client connection if it is active."""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        logger.info("Closed MongoDB client")
