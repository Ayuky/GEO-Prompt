from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_versions_service
from app.schemas.prompt_version import PromptVersionCreate, PromptVersionRead, PromptVersionUpdate
from app.services.versions_service import VersionsService

router = APIRouter(prefix="/versions", tags=["versions"])


@router.get("/list")
def list_versions(
    pageNum: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    experimentId: int | None = Query(default=None),
    roundIndex: int | None = Query(default=None),
    generatorType: str | None = Query(default=None),
    policyAction: str | None = Query(default=None),
    createdAt: str | None = Query(default=None),
    service: VersionsService = Depends(get_versions_service),
):
    skip = (pageNum - 1) * pageSize
    items, total = service.list_with_count(
        skip=skip,
        limit=pageSize,
        experiment_id=experimentId,
        round_index=roundIndex,
        generator_type=generatorType,
        policy_action=policyAction,
        created_at=createdAt,
    )
    return {"items": items, "total": total}


@router.get("/stats", response_model=dict)
def get_versions_stats(
    service: VersionsService = Depends(get_versions_service),
):
    return service.stats()


@router.get("/{version_id}", response_model=PromptVersionRead)
def get_version(
    version_id: int,
    service: VersionsService = Depends(get_versions_service),
):
    version = service.get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    return version


@router.post("", response_model=PromptVersionRead)
def create_version(
    payload: PromptVersionCreate,
    service: VersionsService = Depends(get_versions_service),
):
    return service.create(payload)


@router.put("", response_model=PromptVersionRead)
def update_version(
    payload: PromptVersionUpdate,
    service: VersionsService = Depends(get_versions_service),
):
    if payload.id is None:
        raise HTTPException(status_code=400, detail="id is required for update")
    try:
        return service.update(payload.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{version_id}")
def delete_version(
    version_id: int,
    service: VersionsService = Depends(get_versions_service),
):
    try:
        service.delete(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Prompt version deleted successfully"}
