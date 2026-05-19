from __future__ import annotations

import logging
import re
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import mean
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.evaluation import EvaluationRecord
from app.models.experiment import Experiment, PromptVersion
from app.schemas.experiment import ExperimentCreate, ExperimentRunRequest
from app.services.model_gateway import ModelGateway
from app.services.prompt_generator import PromptGenerator
from app.services.prompt_judge import PromptJudge
from app.services.reward import RewardService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Pause/Resume infrastructure
# ---------------------------------------------------------------
_exp_pause_events: dict[int, threading.Event] = {}
_exp_lock = threading.Lock()


def _get_pause_event(experiment_id: int) -> threading.Event:
    with _exp_lock:
        event = _exp_pause_events.get(experiment_id)
        if event is None:
            event = threading.Event()
            event.set()  # "set" = running (not paused)
            _exp_pause_events[experiment_id] = event
        return event


def _remove_pause_event(experiment_id: int) -> None:
    with _exp_lock:
        _exp_pause_events.pop(experiment_id, None)


class ExperimentService:
    def __init__(
        self,
        db: Session,
        model_gateway: ModelGateway,
        prompt_generator: PromptGenerator,
        reward_service: RewardService,
        prompt_judge: PromptJudge,
    ) -> None:
        self.db = db
        self.model_gateway = model_gateway
        self.prompt_generator = prompt_generator
        self.reward_service = reward_service
        self.prompt_judge = prompt_judge

    def create_experiment(self, payload: ExperimentCreate) -> Experiment:
        experiment = Experiment(
            name=payload.name,
            domain=payload.domain,
            description=payload.description,
            status="created",
            model_id=payload.model_id,
            judge_model_id=payload.judge_model_id,
            target_entities=payload.target_entities,
            context_text=payload.context_text,
            max_rounds=payload.max_rounds,
        )
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment, attribute_names=["model", "judge_model"])
        return experiment

    def get_experiment(self, experiment_id: int) -> Experiment | None:
        return self.db.get(
            Experiment, experiment_id,
            options=[joinedload(Experiment.model), joinedload(Experiment.judge_model)],
        )

    def list_experiments(
        self,
        skip: int = 0,
        limit: int = 20,
        name: str | None = None,
        model_id: int | None = None,
        status: str | None = None,
    ) -> list[Experiment]:
        stmt = select(Experiment)

        if name:
            stmt = stmt.where(Experiment.name.like(f"%{name}%"))
        if model_id:
            stmt = stmt.where(Experiment.model_id == model_id)
        if status:
            stmt = stmt.where(Experiment.status == status)

        stmt = stmt.order_by(Experiment.id.desc()).offset(skip).limit(limit)
        stmt = stmt.options(joinedload(Experiment.model), joinedload(Experiment.judge_model))
        return list(self.db.scalars(stmt).all())

    def count_experiments(
        self,
        name: str | None = None,
        model_id: int | None = None,
        status: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Experiment)
        if name:
            stmt = stmt.where(Experiment.name.like(f"%{name}%"))
        if model_id:
            stmt = stmt.where(Experiment.model_id == model_id)
        if status:
            stmt = stmt.where(Experiment.status == status)
        return self.db.scalar(stmt) or 0

    def delete_experiment(self, experiment_id: int) -> None:
        experiment = self.db.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        self.db.delete(experiment)
        self.db.commit()

    def pause_experiment(self, experiment_id: int) -> dict[str, Any]:
        experiment = self.db.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        if experiment.status != "running":
            raise ValueError(f"Experiment is not running (status={experiment.status})")
        experiment.status = "paused"
        self.db.commit()
        event = _get_pause_event(experiment_id)
        event.clear()
        return {"experiment_id": experiment_id, "status": "paused", "current_round": experiment.current_round}

    def resume_experiment(self, experiment_id: int) -> dict[str, Any]:
        experiment = self.db.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        if experiment.status != "paused":
            raise ValueError(f"Experiment is not paused (status={experiment.status})")
        experiment.status = "running"
        self.db.commit()
        event = _get_pause_event(experiment_id)
        event.set()
        return {"experiment_id": experiment_id, "status": "running", "current_round": experiment.current_round}

    def run_round_async(self, experiment_id: int, payload: ExperimentRunRequest) -> dict[str, Any]:
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        if experiment.status == "running":
            raise ValueError("Experiment is already running, please wait for it to finish")
        if experiment.current_round >= experiment.max_rounds:
            experiment.status = "finished"
            self.db.commit()
            raise ValueError("Experiment reaches max rounds")

        # Pre-validate that both models are loaded and active
        self.model_gateway._load_cache()
        gateway_cache = getattr(self.model_gateway, "_model_cache", {})
        if experiment.model_id not in gateway_cache:
            raise ValueError(
                f"Generation model (id={experiment.model_id}) not found or inactive. "
                "Please check the model configuration."
            )
        if experiment.judge_model_id not in gateway_cache:
            raise ValueError(
                f"Judge model (id={experiment.judge_model_id}) not found or inactive. "
                "Please check the model configuration."
            )

        remaining = experiment.max_rounds - experiment.current_round
        actual_rounds = min(payload.num_rounds, remaining)
        if actual_rounds <= 0:
            raise ValueError("Experiment reaches max rounds")

        experiment.status = "running"
        self.db.commit()

        threading.Thread(
            target=_execute_rounds_bg,
            args=(experiment_id, payload),
            daemon=True,
        ).start()

        return {
            "experiment_id": experiment_id,
            "accepted": True,
            "message": f"已接受 {actual_rounds} 轮任务，后台执行中",
            "current_round": experiment.current_round,
            "max_rounds": experiment.max_rounds,
            "num_rounds_requested": actual_rounds,
        }

    def run_round(self, experiment_id: int, payload: ExperimentRunRequest) -> dict[str, Any]:
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")
        if experiment.current_round >= experiment.max_rounds:
            experiment.status = "finished"
            self.db.commit()
            raise ValueError("Experiment reaches max rounds")

        # Pre-validate that both models are loaded and active
        self.model_gateway._load_cache()
        gateway_cache = getattr(self.model_gateway, "_model_cache", {})
        if experiment.model_id not in gateway_cache:
            raise ValueError(
                f"Generation model (id={experiment.model_id}) not found or inactive. "
                "Please check the model configuration."
            )
        if experiment.judge_model_id not in gateway_cache:
            raise ValueError(
                f"Judge model (id={experiment.judge_model_id}) not found or inactive. "
                "Please check the model configuration."
            )

        remaining = experiment.max_rounds - experiment.current_round
        num_rounds = min(payload.num_rounds, remaining)
        if num_rounds <= 0:
            raise ValueError("Experiment reaches max rounds")

        manual_prompts: list[str] = []
        if payload.manual_prompt:
            manual_prompts = [p.strip() for p in re.split(r'\n---\r?\n|\r\n---\n?', payload.manual_prompt) if p.strip()]

        rounds_results: list[dict[str, Any]] = []

        for round_seq in range(1, num_rounds + 1):
            pause_event = _get_pause_event(experiment_id)
            pause_event.wait()
            self.db.refresh(experiment)
            if experiment.status == "failed":
                break

            round_manual_prompt: str | None = None
            if manual_prompts:
                idx = (round_seq - 1) % len(manual_prompts)
                round_manual_prompt = manual_prompts[idx]

            prompt_result = self._build_prompt(
                mode=payload.generator_mode,
                experiment=experiment,
                source_prompt=payload.source_prompt,
                manual_prompt=round_manual_prompt,
            )

            round_index = experiment.current_round + 1
            prompt_version = PromptVersion(
                experiment_id=experiment.id,
                round_index=round_index,
                generator_type=prompt_result.mode,
                prompt_text=prompt_result.prompt_text,
                policy_action=prompt_result.metadata.get("policy_action"),
                metadata_json={**prompt_result.metadata, **payload.extra_metadata},
            )
            self.db.add(prompt_version)
            self.db.flush()

            scores: list[float] = []
            judge_scores_all: list[float] = []
            mention_rates: list[float] = []
            naturalness_scores: list[float] = []
            context_scores: list[float] = []
            sentiment_scores: list[float] = []
            recommendation_scores: list[float] = []
            summary_items: list[dict[str, Any]] = []

            settings = get_settings()
            max_workers = min(len(payload.questions), settings.experiment_concurrency)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx: dict[Any, int] = {
                    executor.submit(
                        self._process_single_question,
                        question=q,
                        experiment=experiment,
                        system_prompt=prompt_version.prompt_text,
                        round_index=round_index,
                        prompt_version_id=prompt_version.id,
                    enable_llm_scorer=payload.enable_llm_scorer,
                    ): i
                    for i, q in enumerate(payload.questions)
                }

                results_by_idx: dict[int, dict[str, Any]] = {}
                error_count = 0
                error_messages: list[str] = []
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        results_by_idx[idx] = future.result()
                    except Exception as exc:
                        error_count += 1
                        err_msg = f"[Q{idx}] {type(exc).__name__}: {exc}"
                        error_messages.append(err_msg)
                        logger.error(
                            "Experiment %d round %d: question %d failed — %s: %s\n%s",
                            experiment_id,
                            round_index,
                            idx,
                            type(exc).__name__,
                            exc,
                            traceback.format_exc(),
                        )
                        results_by_idx[idx] = {
                            "question": payload.questions[idx],
                            "answer": "",
                            "trace_id": None,
                            "latency_ms": 0,
                            "usage": {},
                            "reward": {
                                "mention_rate": 0.0,
                                "naturalness_score": 0.0,
                                "context_match_score": 0.0,
                                "sentiment_score": 0.0,
                                "recommendation_score": 0.0,
                                "total_reward": 0.0,
                            },
                            "judge_score": {"overall": 0.0},
                            "extracted_entities": [],
                            "error": True,
                        }

            if error_count == len(payload.questions):
                logger.error(
                    "Experiment %d round %d: ALL %d questions failed. Errors: %s",
                    experiment_id,
                    round_index,
                    error_count,
                    error_messages,
                )

            for i, question in enumerate(payload.questions):
                result = results_by_idx[i]
                reward = result["reward"]
                judge_score = result["judge_score"]
                llm_judge_score = float(judge_score.get("overall", 0.0))

                self.model_gateway.tracker.score_trace(
                    trace_id=result["trace_id"],
                    name="total_reward",
                    value=float(reward["total_reward"]),
                    comment="Weighted GEO reward",
                )

                record = EvaluationRecord(
                    experiment_id=experiment.id,
                    prompt_version_id=prompt_version.id,
                    question=question,
                    answer=result["answer"],
                    mention_rate=float(reward["mention_rate"]),
                    naturalness_score=float(reward["naturalness_score"]),
                    context_match_score=float(reward["context_match_score"]),
                    sentiment_score=float(reward["sentiment_score"]),
                    recommendation_score=float(reward["recommendation_score"]),
                    llm_judge_score=llm_judge_score,
                    total_reward=float(reward["total_reward"]),
                    raw_metrics_json={"reward": reward, "judge": judge_score, "usage": result["usage"], "extracted_entities": result["extracted_entities"]},
                    trace_id=result["trace_id"],
                    latency_ms=result["latency_ms"],
                )
                self.db.add(record)
                scores.append(float(reward["total_reward"]))
                judge_scores_all.append(llm_judge_score)
                mention_rates.append(float(reward["mention_rate"]))
                naturalness_scores.append(float(reward["naturalness_score"]))
                context_scores.append(float(reward["context_match_score"]))
                sentiment_scores.append(float(reward["sentiment_score"]))
                recommendation_scores.append(float(reward["recommendation_score"]))
                summary_items.append(
                    {
                        "question": question,
                        "total_reward": float(reward["total_reward"]),
                        "mention_rate": float(reward["mention_rate"]),
                        "naturalness_score": float(reward["naturalness_score"]),
                        "context_match_score": float(reward["context_match_score"]),
                        "sentiment_score": float(reward["sentiment_score"]),
                        "recommendation_score": float(reward["recommendation_score"]),
                        "judge_score": llm_judge_score,
                    }
                )

            prompt_version.mean_reward = mean(scores) if scores else 0.0
            prompt_version.mean_judge_score = mean(judge_scores_all) if judge_scores_all else 0.0
            prompt_version.prompt_mention_rate = sum(1 for m in mention_rates if m > 0) / len(mention_rates) if mention_rates else 0.0
            experiment.current_round = round_index
            experiment.best_reward = max(experiment.best_reward, prompt_version.mean_reward)
            experiment.status = "running" if experiment.current_round < experiment.max_rounds else "finished"

            self.db.commit()
            self.db.refresh(prompt_version)
            self.db.refresh(experiment)

            rounds_results.append({
                "prompt_version_id": prompt_version.id,
                "round_index": prompt_version.round_index,
                "generator_mode": prompt_version.generator_type,
                "prompt_text": prompt_version.prompt_text,
                "mean_reward": prompt_version.mean_reward,
                "metrics": {
                    "mean_judge_score": prompt_version.mean_judge_score,
                    "mention_rate": mean(mention_rates) if mention_rates else 0.0,
                    "naturalness_score": mean(naturalness_scores) if naturalness_scores else 0.0,
                    "context_match_score": mean(context_scores) if context_scores else 0.0,
                    "sentiment_score": mean(sentiment_scores) if sentiment_scores else 0.0,
                    "recommendation_score": mean(recommendation_scores) if recommendation_scores else 0.0,
                    "per_question": summary_items,
                    "error_count": error_count,
                    "total_questions": len(payload.questions),
                },
            })

        return {
            "experiment_id": experiment.id,
            "rounds": rounds_results,
            "total_rounds_ran": len(rounds_results),
            "final_best_reward": experiment.best_reward,
            "final_status": experiment.status,
        }

    def _process_single_question(
        self,
        question: str,
        experiment: Experiment,
        system_prompt: str,
        round_index: int,
        prompt_version_id: int,
        enable_llm_scorer: bool = True,
    ) -> dict[str, Any]:
        model_resp = self.model_gateway.call(
            model_id=experiment.model_id,
            system_prompt=system_prompt,
            user_prompt=question,
            metadata={
                "experiment_id": experiment.id,
                "prompt_version_id": prompt_version_id,
                "round_index": round_index,
            },
        )
        target_entities = experiment.target_entities or []
        if enable_llm_scorer:
            judge_score = self.prompt_judge.score(
                model_id=experiment.judge_model_id,
                question=question,
                answer=model_resp.text,
                context_text=experiment.context_text,
                target_entities=target_entities,
            )
            reward = self.reward_service.evaluate(
                answer=model_resp.text,
                target_entities=target_entities,
                context_text=experiment.context_text,
                judge_scores=judge_score,
            )
        else:
            judge_score = {"naturalness": 0.0, "context_match": 0.0, "sentiment": 0.0, "recommendation": 0.0, "overall": 0.0}
            reward = self.reward_service.evaluate(
                answer=model_resp.text,
                target_entities=target_entities,
                context_text=experiment.context_text,
                judge_scores=None,
            )

        return {
            "question": question,
            "answer": model_resp.text,
            "trace_id": model_resp.trace_id,
            "latency_ms": model_resp.latency_ms,
            "usage": model_resp.usage,
            "reward": reward,
            "judge_score": judge_score,
            "extracted_entities": [e for e in target_entities if e in model_resp.text],
        }

    def list_evaluations(self, experiment_id: int, limit: int = 20) -> list[EvaluationRecord]:
        stmt: Select[tuple[EvaluationRecord]] = (
            select(EvaluationRecord)
            .where(EvaluationRecord.experiment_id == experiment_id)
            .order_by(EvaluationRecord.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_versions(self, experiment_id: int) -> list[PromptVersion]:
        stmt = (
            select(PromptVersion)
            .where(PromptVersion.experiment_id == experiment_id)
            .order_by(PromptVersion.round_index.asc())
        )
        return list(self.db.scalars(stmt).all())

    def _build_prompt(
        self,
        mode: str,
        experiment: Experiment,
        source_prompt: str | None,
        action: int | None = None,
        manual_prompt: str | None = None,
    ):
        normalized = mode.lower().strip()
        if normalized == "manual":
            prompt_text = manual_prompt or source_prompt or ""
            return self.prompt_generator.generate_manual(prompt_text)
        if normalized == "template_mutation":
            base_prompt = source_prompt or (
                "你是一名专业的GEO内容优化专家，请输出自然、专业、可信、可读的详细回答。"
                "分析目标用户的真实需求和使用场景，全面覆盖核心信息点，"
                "简洁地解释关键内容，避免堆砌冗余信息，"
                "基于事实依据给出有说服力的推荐和可执行的建议。"
            )
            return self.prompt_generator.mutate_template(base_prompt)
        if normalized == "policy":
            return self.prompt_generator.generate_by_policy(
                action=action if action is not None else 2,
                entities=experiment.target_entities,
                context_text=experiment.context_text,
                source_prompt=source_prompt,
                domain=experiment.domain,
            )
        return self.prompt_generator.generate_random(
            entities=experiment.target_entities,
            context_text=experiment.context_text,
            domain=experiment.domain,
        )


def _execute_rounds_bg(experiment_id: int, payload) -> None:
    from app.api.deps import get_model_gateway, get_prompt_generator, get_reward_service, get_prompt_judge
    from app.core.database import SessionLocal

    _get_pause_event(experiment_id)  # ensure event exists in "running" state
    db = SessionLocal()
    try:
        service = ExperimentService(
            db=db,
            model_gateway=get_model_gateway(),
            prompt_generator=get_prompt_generator(),
            reward_service=get_reward_service(),
            prompt_judge=get_prompt_judge(),
        )
        service.run_round(experiment_id=experiment_id, payload=payload)
    except Exception:
        logger.exception("Background run_round failed for experiment %d", experiment_id)
        try:
            experiment = db.get(Experiment, experiment_id)
            if experiment and experiment.status == "running":
                experiment.status = "failed"
                db.commit()
        except Exception:
            logger.exception("Failed to mark experiment %d as failed", experiment_id)
    finally:
        _remove_pause_event(experiment_id)
        db.close()
