from __future__ import annotations

from src.agents.services.agent_query_service import AgentQueryService
from src.database import async_session
from src.services.dependencies import get_agent_runs_repository, get_agents_repository


def get_agent_query_service() -> AgentQueryService:
    return AgentQueryService(
        session_factory=async_session,
        agents_repo=get_agents_repository(),
        runs_repo=get_agent_runs_repository(),
    )
