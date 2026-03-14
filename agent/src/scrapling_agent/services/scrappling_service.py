from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from uuid import UUID
import uuid
from typing import Any

from mcp import StdioServerParameters
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Agent, AgentStatus, ProcessingTask, ScrapeRun, ScrapedDocument
from src.orchestrator.client import OrchestratorClient
from src.utils import AgentRunner
from src.scrapling_agent.constants import SYSTEM_PROMPT
from src.scrapling_agent.client import ScraplingClient
from src.logging import logger
from src.services import RunTrackingService


class ScraplingService:
    def __init__(
        self,
        run_tracking_service: RunTrackingService,
        *,
        session_factory,
    ):
        self.scrapling_client = ScraplingClient()
        self.orchestrator_client = OrchestratorClient()
        self.run_tracking_service = run_tracking_service
        self.session_factory = session_factory
        self.agent_slug = "scrapling-agent"

        self.model="gpt-oss:120b-cloud"
        self.orchestrator_model = "gpt-oss:120b-cloud"
        self.mcp_server=StdioServerParameters(
            command="scrapling", args=["mcp"]
        )

        self.agent_runner = AgentRunner(
            client=self.scrapling_client.client,
            model=self.model,
            local_tool_map={},
            tools=[],
            mcp=self.mcp_server
        )

    async def run_agent(self, prompt: str, session_data: dict[str, Any] | None = None) -> str:
        logger.info("scrapling_agent started | prompt_length={}", len(prompt))
        target_url = self._extract_first_url(prompt)
        source_id = self._resolve_source_id(target_url=target_url, session_data=session_data)

        scrape_run = await self._start_scrape_run(
            source_id=source_id,
            url=target_url or prompt,
        )

        run = await self.run_tracking_service.start_run(
            agent_slug=self.agent_slug,
            input_payload=prompt,
        )
        run_id = run.id
        tool_ids_by_call_id: dict[str, UUID] = {}
        call_order = 0

        async def on_tool_start(tool_call_id: str, tool_name: str, tool_input: str) -> None:
            nonlocal call_order
            call_order += 1
            try:
                run_tool = await self.run_tracking_service.start_tool(
                    run_id=run_id,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    call_order=call_order,
                )
                tool_ids_by_call_id[tool_call_id] = run_tool.id
            except Exception:
                logger.exception("failed to track tool start | run_id={} tool={}", run_id, tool_name)

        async def on_tool_success(tool_call_id: str, tool_name: str, tool_output: str) -> None:
            run_tool_id = tool_ids_by_call_id.get(tool_call_id)
            if run_tool_id is None:
                return
            try:
                await self.run_tracking_service.finish_tool_success(
                    run_tool_id=run_tool_id,
                    tool_output=tool_output,
                )
            except Exception:
                logger.exception("failed to track tool success | run_id={} tool={}", run_id, tool_name)

        async def on_tool_failure(tool_call_id: str, tool_name: str, error_message: str) -> None:
            run_tool_id = tool_ids_by_call_id.get(tool_call_id)
            if run_tool_id is None:
                return
            try:
                await self.run_tracking_service.finish_tool_failed(
                    run_tool_id=run_tool_id,
                    error_message=error_message,
                )
            except Exception:
                logger.exception("failed to track tool failure | run_id={} tool={}", run_id, tool_name)

        try:
            response = await self.agent_runner.run(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
                session_data=session_data,
                on_tool_start=on_tool_start,
                on_tool_success=on_tool_success,
                on_tool_failure=on_tool_failure,
            )
            await self.run_tracking_service.finish_run_success(
                run_id=run_id,
                output_payload=response,
            )
            await self._finish_scrape_run_success(scrape_run=scrape_run)
            await self._persist_scrape_output(
                scrape_run_id=scrape_run.id,
                target_url=target_url,
                response=response,
            )
            logger.info("scrapling_agent finished successfully")
            return response
        except Exception as exc:
            try:
                await self.run_tracking_service.finish_run_failed(
                    run_id=run_id,
                    error_message=str(exc),
                )
            except Exception:
                logger.exception("failed to track run failure | run_id={}", run_id)
            try:
                await self._finish_scrape_run_failed(scrape_run=scrape_run, error_message=str(exc))
            except Exception:
                logger.exception("failed to track scrape run failure | scrape_run_id={}", scrape_run.id)
            logger.exception("scrapling_agent failed")
            raise

    def _extract_first_url(self, prompt: str) -> str | None:
        match = re.search(r"https?://[^\s]+", prompt)
        if not match:
            return None
        return match.group(0).strip().rstrip(".,)")

    def _resolve_source_id(self, *, target_url: str | None, session_data: dict[str, Any] | None) -> uuid.UUID:
        if session_data:
            raw_source_id = session_data.get("source_id")
            if isinstance(raw_source_id, str):
                try:
                    return uuid.UUID(raw_source_id)
                except ValueError:
                    pass
        if target_url:
            return uuid.uuid5(uuid.NAMESPACE_URL, target_url)
        return uuid.uuid4()

    async def _start_scrape_run(self, *, source_id: uuid.UUID, url: str) -> ScrapeRun:
        async with self.session_factory() as session:
            scrape_run = ScrapeRun(
                source_id=source_id,
                url=url,
                status="started",
                started_at=datetime.now(timezone.utc),
            )
            session.add(scrape_run)
            await session.commit()
            await session.refresh(scrape_run)
            return scrape_run

    async def _finish_scrape_run_success(self, *, scrape_run: ScrapeRun) -> None:
        async with self.session_factory() as session:
            db_scrape_run = await session.get(ScrapeRun, scrape_run.id)
            if db_scrape_run is None:
                raise ValueError(f"Scrape run not found for id '{scrape_run.id}'")

            db_scrape_run.status = "success"
            db_scrape_run.finished_at = datetime.now(timezone.utc)
            await session.commit()

    async def _finish_scrape_run_failed(self, *, scrape_run: ScrapeRun, error_message: str) -> None:
        async with self.session_factory() as session:
            db_scrape_run = await session.get(ScrapeRun, scrape_run.id)
            if db_scrape_run is None:
                raise ValueError(f"Scrape run not found for id '{scrape_run.id}'")

            db_scrape_run.status = "failed"
            db_scrape_run.error_message = error_message
            db_scrape_run.finished_at = datetime.now(timezone.utc)
            await session.commit()

    async def _persist_scrape_output(self, *, scrape_run_id: uuid.UUID, target_url: str | None, response: str) -> None:
        parsed_payload = self._parse_response_payload(response)

        resolved_url = parsed_payload.get("url")
        if not isinstance(resolved_url, str) or not resolved_url.strip():
            resolved_url = target_url or "unknown"

        raw_html = parsed_payload.get("raw_html")
        if not isinstance(raw_html, str):
            raw_html = response if "<html" in response.lower() else None

        cleaned_text = parsed_payload.get("cleaned_text")
        if not isinstance(cleaned_text, str):
            cleaned_text = response

        checksum = parsed_payload.get("checksum")
        if not isinstance(checksum, str):
            checksum = None

        language = parsed_payload.get("language")
        if not isinstance(language, str):
            language = None

        async with self.session_factory() as session:
            document = ScrapedDocument(
                scrape_run_id=scrape_run_id,
                url=resolved_url,
                raw_html=raw_html,
                cleaned_text=cleaned_text,
                checksum=checksum,
                language=language,
                scraped_at=datetime.now(timezone.utc),
            )
            session.add(document)
            await session.flush()

            selected_agent_type = await self._select_agent_type_for_document(
                session=session,
                document_url=resolved_url,
                document_text=cleaned_text,
            )
            if selected_agent_type:
                session.add(
                    ProcessingTask(
                        document_id=document.id,
                        agent_type=selected_agent_type,
                        status="pending",
                        attempts=0,
                    )
                )

            await session.commit()

    def _parse_response_payload(self, response: str) -> dict[str, Any]:
        response = response.strip()
        if not response:
            return {}

        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            return {}

        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}

        return {}

    async def _select_agent_type_for_document(
        self,
        *,
        session: AsyncSession,
        document_url: str,
        document_text: str,
    ) -> str | None:
        available_agents = await session.scalars(
            select(Agent).where(
                Agent.status == AgentStatus.ACTIVE,
                Agent.slug != self.agent_slug,
            )
        )
        candidates = list(available_agents)
        if not candidates:
            return None

        candidate_payload = [
            {
                "slug": item.slug,
                "name": item.name,
                "description": item.description or "",
            }
            for item in candidates
        ]
        fallback = sorted(item.slug for item in candidates)[0]

        try:
            completion = self.orchestrator_client.client.chat.completions.create(
                model=self.orchestrator_model,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an orchestrator agent. Choose exactly one best agent slug to process"
                            " scraped content. Respond with strict JSON only: "
                            '{"agent_type":"<slug>","reason":"<short reason>"}'
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "document_url": document_url,
                                "document_excerpt": document_text[:4000],
                                "available_agents": candidate_payload,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
            )
            content = completion.choices[0].message.content or ""
            parsed = self._parse_response_payload(content)
            selected = parsed.get("agent_type")
            if isinstance(selected, str) and any(agent.slug == selected for agent in candidates):
                return selected
        except Exception:
            logger.exception("failed to select processing agent type via orchestrator model")

        return fallback
