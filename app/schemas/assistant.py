from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AssistantIntent = Literal[
    "explain_readiness",
    "explain_skill_gap",
    "explain_roadmap",
    "explain_next_best_action",
    "explain_project_recommendation",
    "project_bounded_help",
]


class AssistantChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str | int | None = None
    message: str = Field(..., min_length=1, max_length=2000)
    intent: AssistantIntent | None = None
    context: str | None = None
    locale: Literal["ar", "en"] | None = None

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value

    @field_validator("context", mode="before")
    @classmethod
    def normalize_context(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class AssistantChatResponse(BaseModel):
    status: Literal["answered", "insufficient_context"]
    reply: str
    grounded: bool
    sources: list[str] = Field(default_factory=list)
    provider_used: str | None = None
    prompt_version: str
    request_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
