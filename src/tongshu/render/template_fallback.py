"""Template Fallback — deterministic pre-written strings.

Per output_validation.md §8, when the LLM Validator fails repeatedly,
the system MUST fall back to a deterministic template. No LLM.
"""

from __future__ import annotations


class TemplateFallback:
    """Deterministic template-based fallback rendering.

    Templates are organized by (theme, cross_status) pairs.
    """

    TEMPLATES = {
        ("WORK", "ALIGNED"): "今日【WORK】主题方向清晰。基于你的命盘结构，宜在熟悉的领域推进既定方向。请结合实际情境把握节拍。今日的主题落在执行层面，宜主动推进熟悉的事项，按已有节奏落实计划即可。",
        ("WORK", "PARTIAL"): "今日【WORK】主题存在多种信号叠加。建议先内观方向，再外显行动。今日宜分清轻重缓急，主线明确后再展开枝节，避免方向未定就急于产出。让内在判断先行于外在动作。",
        ("WORK", "INSUFFICIENT"): "今日【WORK】主题信号不足以给出明确方向。建议先观察再行动。今日宜保持中性观察，把注意力从『要不要做』转向『看到什么』，让信号自然浮现后再做判断。",

        ("RELATION", "ALIGNED"): "今日【RELATION】主题方向清晰。宜在关系中表达真实想法。今日宜主动把内心的想法转化为可被对方接收的语言，避免猜测，让沟通成为关系的稳定器，让表达带来靠近而非隔阂。",
        ("RELATION", "PARTIAL"): "今日【RELATION】主题多种信号并存。建议先觉察自己的状态再互动。今日宜先看清自己的内在状态再向外展开，是想靠近还是想保持距离，明确后再决定如何与对方相处。",
        ("RELATION", "INSUFFICIENT"): "今日【RELATION】主题信号不足。建议先内观再对外。今日宜先觉察自己的内在状态再向外展开，让关系互动建立在清晰的自我认知之上。",

        ("EMOTION", "ALIGNED"): "今日【EMOTION】主题方向清晰。宜觉察内在状态。今日宜把注意力从外在收回内在，让情绪成为可观察的对象而非失控的事件，在觉察中让内在自然安定下来。",
        ("EMOTION", "PARTIAL"): "今日【EMOTION】主题能量错综。建议先静默片刻再决定。今日宜给自己一个不被打扰的片刻，让错综的能量自然沉降，不要急着下结论或做决定。",
        ("EMOTION", "INSUFFICIENT"): "今日【EMOTION】主题信号不足。建议保持中性观察。今日宜保持中性的觉察，不强求理解当下的情绪，让内在的状态自然呈现，等待信号清晰。",

        ("LEARNING", "ALIGNED"): "今日【LEARNING】主题方向清晰。宜吸收新知或复述旧学。今日宜打开感官接收新的知识，也可以把已有的认知结构化输出，让学习在内外两个方向同时流动，加深理解。",
        ("LEARNING", "PARTIAL"): "今日【LEARNING】主题多种信号并存。建议先沉淀再扩展。今日宜把过去学习的内容先做内化沉淀，不要急着开拓新领域，把地基打深比扩展边界更重要。",
        ("LEARNING", "INSUFFICIENT"): "今日【LEARNING】主题信号不足。建议先整理现有知识。今日宜把已有的知识做一次回顾整理，建立框架后再考虑新的输入，让学习有结构可依。",

        ("FAMILY_SOCIAL", "ALIGNED"): "今日【FAMILY_SOCIAL】主题方向清晰。宜主动联系或分享。今日宜主动与家人或社交圈建立连接，把内心的近况化为可分享的话语，让关系在具体交流中加深温度。",
        ("FAMILY_SOCIAL", "PARTIAL"): "今日【FAMILY_SOCIAL】主题信号错综。建议先觉察需求再行动。今日宜先觉察自己当下想要的是连接还是独处，明确后再决定是发起互动还是暂时退后，让互动贴合真实需要。",
        ("FAMILY_SOCIAL", "INSUFFICIENT"): "今日【FAMILY_SOCIAL】主题信号不足。建议不强求。今日不强求互动，先观察家庭或社交圈当下的氛围与节拍，让信号自然浮现再决定如何回应。",

        ("ACTION_LIFE", "ALIGNED"): "今日【ACTION_LIFE】主题方向清晰。宜将想法落实为行动。今日宜把脑子里的想法落地为具体动作，哪怕是小步推进，让思考与行动形成正向循环，让方向通过行动被验证。",
        ("ACTION_LIFE", "PARTIAL"): "今日【ACTION_LIFE】主题多种信号并存。建议先内观后行动。今日宜先看清自己的内在状态，再决定是推进还是暂停，把行动建立在清晰的自我判断之上。",
        ("ACTION_LIFE", "INSUFFICIENT"): "今日【ACTION_LIFE】主题信号不足。建议先观望。今日宜先观望当前的生活节拍，不急于推进新动作，让信号浮现后再决定今日的实际方向。",
    }

    def render(self, theme: str, cross_status: str) -> str | None:
        """Report coverage without turning its structural status into a judgment."""
        if (theme, cross_status) not in self.TEMPLATES:
            return None
        return {
            "ALIGNED": "现有来源均有证据记录，覆盖情况不代表结论一致或判断已经获批。",
            "PARTIAL": "部分来源有证据记录，其他来源证据不足，暂不能提供完整判断。",
            "INSUFFICIENT": "当前证据不足以支持判断，请稍后重试或补充资料。",
        }[cross_status]
