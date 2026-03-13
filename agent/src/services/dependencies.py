from __future__ import annotations

from src.database import async_session
from src.repositories import AgentRunToolsRepository, AgentRunsRepository, AgentsRepository
from src.services.run_tracking_service import RunTrackingService


def get_agents_repository() -> AgentsRepository:
    return AgentsRepository()


def get_agent_runs_repository() -> AgentRunsRepository:
    return AgentRunsRepository()


def get_agent_run_tools_repository() -> AgentRunToolsRepository:
    return AgentRunToolsRepository()


def get_run_tracking_service() -> RunTrackingService:
    return RunTrackingService(
        session_factory=async_session,
        agents_repo=get_agents_repository(),
        runs_repo=get_agent_runs_repository(),
        run_tools_repo=get_agent_run_tools_repository(),
    )
