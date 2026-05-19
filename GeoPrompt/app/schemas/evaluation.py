from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvaluationRecordCreate(BaseModel):
    experiment_id: int
    prompt_version_id: int
    question: str
    answer: str
    mention_rate: float = 0.0
    naturalness_score: float = 0.0
    context_match_score: float = 0.0
    sentiment_score: float = 0.0
    recommendation_score: float = 0.0
    llm_judge_score: float = 0.0
    total_reward: float = 0.0
    raw_metrics_json: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None
    latency_ms: int | None = None


class EvaluationRecordUpdate(BaseModel):
    id: int | None = None
    experiment_id: int | None = None
    prompt_version_id: int | None = None
    question: str | None = None
    answer: str | None = None
    mention_rate: float | None = None
    naturalness_score: float | None = None
    context_match_score: float | None = None
    sentiment_score: float | None = None
    recommendation_score: float | None = None
    llm_judge_score: float | None = None
    total_reward: float | None = None
    raw_metrics_json: dict[str, Any] | None = None
    trace_id: str | None = None
    latency_ms: int | None = None


class EvaluationRecordRead(BaseModel):
    id: int
    experiment_id: int
    prompt_version_id: int
    question: str
    answer: str
    mention_rate: float
    naturalness_score: float
    context_match_score: float
    sentiment_score: float
    recommendation_score: float
    llm_judge_score: float
    total_reward: float
    raw_metrics_json: dict[str, Any]
    trace_id: str | None = None
    latency_ms: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
