from __future__ import annotations

from collections.abc import Callable
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces


class PromptOptimizationEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        evaluator: Callable[[int, int], tuple[float, dict[str, Any], bool]],
        max_steps: int = 20,
    ) -> None:
        super().__init__()
        self.evaluator = evaluator
        self.max_steps = max_steps
        self.current_step = 0
        self.last_obs = np.zeros(6, dtype=np.float32)
        self.last_action: int | None = None
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(6,), dtype=np.float32)

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
        super().reset(seed=seed)
        self.current_step = 0
        self.last_obs = np.zeros(6, dtype=np.float32)
        return self.last_obs, {}

    def step(self, action: int):
        self.last_action = int(action)
        reward, metrics, forced_done = self.evaluator(action, self.current_step)
        self.current_step += 1

        mention = float(metrics.get("mention_rate", 0.0))
        natural = float(metrics.get("naturalness_score", 0.0))
        context = float(metrics.get("context_match_score", 0.0))
        recommendation = float(metrics.get("recommendation_score", 0.0))
        progress = min(1.0, self.current_step / max(self.max_steps, 1))
        self.last_obs = np.array(
            [progress, float(reward), mention, natural, context, recommendation],
            dtype=np.float32,
        )

        terminated = forced_done or self.current_step >= self.max_steps
        truncated = False
        info = {"metrics": metrics, "action": self.last_action}
        return self.last_obs, float(reward), terminated, truncated, info
