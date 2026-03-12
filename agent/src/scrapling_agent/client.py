from openai import OpenAI
from src.config import settings


class ScraplingClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.ollama_api_key,
            base_url=settings.ollama_base_url
        )
