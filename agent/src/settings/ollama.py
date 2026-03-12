from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices


class OllamaSettings(BaseSettings):
    ollama_api_key: str = Field(..., validation_alias=AliasChoices("OLLAMA_API_KEY"))
    ollama_base_url: str = Field(..., validation_alias=AliasChoices("OLLAMA_BASE_URL"))
