from openai import OpenAI
from mcp import StdioServerParameters
from src.utils import AgentRunner
from src.config import settings
from src.scrapling_agent.constants import SYSTEM_PROMPT
from src.scrapling_agent.client import ScraplingClient
from src.logging import logger


class ScraplingService:
    def __init__(self):
        self.scrapling_client = ScraplingClient()

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
        try:
            response = await self.agent_runner.run(
                system_prompt=SYSTEM_PROMPT, user_prompt=prompt
            )
            logger.info("scrapling_agent finished successfully")
            return response
        except Exception:
            logger.exception("scrapling_agent failed")
            raise
