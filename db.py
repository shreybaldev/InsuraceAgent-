from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING


COLLECTION = "userpolicies"


async def ensure_indexes(db: AsyncIOMotorDatabase):
    await db[COLLECTION].create_index(
        [("user_id", ASCENDING)],
        unique=True,
    )


async def _ensure_user_doc(db: AsyncIOMotorDatabase, user_id: str):
    """Create the user document if it doesn't exist."""
    await db[COLLECTION].update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc),
                "policies": [],
            }
        },
        upsert=True,
    )


async def _ensure_policy(db: AsyncIOMotorDatabase, user_id: str, policy_name: str):
    """Add a policy entry to the array if it doesn't already exist."""
    await _ensure_user_doc(db, user_id)
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": {"$ne": policy_name}},
        {
            "$push": {
                "policies": {
                    "policy_name": policy_name,
                    "content": {"status": "pending", "data": None},
                    "structured_content": {"status": "pending", "data": None},
                }
            }
        },
    )


async def update_content_status(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, status: str
):
    """Update the content.status for a policy."""
    await _ensure_policy(db, user_id, policy_name)
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$set": {
                "policies.$.content.status": status,
                "timestamp": datetime.now(timezone.utc),
            }
        },
    )


async def update_content_data(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, data: list[dict]
):
    """Set the content.data (page contents) for a policy."""
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$set": {
                "policies.$.content.data": data,
                "timestamp": datetime.now(timezone.utc),
            }
        },
    )


async def update_total_pages(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, total_pages: int
):
    """Set the content.total_pages for a policy."""
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$set": {
                "policies.$.content.total_pages": total_pages,
                "timestamp": datetime.now(timezone.utc),
            }
        },
    )


async def append_page_data(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, page: dict
):
    """Append a single page to the content.data array for a policy."""
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$push": {"policies.$.content.data": page},
            "$set": {"timestamp": datetime.now(timezone.utc)},
        },
    )


async def update_structured_content_status(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, status: str
):
    """Update the structured_content.status for a policy."""
    await _ensure_policy(db, user_id, policy_name)
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$set": {
                "policies.$.structured_content.status": status,
                "timestamp": datetime.now(timezone.utc),
            }
        },
    )


async def update_structured_content_data(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, data: dict
):
    """Set the structured_content.data (extracted metrics) for a policy."""
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$set": {
                "policies.$.structured_content.data": data,
                "timestamp": datetime.now(timezone.utc),
            }
        },
    )


async def update_document_type(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, document_type: str
):
    """Set the document_type classification for a policy."""
    await _ensure_policy(db, user_id, policy_name)
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$set": {
                "policies.$.document_type": document_type,
                "timestamp": datetime.now(timezone.utc),
            }
        },
    )


async def update_rendered_output_status(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, status: str
):
    """Update the rendered_output.status for a policy."""
    await _ensure_policy(db, user_id, policy_name)
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$set": {
                "policies.$.rendered_output.status": status,
                "timestamp": datetime.now(timezone.utc),
            }
        },
    )


async def update_rendered_output_data(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str, data: dict
):
    """Set the rendered_output.data (plain-English JTBD result) for a policy."""
    await db[COLLECTION].update_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {
            "$set": {
                "policies.$.rendered_output.data": data,
                "timestamp": datetime.now(timezone.utc),
            }
        },
    )


async def get_user_policies(db: AsyncIOMotorDatabase, user_id: str) -> dict | None:
    """Get the full user document."""
    return await db[COLLECTION].find_one({"user_id": user_id}, {"_id": 0})


async def get_policy(
    db: AsyncIOMotorDatabase, user_id: str, policy_name: str
) -> dict | None:
    """Get a single policy from a user's policies array."""
    doc = await db[COLLECTION].find_one(
        {"user_id": user_id, "policies.policy_name": policy_name},
        {"_id": 0, "policies.$": 1},
    )
    if doc and doc.get("policies"):
        return doc["policies"][0]
    return None
