from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.services.model_gateway import ModelGateway

logger = logging.getLogger(__name__)


class PromptJudge:
    def __init__(self, model_gateway: ModelGateway) -> None:
        self.model_gateway = model_gateway

    def score(
        self,
        model_id: int,
        question: str,
        answer: str,
        context_text: str | None,
        target_entities: list[str],
    ) -> dict[str, Any]:
        system_prompt = (
            "你是一个严格的回答质量评分器。请根据以下标准对回答进行评分，"
            "所有分数只允许 0, 2, 4, 6, 8, 10 六个整数档位。\n\n"
            "评分标准：\n"
            "- naturalness（自然度）：语言是否流畅自然，无堆砌关键词、无机械感。10=完全自然，0=完全机械\n"
            "- context_match（上下文匹配）：回答是否紧扣上下文和问题。10=完美匹配，0=完全无关\n"
            "- sentiment（情感倾向）：回答对目标实体的情感是否正面积极。10=非常正面，0=负面或中立\n"
            "- recommendation（推荐力度）：回答是否明确给出推荐/建议。10=强烈推荐，0=无推荐\n"
            "- overall（综合质量）：整体回答质量。10=优秀，0=极差\n\n"
            "你必须严格只输出一个JSON对象，不要包含任何其他文字、解释或markdown标记。"
        )
        user_prompt = (
            f"问题：{question}\n"
            f"目标实体：{', '.join(target_entities) if target_entities else '无'}\n"
            f"上下文：{context_text or '无'}\n"
            f"回答：{answer}\n\n"
            "请评分。输出示例：\n"
            '{"naturalness": 8, "context_match": 6, "sentiment": 6, "recommendation": 4, "overall": 6}'
        )
        resp = None
        try:
            resp = self.model_gateway.call(
                model_id=model_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                metadata={"type": "prompt-judge"},
                temperature=0.0,
                response_format={"type": "json_object"},
            )
        except Exception:
            logger.warning(
                "LLM评分器调用模型失败： %d",
                model_id,
                exc_info=True,
            )
            return {
                "naturalness": 0.0,
                "context_match": 0.0,
                "sentiment": 0.0,
                "recommendation": 0.0,
                "overall": 0.0,
                "trace_id": None,
            }

        try:
            parsed = self._extract_json(resp.text)
            result = {
                "naturalness": float(parsed.get("naturalness", 0.0)),
                "context_match": float(parsed.get("context_match", 0.0)),
                "sentiment": float(parsed.get("sentiment", 0.0)),
                "recommendation": float(parsed.get("recommendation", 0.0)),
                "overall": float(parsed.get("overall", 0.0)),
                "trace_id": resp.trace_id,
            }
            logger.debug("Judge scores: %s", result)
            return result
        except Exception:
            logger.warning(
                "LLM评分器解析模型响应失败： %d. 原始响应: %s",
                model_id,
                resp.text,
                exc_info=True,
            )
            return {
                "naturalness": 0.0,
                "context_match": 0.0,
                "sentiment": 0.0,
                "recommendation": 0.0,
                "overall": 0.0,
                "trace_id": resp.trace_id,
            }

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                raise
            return json.loads(match.group(0))
