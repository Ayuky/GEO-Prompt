from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    domain: str = Field(min_length=1, max_length=64)
    description: str | None = None
    model_id: int
    judge_model_id: int
    target_entities: list[str] = Field(default_factory=list)
    context_text: str | None = None
    max_rounds: int = Field(default=20, ge=1, le=500)


class ExperimentRead(BaseModel):
    id: int
    name: str
    status: str
    model_id: int
    judge_model_id: int
    model_name: str = ""
    judge_model_name: str = ""
    target_entities: list[str]
    current_round: int
    max_rounds: int
    best_reward: float
    created_at: datetime

    model_config = {"from_attributes": True}


class ExperimentRunRequest(BaseModel):
    questions: list[str] = Field(min_length=1)
    generator_mode: str = Field(default="random")
    source_prompt: str | None = None
    manual_prompt: str | None = None
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
    num_rounds: int = Field(default=1, ge=1, le=100)
    enable_llm_scorer: bool = Field(default=True)


class RoundRunResult(BaseModel):
    prompt_version_id: int
    round_index: int
    generator_mode: str
    prompt_text: str
    mean_reward: float
    metrics: dict[str, Any]


class ExperimentRunResponse(BaseModel):
    experiment_id: int
    rounds: list[RoundRunResult]
    total_rounds_ran: int
    final_best_reward: float
    final_status: str


class ExperimentRunAcceptedResponse(BaseModel):
    experiment_id: int
    accepted: bool = True
    message: str
    current_round: int
    max_rounds: int
    num_rounds_requested: int


class PromptVersionRead(BaseModel):
    id: int
    round_index: int
    generator_type: str
    prompt_text: str
    mean_reward: float
    mean_judge_score: float
    prompt_mention_rate: float = 0.0
    policy_action: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationRead(BaseModel):
    id: int
    question: str
    answer: str
    mention_rate: float
    naturalness_score: float
    context_match_score: float
    sentiment_score: float
    recommendation_score: float
    llm_judge_score: float
    total_reward: float
    trace_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
