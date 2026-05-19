from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class TrainingStartRequest(BaseModel):
    experiment_id: int
    algorithm: str = Field(default="ppo")
    total_timesteps: int = Field(default=1000, ge=1, le=50000)
    questions: list[str] = Field(min_length=1)
    hyper_params: dict[str, Any] = Field(default_factory=dict)
    enable_llm_scorer: bool = Field(default=True)

    @field_validator("algorithm")
    @classmethod
    def normalize_algorithm(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"ppo", "dqn"}:
            raise ValueError("algorithm must be one of: ppo, dqn")
        return normalized


class TrainingRunRead(BaseModel):
    id: int
    experiment_id: int
    algorithm: str
    status: str
    total_timesteps: int
    current_timestep: int
    best_reward: float
    model_path: str | None
    hyper_params: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
