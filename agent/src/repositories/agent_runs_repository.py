from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AgentRun, AgentRunStatus


class AgentRunsRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        agent_id,
        input_payload: str | None,
    ) -> AgentRun:
        run = AgentRun(
            agent_id=agent_id,
            status=AgentRunStatus.STARTED,
            input_payload=input_payload,
            started_at=datetime.now(timezone.utc),
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)
        return run

    async def mark_success(
        self,
        session: AsyncSession,
        *,
        run: AgentRun,
        output_payload: str | None,
    ) -> AgentRun:
        run.status = AgentRunStatus.SUCCESS
        run.output_payload = output_payload
        run.finished_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(run)
        return run

    async def mark_failed(
        self,
        session: AsyncSession,
        *,
        run: AgentRun,
        error_message: str,
    ) -> AgentRun:
        run.status = AgentRunStatus.FAILED
        run.error_message = error_message
        run.finished_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(run)
        return run
