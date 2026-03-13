from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.orchestrator.dependencies import get_orchestrator_service
from src.orchestrator.schemas import OrchestratorRunRequest, OrchestratorRunResponse
from src.orchestrator.service import OrchestratorService


router = APIRouter()


@router.post("/run", response_model=OrchestratorRunResponse)
async def run_orchestrator(
    body: OrchestratorRunRequest,
    orchestrator_service: OrchestratorService = Depends(get_orchestrator_service),
) -> OrchestratorRunResponse:
    try:
        selected_slug, routing_reason, response = await orchestrator_service.run(
            prompt=body.prompt,
            preferred_agent_slug=body.preferred_agent_slug,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return OrchestratorRunResponse(
        selected_agent_slug=selected_slug,
        routing_reason=routing_reason,
        response=response,
    )
