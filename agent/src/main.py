from fastapi import FastAPI, APIRouter
from src.agents.router import router as agents_router
from src.orchestrator.router import router as orchestrator_router
from src.scrapling_agent.router import router as scrapling_agent_router
from src.logging import setup_logging


setup_logging()

app = FastAPI()

main_router = APIRouter(prefix="/api")



main_router.include_router(agents_router, tags=["Agents"])
main_router.include_router(scrapling_agent_router, prefix="/scrapling-agent", tags=["Scrapling Agent"])
main_router.include_router(orchestrator_router, prefix="/orchestrator", tags=["Orchestrator"])

app.include_router(main_router)
