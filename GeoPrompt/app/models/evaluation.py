from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class EvaluationRecord(Base, TimestampMixin):
    __tablename__ = "evaluation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_version_id: Mapped[int] = mapped_column(
        ForeignKey("prompt_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    mention_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    naturalness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    context_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommendation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    llm_judge_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_reward: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    raw_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
