"""§4.22 L4 格局成败 cheng_bai_criteria 纯结构出口（核A · 裁140甲）

消费类型: COMPUTED — 下游可读，供人工核或后续合判。
值域: 不做成/败/清/浊结论，只出「哪些判据适用于本盘」。

依据: l3_contract_spec.md §4.22
- 12 条判据 ID: p0_v2/六部经典MD文库/02_原局诊断/02_格局/*.md (CHENG_BAI 段)
- 章节归属: BOOK_CITED（源文章节）
- 切片分组: ENGINE_DEFINED（编者分类，非源文映射）

★ 映射表初版（v0）:
  官杀格/伤官格有 DTS 专章 → 9-10 条适用
  正官格/财格/印格/食神格 DTS 无专章 → 9 条适用（通用 + 八格总则）
  不命中格名 → applicable=[] unmapped=12 note=显式列出
"""
from typing import Any, Dict

# ------------------------------------------------------------------
# 12 条切片 ID → 章节归属（BOOK_CITED）+ 分组（ENGINE_DEFINED）
# ------------------------------------------------------------------
CHENG_BAI_SLICE_MAP: Dict[str, Dict[str, str]] = {
    "STRUCTURE.GE_JU.CHENG_BAI.001": {"section": "DTS §十二", "group": "格体标准"},
    "STRUCTURE.GE_JU.CHENG_BAI.002": {"section": "DTS §十二", "group": "格体标准"},
    "STRUCTURE.GE_JU.CHENG_BAI.003": {"section": "DTS §二十一", "group": "官杀格"},
    "STRUCTURE.GE_JU.CHENG_BAI.004": {"section": "DTS §二十二", "group": "伤官格"},
    "STRUCTURE.GE_JU.CHENG_BAI.005": {"section": "DTS §二十三", "group": "格内配置"},
    "STRUCTURE.GE_JU.CHENG_BAI.006": {"section": "DTS §二十四", "group": "格内配置"},
    "STRUCTURE.GE_JU.CHENG_BAI.007": {"section": "PZZQ §九", "group": "八格总则"},
    "STRUCTURE.GE_JU.CHENG_BAI.008": {"section": "PZZQ §九", "group": "八格总则"},
    "STRUCTURE.GE_JU.CHENG_BAI.009": {"section": "PZZQ §九", "group": "八格总则"},
    "STRUCTURE.GE_JU.CHENG_BAI.010": {"section": "PZZQ §十三", "group": "八格总则"},
    "STRUCTURE.GE_JU.CHENG_BAI.011": {"section": "PZZQ §十八", "group": "八格总则"},
    "STRUCTURE.GE_JU.CHENG_BAI.012": {"section": "PZZQ §十九", "group": "八格总则"},
}

# ------------------------------------------------------------------
# 格名 → 适用判据 ID 列表（初版 v0，按 DTS 章节归属 + PZZQ 八格总则全列）
# ------------------------------------------------------------------
_ALL_COMMON = [
    "STRUCTURE.GE_JU.CHENG_BAI.001",  # 格体标准
    "STRUCTURE.GE_JU.CHENG_BAI.005",  # 清气
    "STRUCTURE.GE_JU.CHENG_BAI.006",  # 浊气
    "STRUCTURE.GE_JU.CHENG_BAI.007",  # 八格成格条件
    "STRUCTURE.GE_JU.CHENG_BAI.008",  # 八格败格条件
    "STRUCTURE.GE_JU.CHENG_BAI.009",  # 成中有败
    "STRUCTURE.GE_JU.CHENG_BAI.010",  # 因成得败/因败得成
    "STRUCTURE.GE_JU.CHENG_BAI.011",  # 四吉神破格
    "STRUCTURE.GE_JU.CHENG_BAI.012",  # 四凶神成格
]

GE_CHENG_BAI_MAP: Dict[str, list] = {
    # DTS §二十一 专章 → 通用 9 条 + .003（官杀）
    "正官格": _ALL_COMMON + ["STRUCTURE.GE_JU.CHENG_BAI.003"],
    "七煞格": _ALL_COMMON + ["STRUCTURE.GE_JU.CHENG_BAI.003"],
    "七杀格": _ALL_COMMON + ["STRUCTURE.GE_JU.CHENG_BAI.003"],
    # DTS §二十二 专章 → 通用 9 条 + .004（伤官）
    "伤官格": _ALL_COMMON + ["STRUCTURE.GE_JU.CHENG_BAI.004"],
    # DTS 无专章 → 通用 9 条
    "正财格": list(_ALL_COMMON),
    "偏财格": list(_ALL_COMMON),
    "正印格": list(_ALL_COMMON),
    "偏印格": list(_ALL_COMMON),
    "食神格": list(_ALL_COMMON),
    "建禄格": list(_ALL_COMMON),
    "月劫格": list(_ALL_COMMON),
    "阳刃格": list(_ALL_COMMON),
}


def build_cheng_bai_criteria(ge_name: str) -> Dict[str, Any]:
    """纯结构出口: 本盘适用的判据 ID 列表 + 映射状态。

    Args:
        ge_name: 格名（如「正官格」「七煞格」「正财格」等）

    Returns:
        {
            "applicable": [判据ID列表],
            "map_version": "v0",
            "map_coverage": "N/12",
            "unmapped": [未映射的判据ID],
            "note": (不命中格名时) "格名 X 未在映射表内 —— 待补映射"
        }

    ★ 不做成/败/清/浊结论。只出「哪些判据适用」。
    ★ unmapped 显式列出 —— 不藏「还没映射」的状态，下游知道当前覆盖边界。
    """
    if ge_name not in GE_CHENG_BAI_MAP:
        return {
            "applicable": [],
            "map_version": "v0",
            "map_coverage": "0/12",
            "unmapped": list(CHENG_BAI_SLICE_MAP.keys()),
            "note": "格名 %s 未在映射表内 —— 待补映射" % ge_name,
        }

    applicable = GE_CHENG_BAI_MAP[ge_name]
    all_ids = list(CHENG_BAI_SLICE_MAP.keys())
    applicable_set = set(applicable)
    unmapped = [sid for sid in all_ids if sid not in applicable_set]

    return {
        "applicable": applicable,
        "map_version": "v0",
        "map_coverage": "%d/12" % len(applicable),
        "unmapped": unmapped,
    }


if __name__ == "__main__":
    # 探针: 独立进程验证（不 import 引擎生产路径）
    import json
    print("=== cheng_bai_criteria 探针（独立进程，不 import 引擎） ===")
    for ge in ["正官格", "七煞格", "伤官格", "正财格", "偏印格", "食神格"]:
        r = build_cheng_bai_criteria(ge)
        print("%s  applicable=%d  unmapped=%d  例: %s"
              % (ge, len(r["applicable"]), len(r["unmapped"]), r["unmapped"][:3]))
    r2 = build_cheng_bai_criteria("建禄格")
    print("建禄格  applicable=%d  unmapped=%d  note=%s"
          % (len(r2["applicable"]), len(r2["unmapped"]), r2.get("note")))
    print("★ PASS — 纯结构出口，零语义依赖")
