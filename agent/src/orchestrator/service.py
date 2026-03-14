from __future__ import annotations

import json
import re
from typing import Any
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from src.logging import logger
from src.models import AgentStatus
from src.orchestrator.constants import ROUTER_SYSTEM_PROMPT
from src.repositories import AgentsRepository


SessionFactory = Callable[[], AsyncSession]
AgentRunner = Callable[[str, dict[str, Any] | None], Awaitable[str]]


@dataclass(frozen=True)
class AvailableAgent:
    slug: str
    name: str
    description: str | None


class OrchestratorService:
    def __init__(
        self,
        *,
        session_factory: SessionFactory,
        agents_repo: AgentsRepository,
        router_client: OpenAI,
        router_model: str,
        handlers_by_slug: dict[str, AgentRunner],
    ) -> None:
        self.session_factory = session_factory
        self.agents_repo = agents_repo
        self.router_client = router_client
        self.router_model = router_model
        self.handlers_by_slug = handlers_by_slug

    async def run(
        self,
        *,
        prompt: str,
        preferred_agent_slug: str | None = None,
        session_data: dict[str, Any] | None = None,
    ) -> tuple[str, str, str]:
        available_agents = await self._get_available_agents()
        if not available_agents:
            raise RuntimeError("No active and runnable agents are available")

        selected_slug, routing_reason = self._select_agent(
            prompt=prompt,
            preferred_agent_slug=preferred_agent_slug,
            available_agents=available_agents,
        )
        handler = self.handlers_by_slug[selected_slug]

        logger.info(
            "orchestrator selected agent | slug={} reason={}",
            selected_slug,
            routing_reason,
        )
        response = await handler(prompt, session_data)
        return selected_slug, routing_reason, response

    async def _get_available_agents(self) -> list[AvailableAgent]:
        async with self.session_factory() as session:
            agents = await self.agents_repo.list_all(session)

        return [
            AvailableAgent(
                slug=agent.slug,
                name=agent.name,
                description=agent.description,
            )
            for agent in agents
            if agent.status == AgentStatus.ACTIVE and agent.slug in self.handlers_by_slug
        ]

    def _select_agent(
        self,
        *,
        prompt: str,
        preferred_agent_slug: str | None,
        available_agents: list[AvailableAgent],
    ) -> tuple[str, str]:
        available_slugs = {agent.slug for agent in available_agents}

        if preferred_agent_slug:
            if preferred_agent_slug not in available_slugs:
                raise ValueError(
                    f"Preferred agent '{preferred_agent_slug}' is not available"
                )
            return preferred_agent_slug, "preferred_agent"

        return self._select_agent_with_ai(prompt=prompt, available_agents=available_agents)

    def _select_agent_with_ai(
        self,
        *,
        prompt: str,
        available_agents: list[AvailableAgent],
    ) -> tuple[str, str]:
        available_agents_payload = [
            {
                "slug": agent.slug,
                "name": agent.name,
                "description": agent.description or "",
            }
            for agent in available_agents
        ]
        fallback_slug, fallback_reason = self._fallback_select(prompt, available_agents)

        try:
            response = self.router_client.chat.completions.create(
                model=self.router_model,
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "user_request": prompt,
                                "available_agents": available_agents_payload,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
                temperature=0,
            )
            content = response.choices[0].message.content or ""
            parsed = self._extract_json(content)
            selected_slug = parsed.get("agent_slug")
            reason = parsed.get("reason")
            available_slugs = {agent.slug for agent in available_agents}

            if not isinstance(selected_slug, str) or selected_slug not in available_slugs:
                logger.warning(
                    "orchestrator ai returned invalid agent slug | selected={} content={}",
                    selected_slug,
                    content,
                )
                return fallback_slug, "fallback_invalid_ai_choice"

            if not isinstance(reason, str) or not reason.strip():
                reason = "ai_selected_without_reason"

            return selected_slug, f"ai_router:{reason.strip()}"
        except Exception:
            logger.exception("orchestrator ai routing failed")
            return fallback_slug, fallback_reason

    def _extract_json(self, content: str) -> dict[str, object]:
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}

        return {}

    def _fallback_select(
        self,
        prompt: str,
        available_agents: list[AvailableAgent],
    ) -> tuple[str, str]:
        available_slugs = {agent.slug for agent in available_agents}
        lowered_prompt = prompt.lower()
        scrapling_keywords = (
            "scrape",
            "scraping",
            "crawl",
            "website",
            "url",
            "extract",
            "collect",
            "site",
        )
        if (
            "scrapling-agent" in available_slugs
            and any(keyword in lowered_prompt for keyword in scrapling_keywords)
        ):
            return "scrapling-agent", "fallback_keyword_match_scrapling"

        fallback_slug = sorted(available_slugs)[0]
        return fallback_slug, "fallback_first_available"
