from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from langfuse import Langfuse

from app.core.config import get_settings


@dataclass
class TraceResult:
    trace_id: str | None = None
    generation_id: str | None = None


logger = logging.getLogger(__name__)


class LangfuseTracker:
    def __init__(self) -> None:
        settings = get_settings()
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                self.client: Langfuse | None = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                logger.info(
                    "Langfuse client initialized successfully with host: %s",
                    settings.langfuse_host,
                )
            except Exception as exc:
                logger.error("Failed to initialize Langfuse client: %s", exc)
                self.client = None
        else:
            logger.warning("Langfuse keys not provided, tracking disabled")
            self.client = None

    def track_generation(
        self,
        name: str,
        provider: str,
        model: str,
        input_payload: dict[str, Any],
        output_text: str,
        usage: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceResult:
        if not self.client:
            return TraceResult()

        try:
            usage_details = self._normalize_usage_details(usage)
            if not usage_details:
                logger.debug(
                    "Langfuse generation has empty usage_details for provider=%s model=%s",
                    provider,
                    model,
                )
            generation = self.client.start_generation(
                name=f"{name}:{provider}:{model}",
                model=model,
                input=input_payload,
                output=output_text,
                usage_details=usage_details,
                metadata=metadata or {},
            )
            generation.end()
            self.client.flush()
            return TraceResult(
                trace_id=getattr(generation, "trace_id", None),
                generation_id=getattr(generation, "id", None),
            )
        except Exception as exc:
            logger.warning("Langfuse tracking failed: %s", exc, exc_info=True)
        return TraceResult()

    def score_trace(
        self,
        trace_id: str | None,
        name: str,
        value: float,
        comment: str = "",
    ) -> None:
        if not self.client or not trace_id:
            return
        try:
            self.client.create_score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
            )
            self.client.flush()
        except Exception as exc:
            logger.warning("Langfuse score failed: %s", exc, exc_info=True)

    @staticmethod
    def _normalize_usage_details(usage: dict[str, Any] | None) -> dict[str, Any]:
        if not usage:
            return {}
        normalized = dict(usage)
        prompt_tokens = normalized.get("prompt_tokens")
        completion_tokens = normalized.get("completion_tokens")
        total_tokens = normalized.get("total_tokens")
        if prompt_tokens is not None and "input" not in normalized:
            normalized["input"] = prompt_tokens
        if completion_tokens is not None and "output" not in normalized:
            normalized["output"] = completion_tokens
        if total_tokens is not None and "total" not in normalized:
            normalized["total"] = total_tokens
        return normalized
