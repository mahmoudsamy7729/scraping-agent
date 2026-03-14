from __future__ import annotations
import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from src.orchestrator.dependencies import get_orchestrator_service
from src.orchestrator.schemas import OrchestratorRunRequest, OrchestratorRunResponse
from src.orchestrator.service import OrchestratorService


router = APIRouter()


async def _run_orchestrator_internal(
    *,
    orchestrator_service: OrchestratorService,
    prompt: str,
    preferred_agent_slug: str | None,
    session_data: dict[str, object] | None,
) -> OrchestratorRunResponse:
    try:
        selected_slug, routing_reason, response = await orchestrator_service.run(
            prompt=prompt,
            preferred_agent_slug=preferred_agent_slug,
            session_data=session_data,
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


def _normalize_same_site(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    lowered = value.strip().lower()
    if lowered in {"none", "no_restriction", "no-restriction", "norestriction"}:
        return "None"
    if lowered == "lax":
        return "Lax"
    if lowered == "strict":
        return "Strict"
    return None


def _parse_browser_cookie_export(content: str) -> list[dict[str, Any]]:
    parsed = json.loads(content)
    if not isinstance(parsed, list):
        raise ValueError("cookies JSON must be an array")

    cookies: list[dict[str, Any]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if not isinstance(name, str) or not isinstance(value, str) or not name.strip():
            continue

        cookie: dict[str, Any] = {
            "name": name.strip(),
            "value": value,
        }
        domain = item.get("domain")
        if isinstance(domain, str) and domain.strip():
            cookie["domain"] = domain.strip()

        path = item.get("path")
        if isinstance(path, str) and path.strip():
            cookie["path"] = path.strip()

        expires = item.get("expirationDate")
        if isinstance(expires, (int, float)):
            cookie["expires"] = float(expires)

        if isinstance(item.get("httpOnly"), bool):
            cookie["httpOnly"] = item["httpOnly"]
        if isinstance(item.get("secure"), bool):
            cookie["secure"] = item["secure"]

        same_site = _normalize_same_site(item.get("sameSite"))
        if same_site is not None:
            cookie["sameSite"] = same_site

        cookies.append(cookie)

    if not cookies:
        raise ValueError("cookies JSON does not include valid cookie entries")

    return cookies


@router.post("/run", response_model=OrchestratorRunResponse)
async def run_orchestrator(
    body: OrchestratorRunRequest,
    orchestrator_service: OrchestratorService = Depends(get_orchestrator_service),
) -> OrchestratorRunResponse:
    session_data = body.session_data.model_dump(exclude_none=True) if body.session_data else None
    return await _run_orchestrator_internal(
        orchestrator_service=orchestrator_service,
        prompt=body.prompt,
        preferred_agent_slug=body.preferred_agent_slug,
        session_data=session_data,
    )


@router.post("/run-with-cookies-file", response_model=OrchestratorRunResponse)
async def run_orchestrator_with_cookies_file(
    prompt: str = Form(..., min_length=1),
    preferred_agent_slug: str | None = Form(default=None),
    cookies_file: UploadFile = File(...),
    orchestrator_service: OrchestratorService = Depends(get_orchestrator_service),
) -> OrchestratorRunResponse:
    filename = (cookies_file.filename or "").lower()
    if filename and not (filename.endswith(".txt") or filename.endswith(".cookie")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cookies_file must be a .txt or .cookie file",
        )

    content = await cookies_file.read()
    raw_content = content.decode("utf-8", errors="ignore").strip()
    if not raw_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cookies_file is empty",
        )

    session_data: dict[str, object]
    try:
        parsed_cookies = _parse_browser_cookie_export(raw_content)
        session_data = {"cookies": parsed_cookies}
    except ValueError:
        session_data = {"headers": {"Cookie": raw_content}}

    return await _run_orchestrator_internal(
        orchestrator_service=orchestrator_service,
        prompt=prompt,
        preferred_agent_slug=preferred_agent_slug,
        session_data=session_data,
    )
