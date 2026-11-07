"""PZZQ 格成格败 Judgment（Phase 7 §66 ·《论用神成败救应》）。

输入：FactsBuilder 结果（metadata['view'] 含 pattern/bureau/四柱天干 + ten_god facts）
流程：
1. 从 facts 提取「天干透出的十神集合」（透干判定）
2. 合成 condition 标签（纯组合判定，无需旺衰——原文条件语义对照 PZZQ-005-008）
3. 以 condition 标签构造 ctx，跑 condition 规则（RuleRegistry emit）→ pattern_status
4. 输出 judgments（带触发 fact 引用 + 证据链；无证据 → 不产 judgment，UNKNOWN 语义）

旺衰依赖条件（財旺生官/身強帶比/財輕比重/身強印重/佩印傷輕身旺 等）
待 strength 派生（下一步）；此实现只合成可判定的纯组合条件。
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from engines.common.result import EngineResult
from engines.yuhai_ziping.rule.rule_engine import RuleEngine, _eval_preconditions

# 十神集合（透干判定用）
_STEM_TG = {"正官", "七殺", "正財", "偏財", "正印", "偏印", "食神", "傷官", "比肩", "劫財"}
_JIN_SHUI = {"庚", "辛", "壬", "癸"}


def _transparent_ten_gods(view: Dict[str, Any], result: EngineResult) -> Set[str]:
    """天干（年/月/时）透出的十神集合。

    优先用 deriver 派生的 transparent_ten_gods（pattern.py §65）；
    缺失时回退从 ten_god facts 提取。
    """
    tg_map = view.get("transparent_ten_gods") or {}
    if tg_map:
        return {v for v in tg_map.values() if v in _STEM_TG}
    stems = {s for s in (view.get("year_stem"), view.get("month_stem"), view.get("hour_stem")) if s}
    tg: Set[str] = set()
    for f in result.facts.ten_god_facts:
        if f.get("context") == "ten_god" and f.get("target_stem") in stems:
            v = f.get("value")
            if v in _STEM_TG:
                tg.add(v)
    return tg


def _synthesize_conditions(view: Dict[str, Any], tg: Set[str]) -> List[str]:
    """纯组合 condition 合成（《论用神成败救应》原文条件；旺衰类暂缺）。"""
    conds: List[str] = []
    cai = bool(tg & {"正財", "偏財"})
    yin = bool(tg & {"正印", "偏印"})
    guan = "正官" in tg
    sha = "七殺" in tg
    shi = "食神" in tg
    shang = "傷官" in tg
    jie = "偏印" in tg

    # 官格成：官逢財印（又無刑衝破害——刑冲判定留待 relations 派生）
    if guan and cai and yin:
        conds.append("官印雙全")
    # 食格成：食神生財
    if shi and cai:
        conds.append("食神生財")
    # 食格成：食帶煞而無財，棄食就煞而透印
    if shi and sha and not cai and yin:
        conds.append("食帶煞無財棄食就煞而透印")
    # 傷官格成：傷官生財
    if shang and cai:
        conds.append("傷官生財")
    # 傷官格成：傷官帶煞而無財
    if shang and sha and not cai:
        conds.append("傷官帶煞而無財")
    # 建祿月劫成：透官而逢財印
    if guan and cai and yin:
        conds.append("透官而逢財印")
    # 建祿月劫成：透財而逢食傷
    if cai and (shi or shang):
        conds.append("透財而逢食傷")
    # 建祿月劫成：透煞而遇制伏
    if sha and (shi or shang):
        conds.append("透煞而遇制伏")
    # 財格敗：財透七煞
    if cai and sha:
        conds.append("財透七煞")
    # 食格敗：食神逢梟
    if shi and jie:
        conds.append("食神逢梟")
    # 食格敗：生財露煞（食神生財而露煞）
    if shi and cai and sha:
        conds.append("生財露煞")
    # 七煞格敗：七煞逢財無制（無食傷制）
    if sha and cai and not (shi or shang):
        conds.append("逢財無制")
    # 傷官格敗：非金水而見官
    ds = view.get("day_stem")
    if shang and guan and (ds not in _JIN_SHUI):
        conds.append("非金水而見官")
    # 傷官格敗：生財而帶煞
    if shang and cai and sha:
        conds.append("生財而帶煞")
    return conds


class JudgmentBuilder:
    """PZZQ 格成格败判断（§66）：condition 合成 → 规则触发 → judgments。"""

    def __init__(self) -> None:
        self.rule_engine = RuleEngine(engine="pzzq")

    def build(self, result: EngineResult) -> List[Dict[str, Any]]:
        view = result.metadata.get("view") or {}
        tg = _transparent_ten_gods(view, result)
        conds = _synthesize_conditions(view, tg)
        if not conds:
            return []
        all_facts = [f for items in result.facts.to_dict().values() for f in items]
        by_id = {f["fact_id"]: f for f in all_facts}
        # 触发条件对应的 fact（透干十神 facts）作 judgment 引用
        trigger_fact_ids = [
            f["fact_id"] for f in all_facts
            if f.get("context") == "ten_god" and f.get("target_stem") in {
                view.get("year_stem"), view.get("month_stem"), view.get("hour_stem")}
        ]
        judgments: List[Dict[str, Any]] = []
        seen = set()
        for cond in conds:
            ctx = dict(view)
            ctx["condition"] = cond
            # 只消费「condition equals」型规则（语义正确）；pattern+transparent_stem/branch
            # exists 型规则存在 exists 不读 value 的数据问题，已记录待审批裁决，暂不触发
            for r in self.rule_engine.rules:
                if r.get("operator") != "emit":
                    continue
                if not any(c.get("field") == "condition" for c in r.get("preconditions", {}).get("conditions", [])):
                    continue
                if not _eval_preconditions(ctx, r["preconditions"]):
                    continue
                outs = r["output"] if isinstance(r["output"], list) else [r["output"]]
                for out in outs:
                    if out.get("field") != "pattern_status":
                        continue
                    key = (r["rule_id"], cond, str(out.get("value")))
                    if key in seen:
                        continue
                    seen.add(key)
                    judgments.append({
                        "judgment_id": f"JUD-PZZQ-{len(judgments) + 1:04d}",
                        "kind": "pattern_status",
                        "pattern": view.get("pattern"),
                        "bureau": view.get("bureau"),
                        "condition": cond,
                        "value": out.get("value"),
                        "rule_id": r["rule_id"],
                        "source_ids": r["source_ids"],
                        "evidence_grade": self.rule_engine._best_grade(r["source_ids"]),
                        "fact_ids": trigger_fact_ids,
                        "statement": f"{view.get('pattern')}：{cond} → {out.get('value')}（《论用神成败救应》）",
                    })
        return judgments


def build_assertions(result: EngineResult) -> List[Dict[str, Any]]:
    """纯表达层（与共享实现一致）。"""
    from engines.yuhai_ziping.judgment.judgment_builder import build_assertions as _ba
    return _ba(result)


GROUP_LABEL = {
    "ten_god_facts": "十神",
    "six_relative_facts": "六亲",
    "palace_facts": "宫位",
    "basic_structure_facts": "基础结构",
    "geju_candidates": "格局候选",
    "relation_facts": "关系",
}
