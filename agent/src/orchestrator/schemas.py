from __future__ import annotations

from pydantic import BaseModel, Field


class OrchestratorRunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    preferred_agent_slug: str | None = None


class OrchestratorRunResponse(BaseModel):
    selected_agent_slug: str
    routing_reason: str
    response: str
