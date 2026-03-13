from pydantic_settings import SettingsConfigDict
from pathlib import Path
from src.settings.groq import GroqSettings
from src.settings.ollama import OllamaSettings
from src.settings.db_connection import DBConnection


BASE_DIR = Path(__file__).parent.parent


class Settings(GroqSettings, OllamaSettings, DBConnection):
    
    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8",
    extra="ignore",)


settings = Settings()  #type: ignore