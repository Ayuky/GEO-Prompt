from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Experiment(Base, TimestampMixin):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, default="汽车")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")

    model_id: Mapped[int] = mapped_column(ForeignKey("custom_models.id"), nullable=False)
    judge_model_id: Mapped[int] = mapped_column(ForeignKey("custom_models.id"), nullable=False)

    target_entities: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    context_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    max_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    best_reward: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    model: Mapped["CustomModel"] = relationship(foreign_keys=[model_id])
    judge_model: Mapped["CustomModel"] = relationship(foreign_keys=[judge_model_id])

    @property
    def model_name(self) -> str:
        return self.model.model_name if self.model else ""

    @property
    def judge_model_name(self) -> str:
        return self.judge_model.model_name if self.judge_model else ""

    prompt_versions: Mapped[list["PromptVersion"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class PromptVersion(Base, TimestampMixin):
    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generator_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    policy_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mean_reward: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mean_judge_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    prompt_mention_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    experiment: Mapped[Experiment] = relationship(back_populates="prompt_versions")
