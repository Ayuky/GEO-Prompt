from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.training import TrainingMetric
from app.schemas.training_metric import TrainingMetricCreate, TrainingMetricUpdate


class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _apply_filters(self, stmt, *, training_run_id, timestep, reward_min, reward_max, created_at):
        if training_run_id is not None:
            stmt = stmt.where(TrainingMetric.training_run_id == training_run_id)
        if timestep is not None:
            stmt = stmt.where(TrainingMetric.timestep == timestep)
        if reward_min is not None:
            stmt = stmt.where(TrainingMetric.reward >= reward_min)
        if reward_max is not None:
            stmt = stmt.where(TrainingMetric.reward <= reward_max)
        if created_at is not None:
            start = datetime.combine(created_at, datetime.min.time())
            end = datetime.combine(created_at, datetime.max.time())
            stmt = stmt.where(TrainingMetric.created_at.between(start, end))
        return stmt

    def count(
        self,
        *,
        training_run_id: int | None = None,
        timestep: int | None = None,
        reward_min: float | None = None,
        reward_max: float | None = None,
        created_at: date | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(TrainingMetric)
        stmt = self._apply_filters(stmt, training_run_id=training_run_id, timestep=timestep,
                                   reward_min=reward_min, reward_max=reward_max, created_at=created_at)
        return self.db.scalar(stmt) or 0

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        *,
        training_run_id: int | None = None,
        timestep: int | None = None,
        reward_min: float | None = None,
        reward_max: float | None = None,
        created_at: date | None = None,
    ) -> list[TrainingMetric]:
        stmt = select(TrainingMetric).order_by(TrainingMetric.id.desc())
        stmt = self._apply_filters(stmt, training_run_id=training_run_id, timestep=timestep,
                                   reward_min=reward_min, reward_max=reward_max, created_at=created_at)
        return list(self.db.scalars(stmt.offset(skip).limit(limit)).all())

    def get(self, metric_id: int) -> TrainingMetric | None:
        return self.db.get(TrainingMetric, metric_id)

    def create(self, payload: TrainingMetricCreate) -> TrainingMetric:
        metric = TrainingMetric(**payload.model_dump(by_alias=False))
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def update(self, metric_id: int, payload: TrainingMetricUpdate) -> TrainingMetric:
        metric = self.db.get(TrainingMetric, metric_id)
        if not metric:
            raise ValueError(f"Training metric not found: {metric_id}")
        for field, value in payload.model_dump(exclude_unset=True, by_alias=False).items():
            setattr(metric, field, value)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def delete(self, metric_id: int) -> None:
        metric = self.db.get(TrainingMetric, metric_id)
        if not metric:
            raise ValueError(f"Training metric not found: {metric_id}")
        self.db.delete(metric)
        self.db.commit()

    def stats(self) -> dict:
        total = self.db.query(func.count(TrainingMetric.id)).scalar() or 0
        avgs = self.db.query(
            func.avg(TrainingMetric.reward).label("avg_reward"),
            func.avg(TrainingMetric.entropy_loss).label("avg_entropy"),
            func.avg(TrainingMetric.value_loss).label("avg_value"),
            func.avg(TrainingMetric.policy_loss).label("avg_policy"),
        ).first()
        return {
            "total": total,
            "avg_reward": round(float(avgs.avg_reward or 0), 4),
            "avg_entropy_loss": round(float(avgs.avg_entropy or 0), 4),
            "avg_value_loss": round(float(avgs.avg_value or 0), 4),
            "avg_policy_loss": round(float(avgs.avg_policy or 0), 4),
        }
