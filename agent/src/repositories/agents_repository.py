from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Agent


class AgentsRepository:
    async def list_all(self, session: AsyncSession) -> list[Agent]:
        result = await session.scalars(select(Agent).order_by(Agent.created_at.desc()))
        return list(result)

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Agent | None:
        return await session.scalar(select(Agent).where(Agent.slug == slug))

    async def touch_last_seen(self, session: AsyncSession, agent: Agent) -> Agent:
        agent.last_seen_at = datetime.now(timezone.utc)
        await session.flush()
        return agent
