from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class TrainingRun(Base, TimestampMixin):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    algorithm: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    total_timesteps: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    current_timestep: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    best_reward: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hyper_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class TrainingMetric(Base, TimestampMixin):
    __tablename__ = "training_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    training_run_id: Mapped[int] = mapped_column(
        ForeignKey("training_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestep: Mapped[int] = mapped_column(Integer, nullable=False)
    reward: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    entropy_loss: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    value_loss: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    policy_loss: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
