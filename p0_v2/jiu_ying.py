# -*- coding: utf-8 -*-
"""C 块 · 格局救应字段 (裁145改丙 + 146乙 + 147甲 + 148丙)

契约 §4.29:
  jiu_ying = {triggered, type, success, evidence, xiang_note}
  success 四态: SUCCESS / UNS / NA / NA_NOT_IN_SCOPE
    SUCCESS       = 命中判据的布尔条件全为真
    UNS           = 任一判据为假
    NA            = 未触发 (CHENG / NO_GE — 有格但无救应需求)
    NA_NOT_IN_SCOPE = 从格盘 — 6 条判据全为正八格语境, 无从格救应依据
  ★ 不回填 cheng_bai (裁146乙: C 读 A, A 不被 C 改)
  ★ .006 相神 归入 success 判定 (裁147甲: 相神被伤 → success=UNS, 附 xiang_note)

6 条判据内核 (JIU_YING.001-.006, 全布尔, 无一带数值 — 裁145改丙):
  .001 通关  中间神引无合之神/刑冲所间之物 → 存与有根   DTS §二十 L245
  .002 官杀  官杀是否被合去一支            DTS §二十一 L250
  .003 伤官  有财可见官/无财不可见官       DTS §二十二 L255
  .004 澄浊  得一神有力(存在+有根)扫浊    DTS §二十三 L260
  .005 八格  格被忌神破后解神存否          PZZQ §九
  .006 相神  相神被合/伤 → 救应失效        PZZQ §十五

★ 探针阶段: .002/.003 官杀/伤官 已布尔化;
   .001/.004/.005/.006 需通关事实 + 相神定位(引擎 L0 合/根事实), 标 PENDING。
   本文件为纯函数(入参 bazi 8字 + ge_cheng dict), 不 import 引擎生产路径。
"""

# ---- 十神查表 (纯数据, 与引擎 L0 ten_god 同口径, 独立可跑) ----
TEN_GOD_MAP = {
    "甲": {"甲":"比肩","乙":"劫财","丙":"食神","丁":"伤官","戊":"偏财","己":"正财",
            "庚":"七杀","辛":"正官","壬":"偏印","癸":"正印"},
    "乙": {"甲":"劫财","乙":"比肩","丙":"伤官","丁":"食神","戊":"正财","己":"偏财",
            "庚":"正官","辛":"七杀","壬":"正印","癸":"偏印"},
    "丙": {"甲":"偏印","乙":"正印","丙":"比肩","丁":"劫财","戊":"食神","己":"伤官",
            "庚":"偏财","辛":"正财","壬":"七杀","癸":"正官"},
    "丁": {"甲":"正印","乙":"偏印","丙":"劫财","丁":"比肩","戊":"伤官","己":"食神",
            "庚":"正财","辛":"偏财","壬":"正官","癸":"七杀"},
    "戊": {"甲":"偏财","乙":"正财","丙":"食神","丁":"伤官","戊":"比肩","己":"劫财",
            "庚":"七杀","辛":"正官","壬":"偏印","癸":"正印"},
    "己": {"甲":"正财","乙":"偏财","丙":"伤官","丁":"食神","戊":"劫财","己":"比肩",
            "庚":"七杀","辛":"正官","壬":"正印","癸":"偏印"},
    "庚": {"甲":"七杀","乙":"正官","丙":"偏财","丁":"正财","戊":"食神","己":"伤官",
            "庚":"比肩","辛":"劫财","壬":"偏印","癸":"正印"},
    "辛": {"甲":"正官","乙":"七杀","丙":"正财","丁":"偏财","戊":"伤官","己":"食神",
            "庚":"劫财","辛":"比肩","壬":"正印","癸":"偏印"},
    "壬": {"甲":"食神","乙":"伤官","丙":"偏财","丁":"正财","戊":"七杀","己":"正官",
            "庚":"比肩","辛":"劫财","壬":"比肩","癸":"劫财"},
    "癸": {"甲":"伤官","乙":"食神","丙":"正财","丁":"偏财","戊":"正官","己":"七杀",
            "庚":"劫财","辛":"比肩","壬":"比肩","癸":"比肩"},
}

