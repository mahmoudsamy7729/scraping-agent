from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from src.agents.dependencies import get_agent_query_service
from src.agents.schemas import AgentResponse, AgentRunResponse
from src.agents.services.agent_query_service import AgentQueryService


router = APIRouter()


@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(
    agent_query_service: AgentQueryService = Depends(get_agent_query_service),
) -> list[AgentResponse]:
    return await agent_query_service.list_agents()


@router.get("/agents/{agent_id}/runs", response_model=list[AgentRunResponse])
async def list_agent_runs(
    agent_id: UUID,
    agent_query_service: AgentQueryService = Depends(get_agent_query_service),
) -> list[AgentRunResponse]:
    return await agent_query_service.list_agent_runs(agent_id=agent_id)
