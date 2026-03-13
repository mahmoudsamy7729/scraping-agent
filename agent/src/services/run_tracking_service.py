from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AgentRun, AgentRunTool
from src.repositories import AgentRunToolsRepository, AgentRunsRepository, AgentsRepository


SessionFactory = Callable[[], AsyncSession]


class RunTrackingService:
    def __init__(
        self,
        session_factory: SessionFactory,
        agents_repo: AgentsRepository,
        runs_repo: AgentRunsRepository,
        run_tools_repo: AgentRunToolsRepository,
    ) -> None:
        self.session_factory = session_factory
        self.agents_repo = agents_repo
        self.runs_repo = runs_repo
        self.run_tools_repo = run_tools_repo

    async def start_run(self, *, agent_slug: str, input_payload: str | None) -> AgentRun:
        async with self.session_factory() as session:
            agent = await self.agents_repo.get_by_slug(session, agent_slug)
            if agent is None:
                raise ValueError(f"Agent not found for slug '{agent_slug}'")
            return await self.runs_repo.create(
                session,
                agent_id=agent.id,
                input_payload=input_payload,
            )

    async def finish_run_success(self, *, run_id: UUID, output_payload: str | None) -> AgentRun:
        async with self.session_factory() as session:
            run = await self._get_run_or_raise(session, run_id)
            return await self.runs_repo.mark_success(
                session,
                run=run,
                output_payload=output_payload,
            )

    async def finish_run_failed(self, *, run_id: UUID, error_message: str) -> AgentRun:
        async with self.session_factory() as session:
            run = await self._get_run_or_raise(session, run_id)
            return await self.runs_repo.mark_failed(
                session,
                run=run,
                error_message=error_message,
            )

    async def start_tool(
        self,
        *,
        run_id: UUID,
        tool_name: str,
        tool_input: str | None,
        call_order: int,
    ) -> AgentRunTool:
        async with self.session_factory() as session:
            return await self.run_tools_repo.create_started(
                session,
                run_id=run_id,
                tool_name=tool_name,
                tool_input=tool_input,
                call_order=call_order,
            )

    async def finish_tool_success(self, *, run_tool_id: UUID, tool_output: str | None) -> AgentRunTool:
        async with self.session_factory() as session:
            run_tool = await self._get_run_tool_or_raise(session, run_tool_id)
            return await self.run_tools_repo.mark_success(
                session,
                run_tool=run_tool,
                tool_output=tool_output,
            )

    async def finish_tool_failed(self, *, run_tool_id: UUID, error_message: str) -> AgentRunTool:
        async with self.session_factory() as session:
            run_tool = await self._get_run_tool_or_raise(session, run_tool_id)
            return await self.run_tools_repo.mark_failed(
                session,
                run_tool=run_tool,
                error_message=error_message,
            )

    async def _get_run_or_raise(self, session: AsyncSession, run_id: UUID) -> AgentRun:
        run = await session.get(AgentRun, run_id)
        if run is None:
            raise ValueError(f"Run not found for id '{run_id}'")
        return run

    async def _get_run_tool_or_raise(self, session: AsyncSession, run_tool_id: UUID) -> AgentRunTool:
        run_tool = await session.get(AgentRunTool, run_tool_id)
        if run_tool is None:
            raise ValueError(f"Run tool not found for id '{run_tool_id}'")
        return run_tool
