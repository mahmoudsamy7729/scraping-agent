from __future__ import annotations

from src.database import async_session
from src.orchestrator.client import OrchestratorClient
from src.orchestrator.service import OrchestratorService
from src.scrapling_agent.dependencies import get_scrapling_service
from src.services.dependencies import get_agents_repository


def get_orchestrator_service() -> OrchestratorService:
    scrapling_service = get_scrapling_service()
    orchestrator_client = OrchestratorClient()

    return OrchestratorService(
        session_factory=async_session,
        agents_repo=get_agents_repository(),
        router_client=orchestrator_client.client,
        router_model="gpt-oss:120b-cloud",
        handlers_by_slug={
            "scrapling-agent": scrapling_service.run_agent,
        },
    )
