from __future__ import annotations

from typing import Any

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

from app.core.database import SessionLocal
from app.models.training import TrainingMetric, TrainingRun


class TrainingProgressCallback(BaseCallback):
    def __init__(self, training_run_id: int, algorithm: str = "ppo", log_every: int = 20, verbose: int = 0):
        super().__init__(verbose)
        self.training_run_id = training_run_id
        self.algorithm = algorithm.lower()
        self.log_every = log_every
        self.best_reward = 0.0
        self._last_logged = -1

    def _on_step(self) -> bool:
        timestep = int(self.model.num_timesteps)
        rewards = self.locals.get("rewards")
        reward = self._extract_reward(rewards)
        self.best_reward = max(self.best_reward, reward)

        action = self._extract_action(self.locals.get("infos"))

        if timestep <= self._last_logged or timestep % self.log_every != 0:
            return True

        self._last_logged = timestep

        name_to_value = self.model.logger.name_to_value
        if self.algorithm == "dqn":
            entropy_loss = 0.0
            value_loss = 0.0
            policy_loss = self._safe_float(name_to_value.get("train/loss"))
        else:
            entropy_loss = self._safe_float(name_to_value.get("train/entropy_loss"))
            value_loss = self._safe_float(name_to_value.get("train/value_loss"))
            policy_loss = self._safe_float(name_to_value.get("train/policy_gradient_loss"))

        with SessionLocal() as db:
            run = db.get(TrainingRun, self.training_run_id)
            if not run:
                return False
            run.current_timestep = timestep
            run.best_reward = max(run.best_reward, self.best_reward)
            metric = TrainingMetric(
                training_run_id=self.training_run_id,
                timestep=timestep,
                reward=reward,
                entropy_loss=entropy_loss,
                value_loss=value_loss,
                policy_loss=policy_loss,
                metrics_json={
                    "reward": reward,
                    "entropy_loss": entropy_loss,
                    "value_loss": value_loss,
                    "policy_loss": policy_loss,
                    "action": action,
                },
            )
            db.add(metric)
            db.commit()
        return True

    @staticmethod
    def _extract_action(raw: Any) -> int | None:
        if raw is None:
            return None
        if isinstance(raw, (list, tuple)):
            for item in raw:
                a = TrainingProgressCallback._extract_single_action(item)
                if a is not None:
                    return a
            return None
        return TrainingProgressCallback._extract_single_action(raw)

    @staticmethod
    def _extract_single_action(item: Any) -> int | None:
        if isinstance(item, dict):
            a = item.get("action")
            if a is not None:
                return int(a)
        if isinstance(item, np.ndarray):
            return int(item.flatten()[0]) if item.size else None
        try:
            return int(item)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_reward(raw: Any) -> float:
        if raw is None:
            return 0.0
        if isinstance(raw, (list, tuple)):
            return float(raw[0]) if raw else 0.0
        if isinstance(raw, np.ndarray):
            return float(raw.flatten()[0]) if raw.size else 0.0
        try:
            import torch
            if isinstance(raw, torch.Tensor):
                return float(raw.detach().cpu().flatten()[0]) if raw.numel() else 0.0
        except ImportError:
            pass
        return float(raw)

    @staticmethod
    def _safe_float(value: Any) -> float:
        if value is None:
            return 0.0
        try:
            import torch
            if isinstance(value, torch.Tensor):
                return float(value.detach().cpu().item()) if value.numel() else 0.0
        except ImportError:
            pass
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