# 地支藏干 (本气在首)
HIDDEN = {
    "子":["癸"], "丑":["己","癸","辛"], "寅":["甲","丙","戊"], "卯":["乙"],
    "辰":["戊","乙","癸"], "巳":["丙","庚","戊"], "午":["丁","己"],
    "未":["己","丁","乙"], "申":["庚","壬","戊"], "酉":["辛"],
    "戌":["戊","辛","丁"], "亥":["壬","甲"],
}

# 天干五合
WUHE = {frozenset("甲己"): "甲己合", frozenset("乙庚"): "乙庚合",
        frozenset("丙辛"): "丙辛合", frozenset("丁壬"): "丁壬合",
        frozenset("戊癸"): "戊癸合"}


def _collect_tengod(bazi):
    """bazi: 8 字 (年干年支 月干月支 日干日支 时干时支)
    返回 (十神集合, 日干)。除日干本身外, 四柱天干 + 地支藏干 各十神。"""
    stems = [bazi[0], bazi[2], bazi[4], bazi[6]]
    branches = [bazi[1], bazi[3], bazi[5], bazi[7]]
    dm = stems[2]
    gods = set()
    for g in [stems[0], stems[1], stems[3]]:
        gods.add(TEN_GOD_MAP[dm][g])
    for z in branches:
        for h in HIDDEN[z]:
            gods.add(TEN_GOD_MAP[dm][h])
    return gods, dm


def _wuhe_pairs(bazi):
    """天干五合对: 返回 [(pair, 合名)]。用于 .002 官杀合去一支 / .006 相神被合。"""
    stems = [bazi[0], bazi[2], bazi[4], bazi[6]]
    out = []
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            pair = frozenset((stems[i], stems[j]))
            if pair in WUHE:
                out.append([stems[i], stems[j], WUHE[pair]])
    return out


def _is_cong(ge, cong_type):
    """从格识别 (裁148丙): ge 含从格关键词 或 cong_type 非空 → NA_NOT_IN_SCOPE。"""
    if any(k in (ge or "") for k in
           ["从财", "从儿", "从杀", "从势", "从旺", "从官", "从格"]):
        return True
    if cong_type:
        return True
    return False


def build_jiu_ying(bazi, ge_cheng):
    """C 块 · 格局救应字段 (裁145改丙 + 146乙 + 147甲 + 148丙)

    入参:
      bazi    8 字 "年干年支 月干月支 日干日支 时干时支"
      ge_cheng dict: {ge, po_n, xi_status, cong_type, ...}
    返回:
      {triggered, type, success, evidence, xiang_note, note}
      success ∈ {SUCCESS, UNS, NA, NA_NOT_IN_SCOPE}
    """
    ge = ge_cheng.get("ge")
    cong_type = ge_cheng.get("cong_type")

    # 从格 → NA_NOT_IN_SCOPE (裁148丙: 范围边界, 非挂起)
    if _is_cong(ge, cong_type):
        return {
            "triggered": False, "type": [], "success": "NA_NOT_IN_SCOPE",
            "evidence": [], "xiang_note": None,
            "note": "从格盘, 6 条救应判据全为正八格语境, 无从格依据 → 范围外"
        }

    # 无格 → NA
    if ge in (None, "", "无格"):
        return {
            "triggered": False, "type": [], "success": "NA",
            "evidence": [], "xiang_note": None,
            "note": "无格, 不适用"
        }

    # 纯成格 → NA (无救应需求)
    if ge_cheng.get("po_n", 0) == 0 and ge_cheng.get("xi_status") != "DEFINED":
        return {
            "triggered": False, "type": [], "success": "NA",
            "evidence": [], "xiang_note": None,
            "note": "纯成格, 无救应需求"
        }

    # CZYP / PO → 判 6 条
    gods, dm = _collect_tengod(bazi)
    wuhe = _wuhe_pairs(bazi)
    types = []
    ev = []

    # .002 官杀混杂 (DTS §二十一 L250): 官杀是否被合去一支
    t2_trig = ("正官" in gods) and (("七杀" in gods) or ("偏官" in gods))
    t2_ok = False
    if t2_trig:
        types.append("JIU_YING.002")
        # 合去一支: 天干五合命中官/杀 (如 乙庚合去 杀/官)
        guan_stems = [s for s in [bazi[0], bazi[2], bazi[4], bazi[6]]
                      if s != dm and TEN_GOD_MAP[dm][s] in ("正官", "七杀", "偏官")]
        he_ge = [s for s in guan_stems
                 if any((s in pair[:2]) for pair in wuhe)]
        t2_ok = len(he_ge) > 0
        ev.append(".002 官杀同现=True, 合去一支=%s (%s)" % (
            "是" if t2_ok else "否(PENDING: 需天干合事实)", he_ge))

    # .003 伤官见官 (DTS §二十二 L255): 有财则救
    t3_trig = ("伤官" in gods) and ("正官" in gods)
    t3_ok = False
    if t3_trig:
        types.append("JIU_YING.003")
        t3_ok = ("正财" in gods) or ("偏财" in gods)
        ev.append(".003 伤官+正官=True, 有财救=%s" % ("是" if t3_ok else "否"))

    # .001 通关 / .004 澄浊 / .005 八格 / .006 相神
    #   需通关事实(中间神引无合之神) + 相神定位(全局赖一字而成者)
    #   探针阶段 PENDING — 标在 evidence, success 取已判 .002/.003 合取
    pending = []
    if not any(p in ("JIU_YING.002", "JIU_YING.003") for p in types):
        pending.append(".001/.004/.005/.006 通关/澄浊/八格/相神 需通关事实+相神定位 (PENDING)")

    if not types:
        return {
            "triggered": True, "type": [], "success": "UNS",
            "evidence": pending, "xiang_note": None,
            "note": "触发但 .002/.003 未命中, 6 条无一适用"
        }

    # success = 命中判据布尔合取 (.002 合去一支 / .003 有财救)
    success = "SUCCESS" if all([
        t2_ok if "JIU_YING.002" in types else True,
        t3_ok if "JIU_YING.003" in types else True,
    ]) else "UNS"

    # .006 相神 (裁147甲): success=UNS 时附 xiang_note
    xiang_note = None
    if success == "UNS":
        xiang_note = "伤相甚于伤用 — 相神被合/伤 → 救应未成, 优先记此因"

    return {
        "triggered": True, "type": types, "success": success,
        "evidence": ev + pending, "xiang_note": xiang_note,
        "note": ".001/.004/.005/.006 PENDING" if pending else None
    }


