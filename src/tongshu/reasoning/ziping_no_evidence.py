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
    "COV-014-CONG": {
        "cov_id": "COV-014",
        "topic": "从格破格后格局域喜神如何重定",
        "verdict": "NO_EVIDENCE",
        "evidence": (
            "CONG_GE_001（DTS 下篇从象章，authority=primary）只到「既从矣，当论所从之神」，"
            "破格后喜神未言（Coverage_Closure_Registry COV-014）"
        ),
        "default_behavior": (
            "fail-closed: 从格破格（PO）结论不得臆造/重定格局域喜神；"
            "八格（非从格）破格后的救应喜神另有 PZZQ 成败救应章明文承载，不在本条范围"
        ),
        "guard": (
            "从格入口 facts['special'] 属 special_pattern.py（GPT 热区，pzzq-018 同轨协调）；"
            "协调落地前本条登记生效，不得在从格 PO 路径新增喜神重定"
        ),
    },
    "COV-027-FU": {
        "cov_id": "COV-027",
        "topic": "赋文专篇缺篇（太微赋/病药赋/取用神赋/调候赋）",
        "verdict": "NO_EVIDENCE",
        "evidence": (
            "六部底本无独立专篇（事实排除已定，_问题清单.md）；"
            "调候思想仅由 TIAO_HOU_FU.001（YHZP金玉赋二句）代表（Coverage_Closure_Registry COV-027）"
        ),
        "default_behavior": (
            "fail-closed: 引擎遇太微赋/病药赋/取用神赋名目不得默认按赋文处理；"
            "ziping 线（src/tongshu/reasoning + engines/common）三名目零锚点占用"
        ),
        "guard": "测试结构守卫：ziping 判定线不含三名目锚点标识符",
    },
    "COV-029-DELING": {
        "cov_id": "COV-029①",
        "topic": "「月令相气也算得时」（交办口径）vs SMTH 旺相休囚死（DE_LING.005）",
        "verdict": "NO_EVIDENCE",
        "evidence": (
            "两口径冲突，裁决以 DE_LING.005（SMTH 旺相休囚死，旁参）为准，"
            "不得按交办口径实现（Coverage_Closure_Registry COV-029①）"
        ),
        "default_behavior": (
            "fail-closed: judge_strength 得令按 DE_LING.005 语义（本气人元用事±3、"
            "不据中气余气冒充、月令受冲打折），不实现「相气算得时」——已核验合规"
            "（ziping_classic_check.py:401-416，审计 §二十二；'相气' 零命中）"
        ),
        "guard": "既有 judge_strength 语义测试锁定；登记备案防口径回灌",
    },
    "COV-029-JIXIONG": {
        "cov_id": "COV-029②",
        "topic": "PZZQ 无吉凶寿夭断命专论",
        "verdict": "NO_EVIDENCE",
        "evidence": (
            "PZZQ 无吉凶寿夭断命专论（Coverage_Closure_Registry COV-029②，"
            "来源 04_岁运人事/02_人事论断/_问题清单.md 存疑2）"
        ),
        "default_behavior": (
            "fail-closed: 引擎不得默认为吉；yongyao_resolve.py:15 明示"
            "「只裁决用药方向, 不判吉凶寿夭」——已天然 fail-closed"
        ),
        "guard": "测试结构守卫：寿夭字样仅允许出现在该免责声明注释",
    },
    "COV-029-SAME8ZI": {
        "cov_id": "COV-029③",
        "topic": "SMTH 行2960 同八字异寿夭",
        "verdict": "NO_EVIDENCE",
        "evidence": (
            "SMTH 行2960 同八字异寿夭属哲学论说，不可执行"
            "（Coverage_Closure_Registry COV-029③，_问题清单.md 存疑3）"
        ),
        "default_behavior": "fail-closed: 报不可判，不得二选一；引擎无寿夭判定域",
        "guard": "无寿夭判定域（同 COV-029-JIXIONG 守卫）",
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
