from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Any

from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError

from app.core.config import Settings, get_settings
from app.core.crypto import decrypt
from app.core.langfuse_client import LangfuseTracker, TraceResult

logger = logging.getLogger(__name__)

@dataclass
class ModelResponse:
    text: str
    usage: dict[str, Any]
    model_id: int
    model_name: str
    latency_ms: int
    trace_id: str | None = None


class ModelGateway:
    def __init__(self, settings: Settings | None = None, tracker: LangfuseTracker | None = None) -> None:
        self.settings = settings or get_settings()
        self.tracker = tracker or LangfuseTracker()
        self._clients: dict[str, OpenAI] = {}
        self._model_cache: dict[int, dict[str, str]] = {}
        self._cache_loaded = False

    def _load_cache(self) -> None:
        if self._cache_loaded:
            return
        from app.core.database import SessionLocal
        from app.models.custom_model import CustomModel

        with SessionLocal() as db:
            models = db.query(CustomModel).filter(CustomModel.is_active == True).all()
            self._model_cache = {}
            for m in models:
                self._model_cache[m.id] = {
                    "name": m.name,
                    "base_url": m.base_url,
                    "model_name": m.model_name,
                    "api_key": decrypt(m.encrypted_api_key),
                }
        self._cache_loaded = True

    def refresh_cache(self) -> None:
        self._cache_loaded = False
        self._clients.clear()
        self._load_cache()

    def call(
        self,
        model_id: int,
        system_prompt: str,
        user_prompt: str,
        metadata: dict[str, Any] | None = None,
        temperature: float | None = None,
        response_format: dict[str, str] | None = None,
    ) -> ModelResponse:
        self._load_cache()
        if model_id not in self._model_cache:
            raise ValueError(f"模型未响应或失效: {model_id}")

        cfg = self._model_cache[model_id]
        started = time.perf_counter()

        client = self._get_client(model_id, cfg["base_url"], cfg["api_key"])

        kwargs: dict[str, Any] = {
            "model": cfg["model_name"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature if temperature is not None else 0.6,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        max_attempts = 3
        last_exception = None
        response = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = client.chat.completions.create(**kwargs)
                break
            except (APIConnectionError, APITimeoutError) as e:
                last_exception = e
                if attempt < max_attempts:
                    wait_time = min(2 ** attempt, 10)
                    logger.warning(
                        "Model %d call failed (attempt %d/%d): %s. Retrying in %ds...",
                        model_id, attempt, max_attempts, str(e), wait_time
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "Model %d call failed after %d attempts: %s",
                        model_id, max_attempts, str(e)
                    )
                    raise
            except RateLimitError as e:
                last_exception = e
                if attempt < max_attempts:
                    wait_time = min(2 ** attempt * 5, 30)
                    logger.warning(
                        "Model %d rate limited (attempt %d/%d). Retrying in %ds...",
                        model_id, attempt, max_attempts, wait_time
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "Model %d rate limited after %d attempts: %s",
                        model_id, max_attempts, str(e)
                    )
                    raise

        text, usage = self._parse_response(response)
        latency_ms = int((time.perf_counter() - started) * 1000)

        payload = {
            "model_id": model_id,
            "model_name": cfg["model_name"],
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "metadata": metadata or {},
        }
        trace: TraceResult = self.tracker.track_generation(
            name="geo-prompt-model-call",
            provider=cfg["name"],
            model=cfg["model_name"],
            input_payload=payload,
            output_text=text,
            usage=usage,
            metadata=metadata,
        )

        return ModelResponse(
            text=text,
            usage=usage,
            model_id=model_id,
            model_name=cfg["model_name"],
            latency_ms=latency_ms,
            trace_id=trace.trace_id,
        )

    def _get_client(self, model_id: int, base_url: str, api_key: str) -> OpenAI:
        cache_key = f"{model_id}:{base_url}"
        if cache_key not in self._clients:
            self._clients[cache_key] = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self.settings.llm_call_timeout,
                max_retries=3,
            )
        return self._clients[cache_key]

    @staticmethod
    def _parse_response(response: Any) -> tuple[str, dict[str, Any]]:
        text = ""
        usage = {}
        if isinstance(response, str):
            text = response
        elif hasattr(response, "choices") and response.choices:
            text = response.choices[0].message.content or ""
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
        elif isinstance(response, dict) and "choices" in response:
            text = response["choices"][0]["message"]["content"] or ""
        else:
            text = str(response)
        return text, usage
