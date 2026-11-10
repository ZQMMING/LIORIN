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
    """月令取格（2026-11-10 对齐 bac206b8 裁决/审计文档§六: 本气立格为格名，透干只定
    「格之真假」——YUE_LING_GE_JU.001「格之真者，月支之神，透于天干也」；月令本气为
    比劫时格名=禄/刃，用神另看人元透干配合。四季月非土日主本气土）。

    Returns:
        {"ge": str|None, "ten_god": str, "via": "透干"|"本气"|"四季土格", "detail": str}
    """
    dm, mb = _zhengyan(p)
    hidden = _hidden_visible(p, mb)
    trans = set(_transparent(p))

    # 四季月(CHENG_BAI.002): 非土日主「只当取土为格」(本气土); 土日主本气=比劫→禄刃条款
    if mb in ("辰", "戌", "丑", "未") and STEM_ELEM[dm] != "土":
        chosen, via = hidden[0], "四季土格"
    else:
        # 2026-11-10 回撤「透出优先」: 透干不定格名只定真假（bac206b8 revert PATCH-GE-TOU）
        chosen = hidden[0]
        via = "透干" if chosen in trans else "本气"

    tg = ten_god(dm, chosen)

    ge = GE_NAME.get(tg)
    if tg == "比肩":
        ge = "建禄月劫格"
    elif tg == "劫财":
        # 阳干月支为刃（甲卯/丙午/戊午/庚酉/壬子）→ 阳刃格，其余为月劫
        if STEM_YANG[dm] and mb in ("卯", "午", "酉", "子"):
            ge = "阳刃格"
        else:
            ge = "建禄月劫格"
    # 刃表特例(V7.83 裁决锚 PZZQ L4505): 戊日午月本气丁=正印, 仍作阳刃论——
    #   阳刃以禄前一位支论, 不问本气十神: 甲刃卯/丙刃午/戊刃午/庚刃酉/壬刃子。
    #   (其余阳干刃支本气即劫财, 上分支已覆盖; 此特例只实际改写 戊午。)
    _RENGE = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
    if ge != "阳刃格" and STEM_YANG[dm] and _RENGE.get(dm) == mb:
        ge = "阳刃格"
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



