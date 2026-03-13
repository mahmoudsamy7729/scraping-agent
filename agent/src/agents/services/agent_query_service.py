from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Agent, AgentRun, AgentRunTool
from src.repositories import AgentRunsRepository, AgentsRepository

from src.agents.schemas import AgentResponse, AgentRunResponse, AgentToolResponse


SessionFactory = Callable[[], AsyncSession]


class AgentQueryService:
    def __init__(
        self,
        session_factory: SessionFactory,
        agents_repo: AgentsRepository,
        runs_repo: AgentRunsRepository,
    ) -> None:
        self.session_factory = session_factory
        self.agents_repo = agents_repo
        self.runs_repo = runs_repo

    async def list_agents(self) -> list[AgentResponse]:
        async with self.session_factory() as session:
            agents = await self.agents_repo.list_all(session)
            return [self._map_agent(agent) for agent in agents]

    async def list_agent_runs(self, *, agent_id: UUID) -> list[AgentRunResponse]:
        async with self.session_factory() as session:
            agent = await session.get(Agent, agent_id)
            if agent is None:
                raise HTTPException(status_code=404, detail=f"Agent not found for id '{agent_id}'")

            runs = await self.runs_repo.list_by_agent_id_with_tools(
                session,
                agent_id=agent_id,
            )
            return [self._map_run(run) for run in runs]

    def _map_agent(self, agent: Agent) -> AgentResponse:
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            slug=agent.slug,
            description=agent.description,
            model=agent.model,
            status=agent.status.value,
            last_seen_at=agent.last_seen_at,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    def _map_run(self, run: AgentRun) -> AgentRunResponse:
        tools = sorted(run.tools, key=lambda tool: tool.call_order)
        return AgentRunResponse(
            id=run.id,
            status=run.status.value,
            input_payload=run.input_payload,
            output_payload=run.output_payload,
            error_message=run.error_message,
            started_at=run.started_at,
            finished_at=run.finished_at,
            tools=[self._map_tool(tool) for tool in tools],
        )

    def _map_tool(self, tool: AgentRunTool) -> AgentToolResponse:
        return AgentToolResponse(
            id=tool.id,
            tool_name=tool.tool_name,
            call_order=tool.call_order,
            status=tool.status.value,
            tool_input=tool.tool_input,
            tool_output=tool.tool_output,
            error_message=tool.error_message,
        )
