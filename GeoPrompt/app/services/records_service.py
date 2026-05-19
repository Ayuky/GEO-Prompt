from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationRecord
from app.schemas.evaluation import EvaluationRecordCreate, EvaluationRecordUpdate


class RecordsService:
    VALID_METRICS = {
        "total_reward",
        "mention_rate",
        "naturalness_score",
        "context_match_score",
        "sentiment_score",
        "recommendation_score",
        "llm_judge_score",
    }

    def __init__(self, db: Session) -> None:
        self.db = db

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        experiment_id: int | None = None,
        prompt_version_id: int | None = None,
        keyword: str | None = None,
        total_reward_min: float | None = None,
        total_reward_max: float | None = None,
        latency_ms_min: int | None = None,
        latency_ms_max: int | None = None,
    ) -> list[EvaluationRecord]:
        stmt = select(EvaluationRecord).order_by(EvaluationRecord.id.desc())
        stmt = self._apply_filters(stmt, experiment_id, prompt_version_id, keyword, total_reward_min, total_reward_max, latency_ms_min, latency_ms_max)
        return list(self.db.scalars(stmt.offset(skip).limit(limit)).all())

    def list_with_count(
        self,
        skip: int = 0,
        limit: int = 100,
        experiment_id: int | None = None,
        prompt_version_id: int | None = None,
        keyword: str | None = None,
        total_reward_min: float | None = None,
        total_reward_max: float | None = None,
        latency_ms_min: int | None = None,
        latency_ms_max: int | None = None,
    ) -> tuple[list[EvaluationRecord], int]:
        base = select(EvaluationRecord)
        base = self._apply_filters(base, experiment_id, prompt_version_id, keyword, total_reward_min, total_reward_max, latency_ms_min, latency_ms_max)
        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(self.db.scalars(
            base.order_by(EvaluationRecord.id.desc()).offset(skip).limit(limit)
        ).all())
        return items, total

    def _apply_filters(self, stmt, experiment_id, prompt_version_id, keyword, total_reward_min, total_reward_max, latency_ms_min, latency_ms_max):
        if experiment_id is not None:
            stmt = stmt.where(EvaluationRecord.experiment_id == experiment_id)
        if prompt_version_id is not None:
            stmt = stmt.where(EvaluationRecord.prompt_version_id == prompt_version_id)
        if keyword:
            stmt = stmt.where(
                EvaluationRecord.question.contains(keyword)
                | EvaluationRecord.answer.contains(keyword)
            )
        if total_reward_min is not None:
            stmt = stmt.where(EvaluationRecord.total_reward >= total_reward_min)
        if total_reward_max is not None:
            stmt = stmt.where(EvaluationRecord.total_reward <= total_reward_max)
        if latency_ms_min is not None:
            stmt = stmt.where(EvaluationRecord.latency_ms >= latency_ms_min)
        if latency_ms_max is not None:
            stmt = stmt.where(EvaluationRecord.latency_ms <= latency_ms_max)
        return stmt

    def get(self, record_id: int) -> EvaluationRecord | None:
        return self.db.get(EvaluationRecord, record_id)

    def create(self, payload: EvaluationRecordCreate) -> EvaluationRecord:
        record = EvaluationRecord(**payload.model_dump())
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update(self, record_id: int, payload: EvaluationRecordUpdate) -> EvaluationRecord:
        record = self.db.get(EvaluationRecord, record_id)
        if not record:
            raise ValueError(f"Evaluation record not found: {record_id}")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def delete(self, record_id: int) -> None:
        record = self.db.get(EvaluationRecord, record_id)
        if not record:
            raise ValueError(f"Evaluation record not found: {record_id}")
        self.db.delete(record)
        self.db.commit()

    def summary(self) -> dict:
        total = self.db.query(func.count(EvaluationRecord.id)).scalar() or 0
        avg_reward = self.db.query(func.avg(EvaluationRecord.total_reward)).scalar() or 0.0
        avg_latency = self.db.query(func.avg(EvaluationRecord.latency_ms)).scalar() or 0.0
        latest = self.db.scalar(
            select(EvaluationRecord.created_at).order_by(EvaluationRecord.created_at.desc()).limit(1)
        )
        return {
            "totalCount": total,
            "avgTotalReward": round(float(avg_reward), 4),
            "avgLatencyMs": round(float(avg_latency)) if avg_latency else 0,
            "latestRecordAt": latest.isoformat() if latest else None,
        }

    def stats(self, stat_type: str | None = None, experiment_id: int | None = None, metric: str | None = None) -> dict | list:
        if stat_type == "byScores":
            return self._score_distribution()
        elif stat_type == "byExperiment":
            return self._by_experiment()
        elif stat_type == "byTimeline":
            return self._by_timeline()
        elif stat_type == "byScoreRadar":
            return self._score_radar()
        elif stat_type == "byPromptTrend":
            if experiment_id is None:
                raise ValueError("experiment_id is required for byPromptTrend")
            if metric is None or metric not in self.VALID_METRICS:
                raise ValueError(f"Invalid or missing metric: {metric}")
            return self._by_prompt_trend(experiment_id, metric)
        return self.summary()

    def _score_distribution(self) -> list[dict]:
        records = self.db.scalars(
            select(EvaluationRecord).order_by(EvaluationRecord.id.desc()).limit(500)
        ).all()
        buckets = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
        for r in records:
            s = r.total_reward
            if s < 2:
                buckets["0-2"] += 1
            elif s < 4:
                buckets["2-4"] += 1
            elif s < 6:
                buckets["4-6"] += 1
            elif s < 8:
                buckets["6-8"] += 1
            else:
                buckets["8-10"] += 1
        return [{"name": k, "value": v} for k, v in buckets.items()]

    def _by_experiment(self) -> list[dict]:
        rows = (
            self.db.query(
                EvaluationRecord.experiment_id,
                func.count(EvaluationRecord.id).label("cnt"),
                func.avg(EvaluationRecord.total_reward).label("avg_r"),
            )
            .group_by(EvaluationRecord.experiment_id)
            .order_by(EvaluationRecord.experiment_id)
            .all()
        )
        return [
            {"name": f"实验 {row.experiment_id}", "value": row.cnt, "avg_reward": round(float(row.avg_r), 4), "experiment_id": row.experiment_id}
            for row in rows
        ]

    def _by_prompt_trend(self, experiment_id: int, metric: str) -> list[dict]:
        col = getattr(EvaluationRecord, metric)
        rows = (
            self.db.query(
                EvaluationRecord.prompt_version_id,
                func.avg(col).label("avg_val"),
                func.count(EvaluationRecord.id).label("cnt"),
            )
            .filter(EvaluationRecord.experiment_id == experiment_id)
            .group_by(EvaluationRecord.prompt_version_id)
            .order_by(EvaluationRecord.prompt_version_id)
            .all()
        )
        return [
            {
                "name": f"{row.prompt_version_id}",
                "value": round(float(row.avg_val or 0), 4),
                "count": row.cnt,
            }
            for row in rows
        ]

    def _by_timeline(self) -> list[dict]:
        records = self.db.scalars(
            select(EvaluationRecord).order_by(EvaluationRecord.created_at.asc()).limit(500)
        ).all()
        return [
            {
                "name": r.created_at.strftime("%m-%d %H:%M") if r.created_at else "",
                "value": r.total_reward,
            }
            for r in records
        ]

    def _score_radar(self) -> list[dict]:
        avgs = self.db.query(
            func.avg(EvaluationRecord.mention_rate).label("mention"),
            func.avg(EvaluationRecord.naturalness_score).label("naturalness"),
            func.avg(EvaluationRecord.context_match_score).label("context_match"),
            func.avg(EvaluationRecord.sentiment_score).label("sentiment"),
            func.avg(EvaluationRecord.recommendation_score).label("recommendation"),
        ).first()
        if not avgs:
            return []
        return [
            {"name": "提及率", "value": round(float(avgs.mention or 0), 4)},
            {"name": "自然度", "value": round(float(avgs.naturalness or 0), 4)},
            {"name": "上下文匹配", "value": round(float(avgs.context_match or 0), 4)},
            {"name": "情感", "value": round(float(avgs.sentiment or 0), 4)},
            {"name": "推荐度", "value": round(float(avgs.recommendation or 0), 4)},
        ]
