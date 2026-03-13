from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Agent


class AgentsRepository:
    async def get_by_slug(self, session: AsyncSession, slug: str) -> Agent | None:
        return await session.scalar(select(Agent).where(Agent.slug == slug))
