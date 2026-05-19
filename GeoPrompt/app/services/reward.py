from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any



@dataclass
class RewardWeights:
    mention_rate: float = 0.5
    naturalness: float = 0.10
    context_match: float = 0.15
    sentiment: float = 0.10
    recommendation: float = 0.15


class RewardService:
    def __init__(self, weights: RewardWeights | None = None) -> None:
        self.weights = weights or RewardWeights()
        self.positive_words = {
            "推荐", "适合", "优秀", "可靠", "平衡", "出色", "值得", "优质", "满意", "好评",
            "最佳", "首选", "极佳", "卓越", "完美",
        }
        self.negative_words = {
            "避免", "不要", "较差", "劣质", "风险", "缺点", "不足", "遗憾", "失败",
            "糟糕", "不推荐", "不理想", "失望", "缺陷",
        }
        self.recommend_patterns = [
            r"推荐", r"建议", r"更适合", r"优先考虑", r"更好",
            r"更优秀", r"更可靠", r"更平衡", r"更出色", r"更值得",
            r"更优质", r"更满意", r"首选", r"值得购买", r"不容错过",
        ]

        # 惩罚系数
        self.penalty_no_mention = 2.5     # 未提及任何目标实体
        self.penalty_too_short = 1.5     # 回答过短（< 30 字）
        self.penalty_stuffing = 2.0      # 明显关键词堆砌
        self.penalty_negative = 1.5      # 负面词占优

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def evaluate(
        self,
        answer: str,
        target_entities: list[str],
        context_text: str | None,
        judge_scores: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        # 1. 各维度原始分（0–10）
        mention_raw = self._mention_rate(answer, target_entities)
        natural_raw = self._naturalness(answer)
        context_raw = self._context_match(answer, context_text)
        sentiment_raw = self._sentiment_score(answer)
        recommendation_raw = self._recommendation_score(answer)

        # 2. LLM 评判融合（如果有）
        if judge_scores:
            natural_raw = self._mean_score(natural_raw, judge_scores.get("naturalness", natural_raw))
            context_raw = self._mean_score(context_raw, judge_scores.get("context_match", context_raw))
            sentiment_raw = self._mean_score(sentiment_raw, judge_scores.get("sentiment", sentiment_raw))
            recommendation_raw = self._mean_score(
                recommendation_raw, judge_scores.get("recommendation", recommendation_raw),
            )

        # 3. 加权总分（直接使用连续原始分，不离散化，给 RL 更细粒度的梯度信号）
        weighted = (
            mention_raw * self.weights.mention_rate
            + natural_raw * self.weights.naturalness
            + context_raw * self.weights.context_match
            + sentiment_raw * self.weights.sentiment
            + recommendation_raw * self.weights.recommendation
        )

        # 4. 惩罚项
        penalty, penalty_reasons = self._calculate_penalty(answer, target_entities)
        total_reward = max(0.0, weighted - penalty)

        return {
            "mention_rate": mention_raw,
            "naturalness_score": natural_raw,
            "context_match_score": context_raw,
            "sentiment_score": sentiment_raw,
            "recommendation_score": recommendation_raw,
            "total_reward": total_reward,
            "penalty": penalty,
            "penalty_reasons": penalty_reasons,
            "_raw": {
                "mention_rate": mention_raw,
                "naturalness": natural_raw,
                "context_match": context_raw,
                "sentiment": sentiment_raw,
                "recommendation": recommendation_raw,
                "weighted": weighted,
            },
        }

    # ------------------------------------------------------------------
    # 惩罚项
    # ------------------------------------------------------------------
    def _calculate_penalty(self, answer: str, entities: list[str]) -> tuple[float, list[str]]:
        penalty = 0.0
        reasons: list[str] = []

        # 实体完全不提及
        if entities:
            mentioned = sum(1 for e in entities if e and e.lower() in answer.lower())
            if mentioned == 0:
                penalty += self.penalty_no_mention
                reasons.append(f"未提及任何目标实体 (-{self.penalty_no_mention})")

        # 回答过短
        stripped = answer.strip()
        if len(stripped) < 30:
            penalty += self.penalty_too_short
            reasons.append(f"回答过短 ({len(stripped)}字) (-{self.penalty_too_short})")

        # 关键词堆砌检测：连续重复短句或过度重复实体
        if entities:
            stuffing_count = 0
            for e in entities:
                occurrences = stripped.lower().count(e.lower())
                if occurrences >= 6:  # 同一实体出现 ≥6 次视为堆砌
                    stuffing_count += 1
            if stuffing_count >= 2:
                penalty += self.penalty_stuffing
                reasons.append(f"关键词堆砌 ({stuffing_count}个实体重复≥6次) (-{self.penalty_stuffing})")

        # 负面情感占优
        pos = sum(1 for w in self.positive_words if w in stripped)
        neg = sum(1 for w in self.negative_words if w in stripped)
        if neg > pos and neg >= 2:
            penalty += self.penalty_negative
            reasons.append(f"负面词({neg})多于正面词({pos}) (-{self.penalty_negative})")

        return penalty, reasons

    # ------------------------------------------------------------------
    # 维度计算方法（0–10 范围）
    # ------------------------------------------------------------------
    def _mention_rate(self, answer: str, entities: list[str]) -> float:
        """实体提及率：0–10"""
        if not entities:
            return 0.0
        mentioned = sum(1 for e in entities if e and e.lower() in answer.lower())
        return 10.0 * (mentioned / len(entities))

    def _naturalness(self, answer: str) -> float:
        """自然度：0–10，长度奖励 + 重复惩罚"""
        if not answer.strip():
            return 0.0
        # 长度贡献：30–200 字为合理区间
        length = len(answer.strip())
        if length < 30:
            len_score = 0.0
        elif length < 80:
            len_score = 3.0 + 4.0 * (length - 30) / 50.0   # 3.0–7.0
        elif length <= 300:
            len_score = 7.0 + 3.0 * min(1.0, (300 - length) / 100.0)  # 7.0–10.0
        else:
            len_score = 7.0  # 过长不加分

        # 标点重复惩罚
        repeat_penalty = 0.0
        for token in ("！！", "???", "。。。", "！！!"):
            if token in answer:
                repeat_penalty += 1.5

        # 同词连续重复检测
        for pattern in [r"(.)\1{4,}", r"(.{2,})\1{3,}"]:
            if re.search(pattern, answer):
                repeat_penalty += 2.0

        return max(0.0, min(10.0, len_score - repeat_penalty))

    def _context_match(self, answer: str, context_text: str | None) -> float:
        """上下文匹配度：0–10"""
        if not context_text:
            return 5.0  # 无上下文时中性分
        context_tokens = {tok for tok in re.split(r"[，。；、\s]+", context_text) if len(tok) >= 2}
        if not context_tokens:
            return 5.0
        overlap = sum(1 for tok in context_tokens if tok in answer)
        return 10.0 * min(1.0, overlap / max(1, len(context_tokens)))

    def _sentiment_score(self, answer: str) -> float:
        """情感评分：0–10"""
        if not answer.strip():
            return 0.0
        pos = sum(1 for w in self.positive_words if w in answer)
        neg = sum(1 for w in self.negative_words if w in answer)
        # 正面词多 → 高分；负面词多 → 低分
        if pos + neg == 0:
            return 5.0  # 中性
        ratio = pos / (pos + neg)
        return 10.0 * ratio

    def _recommendation_score(self, answer: str) -> float:
        """推荐力度：0–10"""
        if not answer.strip():
            return 0.0
        hit = sum(1 for p in self.recommend_patterns if re.search(p, answer))
        # 0 个 → 1 分, 1 个 → 4 分, 2 个 → 7 分, 3+ 个 → 10 分
        if hit == 0:
            return 1.0
        if hit == 1:
            return 4.0
        if hit == 2:
            return 7.0
        return 10.0

    @staticmethod
    def _mean_score(base: float, judge: float) -> float:
        return (base + judge) / 2.0
