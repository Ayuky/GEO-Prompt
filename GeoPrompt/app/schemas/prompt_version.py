from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PromptVersionCreate(BaseModel):
    experiment_id: int
    round_index: int = 0
    generator_type: str = "random"
    prompt_text: str
    policy_action: str | None = None
    mean_reward: float = 0.0
    mean_judge_score: float = 0.0
    prompt_mention_rate: float = 0.0
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class PromptVersionUpdate(BaseModel):
    id: int | None = None
    experiment_id: int | None = None
    round_index: int | None = None
    generator_type: str | None = None
    prompt_text: str | None = None
    policy_action: str | None = None
    mean_reward: float | None = None
    mean_judge_score: float | None = None
    prompt_mention_rate: float | None = None
    metadata_json: dict[str, Any] | None = None


class PromptVersionRead(BaseModel):
    id: int
    experiment_id: int
    round_index: int
    generator_type: str
    prompt_text: str
    policy_action: str | None = None
    mean_reward: float
    mean_judge_score: float
    prompt_mention_rate: float = 0.0
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
