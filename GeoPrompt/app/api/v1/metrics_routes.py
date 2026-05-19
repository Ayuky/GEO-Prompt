from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_metrics_service
from app.schemas import PaginatedResponse
from app.schemas.training_metric import TrainingMetricCreate, TrainingMetricRead, TrainingMetricUpdate
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/list", response_model=PaginatedResponse[TrainingMetricRead])
def list_metrics(
    pageNum: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    trainingRunId: int | None = Query(default=None),
    timestep: int | None = Query(default=None),
    rewardMin: float | None = Query(default=None),
    rewardMax: float | None = Query(default=None),
    createdAt: date | None = Query(default=None),
    service: MetricsService = Depends(get_metrics_service),
):
    skip = (pageNum - 1) * pageSize
    total = service.count(
        training_run_id=trainingRunId,
        timestep=timestep,
        reward_min=rewardMin,
        reward_max=rewardMax,
        created_at=createdAt,
    )
    items = service.list(
        skip=skip,
        limit=pageSize,
        training_run_id=trainingRunId,
        timestep=timestep,
        reward_min=rewardMin,
        reward_max=rewardMax,
        created_at=createdAt,
    )
    return {"items": items, "total": total}


@router.get("/stats", response_model=dict)
def get_metrics_stats(
    service: MetricsService = Depends(get_metrics_service),
):
    return service.stats()


@router.get("/{metric_id}", response_model=TrainingMetricRead)
def get_metric(
    metric_id: int,
    service: MetricsService = Depends(get_metrics_service),
):
    metric = service.get(metric_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Training metric not found")
    return metric


@router.post("", response_model=TrainingMetricRead)
def create_metric(
    payload: TrainingMetricCreate,
    service: MetricsService = Depends(get_metrics_service),
):
    return service.create(payload)


@router.put("", response_model=TrainingMetricRead)
def update_metric(
    payload: TrainingMetricUpdate,
    service: MetricsService = Depends(get_metrics_service),
):
    if payload.id is None:
        raise HTTPException(status_code=400, detail="id is required for update")
    try:
        return service.update(payload.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{metric_id}")
def delete_metric(
    metric_id: int,
    service: MetricsService = Depends(get_metrics_service),
):
    try:
        service.delete(metric_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Training metric deleted successfully"}
