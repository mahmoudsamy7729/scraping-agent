from __future__ import annotations
from typing import Any

from pydantic import BaseModel, Field


class SessionData(BaseModel):
    cookies: Any | None = None
    headers: dict[str, str] | None = None


class OrchestratorRunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    preferred_agent_slug: str | None = None
    session_data: SessionData | None = None


class OrchestratorRunResponse(BaseModel):
    selected_agent_slug: str
    routing_reason: str
    response: str
