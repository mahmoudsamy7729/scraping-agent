from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices

class GroqSettings(BaseSettings):
    groq_api_key: str = Field(..., validation_alias=AliasChoices("GROQ_API_KEY"))
    groq_base_url: str = Field(..., validation_alias=AliasChoices("GROQ_BASE_URL"))