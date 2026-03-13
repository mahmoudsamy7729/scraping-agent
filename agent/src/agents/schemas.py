from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AgentToolResponse(BaseModel):
    id: UUID
    tool_name: str
    call_order: int
    status: str
    tool_input: str | None
    tool_output: str | None
    error_message: str | None


class AgentRunResponse(BaseModel):
    id: UUID
    status: str
    input_payload: str | None
    output_payload: str | None
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None
    tools: list[AgentToolResponse]


class AgentResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    model: str
    status: str
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime
