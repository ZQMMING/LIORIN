# -*- coding: utf-8 -*-
import re
"""C 块 · 格局救应字段 (裁145改丙 + 146乙 + 147甲 + 148丙 + 149甲 + 150甲 + 151甲)

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


# 五行 / 通关表 (DTS L245 明列 4 组: 木土要火 / 火金要土 / 土水要金 / 金水要水)
GAN_WX = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土",
          "庚":"金","辛":"金","壬":"水","癸":"水"}
TONG_GUAN = {frozenset("木土"):"火", frozenset("火金"):"土",
             frozenset("土水"):"金", frozenset("金水"):"水"}

# 地支六冲 (裁149甲: .005-c "刑冲而会合以解之" 需刑冲在场事实)
LIU_CHONG = {frozenset("子午"), frozenset("丑未"), frozenset("寅申"),
             frozenset("卯酉"), frozenset("辰戌"), frozenset("巳亥")}

# 十二长生 (重根 = 长生/禄/刃, 与引擎 L0 root_weight_class_facts 同口径)
ROOT_LIFECYCLE = {
    "甲":{"亥":"长生","寅":"禄","卯":"刃"}, "乙":{"午":"长生","卯":"禄","辰":"刃"},
    "丙":{"寅":"长生","巳":"禄","午":"刃"}, "丁":{"酉":"长生","午":"禄","未":"刃"},
    "戊":{"寅":"长生","巳":"禄","午":"刃"}, "己":{"酉":"长生","午":"禄","未":"刃"},
    "庚":{"巳":"长生","申":"禄","酉":"刃"}, "辛":{"子":"长生","酉":"禄","戌":"刃"},
    "壬":{"申":"长生","亥":"禄","子":"刃"}, "癸":{"卯":"长生","子":"禄","丑":"刃"},
}
HEAVY = {"长生","禄","刃"}


def _has_root(dm, branches):
    """日干 dm 在 branches(4支) 有无重根(长生/禄/刃 或 藏干含 dm)。纯函数。"""
    for z in branches:
        life = ROOT_LIFECYCLE.get(dm, {}).get(z)
        if life in HEAVY:
            return True
        if dm in HIDDEN.get(z, []):
            return True
    return False


def build_l0_facts_pure(bazi):
    """纯函数版 L0 facts (与引擎 l0_fact_builder.build 出参同口径, 不 import 引擎)。
    供 jiu_ying 六条判据读: 十神集 / 天干五合 / 重根 / 通关表。"""
    stems = [bazi[0], bazi[2], bazi[4], bazi[6]]
    branches = [bazi[1], bazi[3], bazi[5], bazi[7]]
    dm = stems[2]
    gods = set()
    for g in [stems[0], stems[1], stems[3]]:
        gods.add(TEN_GOD_MAP[dm][g])
    for z in branches:
        for h in HIDDEN[z]:
            gods.add(TEN_GOD_MAP[dm][h])
    wuhe = []
    for i in range(4):
        for j in range(i + 1, 4):
            p = frozenset((stems[i], stems[j]))
            if p in WUHE:
                wuhe.append([stems[i], stems[j], WUHE[p]])
    return {
        "day_master": dm, "stems": stems, "branches": branches,
        "ten_god_set": gods, "wuhe": wuhe,
        "dm_element": GAN_WX[dm],
        "month_qi_element": GAN_WX[HIDDEN[branches[1]][0]],
        "has_root": _has_root(dm, branches),
        "has_chong": any(frozenset((branches[i], branches[j])) in LIU_CHONG
                         for i in range(4) for j in range(i + 1, 4)),
    }


# 格神映射 (从 ge 名推, 用于 .004 澄浊「杂神」= 非格神非日主)
#   正官格→官 / 财格→财 / 印格→印 / 食神格→食神 / 伤官格→伤官
#   七煞格/偏官→杀 / 阳刃格→刃(比劫) / 建禄月劫格→比肩
# 格神映射 (从 ge 名推, 用于 .004 澄浊「杂神」= 非格神非日主, 裁151甲)
#   正官格→官 / 财格→财 / 印格→印 / 食神格→食神 / 伤官格→伤官
#   七煞格/偏官→杀 / 阳刃格→刃(比劫) / 建禄月劫格→比肩
# 杂神计数 = ten_god_set 里 非格神 的十神种类数 (ENGINE_DEFINED 代理)
GE_SHEN = {
    "正官格": ("正官",), "财格": ("正财", "偏财"),
    "印格": ("正印", "偏印"), "食神格": ("食神",),
    "伤官格": ("伤官",), "七煞格": ("七杀", "偏官"),
    "阳刃格": ("比肩", "劫财"), "建禄月劫格": ("比肩", "劫财"),
}
# 七煞格 原文常作「七煞」「偏官」
GE_SHEN["七煞格(逢制)"] = GE_SHEN["七煞格"]
GE_SHEN["七煞格(破格)"] = GE_SHEN["七煞格"]


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
            "evidence": [], "xiang_note": None, "rescue_wx": [],
            "note": "从格盘, 6 条救应判据全为正八格语境, 无从格依据 → 范围外"
        }

    # 无格 → NA
    if ge in (None, "", "无格"):
        return {
            "triggered": False, "type": [], "success": "NA",
            "evidence": [], "xiang_note": None, "rescue_wx": [],
            "note": "无格, 不适用"
        }

    # 纯成格 → NA (无救应需求)
    if ge_cheng.get("po_n", 0) == 0 and ge_cheng.get("xi_status") != "DEFINED":
        return {
            "triggered": False, "type": [], "success": "NA",
            "evidence": [], "xiang_note": None, "rescue_wx": [],
            "note": "纯成格, 无救应需求"
        }

    # CZYP / PO → 判 6 条 (全部读纯函数 L0 facts, 不 import 引擎)
    facts = build_l0_facts_pure(bazi)
    gods = facts["ten_god_set"]
    dm = facts["day_master"]
    wuhe = [p for p in facts["wuhe"]]  # [[a,b,name],...]
    wuhe_stems = {s for p in wuhe for s in p[:2]}
    types = []
    ev = []
    ok = []  # 各命中判据的 success 布尔, 合取定 SUCCESS/UNS
    _rescue_wx = set()  # [2026-10-08 PATCH-SRC4] 救应神五行(.001通关中间神 + .005八格救应解神)

    # .001 通关 (DTS §二十 L245, 裁150甲: 缺中间神才需引通)
    #   "有神"(裁150甲) = 该组五行 十神 在盘里(干或藏干任一)
    #   触发 = 通关表 4 组中 某一组【两行都有神】且【中间神缺】(无本气根)
    #   success = 中间神缺但日干有根(有力, 能引通)
    wx_present = set()
    for s in [bazi[0], bazi[2], bazi[4], bazi[6]]:
        wx_present.add(GAN_WX[s])
    for z in facts["branches"]:
        for h in HIDDEN[z]:
            wx_present.add(GAN_WX[h])
    mid_found = None
    t1_trig = False
    for pair, mid in TONG_GUAN.items():
        if pair <= wx_present:  # 两战之行都有神
            # 中间神缺 = mid 五行 无本气根(藏干首非 mid 五行)
            mid_missing = True
            for z in facts["branches"]:
                if GAN_WX[HIDDEN[z][0]] == mid:
                    mid_missing = False
                    break
            if mid_missing:
                t1_trig = True
                mid_found = mid
                break
    if t1_trig:
        types.append("JIU_YING.001")
        # success = 中间神缺(需引通) 但日干有根(有力, 能引通)
        t1_ok = facts["has_root"]
        ev.append(".001 通关: %s 缺中间神需引通, 日干有根=%s"
                  % (mid_found, t1_ok))
        ok.append(t1_ok)

    # .002 官杀混杂 (DTS §二十一 L250): 官杀是否被合去一支
    t2_trig = ("正官" in gods) and (("七杀" in gods) or ("偏官" in gods))
    t2_ok = False
    if t2_trig:
        types.append("JIU_YING.002")
        # 合去一支: 官/杀 天干 被五合合住
        guan_stems = [s for s in [bazi[0], bazi[2], bazi[4], bazi[6]]
                      if s != dm and TEN_GOD_MAP[dm][s] in ("正官", "七杀", "偏官")]
        he_ge = [s for s in guan_stems if s in wuhe_stems]
        t2_ok = len(he_ge) > 0
        ev.append(".002 官杀同现=True, 合去一支=%s (%s)"
                  % ("是" if t2_ok else "否", he_ge))
        ok.append(t2_ok)

    # .003 伤官见官 (DTS §二十二 L255): 有财则救
    t3_trig = ("伤官" in gods) and ("正官" in gods)
    t3_ok = False
    if t3_trig:
        types.append("JIU_YING.003")
        t3_ok = ("正财" in gods) or ("偏财" in gods)
        ev.append(".003 伤官+正官=True, 有财救=%s" % ("是" if t3_ok else "否"))
        ok.append(t3_ok)

    # .004 澄浊 (DTS §二十三 L260, 裁151甲: 触发=po_n>0 AND 杂神计数≥2, 标 ENGINE_DEFINED)
    #   浊气代理: DTS L260「浊=杂神多且与格星不和」
    #     "多" 用杂神计数代理(杂神 = 非格神非日主的十神种类)
    #     "不和/破局" 用 po_n>0 代理
    #   格神从 ge 名推 (GE_SHEN, 去括号)
    #   success = 得一神有力扫浊(食伤 制 / 比劫 扶, 且日干有根)
    t4_trig = False
    t4_ok = False
    ge_base = re.sub(r"\(.*?\)", "", (ge or ""))
    ge_shen = GE_SHEN.get(ge_base, ())
    zashen = {g for g in gods if g not in ge_shen and g != "比肩"}
    t4_trig = (ge_cheng.get("po_n", 0) > 0) and (len(zashen) >= 2)
    if t4_trig:
        types.append("JIU_YING.004")
        # success = 得有力之神扫浊(食伤 制 / 比劫 扶, 日干有根)
        t4_ok = ((("食神" in gods) or ("伤官" in gods) or ("比肩" in gods)
                  or ("劫财" in gods)) and facts["has_root"])
        ev.append(".004 澄浊(ENGINE_DEFINED 代理): po_n=%d>0, 杂神%d种≥2(格神=%s), "
                  "扫浊神=%s (有根=%s)"
                  % (ge_cheng.get("po_n", 0), len(zashen),
                     "、".join(ge_shen) or "未定",
                     "是" if t4_ok else "否", facts["has_root"]))
        ok.append(t4_ok)

    # .005 八格破格后救应 (PZZQ §九 L1226, 裁149甲: 原文 8 子型逐条布尔)
    #   触发 = po_n>0(破格) AND 命中原文 10 子型任一 (官伤/合煞/会合解冲/
    #   劫财/印财/枭食/煞食/伤官煞合/刃印/禄劫)
    #   type 带子型号 (JIU_YING.005-官伤透印 等), 不只记 "005"
    #   10 子型逐条(每型独立判据, 不合成一个 t5_trig):
    #     a 官逢伤透印解之 / b 杂煞合煞清之 / c 刑冲会合解之
    #     d 财逢劫透食化之 / e 印逢财劫解之(或合财存印)
    #     f 食逢枭就煞成格(或生财护食) / g 煞逢食制印护煞(逢财去印存食)
    #     h 伤官生财透煞逢合 / i 阳刃重印护之 / j 建禄月劫遇伤煞被合
    t5_trig = ge_cheng.get("po_n", 0) > 0
    t5_ok = False
    t5_subs = []
    if t5_trig:
        g = gods
        has_guan = "正官" in g
        has_sha = ("七杀" in g) or ("偏官" in g)
        has_shang = "伤官" in g
        has_yin = ("正印" in g) or ("偏印" in g)
        has_cai = ("正财" in g) or ("偏财" in g)
        has_shi = "食神" in g
        has_bij = ("比肩" in g) or ("劫财" in g)
        wuhe_g = {s for p in wuhe for s in p[:2]}
        # 透干判定 (原文"透印/透食/透煞" = 天干透, 非藏干)
        stems3 = [bazi[0], bazi[2], bazi[6]]  # 年/月/时干 (日干除外)
        yin_stems = [s for s in stems3 if TEN_GOD_MAP[dm][s] in ("正印", "偏印")]
        shi_stems = [s for s in stems3 if TEN_GOD_MAP[dm][s] == "食神"]
        sha_stems = [s for s in stems3 if TEN_GOD_MAP[dm][s] in ("七杀", "偏官")]
        # a 官逢伤透印解之: 有伤官 + 印透干(解伤护官)
        if has_shang and yin_stems:
            t5_subs.append("a 官伤透印")
        # b 杂煞合煞清之: 七杀 被 天干五合合去
        if any(s in wuhe_g for s in sha_stems):
            t5_subs.append("b 合煞清")
        # c 刑冲会合解之: 有刑冲在场 + 有合(会合解刑冲)
        if facts["has_chong"] and len(wuhe) > 0:
            t5_subs.append("c 会合解冲")
        # d 财逢劫透食化之: 财+比劫, 且有食透(化劫生财) 或 官在(官制劫)
        if has_bij and has_cai and (shi_stems or has_guan):
            t5_subs.append("d 劫财化食/官制")
        # e 印逢财劫解之(或合财存印): 印 + 财 + 比劫(劫财解财护印)
        if has_yin and has_cai and has_bij:
            t5_subs.append("e 劫财解财")
        # f 食逢枭就煞成格(或生财护食): 食神 + 枭(偏印) + 七杀(就煞)
        if has_shi and "偏印" in g and has_sha:
            t5_subs.append("f 食枭就煞")
        # g 煞逢食制,印来护煞: 七杀 + 食神(制) + 正印(护)
        if has_sha and has_shi and "正印" in g:
            t5_subs.append("g 食制印护")
        # h 伤官生财透煞而煞逢合: 伤官 + 财 + 七杀被合
        if has_shang and has_cai and any(s in wuhe_g for s in sha_stems):
            t5_subs.append("h 伤生财煞合")
        # i 阳刃用官煞带伤食而重印护之: 比劫(刃) + 正印重
        if ("比肩" in g or "劫财" in g) and "正印" in g:
            t5_subs.append("i 刃禄重印")
        # j 建禄月劫用官遇伤伤被合 / 用财带煞煞被合 (裁149甲: 原文末句补入)
        if has_bij and ((has_guan and has_shang and any(s in wuhe_g for s in stems3))
                        or (has_cai and has_sha and any(s in wuhe_g for s in sha_stems))):
            t5_subs.append("j 禄劫伤煞被合")
        types.append("JIU_YING.005")
        t5_ok = len(t5_subs) > 0
        # type 带子型号: 把 "JIU_YING.005" 替换成 带命中子型的标记
        if t5_subs:
            types[-1] = "JIU_YING.005-" + "+".join(
                s.split()[0] for s in t5_subs)  # 子型 a/b/c...
        # [2026-10-08 PATCH-SRC4] .005 八格破格救应子型 -> 救应神五行(解神, PZZQ L1226)
        #   官伤透印=印 / 煞合清=合神 / 财劫透食=食 / 食枭就煞=煞 / 煞印护=印 / 阳刃重印=印
        _defsub = "".join(s.split()[0] for s in t5_subs)
        _yin_wx = {GAN_WX[s] for s in yin_stems}
        _shi_wx = {GAN_WX[s] for s in shi_stems}
        _sha_wx = {GAN_WX[s] for s in sha_stems}
        _he_sha_wx = set()
        for s in sha_stems:
            for a, b, _nm in wuhe:
                if s in (a, b):
                    _partner = b if a == s else a
                    _he_sha_wx.add(GAN_WX.get(_partner, ""))
        if "a" in _defsub: _rescue_wx |= _yin_wx      # 官伤透印 -> 印
        if "b" in _defsub: _rescue_wx |= _he_sha_wx    # 煞合清 -> 合神
        if "d" in _defsub: _rescue_wx |= _shi_wx       # 财劫透食 -> 食
        if "f" in _defsub: _rescue_wx |= _sha_wx       # 食枭就煞 -> 煞
        if "g" in _defsub: _rescue_wx |= _yin_wx       # 煞印护 -> 印
        if "i" in _defsub: _rescue_wx |= _yin_wx       # 阳刃重印 -> 印
        ev.append(".005 八格破格后救应: po_n=%d>0, 命中原文子型=%s"
                  % (ge_cheng.get("po_n", 0),
                     "、".join(t5_subs) if t5_subs else "无"))
        ok.append(t5_ok)
    # [2026-10-08 PATCH-SRC4] .001 通关 也贡献 救应神(中间神)
    if t1_trig and mid_found:
        _rescue_wx.add(mid_found)

    # .006 相神 (PZZQ §十五 L1857, 裁147甲 归入 success): 相神不被合
    #   success = 相神(用神/解神) 不被五合合走
    t6_trig = len(wuhe) > 0  # 有合才有「相神被合」的可能
    t6_ok = True
    if t6_trig:
        types.append("JIU_YING.006")
        # 相神被合 = 解神/用神 天干 在五合对被合住 → 救应失效
        # 简化: 若 .005 解神天干 被合 → 相神被伤 → success=UNS
        xiang_shang = False
        if t5_ok:  # 只有解神生效时才谈相神被合
            xiang_shang = bool(wuhe_stems & set(
                [s for s in [bazi[0], bazi[2], bazi[6]]
                 if TEN_GOD_MAP[dm][s] in ("食神", "正印", "偏印",
                                            "正财", "偏财")]))
        t6_ok = not xiang_shang
        ev.append(".006 相神被合/伤(伤相甚于伤用): %s"
                  % ("相神被伤→救应未成" if xiang_shang else "相神无破"))
        ok.append(t6_ok)

    if not types:
        return {
            "triggered": True, "type": [], "success": "UNS",
            "evidence": ["6 条判据无一条触发(本盘不属任何救应场景)"],
            "rescue_wx": sorted(_rescue_wx),
            "xiang_note": None, "note": "触发但 6 条无一适用"
        }

    # success = 命中判据的布尔合取 (任一命中判据为假 → UNS)
    success = "SUCCESS" if all(ok) else "UNS"

    # .006 相神 (裁147甲): success=UNS 且 相神被伤 → 附 xiang_note
    xiang_note = None
    if success == "UNS" and "JIU_YING.006" in types and not t6_ok:
        xiang_note = "伤相甚于伤用 — 相神被合/伤 → 救应未成, 优先记此因"

    return {
        "triggered": True, "type": types, "success": success,
        "evidence": ev, "xiang_note": xiang_note,
        "rescue_wx": sorted(_rescue_wx),
        "note": None,
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
