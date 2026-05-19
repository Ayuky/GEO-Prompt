from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.experiment import Experiment, PromptVersion
from app.models.training import TrainingRun
from app.schemas.experiment import ExperimentRunRequest
from app.schemas.training import TrainingStartRequest
from app.services.experiment_service import ExperimentService
from app.services.model_gateway import ModelGateway
from app.services.prompt_generator import PromptGenerator
from app.services.prompt_judge import PromptJudge
import threading

from app.services.reward import RewardService

# ---------------------------------------------------------------
# Pause/Resume infrastructure
# ---------------------------------------------------------------
_train_pause_events: dict[int, threading.Event] = {}
_train_lock = threading.Lock()


def _get_train_pause_event(training_run_id: int) -> threading.Event:
    with _train_lock:
        event = _train_pause_events.get(training_run_id)
        if event is None:
            event = threading.Event()
            event.set()  # "set" = running (not paused)
            _train_pause_events[training_run_id] = event
        return event


def _remove_train_pause_event(training_run_id: int) -> None:
    with _train_lock:
        _train_pause_events.pop(training_run_id, None)


class TrainingService:
    def __init__(
        self,
        model_gateway: ModelGateway,
        prompt_generator: PromptGenerator,
        reward_service: RewardService,
        prompt_judge: PromptJudge,
    ) -> None:
        self.model_gateway = model_gateway
        self.prompt_generator = prompt_generator
        self.reward_service = reward_service
        self.prompt_judge = prompt_judge

    def create_run(self, payload: TrainingStartRequest) -> TrainingRun:
        with SessionLocal() as db:
            experiment = db.get(Experiment, payload.experiment_id)
            if not experiment:
                raise ValueError(f"未找到实验: {payload.experiment_id}")

            run = TrainingRun(
                experiment_id=payload.experiment_id,
                algorithm=payload.algorithm,
                status="queued",
                total_timesteps=payload.total_timesteps,
                current_timestep=0,
                best_reward=0.0,
                hyper_params={**payload.hyper_params, "enable_llm_scorer": payload.enable_llm_scorer},
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run

    def pause_training(self, training_run_id: int) -> dict[str, Any]:
        with SessionLocal() as db:
            run = db.get(TrainingRun, training_run_id)
            if not run:
                raise ValueError(f"Training run not found: {training_run_id}")
            if run.status != "running":
                raise ValueError(f"Training run is not running (status={run.status})")
            run.status = "paused"
            db.commit()
            current_timestep = run.current_timestep
        event = _get_train_pause_event(training_run_id)
        event.clear()
        return {"training_run_id": training_run_id, "status": "paused", "current_timestep": current_timestep}

    def resume_training(self, training_run_id: int) -> dict[str, Any]:
        with SessionLocal() as db:
            run = db.get(TrainingRun, training_run_id)
            if not run:
                raise ValueError(f"Training run not found: {training_run_id}")
            if run.status != "paused":
                raise ValueError(f"Training run is not paused (status={run.status})")
            run.status = "running"
            db.commit()
            current_timestep = run.current_timestep
        event = _get_train_pause_event(training_run_id)
        event.set()
        return {"training_run_id": training_run_id, "status": "running", "current_timestep": current_timestep}

    def execute_run(self, training_run_id: int, questions: list[str]) -> None:
        _get_train_pause_event(training_run_id)  # ensure event exists in "running" state
        try:
            self._do_execute_run(training_run_id, questions)
        finally:
            _remove_train_pause_event(training_run_id)

    def _do_execute_run(self, training_run_id: int, questions: list[str]) -> None:
        with SessionLocal() as db:
            run = db.get(TrainingRun, training_run_id)
            if not run:
                return
            experiment = db.get(Experiment, run.experiment_id)
            if not experiment:
                run.status = "failed"
                run.hyper_params = {**run.hyper_params, "error": "Experiment not found"}
                db.commit()
                return
            if experiment.max_rounds < experiment.current_round + run.total_timesteps:
                experiment.max_rounds = experiment.current_round + run.total_timesteps
            run.status = "running"
            llm_scorer_enabled = run.hyper_params.get("enable_llm_scorer", True) if run.hyper_params else True
            db.commit()

        action_mode_map = {0: "random", 1: "template_mutation", 2: "policy"}
        # 通过evaluator包装单轮实验
        def evaluator(action: int, _step_idx: int):
            pause_event = _get_train_pause_event(training_run_id)
            pause_event.wait()
            with SessionLocal() as local_db:
                service = ExperimentService(
                    db=local_db,
                    model_gateway=self.model_gateway,
                    prompt_generator=self.prompt_generator,
                    reward_service=self.reward_service,
                    prompt_judge=self.prompt_judge,
                )
                run_obj = local_db.get(TrainingRun, training_run_id)
                if not run_obj:
                    return 0.0, {}, True
                experiment_obj = local_db.get(Experiment, run_obj.experiment_id)
                if not experiment_obj:
                    return 0.0, {}, True

                source_prompt = self._latest_prompt(local_db, experiment_obj.id)
                #action由RL算法决定 (0=random, 1=mutation, 2=policy)
                mode = action_mode_map.get(action, "random")
                payload = ExperimentRunRequest(
                    questions=questions,
                    generator_mode=mode,
                    source_prompt=source_prompt,
                    extra_metadata={"trigger": "rl-training", "training_run_id": training_run_id},
                    enable_llm_scorer=llm_scorer_enabled,
                )
                try:
                    # 调用单轮实验
                    result = service.run_round(experiment_obj.id, payload)
                except ValueError:
                    return 0.0, {}, True

                rounds = result.get("rounds", [])
                if rounds:
                    metrics = rounds[0].get("metrics", {})
                    mean_reward = float(rounds[0].get("mean_reward", 0.0))
                else:
                    metrics = {}
                    mean_reward = 0.0
                return mean_reward, metrics, False

        with SessionLocal() as db:
            run = db.get(TrainingRun, training_run_id)
            if not run:
                return
            total_steps = run.total_timesteps
            algorithm = run.algorithm.lower()
            hyper_params = run.hyper_params or {}

        try:
            from stable_baselines3 import DQN, PPO

            from app.rl.callbacks import TrainingProgressCallback
            from app.rl.env import PromptOptimizationEnv
        except Exception as exc:
            with SessionLocal() as db:
                run = db.get(TrainingRun, training_run_id)
                if run:
                    run.status = "failed"
                    run.hyper_params = {**(run.hyper_params or {}), "error": str(exc)}
                    db.commit()
            return
        # 交给Stable Baselines3训练
        env = PromptOptimizationEnv(evaluator=evaluator, max_steps=total_steps)
        callback = TrainingProgressCallback(
            training_run_id=training_run_id,
            algorithm=algorithm,
            log_every=int(hyper_params.get("log_every", 20)),
        )

        try:
            if algorithm == "ppo":
                model = PPO(
                    policy="MlpPolicy",
                    env=env,
                    #ppo超参数
                    verbose=0,
                    n_steps=int(hyper_params.get("n_steps", 64)),
                    batch_size=int(hyper_params.get("batch_size", 64)),
                    learning_rate=float(hyper_params.get("learning_rate", 3e-4)),
                    gamma=float(hyper_params.get("gamma", 0.99)),
                )
            elif algorithm == "dqn":
                model = DQN(
                    policy="MlpPolicy",
                    env=env,
                    #dqn超参数
                    verbose=0,
                    learning_starts=int(hyper_params.get("learning_starts", 64)),
                    buffer_size=int(hyper_params.get("buffer_size", 5000)),
                    batch_size=int(hyper_params.get("batch_size", 32)),
                    learning_rate=float(hyper_params.get("learning_rate", 1e-4)),
                    gamma=float(hyper_params.get("gamma", 0.99)),
                )
            else:
                raise ValueError(f"不支持算法: {algorithm}")

            model.learn(total_timesteps=total_steps, callback=callback)
            model_path = Path("runs") / f"training_{training_run_id}_{algorithm}"
            model.save(str(model_path))

            with SessionLocal() as db:
                run = db.get(TrainingRun, training_run_id)
                if run:
                    run.status = "finished"
                    run.current_timestep = total_steps
                    run.model_path = f"{model_path}.zip"
                    run.best_reward = max(run.best_reward, callback.best_reward)
                    db.commit()
        except Exception as exc:
            with SessionLocal() as db:
                run = db.get(TrainingRun, training_run_id)
                if run:
                    run.status = "failed"
                    run.hyper_params = {**(run.hyper_params or {}), "error": str(exc)}
                    db.commit()
        finally:
            env.close()

    @staticmethod
    def _latest_prompt(db, experiment_id: int) -> str | None:
        stmt = (
            select(PromptVersion.prompt_text)
            .where(PromptVersion.experiment_id == experiment_id)
            .order_by(PromptVersion.id.desc())
            .limit(1)
        )
        return db.scalar(stmt)
