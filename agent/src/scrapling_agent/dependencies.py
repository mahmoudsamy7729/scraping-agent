from __future__ import annotations

from src.scrapling_agent.services.scrappling_service import ScraplingService
from src.services.dependencies import get_run_tracking_service


def get_scrapling_service() -> ScraplingService:
    return ScraplingService(run_tracking_service=get_run_tracking_service())
