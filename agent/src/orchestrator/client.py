from openai import OpenAI

from src.config import settings


class OrchestratorClient:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=settings.ollama_api_key,
            base_url=settings.ollama_base_url,
        )
