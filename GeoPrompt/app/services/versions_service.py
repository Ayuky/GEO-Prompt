from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.experiment import PromptVersion
from app.schemas.prompt_version import PromptVersionCreate, PromptVersionUpdate


class VersionsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        experiment_id: int | None = None,
        generator_type: str | None = None,
    ) -> list[PromptVersion]:
        stmt = select(PromptVersion).order_by(PromptVersion.id.desc())
        if experiment_id is not None:
            stmt = stmt.where(PromptVersion.experiment_id == experiment_id)
        if generator_type:
            stmt = stmt.where(PromptVersion.generator_type == generator_type)
        return list(self.db.scalars(stmt.offset(skip).limit(limit)).all())

    def list_with_count(
        self,
        skip: int = 0,
        limit: int = 100,
        experiment_id: int | None = None,
        round_index: int | None = None,
        generator_type: str | None = None,
        policy_action: str | None = None,
        created_at: str | None = None,
    ) -> tuple[list[PromptVersion], int]:
        base = select(PromptVersion)
        if experiment_id is not None:
            base = base.where(PromptVersion.experiment_id == experiment_id)
        if round_index is not None:
            base = base.where(PromptVersion.round_index == round_index)
        if generator_type:
            base = base.where(PromptVersion.generator_type == generator_type)
        if policy_action:
            base = base.where(PromptVersion.policy_action == policy_action)
        if created_at:
            base = base.where(func.date(PromptVersion.created_at) == created_at)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(
            base.order_by(PromptVersion.id.desc()).offset(skip).limit(limit)
        ).all())
        return items, total

    def get(self, version_id: int) -> PromptVersion | None:
        return self.db.get(PromptVersion, version_id)

    def create(self, payload: PromptVersionCreate) -> PromptVersion:
        version = PromptVersion(**payload.model_dump())
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def update(self, version_id: int, payload: PromptVersionUpdate) -> PromptVersion:
        version = self.db.get(PromptVersion, version_id)
        if not version:
            raise ValueError(f"Prompt version not found: {version_id}")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(version, field, value)
        self.db.commit()
        self.db.refresh(version)
        return version

    def delete(self, version_id: int) -> None:
        version = self.db.get(PromptVersion, version_id)
        if not version:
            raise ValueError(f"Prompt version not found: {version_id}")
        self.db.delete(version)
        self.db.commit()

    def stats(self) -> dict:
        total = self.db.query(func.count(PromptVersion.id)).scalar() or 0
        type_counts = (
            self.db.query(
                PromptVersion.generator_type,
                func.count(PromptVersion.id).label("cnt"),
            )
            .group_by(PromptVersion.generator_type)
            .all()
        )
        by_type = {row.generator_type: row.cnt for row in type_counts}
        avg_mention_rate = self.db.query(func.round(func.avg(PromptVersion.prompt_mention_rate), 4)).scalar() or 0.0
        avg_reward = self.db.query(func.round(func.avg(PromptVersion.mean_reward), 4)).scalar() or 0.0
        avg_judge = self.db.query(func.round(func.avg(PromptVersion.mean_judge_score), 2)).scalar() or 0.0
        return {
            "total": total,
            "avg_mention_rate": float(avg_mention_rate),
            "avg_reward": float(avg_reward),
            "avg_judge_score": float(avg_judge),
            "by_generator_type": by_type,
        }