def _count_ten_god(p: Dict[str, List[str]], tgs) -> int:
    """统计十神（含藏干）出现次数——用于「轻/重」量词判据（印轻/印多/财轻比重）。"""
    dm = _zhengyan(p)[0]
    n = 0
    for s in _transparent(p):
        if ten_god(dm, s) in tgs:
            n += 1
    for _s, b in _pillars(p):
        for h in HIDDEN.get(b, ()):
            if ten_god(dm, h) in tgs:
                n += 1
    return n

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
        # 2026-11-10 对齐败句(CHENG_BAI.008 L1145「官逢伤克刑冲」): 伤克=伤官【透干】克官
        # (引擎 V7.170 锚 L2825「透丁则伤官, 逢午不作此例」; 食神不克官、藏干伤官力微不作伤克);
        # 刑冲=月令官星逢刑冲(徐注 L1149「冲官星者，非伤即刃，同为破格」);
        # 害/破不在败句、只破成句「无刑冲破害」(.007) → 既有财印又只害破 = 成句不备败句未触
        # → NOT_EVALUABLE(宁缺勿猜)。
        shang = _trans_ten_god(p, "伤官")
        _chong_xing = bool(rel["冲"] or rel["刑"])
        if shang:
            add("BAI", "官逢伤克(伤官透干)")
            state = "BAI"
        elif _chong_xing:
            add("BAI", "官逢刑冲")
            state = "BAI"
        elif (cai or yin) and not broken:
            add("CHENG", "官逢财印又无刑冲破害")
            state = "CHENG"
        elif cai or yin:
            add("NOT_EVALUABLE", "官逢财印然月令有害破(败句只载伤克刑冲)")
    # 财格
    elif name == "财格":
        guan = _has_ten_god(p, "正官") or _has_ten_god(p, "七杀")
        # 2026-11-10: 「财透七煞」须煞透干(徐注 L1151「财透七煞，则财不为我用而党煞」;
        # 引擎 V7.169 透口径锚 L1145/L1243/L1246/L1492, 藏支煞有制不破 毛状元反例 L3487)
        sha = _trans_ten_god(p, "七杀")
        if guan:
            add("CHENG", "财生官旺")
        if sha:
            add("BAI", "财透七煞")
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
        # V7.189 量词落地: 「印轻逢财」败(.008) vs 「印多逢财而财透根轻」成(.007)
        _yin_n = _count_ten_god(p, ("正印", "偏印"))
        _cai_t = _trans_ten_god(p, "正财") or _trans_ten_god(p, "偏财")
        if cai and not sha and _yin_n <= 1:
            add("BAI", "印轻逢财(印%d见)" % _yin_n)
            state = "BAI"
        elif cai and not sha and _yin_n >= 3:
            add("CHENG", "印多逢财(印重, 财透根轻不为害)" if _cai_t else "印多逢财")
            state = "CHENG"
        elif cai and not sha:
            add("NOT_EVALUABLE", "印逢财(须辨印轻印重)")
        if sha:
            state = "CHENG"
    # 食神格
    elif name == "食神格":
        # V7.198 生财露煞/食神生财口径(PZZQ L1132 徐注「月令食神，四柱见财，为食神生财，
        # 格之正也。若四柱透煞，则食神制煞为用，忌财党煞，故以无财为美」+ L1115 成句
        # 「食神生财，或食带煞而无财，弃食就煞而透印，食格成也」+ L1154「露煞则财转而生煞」):
        # 成句/败句的财都是【见】(含藏干), 煞按透干(「露煞」), 枭=偏印透干。
        # 旧透干口径系把 PZ-0118(枭夺食·财制枭语境「无财为救应」)误挪用, 已纠正。
        cai = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财")
        xiao = _trans_ten_god(p, "偏印")
        sha = _trans_ten_god(p, "七杀")
        yin_t = _trans_ten_god(p, "正印") or _trans_ten_god(p, "偏印")
        if cai:
            add("CHENG", "食神生财")
        if sha and not cai and yin_t:
            # 成句: 食带煞而无财, 弃食就煞而透印(转败为成)
            add("CHENG", "弃食就煞透印")
        if xiao:
            add("BAI", "食神逢枭")
        if cai and sha:
            add("BAI", "生财露煞")
        if xiao or (cai and sha):
            state = "BAI"
        elif sha and not cai and yin_t:
            state = "CHENG"
        elif cai:
            state = "CHENG"
    # 七煞格
    elif name == "七煞格":
        # V7.189: 「七煞逢财无制」败(.008) / 「身强七煞逢制」成(.007)
        # V7.198 制化=食制/伤驾/印化(V7.190 引擎 has_zhi 镜像, 透干口径):
        # 藏支食神不构成「逢制」的机读判据。
        zhi = (_trans_ten_god(p, "食神") or _trans_ten_god(p, "伤官")
               or _trans_ten_god(p, "正印") or _trans_ten_god(p, "偏印"))
        shi_t = _trans_ten_god(p, "食神")
        shang_t = _trans_ten_god(p, "伤官")
        # 2026-11-10: 煞党煞之财须透干(徐注 L1155「财党煞攻身」; 引擎 V7.169 透口径)
        cai = _trans_ten_god(p, "正财") or _trans_ten_god(p, "偏财")
        _st7 = judge_strength(p).get("conclusion", "")
        if cai and not zhi:
            add("BAI", "七煞逢财无制")
            state = "BAI"
        elif cai and zhi and _st7 == "STRONG":
            add("CHENG", "身强七煞逢制")
            state = "CHENG"
        elif cai and (shi_t or shang_t):
            # V7.199: 救应篇明文(PZZQ L1210/L1212 谭延闿案亲证): 食神制煞而中隔以财,
            # 「财逢煞而食神制煞以生, 有救应, 即是败中有成, 为贵也」——食/伤制神透+
            # 财透党煞+非身强(不满足 .007 成句) -> 败中有成, 用神专取食神。
            add("CHENG_ZHONG_YOU_PO", "食神制煞而中隔以财, 败中有成(救应)")
            state = "CHENG_ZHONG_YOU_PO"
        elif cai and zhi:
            add("NOT_EVALUABLE", "七煞逢财有制(印化+财透, 须辨制神有力)")
        # 2026-11-10 删「七煞逢冲」: 败格权威句(.008/STRUCTURE_GE_JU_CHENG_BAI_008 L258)
        # 七煞只有「逢财无制」, 无逢冲条款; 旧条款月支任意刑冲害破都触发=过度延伸。
    # 伤官格
    elif name == "伤官格":
        cai = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财")
        guan = _trans_ten_god(p, "正官")
        yin = _has_ten_god(p, "正印") or _has_ten_god(p, "偏印")
        sha_t = _trans_ten_god(p, "七杀")
        # 2026-11-10 金水例外(徐注 L1156「惟金水伤官，金寒水冷，调候为急，可以见官」):
        # 窄口径=金日主(庚辛)生于水月(亥子)——金寒水冷专指冬月金伤官。
        _jshui = STEM_ELEM[dm] == "金" and mb in ("亥", "子")
        if cai:
            add("CHENG", "伤官生财")
        if yin:
            add("CHENG", "伤官佩印")
        if guan and not cai and not yin and not _jshui:
            add("BAI", "伤官见官(无财无印)")
        if cai and sha_t:
            add("BAI", "伤官生财带煞(财转生煞)")
        if cai and sha_t:
            state = "BAI"
        elif cai:
            state = "CHENG"
        elif guan and not yin and not _jshui:
            state = "BAI"
    # 阳刃格
    elif name == "阳刃格":
        # V7.198 全透干口径(「透官煞」「露财印」「不见伤官」皆为干头判据; L1223 案证
        # 「丁卯 丙午 丙子 壬辰，煞刃格成也」=乙印透年干成):
        # V7.198b 撤「财印露门」: L1140 徐注「以官煞制刃，格局最美…以财印并见为吉」
        # ——财印是辅弼非前提; L1220 石友三/L1223 龙济光两案财印不透而格成。败句
        # 只有「阳刃无官煞」(L1148/L1159)。
        guan = _trans_ten_god(p, "正官") or _trans_ten_god(p, "七杀")
        # V7.199b L1245「带伤食制官煞」=食神+伤官并计(镜像引擎 po required 食神+伤官)
        shang = _trans_ten_god(p, "伤官") or _trans_ten_god(p, "食神")
        cai_yin = (_trans_ten_god(p, "正财") or _trans_ten_god(p, "偏财")
                   or _trans_ten_god(p, "正印") or _trans_ten_god(p, "偏印"))
        yin_t = _trans_ten_god(p, "正印") or _trans_ten_god(p, "偏印")
        if guan and not shang:
            # L1140「月令阳刃，以官煞制刃…以不见伤官为格之成也」+ L1223 煞刃格成
            add("CHENG", "官煞制刃为用" + ("，财印并见为吉" if cai_yin else "（财印未露，L1220/L1223 制刃即成）"))
            state = "CHENG"
        if not guan:
            add("BAI", "阳刃无官煞")
            state = "BAI"
        elif guan and shang:
            # L1245 并透两势: 得重印以去食则成; 重印量化无原典判据(宁缺勿猜):
            # 印透 -> 须辨重印 NE; 印不透 -> 伤官制官煞破刃用 -> 败。
            if yin_t:
                add("NOT_EVALUABLE", "官煞与伤官并透(须辨重印以去食)")
            else:
                # V7.199b 成中有败镜像(PZZQ L1220 石友三「时透七煞，制刃为用，格之成也。
                # 无如月干辛金合丙，年上癸水制煞，为成中有败也」+ L1222 郭松龄
                # 「亦成中有败也」): 官煞被合去(五合伙伴在干) -> 成中有败;
                # 未被合(伤食纯制) -> 带伤食制官煞而格破(L1245)。
                _WUHE = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙",
                         "丙": "辛", "辛": "丙", "丁": "壬", "壬": "丁",
                         "戊": "癸", "癸": "戊"}
                _ks_stems = [s for s in _transparent(p)
                             if ten_god(dm, s) in ("正官", "七杀")]
                _hequ = any(_WUHE.get(s) in _transparent(p) for s in _ks_stems)
                if _hequ:
                    add("CHENG_ZHONG_YOU_PO", "官煞制刃为成, 官煞被合去/伤食制官煞 -> 成中有败(石友三 L1220 辛合丙)")
                    state = "CHENG_ZHONG_YOU_PO"
                else:
                    add("BAI", "带伤食制官煞而格破(印不透无从去食)")
                    state = "BAI"
    # 建禄月劫格
    elif name == "建禄月劫格":
        # 2026-11-10 镜像引擎禄劫路径(PZZQ L1142 原文逐字): 「透官而逢财印/透财而
        # 逢食伤/透煞而遇制伏」——命名人元(官/财/煞)须【透干】; 配合神(财印/食伤)
        # 「逢/遇」=见(含藏干)。
        guan_t = _trans_ten_god(p, "正官")
        cai_t = _trans_ten_god(p, "正财") or _trans_ten_god(p, "偏财")
        sha_t = _trans_ten_god(p, "七杀")
        cai_seen = _has_ten_god(p, "正财") or _has_ten_god(p, "偏财")
        yin_seen = _has_ten_god(p, "正印") or _has_ten_god(p, "偏印")
        shi_seen = _has_ten_god(p, "食神") or _has_ten_god(p, "伤官")
        # V7.199b 「遇制伏」=功能要求须透干(镜像引擎 shi_t, 七煞格 V7.190 has_zhi 同口径)
        shi_t = _trans_ten_god(p, "食神") or _trans_ten_god(p, "伤官")
        guan_seen = _has_ten_god(p, "正官")
        yin_t = _trans_ten_god(p, "正印") or _trans_ten_god(p, "偏印")
        if guan_t and (cai_seen or yin_seen):
            add("CHENG", "透官而逢财印(同官格)")
            state = "CHENG"
        if cai_t and shi_seen:
            add("CHENG", "透财而逢食伤(同财格)")
            state = "CHENG"
        if sha_t and shi_t:
            add("CHENG", "透煞而遇制伏(同煞格)")
            state = "CHENG"
        # 败句(.008 L1147「无财官，透煞印」/徐注 L1160「煞生印，转而助身，其旺无极」):
        # 财官全无(藏亦无)+煞印双透
        if (not guan_seen and not cai_seen) and sha_t and yin_t:
            add("BAI", "建禄月劫无财官透煞印")
            state = "BAI"
        # 泄秀成路(引擎 path④, PZZQ「无财官而用伤食泄其太过亦为秀气」)
        # V7.199b 全透干口径(镜像引擎 path④ `not guan and not cai_t and not sha and shi_t`):
        #   泄秀=财官煞【透干】全无+食伤【透】(1980-04-15 庚申庚辰戊午戊午 契约)。
        if state == "NOT_EVALUABLE" and not guan_t and not cai_t and not sha_t and shi_t:
            add("CHENG", "无财官煞用伤食泄秀")
            state = "CHENG"

    # V7.199b 全局: 四生/四专月令逢冲破格(PZZQ L2023-2026 徐注: 「忌者冲而去之为成,
    # 喜者逢冲为败」随支而有成有败 + L2686 寅申巳亥「气尚微弱, 逢冲则坏」; 四库
    # 「不忌刑冲」)——镜像引擎 apply_he_po_ge: 六格月令本气即格神=喜者(mwx∈ti|xi 恒真)
    # → 被存活冲则格破(四生+四专同一确定性口径); 建禄月劫格/阳刃格月令=比劫(身非格神,
    # 忌者冲而去之为成——龙济光 L1223 煞刃格成), .008 禄劫败句亦无冲条 → 不判。
    # 月支被年/日支六冲(相邻位) 且 月支/冲伴不参与六合(合解未验, 宁缺勿猜) -> 败。
    _SIX_GE = ("正官格", "财格", "印格", "食神格", "七煞格", "伤官格")
    if name in _SIX_GE and mb in ("寅", "申", "巳", "亥", "子", "午", "卯", "酉") and rel["冲"]:
        _pl = _pillars(p)
        _year_b, _day_b = _pl[0][1], _pl[2][1]
        _partners = [b for b in rel["冲"] if b in (_year_b, _day_b)]
        if _partners:
            _LH6 = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌",
                    "戌": "卯", "辰": "酉", "酉": "辰", "巳": "申", "申": "巳",
                    "午": "未", "未": "午"}
            _all_b = [b for _s, b in _pl]
            _has_lh = (any(_LH6.get(mb) == b for b in _all_b if b != mb)
                       or any(_LH6.get(pb) in _all_b for pb in _partners))
            if not _has_lh:
                add("BAI", "四生四专月令逢冲(喜者逢冲为败, L2023-2026/L2686)")
                state = "BAI"

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
