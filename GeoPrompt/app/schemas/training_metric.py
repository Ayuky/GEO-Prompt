from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TrainingMetricBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class TrainingMetricCreate(TrainingMetricBase):
    training_run_id: int
    timestep: int
    reward: float = 0.0
    entropy_loss: float = 0.0
    value_loss: float = 0.0
    policy_loss: float = 0.0
    metrics_json: dict[str, Any] = Field(default_factory=dict)


class TrainingMetricUpdate(TrainingMetricBase):
    id: int | None = None
    training_run_id: int | None = None
    timestep: int | None = None
    reward: float | None = None
    entropy_loss: float | None = None
    value_loss: float | None = None
    policy_loss: float | None = None
    metrics_json: dict[str, Any] | None = None


class TrainingMetricRead(TrainingMetricBase):
    id: int
    training_run_id: int
    timestep: int
    reward: float
    entropy_loss: float
    value_loss: float
    policy_loss: float
    metrics_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )
