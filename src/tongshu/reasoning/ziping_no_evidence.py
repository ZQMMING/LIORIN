# -*- coding: utf-8 -*-
"""子平引擎覆盖缺口（COV）显式 NO_EVIDENCE 登记 —— fail-closed 缺省行为。

依据 p0_v2/六部经典MD文库/00_元数据/G1-A_Ontology/必补项登记_Coverage_Closure_Registry.md
总则：「宁缺勿滥/宁漏勿错」不得作为覆盖缺口结案理由；引擎必需且底本无确定答案的
主题必须显式登记 NO_EVIDENCE，缺省行为为 fail-closed——报「无原文依据」，不输出结论。

相关条目（非 NO_EVIDENCE，仅指针）：
- COV-019 暗合支对表：live 线 engines/common/l0_fact_builder.py:651-661 已按 PZZQ
  明文窄口径实现卯申相邻暗合（锚 PZZQ 900/1354/3228）+ 暗合解冲（PZ-0046）；
  其余支对无原典明文 → fail-closed 不产出暗合（窄口径即显式缺省行为，证据链见
  docs/audit/ZIPING_CLASSIC_RULES_20261108.md §二十三）。
- COV-006 小运起法两说：待裁决，裁决前引擎不计算小运（同 COV-013② 缺省行为）。
"""

NO_EVIDENCE_TOPICS = {
    "COV-013-1": {
        "cov_id": "COV-013①",
        "topic": "大运改变原局喜用神性质（大运帮身后原局喜神变忌神）",
        "verdict": "NO_EVIDENCE",
        "evidence": "岁运篇底本检索零命中（Coverage_Closure_Registry COV-013① 证据栏，2026-11-10）",
        "default_behavior": (
            "fail-closed: 大运仅提供事件域触发符号（流年冲命局/流年冲大运，"
            "ziping_bridge._shijian_from_facts）；不参与任何喜忌/旺衰/用神重定，"
            "不输出喜忌翻变结论"
        ),
        "guard": "ziping_bridge 内 current_dayun 仅允许流向 _shijian_from_facts（测试结构守卫）",
    },
    "COV-013-2": {
        "cov_id": "COV-013②",
        "topic": "小运与大运相冲相刑主灾",
        "verdict": "NO_EVIDENCE",
        "evidence": (
            "岁运篇底本检索零命中（Coverage_Closure_Registry COV-013② 证据栏）；"
            "小运起法两说另见 COV-006 待裁决"
        ),
        "default_behavior": (
            "fail-closed: 引擎不计算小运（ziping 线 grep '小运' 零命中），"
            "不输出小运相关结论"
        ),
        "guard": "无小运计算路径（测试结构守卫：bridge 源码不含 '小运'）",
    },
}


def assert_topic_not_concluded(topic_id: str) -> None:
    """fail-closed 钩子：任何代码路径试图在 NO_EVIDENCE 主题上产出结论时抛错。

    - 未登记主题 → KeyError（新增 NO_EVIDENCE 主题须先入表）。
    - 已登记且 verdict=NO_EVIDENCE → NotImplementedError（无原文依据，不输出结论）。
    - verdict 已变更 → RuntimeError（登记表口径变更须走裁决，不得绕过）。
    """
    t = NO_EVIDENCE_TOPICS.get(topic_id)
    if t is None:
        raise KeyError(f"未登记主题 {topic_id}（新增 NO_EVIDENCE 主题须先入表）")
    if t.get("verdict") != "NO_EVIDENCE":
        raise RuntimeError(f"主题 {topic_id} 已非 NO_EVIDENCE，登记口径变更须走裁决")
    raise NotImplementedError(
        f"{topic_id} {t['topic']}: 无原文依据（{t['evidence']}），fail-closed 不输出结论"
    )
