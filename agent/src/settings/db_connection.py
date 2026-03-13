from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices


class DBConnection(BaseSettings):
    async_database_url: str = Field(..., validation_alias=AliasChoices("ASYNC_DATABASE_URL"))