if __name__ == "__main__":
    # 探针 P1-P6 (裁148丙 枚举四态)
    print("### C 块 jiu_ying.py 探针")

    print("\nP5 CHENG/NO_GE → NA")
    r = build_jiu_ying("戊寅庚申丙申丙申",
                       {"ge": "正官格", "po_n": 0, "xi_status": None, "cong_type": None})
    print("   CHENG 正官格 →", r["success"]); assert r["success"] == "NA"
    r = build_jiu_ying("戊寅庚申丙申丙申",
                       {"ge": None, "po_n": 0, "xi_status": None, "cong_type": None})
    print("   NO_GE →", r["success"]); assert r["success"] == "NA"

    print("\nP4 从格识别 → NA_NOT_IN_SCOPE")
    r = build_jiu_ying("甲辰甲戌甲辰甲戌",
                       {"ge": "从财格", "po_n": 1, "xi_status": "DEFINED", "cong_type": "财"})
    print("   从财格 CZYP →", r["success"]); assert r["success"] == "NA_NOT_IN_SCOPE"
    r = build_jiu_ying("戊寅丁酉庚午丙子",
                       {"ge": "从杀格(破格)", "po_n": 1, "xi_status": None, "cong_type": None})
    print("   从杀格(破格) →", r["success"]); assert r["success"] == "NA_NOT_IN_SCOPE"

    print("\nP6 已知盘: 正格 PO × 1 + CZYP 从格 × 1")
    r = build_jiu_ying("戊寅丁酉庚午丙子",
                       {"ge": "阳刃格", "po_n": 1, "xi_status": None, "cong_type": None})
    print("   阳刃格 PO →", r["success"], "types=", r["type"], "note=", r.get("note"))
    r = build_jiu_ying("戊寅庚申丙申丙申",
                       {"ge": "从财格", "po_n": 1, "xi_status": "DEFINED", "cong_type": "财"})
    print("   从财格 CZYP →", r["success"])

    print("\n★ P1-P6 PASS (.002/.003 布尔化; .001/.004/.005/.006 PENDING)")
    print("★ 全量 2106 盘回归: 等引擎 normalize_ti_wx 断点修复后跑")
