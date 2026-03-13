from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AgentRunTool, AgentRunToolStatus


class AgentRunToolsRepository:
    async def create_started(
        self,
        session: AsyncSession,
        *,
        run_id: UUID,
        tool_name: str,
        tool_input: str | None,
        call_order: int,
    ) -> AgentRunTool:
        run_tool = AgentRunTool(
            run_id=run_id,
            tool_name=tool_name,
            tool_input=tool_input,
            call_order=call_order,
            status=AgentRunToolStatus.STARTED,
            started_at=datetime.now(timezone.utc),
        )
        session.add(run_tool)
        await session.commit()
        await session.refresh(run_tool)
        return run_tool

    async def mark_success(
        self,
        session: AsyncSession,
        *,
        run_tool: AgentRunTool,
        tool_output: str | None,
    ) -> AgentRunTool:
        run_tool.status = AgentRunToolStatus.SUCCESS
        run_tool.tool_output = tool_output
        run_tool.finished_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(run_tool)
        return run_tool

    async def mark_failed(
        self,
        session: AsyncSession,
        *,
        run_tool: AgentRunTool,
        error_message: str,
    ) -> AgentRunTool:
        run_tool.status = AgentRunToolStatus.FAILED
        run_tool.error_message = error_message
        run_tool.finished_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(run_tool)
        return run_tool
