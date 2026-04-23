from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    status: str = "pending"  # pending, in_progress, completed, failed
    data: Any = None


class Policy(BaseModel):
    policy_name: str
    document_type: Optional[str] = None
    content: ContentBlock = Field(default_factory=ContentBlock)
    structured_content: ContentBlock = Field(default_factory=ContentBlock)
    rendered_output: ContentBlock = Field(default_factory=ContentBlock)


class UserPolicies(BaseModel):
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policies: list[Policy] = []
