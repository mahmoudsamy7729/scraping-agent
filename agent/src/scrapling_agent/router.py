from fastapi import APIRouter, Depends
from src.scrapling_agent.dependencies import get_scrapling_service
from src.scrapling_agent.services.scrappling_service import ScraplingService



router = APIRouter()

@router.get('/health-check')
async def health_check():
    return {'status': 'ok'}


@router.post('/run-agent')
async def run_agent(
    prompt: str,
    scrapling_service: ScraplingService = Depends(get_scrapling_service),
):
    response = await scrapling_service.run_agent(prompt)
    return {'response': response}
