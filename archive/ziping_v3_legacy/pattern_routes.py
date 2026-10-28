# -*- coding: utf-8 -*-
"""P5 格局路线召回层 (八族25路线, 纯布尔枚举).

设计 (移植五书skill包 bazi_rules.json 结构, 数据已复制入库 data/pattern_routes.json):
- 输入: FrozenBazi 事实 (四柱天干/藏干/日主), 只读不重排
- 召回: 逐路线查表, 4种布尔predicate枚举求值 (full_chart/present_any/exposed_any/exposed_none)
- 状态枚举: CANDIDATE (布尔全过) / PENDING_REVIEW (布尔过+有interpretive待审) / NOT_TRIGGERED
- fail-closed: 例外条款原文本地未定位 → exceptions_unlocated 标记, 不强行消解
- 结论限域: 召回层只报"路线候选+成立条件", 不代替 PATTERN 域定格裁定 (互补不比较)

铁律: 纯查表/枚举, 无百分比, 无大小比较, 无打分.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# 十神角色 → 天干映射 (日主为基准, 确定性枚举)
# 日主→(我生/我克/生我/同我/克我) 十神: 简化为按日主五行定位
_DAY_MASTER_WUXING = {
    "JIA": "WOOD", "YI": "WOOD", "BING": "FIRE", "DING": "FIRE",
    "WU": "EARTH", "JI": "EARTH", "GENG": "METAL", "XIN": "METAL",
    "REN": "WATER", "GUI": "WATER",
}
_WX_SHENG = {"WOOD": "FIRE", "FIRE": "EARTH", "EARTH": "METAL", "METAL": "WATER", "WATER": "WOOD"}
_WX_KE = {"WOOD": "EARTH", "EARTH": "WATER", "WATER": "FIRE", "FIRE": "METAL", "METAL": "WOOD"}

# 十神 (日主视角) → 五行关系 + 阴阳
# 正/偏 由阴阳同异决定; 召回层按"十神名"匹配, 需日主天干
_TEN_GOD_BY_WX_REL = {
    # (关系, 同阴阳) → 十神
    ("SHENG_ME", "SAME"): "正印", ("SHENG_ME", "DIFF"): "偏印",
    ("SAME", "SAME"): "比肩", ("SAME", "DIFF"): "劫财",
    ("I_SHENG", "SAME"): "食神", ("I_SHENG", "DIFF"): "伤官",
    ("I_KE", "SAME"): "正财", ("I_KE", "DIFF"): "偏财",
    ("KE_ME", "SAME"): "正官", ("KE_ME", "DIFF"): "七杀",
}
_YANG = {"JIA", "BING", "WU", "GENG", "REN"}


def ten_god_of(day_master: str, other_stem: str) -> str:
    """日主 vs 他干 → 十神名 (纯枚举查表)."""
    if day_master not in _DAY_MASTER_WUXING or other_stem not in _DAY_MASTER_WUXING:
        return ""
    dm_wx = _DAY_MASTER_WUXING[day_master]
    ot_wx = _DAY_MASTER_WUXING[other_stem]
    same_yin = (day_master in _YANG) == (other_stem in _YANG)
    if dm_wx == ot_wx:
        rel = "SAME"
    elif _WX_SHENG[dm_wx] == ot_wx:
        rel = "I_SHENG"
    elif _WX_KE[dm_wx] == ot_wx:
        rel = "I_KE"
    elif _WX_KE[ot_wx] == dm_wx:
        rel = "KE_ME"
    else:  # 他生我
        rel = "SHENG_ME"
    key = (rel, "SAME" if same_yin else "DIFF")
    return _TEN_GOD_BY_WX_REL.get(key, "")


@dataclass
class PatternRouteRecall:
    """单条路线召回结果."""
    route_id: str
    family: str
    status: str                      # CANDIDATE / PENDING_REVIEW / NOT_TRIGGERED
    failed_predicates: List[str] = field(default_factory=list)   # NOT_TRIGGERED 时
    pending_review: List[str] = field(default_factory=list)       # 待人工/辨层核的条件
    exceptions_unlocated: List[str] = field(default_factory=list) # 例外条款本地未定位 (fail-closed)
    quote: str = ""
    passage_id: str = ""
    allowed_conclusion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route_id": self.route_id, "family": self.family, "status": self.status,
            "failed_predicates": self.failed_predicates,
            "pending_review": self.pending_review,
            "exceptions_unlocated": self.exceptions_unlocated,
            "quote": self.quote, "passage_id": self.passage_id,
            "allowed_conclusion": self.allowed_conclusion,
        }


class PatternRouteRecaller:
    """八族25路线召回 — 纯查表, 无比较运算."""

    PREDICATES = ("full_chart", "present_any", "exposed_any", "exposed_none")

    def __init__(self, data_path: Optional[str] = None):
        p = Path(data_path) if data_path else \
            Path(__file__).parent / "data" / "pattern_routes.json"
        self._data = json.loads(p.read_text(encoding="utf-8"))

    def _collect_roles(self, chart_info: Dict[str, Any]) -> Dict[str, set]:
        """从四柱(天干+藏干)收集每个十神出现的可见性.
        返回 {十神名: {"exposed"(明干), "present"(明干或藏干)}}."""
        day_master = chart_info.get("day_master", "").upper()
        four_stems = [s.upper() for s in chart_info.get("four_stems", [])]
        hidden = chart_info.get("hidden_stems", {})  # {"ZI": ["REN"], ...} 或 {位置: [干]}

        exposed: set = set()
        present: set = set()
        # 明干 (除日主自身柱外, 日干本身是参照不算他干; 但比肩在日干上 → 只计他柱)
        for s in four_stems:
            god = ten_god_of(day_master, s)
            if god:
                exposed.add(god)
                present.add(god)
        # 藏干: 结构 {位置: {"main","middle","residual","all":[...]}}
        if isinstance(hidden, dict):
            for pos, hd in hidden.items():
                stems = hd.get("all") if isinstance(hd, dict) else hd
                if not stems:
                    continue
                for s in stems:
                    s = str(s).upper()
                    god = ten_god_of(day_master, s)
                    if god:
                        present.add(god)
        return {"exposed": exposed, "present": present}

    def _eval_predicate(self, pred: str, roles: List[str], vis: Dict[str, set],
                        chart_complete: bool) -> bool:
        """单 predicate 布尔求值 (纯查集合, 无比较)."""
        if pred == "full_chart":
            return chart_complete
        if pred == "present_any":
            return bool(set(roles) & vis["present"])
        if pred == "exposed_any":
            return bool(set(roles) & vis["exposed"])
        if pred == "exposed_none":
            return not (set(roles) & vis["exposed"])
        return False  # 未知 predicate → fail-closed (False)

    def recall(self, chart_info: Dict[str, Any]) -> List[PatternRouteRecall]:
        """召回全部25路线 → 状态枚举."""
        day_master = chart_info.get("day_master", "").upper()
        chart_complete = bool(chart_info.get("hour_known", True)) and len(
            [s for s in chart_info.get("four_stems", []) if s]) == 4
        vis = self._collect_roles(chart_info)
        results: List[PatternRouteRecall] = []
        for fam in self._data.get("families", []):
            for route in fam.get("routes", []):
                preds = route.get("predicates", [])
                role_lists = route.get("roles", [])
                rec = PatternRouteRecall(
                    route_id=route["id"], family=fam["id"],
                    status="NOT_TRIGGERED",
                    pending_review=list(route.get("pending_review", [])),
                    quote=route.get("quote", ""),
                    passage_id=route.get("passage_id", ""),
                    allowed_conclusion=route.get("allowed_conclusion", ""),
                )
                # predicates 与 roles 列表按序对应 (生成时等长配对)
                all_pass = True
                pairs = list(zip(preds, role_lists))
                if len(preds) != len(role_lists):
                    # 数据表异长 → fail-closed, 该路线不召回
                    rec.failed_predicates.append("DATA_MISALIGNED")
                    all_pass = False
                else:
                    for pred, roles in pairs:
                        if pred not in self.PREDICATES:
                            all_pass = False
                            rec.failed_predicates.append(pred)
                            break
                        if not self._eval_predicate(pred, roles, vis, chart_complete):
                            all_pass = False
                            rec.failed_predicates.append(pred)
                            break
                if all_pass:
                    # 有 interpretive 待审条件 → PENDING_REVIEW, 否则 CANDIDATE
                    rec.status = "PENDING_REVIEW" if rec.pending_review else "CANDIDATE"
                    # fail-closed: 例外条款本地未定位 → 不得直报 CANDIDATE
                    exc = route.get("exception_passage_ids", [])
                    if exc:
                        rec.exceptions_unlocated = list(exc)
                        if rec.status == "CANDIDATE":
                            rec.status = "PENDING_REVIEW"
                    results.append(rec)
        return results

    @staticmethod
    def to_dicts(recalls: List[PatternRouteRecall]) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in recalls]
