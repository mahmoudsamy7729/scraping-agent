from fastapi import APIRouter
from src.scrapling_agent.services.scrappling_service import ScraplingService



router = APIRouter()

scrapling_service = ScraplingService()

@router.get('/health-check')
async def health_check():
    return {'status': 'ok'}


@router.post('/run-agent')
async def run_agent(prompt: str):
    response = await scrapling_service.run_agent(prompt)
    return {'response': response}
