"""子平经典判据独立核验器 — 取格/成败（原典条文机读化）。

用途:
    以《子平真诠》原文（p0_v2 切片
    `FOUNDATION.MONTH_COMMAND.YUE_LING_GE_JU.001~014`、
    `STRUCTURE.GE_JU.CHENG_BAI.007/008/009`）为据，独立实现「月令取格」与
    「八格成败」的可机读判据，用来**核验** p0 引擎（engines/production_entry）
    的 ge_cheng 输出，不用引擎自身中间结果自证。

边界（诚实）:
    - 只判定原典明文、且不依赖身强弱的条款；依赖旺衰的条款标 NOT_EVALUABLE。
    - 原典未列之特殊格（从格/化气/曲直等）→ NOT_APPLICABLE，交引擎特格层。
    - 本模块不参与生产链路，只做审计。

原典依据（逐字）:
    取格: 「格之真者，月支之神，透于天干也。」（YUE_LING_GE_JU.001）
          「八字用神，专求月令，以日干配月令地支，而生克不同，格局分焉。」（.002）
          「如四季月生人，只当取土为格，不可言杂气财官；戊己日生于四季月者，
            当看人元透出天干者取格。」（CHENG_BAI.002）
          「至于建禄月劫羊刃，亦当看月令中人元透于天干者取格。」（CHENG_BAI.002）
    成败: CHENG_BAI.007（八格成）、.008（八格败）、.009（带忌/救应）。
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# ---- 基础表（子平十神/藏干/刑冲破害） ----
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

STEM_ELEM = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
             "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
STEM_YANG = {"甲": 1, "乙": 0, "丙": 1, "丁": 0, "戊": 1, "己": 0,
             "庚": 1, "辛": 0, "壬": 1, "癸": 0}

# 月支藏干（本气, 中气, 余气）——依通行子平藏干表
HIDDEN = {
    "子": ("癸",), "丑": ("己", "癸", "辛"), "寅": ("甲", "丙", "戊"),
    "卯": ("乙",), "辰": ("戊", "乙", "癸"), "巳": ("丙", "庚", "戊"),
    "午": ("丁", "己"), "未": ("己", "丁", "乙"), "申": ("庚", "壬", "戊"),
    "酉": ("辛",), "戌": ("戊", "辛", "丁"), "亥": ("壬", "甲"),
}

# 六冲 / 六害 / 六破 / 三刑（仅用于「刑冲破害」条款）
CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
         "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
HAI = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅",
       "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}
PO = {"子": "酉", "酉": "子", "丑": "辰", "辰": "丑", "寅": "亥", "亥": "寅",
      "卯": "午", "午": "卯", "巳": "申", "申": "巳", "未": "戌", "戌": "未"}
XING = {("寅", "巳"), ("巳", "申"), ("申", "寅"), ("丑", "戌"), ("戌", "未"),
        ("未", "丑"), ("子", "卯"), ("卯", "子"), ("辰", "辰"), ("午", "午"),
        ("酉", "酉"), ("亥", "亥")}

GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def ten_god(day_master: str, other: str) -> str:
    """日主 vs 他干的十神（同阴阳=偏，异阴阳=正；比劫不分正偏）。"""
    de, oe = STEM_ELEM[day_master], STEM_ELEM[other]
    same = STEM_YANG[day_master] == STEM_YANG[other]
    if de == oe:
        return "比肩" if same else "劫财"
    if GEN[de] == oe:
        return "食神" if same else "伤官"
    if KE[de] == oe:
        return "偏财" if same else "正财"
    if KE[oe] == de:
        return "七杀" if same else "正官"
    return "偏印" if same else "正印"


GE_NAME = {
    "正官": "正官格", "七杀": "七煞格", "正财": "财格", "偏财": "财格",
    "正印": "印格", "偏印": "印格", "食神": "食神格", "伤官": "伤官格",
    "比肩": "建禄月劫格", "劫财": "建禄月劫格",
}


def _pillars(p: Dict[str, List[str]]) -> List[Tuple[str, str]]:
    return [(p[k][0], p[k][1]) for k in ("year", "month", "day", "hour")]


def _zhengyan(p: Dict[str, List[str]]) -> Tuple[str, str]:
    ps = _pillars(p)
    return ps[2][0], ps[1][1]


def _transparent(p: Dict[str, List[str]]) -> List[str]:
    """透于天干的字（日干为日主，不计）。"""
    ps = _pillars(p)
    return [ps[0][0], ps[1][0], ps[3][0]]


def _hidden_visible(p: Dict[str, List[str]], b: str) -> List[str]:
    return list(HIDDEN.get(b, ()))


def derive_ge(p: Dict[str, List[str]]) -> Dict[str, object]:
    """月令取格（原典: 月支之神透于天干；四季月看人元透干；比劫→建禄月劫）。

    Returns:
        {"ge": str|None, "ten_god": str, "via": "透干"|"本气"|"四季土", "detail": str}
    """
    dm, mb = _zhengyan(p)
    hidden = _hidden_visible(p, mb)
    trans = set(_transparent(p))

    # 四季月(CHENG_BAI.002): 非土日主「只当取土为格」(本气土); 土日主看人元透干
    if mb in ("辰", "戌", "丑", "未") and STEM_ELEM[dm] != "土":
        chosen, via = hidden[0], "四季土格"
    else:
        # 透出优先：按 本气→中气→余气 顺序找第一个透出的藏干
        chosen = None
        for h in hidden:
            if h in trans:
                chosen = h
                break
        if chosen is None:
            chosen = hidden[0]  # 本气
        via = "透干" if chosen in trans else "本气"

    tg = ten_god(dm, chosen)

    # 四季月（辰戌丑未）且藏干有透 → 仍按透干取格（原典「看人元透出天干者取格」）
    if mb in ("辰", "戌", "丑", "未") and chosen in trans:
        via = "四季土透干"

    ge = GE_NAME.get(tg)
    if tg == "比肩":
        ge = "建禄月劫格"
    elif tg == "劫财":
        # 阳干月支为刃（甲卯/丙午/戊午/庚酉/壬子）→ 阳刃格，其余为月劫
        if STEM_YANG[dm] and mb in ("卯", "午", "酉", "子"):
            ge = "阳刃格"
        else:
            ge = "建禄月劫格"
    evidence = f"透干{chosen}" if chosen in trans else f"本气{chosen}（未透干）"
    return {"ge": ge, "ten_god": tg, "via": via, "stem": chosen,
            "detail": f"月支{mb}藏{'/'.join(hidden)}，{evidence}({tg}) → {ge}"}


def _branch_relations(p: Dict[str, List[str]], b: str) -> Dict[str, List[str]]:
    """月支 b 与其余三支的 冲/害/破/刑 关系。"""
    others = [x[1] for x in _pillars(p)]
    out = {"冲": [], "害": [], "破": [], "刑": []}
    for o in others:
        if o == b:
            continue
        if CHONG.get(b) == o:
            out["冲"].append(o)
        if HAI.get(b) == o:
            out["害"].append(o)
        if PO.get(b) == o:
            out["破"].append(o)
        if (b, o) in XING or (o, b) in XING:
            out["刑"].append(o)
    return out


def _has_ten_god(p: Dict[str, List[str]], tg: str) -> bool:
    """该十神是否出现在天干（含藏干）——「见/透」的宽松口径。"""
    dm = _zhengyan(p)[0]
    for s in _transparent(p):
        if ten_god(dm, s) == tg:
            return True
    for s, _b in _pillars(p):
        for h in HIDDEN.get(_b, ()):
            if ten_god(dm, h) == tg:
                return True
    return False


def _trans_ten_god(p: Dict[str, List[str]], tg: str) -> bool:
    """该十神是否透于天干。"""
    dm = _zhengyan(p)[0]
    return any(ten_god(dm, s) == tg for s in _transparent(p))


def judge_cheng_bai(p: Dict[str, List[str]]) -> Dict[str, object]:
    """按原典 CHENG_BAI.007/.008 判定成败（仅可机读条款）。"""
    dm, mb = _zhengyan(p)
    ge = derive_ge(p)
    name = ge["ge"]
    rel = _branch_relations(p, mb)
    broken = any(rel[k] for k in ("冲", "害", "破", "刑"))

    clauses: List[Dict[str, str]] = []
    state = "NOT_EVALUABLE"

    def add(res: str, text: str) -> None:
        clauses.append({"result": res, "clause": text})

    # 官格（正官）
    if name == "正官格":
        cai, yin = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财"), _has_ten_god(p, "正印") or _has_ten_god(p, "偏印")
        shang = _has_ten_god(p, "伤官") or _has_ten_god(p, "食神")
        if cai or yin:
            add("CHENG", "官逢财印")
        if not broken and (cai or yin):
            add("CHENG", "无刑冲破害")
        if shang:
            add("BAI", "官逢伤克")
        if broken:
            add("BAI", "官逢刑冲破害")
        if shang or broken:
            state = "BAI"
        elif cai or yin:
            state = "CHENG"
    # 财格
    elif name == "财格":
        guan = _has_ten_god(p, "正官") or _has_ten_god(p, "七杀")
        sha = _has_ten_god(p, "七杀")
        if guan:
            add("CHENG", "财生官旺")
        if sha:
            add("BAI", "财透七煞")
        if sha:
            state = "BAI"
        elif guan:
            state = "CHENG"
    # 印格
    elif name == "印格":
        sha = _has_ten_god(p, "七杀")
        guan = _has_ten_god(p, "正官")
        cai = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财")
        if sha:
            add("CHENG", "印轻逢煞")
        if sha and guan:
            add("CHENG", "官印双全")
        if cai and not sha:
            add("NOT_EVALUABLE", "印轻逢财(须辨印轻重)")
        if sha:
            state = "CHENG"
    # 食神格
    elif name == "食神格":
        cai = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财")
        xiao = _has_ten_god(p, "偏印")
        sha = _has_ten_god(p, "七杀")
        if cai:
            add("CHENG", "食神生财")
        if xiao:
            add("BAI", "食神逢枭")
        if cai and sha:
            add("BAI", "生财露煞")
        if xiao or (cai and sha):
            state = "BAI"
        elif cai:
            state = "CHENG"
    # 七煞格
    elif name == "七煞格":
        zhi = any(t in ("食神", "伤官", "正印", "偏印", "阳刃") for t in [])
        cai = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财")
        if cai:
            add("NOT_EVALUABLE", "七煞逢财(须辨有无制)")
        if broken:
            add("BAI", "七煞逢冲")
        if broken:
            state = "BAI"
    # 伤官格
    elif name == "伤官格":
        cai = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财")
        guan = _has_ten_god(p, "正官")
        yin = _has_ten_god(p, "正印") or _has_ten_god(p, "偏印")
        if cai:
            add("CHENG", "伤官生财")
        if yin:
            add("CHENG", "伤官佩印")
        if guan and not cai and not yin:
            add("BAI", "伤官见官(无财无印)")
        if cai:
            state = "CHENG"
        elif guan and not yin:
            state = "BAI"
    # 阳刃格
    elif name == "阳刃格":
        guan = _has_ten_god(p, "正官") or _has_ten_god(p, "七杀")
        shang = _has_ten_god(p, "伤官")
        if guan and not shang:
            add("CHENG", "阳刃透官煞，不见伤官")
        if not guan:
            add("BAI", "阳刃无官煞")
            state = "BAI"
        elif not shang:
            state = "CHENG"
    # 建禄月劫格
    elif name == "建禄月劫格":
        guan = _has_ten_god(p, "正官")
        cai = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财")
        sha = _has_ten_god(p, "七杀")
        if guan and cai:
            add("CHENG", "透官逢财")
        if cai and _has_ten_god(p, "食神"):
            add("CHENG", "透财逢食伤")
        if not guan and not cai and sha:
            add("BAI", "建禄月劫无财官透煞")
            state = "BAI"
        elif guan or cai:
            state = "CHENG"

    return {
        "ge": name,
        "state": state,
        "clauses": clauses,
        "broken": broken,
        "relations": rel,
        "basis": ["STRUCTURE.GE_JU.CHENG_BAI.007", "STRUCTURE.GE_JU.CHENG_BAI.008"],
    }


# ============================================================
# 旺衰（身强弱）——得令/得地/得势 三才合参 + 成局，不执月令一端
# ============================================================
# 原典依据：
#   STATE.WANG_SHUAI.PAN_DUAN_FA.001「阴阳顺逆之说…其法不可执一」
#   STATE.WANG_SHUAI.DE_LING.001「不必论当令不令，只论取最多最旺」
#   STATE.WANG_SHUAI.DE_LING.002「月令乃提纲之府…人元为用事之神」
#   STATE.WANG_SHUAI.DE_DI.001「天地顺遂而精粹者昌」/ DE_DI.002「地生天者，天衰怕冲」
#   STATE.WANG_SHUAI.DE_SHI.001「强众而敌寡者，势在去其寡」（得势=党众）
#   STATE.WANG_SHUAI.SHUAI.003「日主孤立无气，无地人元，绝无一毫生扶…乃为真从」

SHENG_ME = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}  # 生我者

WANG_SHUAI_BASIS = [
    "STATE.WANG_SHUAI.DE_LING.001",
    "STATE.WANG_SHUAI.DE_LING.002",
    "STATE.WANG_SHUAI.DE_DI.001",
    "STATE.WANG_SHUAI.DE_SHI.001",
    "STATE.WANG_SHUAI.PAN_DUAN_FA.001",
]

# 地支三合 / 三会（成局则党众之力按局论，不按单支论）
_SANHE = [("申", "子", "辰", "水"), ("亥", "卯", "未", "木"),
          ("寅", "午", "戌", "火"), ("巳", "酉", "丑", "金")]
_SANHUI = [("寅", "卯", "辰", "木"), ("巳", "午", "未", "火"),
           ("申", "酉", "戌", "金"), ("亥", "子", "丑", "水")]


def _branch_elem(b: str) -> str:
    return STEM_ELEM[HIDDEN[b][0]]


def _is_help(elem: str, dm_elem: str) -> bool:
    """比劫(同我)或印(生我)为帮身；财官食伤为耗身。"""
    return elem == dm_elem or SHENG_ME[dm_elem] == elem


def _detect_ju(branches: List[str]) -> List[Tuple[str, str]]:
    """成局：三支齐备才算（半合不算）。返回 [(局五行, '三合/三会')]。"""
    out: List[Tuple[str, str]] = []
    bset = set(branches)
    for a, b, c, e in _SANHE:
        if {a, b, c} <= bset:
            out.append((e, "三合"))
    for a, b, c, e in _SANHUI:
        if {a, b, c} <= bset:
            out.append((e, "三会"))
    return out


def _ling_score(p: Dict[str, List[str]]) -> Tuple[int, List[str]]:
    """得令分：月支**本气**人元用事之神是否帮身（+3 / -3）。

    原典 DE_LING.002「人元为用事之神」——月令之用事以本气为主（节气先后之
    浅深需节气时刻，三柱数据不足，不据中气/余气冒充得令，只记于 reasons）。
    """
    dm, mb = _zhengyan(p)
    dm_e = STEM_ELEM[dm]
    hidden = HIDDEN[mb]
    main = hidden[0]
    # 月令受冲：提纲之根被冲，得令打折（DE_DI.002「天衰怕冲…根拔而祸更甚」）
    clashed = any(p[pos][1] == CHONG[mb] for pos in ("year", "day", "hour"))
    if _is_help(STEM_ELEM[main], dm_e):
        if clashed:
            return 1, [f"得令：{mb}月{main}用事，{ten_god(dm, main)}帮身，"
                       f"然月支{mb}被{CHONG[mb]}冲，令根受损，得令减等"]
        return 3, [f"得令：{mb}月{main}用事，{ten_god(dm, main)}帮身"]
    extra = ""
    for h in hidden[1:]:
        if _is_help(STEM_ELEM[h], dm_e):
            extra = f"（藏{h}{ten_god(dm, h)}，然非用事之神，不作得令）"
            break
    return -3, [f"失令：{mb}月{main}用事，{ten_god(dm, main)}不帮身{extra}"]


def _di_score(p: Dict[str, List[str]]) -> Tuple[int, List[str]]:
    """得地分：四支通根（本气 2 / 中气 1 / 余气 0.5，封顶 3）；无根 0。

    原典 DE_DI.001「有根无根，俱要天覆地载」——有根方为得地。
    """
    dm = _zhengyan(p)[0]
    dm_e = STEM_ELEM[dm]
    pts = 0.0
    reasons: List[str] = []
    for pos in ("year", "month", "day", "hour"):
        b = p[pos][1]
        for i, h in enumerate(HIDDEN[b]):
            if STEM_ELEM[h] == dm_e:  # 通根只看同五行（比劫根），印根另计于得势
                w = (2.0, 1.0, 0.5)[i] if len(HIDDEN[b]) >= 3 else (2.0, 1.0)[i]
                pts += w
                reasons.append(f"得地：{pos}支{b}藏{h}({('本','中','余')[i] if i < 3 else '余'})为根")
                break
    pts = int(min(pts, 2.0))
    if pts == 0:
        reasons.append("失地：四支无日主本气根")
    return pts, reasons


def _shi_score(p: Dict[str, List[str]]) -> Tuple[int, List[str]]:
    """得势分：天干（除日主）党众 —— 比劫/印 +1（封顶 +2），财官食伤 -1（封底 -2）。"""
    dm = _zhengyan(p)[0]
    dm_e = STEM_ELEM[dm]
    ps = _pillars(p)
    plus = minus = 0
    helpers: List[str] = []
    drainers: List[str] = []
    for i, (s, _b) in enumerate(ps):
        if i == 2:  # 日干为日主本身
            continue
        if _is_help(STEM_ELEM[s], dm_e):
            plus += 1
            helpers.append(s)
        else:
            minus += 1
            drainers.append(s)
    score = min(plus, 2) - min(minus, 2)
    reasons = [f"党众：天干帮身{'、'.join(helpers) or '无'}（{plus}），"
               f"克泄{'、'.join(drainers) or '无'}（{minus}）"]
    return score, reasons


def judge_strength(p: Dict[str, List[str]]) -> Dict[str, object]:
    """身强弱判定（三才 + 成局）。

    Returns:
        {"conclusion": "STRONG"|"MODERATE"|"WEAK", "score": int,
         "get_ling_score": int, "de_di_score": int, "dangzhong_score": int,
         "ju_score": int, "reasons": list[str], "basis": list[str],
         "ju": list[(elem, kind)]}
    """
    dm, mb = _zhengyan(p)
    dm_e = STEM_ELEM[dm]
    ling, r1 = _ling_score(p)
    di, r2 = _di_score(p)
    shi, r3 = _shi_score(p)
    branches = [p[k][1] for k in ("year", "month", "day", "hour")]
    jus = _detect_ju(branches)
    ju_score = 0
    ju_same_party = False
    for elem, kind in jus:
        if _is_help(elem, dm_e):
            ju_score += 2
            ju_same_party = True
            r3.append(f"成局：{kind}成{elem}局，与日主同党")
        else:
            ju_score -= 2
            r3.append(f"成局：{kind}成{elem}局，非日主之党")
    if ju_same_party:
        # 三合/三会成局同党 → 局代月令（月支本气不再作对立降分；
        # 原典「日元太旺」类盘（PZZQ L984 王克敏造 申子辰水局）皆以成局论旺）。
        if ling < 3:
            r1.append("成局同党，局代月令（月支本气失权）")
            ling = 3
    total = ling + di + shi + ju_score
    if total >= 5:
        concl = "STRONG"
    elif total >= 2:
        concl = "MODERATE"
    else:
        concl = "WEAK"
    return {
        "conclusion": concl,
        "score": total,
        "get_ling_score": ling,
        "de_di_score": di,
        "dangzhong_score": shi,
        "ju_score": ju_score,
        "ju": jus,
        "reasons": r1 + r2 + r3,
        "basis": list(WANG_SHUAI_BASIS),
    }
