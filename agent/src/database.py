from typing import Annotated
from fastapi import Depends 
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from src.config import settings


engine = create_async_engine(settings.async_database_url, echo=False)


async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


Base = declarative_base()


async def get_db():
    async with async_session() as session:
        yield session


db_dependency = Annotated[AsyncSession, Depends(get_db)]
