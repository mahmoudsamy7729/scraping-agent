from uuid import UUID

from mcp import StdioServerParameters
from src.utils import AgentRunner
from src.scrapling_agent.constants import SYSTEM_PROMPT
from src.scrapling_agent.client import ScraplingClient
from src.logging import logger
from src.services import RunTrackingService


class ScraplingService:
    def __init__(self, run_tracking_service: RunTrackingService):
        self.scrapling_client = ScraplingClient()
        self.run_tracking_service = run_tracking_service
        self.agent_slug = "scrapling-agent"

        self.model="gpt-oss:120b-cloud"
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

    async def run_agent(self, prompt: str) -> str:
        logger.info("scrapling_agent started | prompt_length={}", len(prompt))
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
                on_tool_start=on_tool_start,
                on_tool_success=on_tool_success,
                on_tool_failure=on_tool_failure,
            )
            await self.run_tracking_service.finish_run_success(
                run_id=run_id,
                output_payload=response,
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
            logger.exception("scrapling_agent failed")
            raise
