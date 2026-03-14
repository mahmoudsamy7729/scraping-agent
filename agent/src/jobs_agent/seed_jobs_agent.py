from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.models import Agent, AgentStatus


SLUG = "jobs-agent"
NAME = "Jobs Agent"
DESCRIPTION = "Agent responsible for extracting and processing jobs-related entities."
MODEL = "gpt-oss:120b-cloud"


async def seed_jobs_agent() -> None:
    engine = create_async_engine(settings.async_database_url, future=True, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        existing_agent = await session.scalar(select(Agent).where(Agent.slug == SLUG))

        if existing_agent:
            existing_agent.name = NAME
            existing_agent.description = DESCRIPTION
            existing_agent.model = MODEL
            existing_agent.status = AgentStatus.ACTIVE
            action = "updated"
        else:
            session.add(
                Agent(
                    name=NAME,
                    slug=SLUG,
                    description=DESCRIPTION,
                    model=MODEL,
                    status=AgentStatus.ACTIVE,
                )
            )
            action = "created"

        await session.commit()
        print(f"Jobs agent {action}: {SLUG}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_jobs_agent())
