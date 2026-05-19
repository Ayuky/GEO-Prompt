from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_training_service
from app.core.database import get_db
from app.models.training import TrainingMetric, TrainingRun
from app.schemas import PaginatedResponse
from app.schemas.training import TrainingRunRead, TrainingStartRequest
from app.schemas.training_metric import TrainingMetricRead
from app.services.training_service import TrainingService

router = APIRouter(prefix="/trainings", tags=["trainings"])


@router.post("/start", response_model=TrainingRunRead)
def start_training(
    payload: TrainingStartRequest,
    background_tasks: BackgroundTasks,
    service: TrainingService = Depends(get_training_service),
):
    try:
        run = service.create_run(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    background_tasks.add_task(service.execute_run, run.id, payload.questions)
    return run


@router.get("/", response_model=PaginatedResponse[TrainingRunRead])
def list_training_runs(
    experiment_id: int | None = Query(None),
    status: str | None = Query(None),
    algorithm: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    base = select(TrainingRun)
    if experiment_id is not None:
        base = base.where(TrainingRun.experiment_id == experiment_id)
    if status is not None:
        base = base.where(TrainingRun.status == status)
    if algorithm is not None:
        base = base.where(TrainingRun.algorithm == algorithm)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    stmt = base.order_by(TrainingRun.created_at.desc()).offset(skip).limit(limit)
    items = list(db.scalars(stmt).all())
    return {"items": items, "total": total}


@router.get("/{training_run_id}", response_model=TrainingRunRead)
def get_training_status(training_run_id: int, db: Session = Depends(get_db)):
    run = db.get(TrainingRun, training_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    return run


@router.post("/{training_run_id}/pause")
def pause_training(
    training_run_id: int,
    service: TrainingService = Depends(get_training_service),
):
    try:
        return service.pause_training(training_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{training_run_id}/resume")
def resume_training(
    training_run_id: int,
    service: TrainingService = Depends(get_training_service),
):
    try:
        return service.resume_training(training_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{training_run_id}/metrics", response_model=list[TrainingMetricRead])
def get_training_metrics(
    training_run_id: int,
    db: Session = Depends(get_db),
):
    run = db.get(TrainingRun, training_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    stmt = (
        select(TrainingMetric)
        .where(TrainingMetric.training_run_id == training_run_id)
        .order_by(TrainingMetric.timestep.asc())
    )
    return list(db.scalars(stmt).all())
