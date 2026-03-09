from fastapi import FastAPI, APIRouter
from src.scrapling_agent.router import router as scrapling_agent_router



app = FastAPI()

main_router = APIRouter(prefix="/api")


app.include_router(scrapling_agent_router, prefix="/scrapling-agent")