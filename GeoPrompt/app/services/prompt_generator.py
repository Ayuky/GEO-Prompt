from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

# Prompt生成结果:
# 生成的Prompt文本、
# 生成模式
# 相关元数据(风格，变异规则)。
@dataclass
class PromptGenerationResult:
    prompt_text: str
    mode: str
    metadata: dict[str, Any]


class PromptGenerator:
    def __init__(self, seed: int | None = None) -> None:
        #随机种子
        self.random = random.Random(seed)
        # 基础模板（不显式点名实体，靠角色和框架自然引导覆盖）
        self.base_templates = [
            # 专家角色类
            (
                "你是一名{domain}领域的GEO内容优化专家。"
                "要求语言自然流畅，给出可执行的推荐建议，并保持上下文一致性。"
            ),
            (
                "扮演资深{domain}行业顾问，目标是提升目标品牌在生成式搜索中的曝光度。"
                "请给出以用户为中心的专业建议。"
            ),
            (
                "你负责{domain}知识问答与产品推荐。输出需明确、可信、易读，"
                "详细解释推荐理由。"
            ),
            # 助手角色类
            (
                "你是一个智能购物助手，帮助用户了解相关产品。"
                "请用通俗易懂的语言，结合用户需求给出个性化建议。"
            ),
            (
                "作为AI推荐引擎，你的任务是综合评估各类选项并提供最优选择。"
                "综合考虑性能、价格、口碑等因素，给出平衡的推荐。"
            ),
            # 评测者角色类
            (
                "你是专业的{domain}产品评测师。请客观分析各选项的优缺点。"
                "从用户体验角度出发，给出公正的评价和购买建议。"
            ),
            (
                "扮演独立第三方评测机构，对相关产品进行深度对比分析。"
                "基于数据和事实，提供权威的推荐意见。"
            ),
            # 教育者角色类
            (
                "你是一位{domain}科普作者，任务是向普通用户介绍相关知识。"
                "用生动有趣的语言，帮助用户快速理解核心信息。"
            ),
            (
                "作为行业培训师，你需要向新手讲解关键知识点。"
                "结构化呈现信息，确保用户能够轻松掌握要点。"
            ),
            # 营销者角色类
            (
                "你是品牌营销策略师，需要突出产品的核心竞争优势。"
                "用有说服力的语言，激发用户的购买兴趣。"
            ),
            (
                "扮演数字营销专家，优化内容在搜索引擎中的表现。"
                "平衡SEO需求与用户体验，创造高转化内容。"
            ),
            # 咨询者角色类
            (
                "你是个人消费顾问，根据用户需求提供个性化推荐。"
                "注重实用性和性价比，帮助用户做出明智决策。"
            ),
            (
                "作为企业采购顾问，需要从专业角度评估各类选项。"
                "关注长期价值、售后服务和总拥有成本(TCO)。"
            ),
            # 社区达人角色类
            (
                "你是活跃的{domain}社区达人，分享真实体验和心得。"
                "用接地气的语言，提供来自一线用户的实用建议。"
            ),
            (
                "扮演知乎/小红书优质答主，深度解析热门话题。"
                "结合个人经历和专业分析，产出高质量种草内容。"
            ),
        ]
        # 风格池和变异规则
        # ========== 多维度风格系统 ==========
        # 语气风格
        self.tone_styles = [
            "专业严谨",
            "亲切友好",
            "活泼轻松",
            "权威自信",
            "温和委婉",
            "直接干练",
        ]

        # 输出长度
        self.length_styles = [
            "简洁精炼(50-100字)",
            "适中详细(100-200字)",
            "深度全面(200-500字)",
        ]

        # 结构化格式
        self.format_styles = [
            "段落叙述式",
            "分点列举式",
            "表格对比式",
            "问答互动式",
            "故事案例式",
        ]

        # 强调重点
        self.emphasis_styles = [
            "突出性价比",
            "强调用户体验",
            "聚焦技术创新",
            "重视品牌口碑",
            "关注售后服务",
            "平衡综合因素",
        ]

        # 目标受众
        self.audience_styles = [
            "面向新手小白",
            "面向专业人士",
            "面向家庭用户",
            "面向年轻群体",
            "面向商务人士",
        ]

        # 变异规则
        self.mutation_tokens = [
            # 形容词增强
            ("自然", "自然且有说服力"),
            ("自然", "流畅且引人入胜"),
            ("专业", "专业且易于理解"),
            ("详细", "详尽且条理清晰"),
            ("简洁", "精炼且重点突出"),

            # 动词增强
            ("推荐", "强烈推荐并说明理由"),
            ("提及", "重点突出并深入分析"),
            ("覆盖", "全面覆盖且不遗漏关键点"),
            ("解释", "深入浅出地解释"),
            ("分析", "多角度深入分析"),

            # 名词增强
            ("建议", " actionable 可执行建议"),
            ("信息", "有价值的参考信息"),
            ("内容", "高质量原创内容"),
            ("回答", "完整且有帮助的回答"),

            # 上下文增强
            ("上下文", "上下文和用户真实意图"),
            ("需求", "显性需求和隐性需求"),
            ("场景", "使用场景和痛点"),

            # 追加指令
            ("避免堆砌", "避免关键词堆砌，保持自然流畅"),
            ("可信", "可信且基于事实依据"),
            ("可读", "可读性强，排版清晰美观"),
        ]

        # 追加指令池
        self.append_instructions = [
            "\n请给出明确的结论与行动建议。",
            "\n最后总结核心观点，方便用户快速把握要点。",
            "\n如有可能，提供具体的使用场景示例。",
            "\n注意平衡正面和负面信息，保持客观中立。",
            "\n用具体数据或案例支撑你的观点。",
            "\n考虑不同用户群体的差异化需求。",
            "\n提醒用户注意常见的误区或陷阱。",
            "\n如果适用，提供替代方案或备选推荐。",
        ]





    """随机生成Prompt：
    1. 从基础模板中随机选择一个
    2. 从风格池中随机选择一种风格
    3. 将领域填充到模板中
    4. 可选添加额外上下文
    5. 附加写作风格要求
    """
    def generate_manual(self, prompt_text: str) -> PromptGenerationResult:
        """直接使用人工编写的Prompt，不做任何生成或优化"""
        return PromptGenerationResult(
            prompt_text=prompt_text,
            mode="manual",
            metadata={"source": "manual"},
        )

    def generate_random(self, entities: list[str], context_text: str | None = None, domain: str | None = None) -> PromptGenerationResult:
        """增强的随机生成：多维度组合（不显式点名实体）"""
        template = self.random.choice(self.base_templates)
        # 多维度风格组合
        tone = self.random.choice(self.tone_styles)
        length = self.random.choice(self.length_styles)
        fmt = self.random.choice(self.format_styles)
        emphasis = self.random.choice(self.emphasis_styles)
        audience = self.random.choice(self.audience_styles)
        # 填充模板
        prompt = template.format(
            entities="、".join(entities) if entities else "核心品牌",
            domain=domain
        )
        # 添加上下文
        if context_text:
            prompt += f"\n用户背景：{context_text}"
        # 添加多维度风格要求
        prompt += f"\n写作要求："
        prompt += f"\n- 语气风格：{tone}"
        prompt += f"\n- 内容长度：{length}"
        prompt += f"\n- 输出格式：{fmt}"
        prompt += f"\n- 强调重点：{emphasis}"
        prompt += f"\n- 目标受众：{audience}"
        # 随机追加1-2条额外指令
        num_appends = self.random.randint(1, 2)
        extra_instructions = self.random.sample(self.append_instructions, num_appends)
        for instruction in extra_instructions:
            prompt += instruction

        return PromptGenerationResult(
            prompt_text=prompt,
            mode="random",
            metadata={
                "tone": tone,
                "length": length,
                "format": fmt,
                "emphasis": emphasis,
                "audience": audience,
                "domain": domain,
                "extra_instructions_count": num_appends,
            },
        )



    """模板变异：
    1. 接收源提示词
    2. 遍历变异令牌,以65%概率替换关键词
    (如:"自然" → "自然且有说服力")
    3. 以50%概率追加结论要求
    4. 记录所有应用的变异规则
    """
    def mutate_template(self, source_prompt: str) -> PromptGenerationResult:
        """增强的模板变异：更丰富的变异策略"""
        mutated = source_prompt
        applied_rules: list[str] = []

        # 应用词对替换（提高概率到70%）
        for old, new in self.mutation_tokens:
            if old in mutated and self.random.random() > 0.30:
                mutated = mutated.replace(old, new, 1)  # 只替换第一次出现，避免过度修改
                applied_rules.append(f"replace:{old}->{new}")

        # 随机追加指令（提高到60%概率）
        if self.random.random() > 0.40:
            instruction = self.random.choice(self.append_instructions)
            # 避免重复追加
            if instruction.strip() not in mutated:
                mutated += instruction
                applied_rules.append(f"append:{instruction[:20]}...")

        # 随机调整语气（30%概率）
        if self.random.random() > 0.70:
            new_tone = self.random.choice(self.tone_styles)
            mutated += f"\n语气调整为：{new_tone}"
            applied_rules.append(f"tone_adjust:{new_tone}")

        # 随机调整长度要求（20%概率）
        if self.random.random() > 0.80:
            new_length = self.random.choice(self.length_styles)
            mutated += f"\n长度要求：{new_length}"
            applied_rules.append(f"length_adjust:{new_length}")

        return PromptGenerationResult(
            prompt_text=mutated,
            mode="template_mutation",
            metadata={
                "mutation_rules": applied_rules,
                "mutation_count": len(applied_rules),
            },
        )

    """策略生成Prompt：
    1. 策略映射表
    支持3种动作:
    action=0: random (随机生成，不点名实体)
    action=1: template_mutation (模板变异，不点名实体)
    action=2: policy (策略模板，显式点名实体)
    2. 策略选择
    3. 策略执行
    4. 策略元数据
    """
    def generate_by_policy(
        self,
        action: int,
        entities: list[str],
        context_text: str | None = None,
        source_prompt: str | None = None,
        domain: str | None = None,
    ) -> PromptGenerationResult:
        """增强的策略生成"""
        if action == 1 and source_prompt:
            result = self.mutate_template(source_prompt)
            result.metadata["policy_action"] = "template_mutation"
            return result

        # 结构化策略 - 显式点名实体
        if action == 2:
            templates = [
                (
                    "你是{domain}领域的专业内容顾问。\n"
                    "请按以下结构组织你的回答：\n"
                    "1️⃣ 核心要点（3-5条）\n"
                    "2️⃣ 推荐理由（每条配1-2句说明）\n"
                    "3️⃣ 潜在风险或注意事项\n"
                    "4️⃣ 总结与建议\n"
                    f"\n必须涵盖的实体：{'、'.join(entities) if entities else '核心品牌'}\n"
                    "要求：表达自然流畅，避免生硬堆砌关键词。"
                ),
                (
                    "作为{domain}领域的专业顾问，请采用SCQA框架回答：\n"
                    "-情境：描述用户当前状况\n"
                    "-冲突：指出痛点或挑战\n"
                    "-问题：明确核心问题\n"
                    f"-答案：针对{'、'.join(entities) if entities else '核心品牌'}给出解决方案\n"
                    "\n确保内容实用、可操作。"
                ),
                (
                "你是{domain}领域的公正的产品对比分析师。\n"
                "请对以下实体进行横向对比：\n"
                f"对比对象：{'、'.join(entities) if entities else '多个品牌'}\n"
                "\n对比维度：\n"
                "- 核心功能/特性\n"
                "- 价格与性价比\n"
                "- 用户口碑与评价\n"
                "- 适用人群与场景\n"
                "- 优势与劣势\n"
                "\n输出格式：先用表格概览，再用文字详细解读。\n"
                "最后给出针对不同需求的差异化推荐。"
                )
            ]
            template = self.random.choice(templates)
            prompt = template.format(domain=domain)
            if context_text:
                prompt += f"\n\n上下文背景信息：{context_text}"

            return PromptGenerationResult(
                prompt_text=prompt,
                mode="structured_template",
                metadata={"policy_action": "structured_template", "template_variant": templates.index(template)},
            )
        # 默认回退到随机生成（action 0 或 action 1 无 source_prompt）
        result = self.generate_random(entities=entities, context_text=context_text)
        if action == 0:
            result.metadata["policy_action"] = "random"
        elif action == 1:
            result.metadata["policy_action"] = "template_mutation"
        return result
