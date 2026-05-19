from __future__ import annotations

import logging
from typing import Any

from langfuse import Langfuse

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LangfuseService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client: Langfuse | None = None
        
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                self.client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
                logger.info("Langfuse service initialized successfully")
            except Exception as exc:
                logger.error(f"Failed to initialize Langfuse client: {exc}")
        else:
            logger.warning("Langfuse credentials not configured")

    def get_stats(self) -> dict[str, Any]:
        """获取 Langfuse 统计数据"""
        if not self.client:
            return {
                "totalTraces": 0,
                "avgScore": 0,
                "avgLatency": 0,
                "totalTokens": 0
            }
        
        try:
            from langfuse.api.resources.commons.types.traces_with_scores import TracesWithScores
            
            traces_response = self.client.client.trace.list(limit=100)
            
            total_traces = len(traces_response.data) if traces_response.data else 0
            total_score = 0
            score_count = 0
            total_latency = 0
            latency_count = 0
            total_tokens = 0
            
            for trace in traces_response.data:
                if hasattr(trace, 'scores') and trace.scores:
                    for score in trace.scores:
                        if hasattr(score, 'value'):
                            total_score += float(score.value)
                            score_count += 1
                
                if hasattr(trace, 'latency') and trace.latency is not None:
                    total_latency += float(trace.latency)
                    latency_count += 1
                
                if hasattr(trace, 'usage') and trace.usage:
                    if isinstance(trace.usage, dict):
                        total_tokens += trace.usage.get('total_tokens', 0) or 0
                    elif hasattr(trace.usage, 'total_tokens'):
                        total_tokens += trace.usage.total_tokens or 0
            
            avg_score = round(total_score / score_count, 2) if score_count > 0 else 0
            avg_latency = round(total_latency / latency_count, 2) if latency_count > 0 else 0
            
            return {
                "totalTraces": total_traces,
                "avgScore": avg_score,
                "avgLatency": avg_latency,
                "totalTokens": total_tokens
            }
        except Exception as e:
            logger.error(f"Error fetching Langfuse stats: {e}", exc_info=True)
            return {
                "totalTraces": 0,
                "avgScore": 0,
                "avgLatency": 0,
                "totalTokens": 0,
                "error": str(e)
            }

    def get_traces(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取最近的追踪记录"""
        if not self.client:
            return []
        
        try:
            traces_response = self.client.client.trace.list(limit=limit)
            
            result = []
            for trace in traces_response.data:
                trace_data = {
                    "id": trace.id,
                    "name": trace.name or "N/A",
                    "score": 0,
                    "latency": 0,
                    "createdAt": trace.timestamp.isoformat() if hasattr(trace, 'timestamp') and trace.timestamp else None
                }
                
                if hasattr(trace, 'scores') and trace.scores:
                    for score in trace.scores:
                        if hasattr(score, 'value'):
                            trace_data["score"] = round(float(score.value), 2)
                            break
                
                if hasattr(trace, 'latency') and trace.latency is not None:
                    trace_data["latency"] = float(trace.latency)
                
                result.append(trace_data)
            
            return result
        except Exception as e:
            logger.error(f"Error fetching Langfuse traces: {e}", exc_info=True)
            return []