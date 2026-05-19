from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_experiment_service
from app.schemas import PaginatedResponse
from app.schemas.experiment import (
    EvaluationRead,
    ExperimentCreate,
    ExperimentRead,
    ExperimentRunAcceptedResponse,
    ExperimentRunRequest,
    PromptVersionRead,
)
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=PaginatedResponse[ExperimentRead])
def list_experiments(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    name: str | None = Query(default=None),
    model_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    service: ExperimentService = Depends(get_experiment_service),
):
    items = service.list_experiments(skip=skip, limit=limit, name=name, model_id=model_id, status=status)
    total = service.count_experiments(name=name, model_id=model_id, status=status)
    return {"items": items, "total": total}


@router.post("", response_model=ExperimentRead)
def create_experiment(
    payload: ExperimentCreate,
    service: ExperimentService = Depends(get_experiment_service),
):
    return service.create_experiment(payload)


@router.get("/{experiment_id}", response_model=ExperimentRead)
def get_experiment(
    experiment_id: int,
    service: ExperimentService = Depends(get_experiment_service),
):
    experiment = service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.get("/{experiment_id}/versions", response_model=list[PromptVersionRead])
def list_prompt_versions(
    experiment_id: int,
    service: ExperimentService = Depends(get_experiment_service),
):
    experiment = service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return service.list_versions(experiment_id)


@router.post("/{experiment_id}/run", response_model=ExperimentRunAcceptedResponse)
def run_experiment_round(
    experiment_id: int,
    payload: ExperimentRunRequest,
    service: ExperimentService = Depends(get_experiment_service),
):
    try:
        return service.run_round_async(experiment_id=experiment_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{experiment_id}/evaluations", response_model=list[EvaluationRead])
def list_evaluations(
    experiment_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    service: ExperimentService = Depends(get_experiment_service),
):
    experiment = service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return service.list_evaluations(experiment_id=experiment_id, limit=limit)


@router.delete("/{experiment_id}")
def delete_experiment(
    experiment_id: int,
    service: ExperimentService = Depends(get_experiment_service),
):
    experiment = service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    service.delete_experiment(experiment_id)
    return {"message": "Experiment deleted successfully"}


@router.post("/{experiment_id}/pause")
def pause_experiment(
    experiment_id: int,
    service: ExperimentService = Depends(get_experiment_service),
):
    try:
        return service.pause_experiment(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{experiment_id}/resume")
def resume_experiment(
    experiment_id: int,
    service: ExperimentService = Depends(get_experiment_service),
):
    try:
        return service.resume_experiment(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
