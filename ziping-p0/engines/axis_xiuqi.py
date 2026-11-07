# -*- coding: utf-8 -*-
"""B轴（秀气侧/干合侧）计分

修正Bug A(争合统计方向) + Bug B(化神取错) + B4复用闸门
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

HE = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙",
      "丙": "辛", "辛": "丙", "丁": "壬", "壬": "丁",
      "戊": "癸", "癸": "戊"}

HUA_SHEN = {"甲己": "土", "己甲": "土", "乙庚": "金", "庚乙": "金",
            "丙辛": "水", "辛丙": "水", "丁壬": "木", "壬丁": "木",
            "戊癸": "火", "癸戊": "火"}

WUXING = {}
for g in "甲乙寅卯": WUXING[g] = "木"
for g in "丙丁巳午": WUXING[g] = "火"
for g in "戊己辰戌丑未": WUXING[g] = "土"
for g in "庚辛申酉": WUXING[g] = "金"
for g in "壬癸亥子": WUXING[g] = "水"

MONTH_WANG = {"寅": "木", "卯": "木", "巳": "火", "午": "火",
              "申": "金", "酉": "金", "亥": "水", "子": "水",
              "辰": "土", "戌": "土", "丑": "土", "未": "土"}

@dataclass
class XiuqiResult:
    pattern_root: Optional[str]
    pattern_type: str
    day_stem: str
    b1a: bool
    b1b: bool
    b2: bool
    b3: bool
    b4: bool
    b5: bool  # 化神支局全
    b6: bool  # G4：无克化神透干
    b7: bool  # G8：财星不超标（财透一位虚浮尚可，两位/根深则转格）
    b8: bool  # G7：日主有根→降档（不是硬闸，是减项）
    score: int
    gate_debug: List[str]

def hx_to_ge(hx: str) -> str:
    return {"木": "曲直", "火": "炎上", "土": "稼穑", "金": "从革", "水": "润下"}[hx]

def _stems(pillars: Dict[str, List[str]]) -> tuple:
    return (pillars["year"][0], pillars["month"][0],
            pillars["day"][0],   pillars["hour"][0])

def _branches(pillars: Dict[str, List[str]]) -> tuple:
    return (pillars["year"][1], pillars["month"][1],
            pillars["day"][1],   pillars["hour"][1])

def xiuqi_axis(pillars: Dict[str, List[str]],
               facts: Dict[str, Any],
               gate_debug: List[str]) -> XiuqiResult:
    ys, ms, ds, hs = _stems(pillars)
    br = _branches(pillars)
    mb = facts["month_branch"]

    g = HE.get(ds)
    if g is None or g not in (ms, hs):
        return XiuqiResult(None, "化气型", ds, False, False, False, False, False, False, False, False, False, 0, [])

    # B1：独合/争合（修正Bug A：统计方向反了）
    # 争合：两个相同的天干争合一个
    # 比如两丁争合一壬：日干壬，年/月干丁出现两次
    # 或两癸争合一戊：日干癸，年干癸，时干戊 → 两个癸争合一个戊
    all_stems = (ys, ms, ds, hs)
    same_day = sum(1 for x in all_stems if x == ds)  # 日干出现总次数（含自己）
    same_he  = sum(1 for x in all_stems if x == g)   # 合神出现总次数
    zheng_he = (same_day >= 2) or (same_he >= 2)
    b1a, b1b = (not zheng_he), zheng_he

    # B2：化神当令（按《三命通会·论十干化气》+ 季月引化择一）
    # 本气月=化神三合局，次旺月=原文"其次X月亦化"
    # 季月引化：月令为四季（辰戌丑未）之一，且化神支局全，则视为当令，降MID
    pair = "".join(sorted([ds, g]))
    hx = HUA_SHEN.get(pair, "")
    HUA_MONTHS = {
        "木": {"本气": {"亥", "卯", "未"}, "次旺": {"寅"}},
        "火": {"本气": {"寅", "午", "戌"}, "次旺": {"巳"}},
        "土": {"本气": {"辰", "戌", "丑", "未"}, "次旺": {"午"}},
        "金": {"本气": {"巳", "酉", "丑"}, "次旺": {"申"}},
        "水": {"本气": {"申", "子", "辰"}, "次旺": {"亥"}},
    }
    months = HUA_MONTHS.get(hx, {})
    allowed = months.get("本气", set()) | months.get("次旺", set())
    b2 = mb in allowed
    # 季月引化：季月 + 化神支局全 → 当令
    SI_JI = {"辰", "戌", "丑", "未"}
    # 先算b5，再回头看季月引化
    cf = facts.get("combination_facts", {})
    sh_list = cf.get("sanhe", [])
    sf_list = cf.get("sanhui", [])
    hx_ju_map = {
        "木": ("亥卯未合木", "寅卯辰三会木"),
        "火": ("寅午戌合火", "巳午未三会火"),
        "土": (None, None),
        "金": ("巳酉丑合金", "申酉戌三会金"),
        "水": ("申子辰合水", "亥子丑三会水"),
    }
    sanhe_name, sanhui_name = hx_ju_map.get(hx, (None, None))
    if hx == "土":
        b5_tmp = all(x in br for x in ("辰", "戌", "丑", "未"))
    else:
        sanhe_ok = sanhe_name and sanhe_name in sh_list
        sanhui_ok = sanhui_name and sanhui_name in sf_list
        b5_tmp = sanhe_ok or sanhui_ok
    if not b2 and mb in SI_JI and b5_tmp:
        b2 = True  # 季月引化，当令

    # B3：逢龙引化，与稼穑去重
    chen = ("辰" in br)
    si_zhu_cxsw = all(x in br for x in ("辰", "戌", "丑", "未"))
    b3 = chen and (not si_zhu_cxsw)

    # B4：无破（化气型自建：无克化神透干 + 财星不超标；不复用旧专旺闸门）
    # 旧版复用gate_debug是bug：专旺的官杀/财星判定逻辑不适用于化气型
    b4 = True  # 占位，b6/b7算完后覆盖

    # B5：化神支局全（按化神五行查三合/三会）
    b5 = b5_tmp

    # B6：G4 无克化神透干（排除合化之干）
    ke_map = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
    ke_wx = ke_map.get(hx, "")
    ke_stems = [s for s in "甲乙丙丁戊己庚辛壬癸" if WUXING.get(s) == ke_wx]
    # 排除合化之干（日干+合神）
    exclude = {ds, g}
    check_stems = [s for s in (ys, ms, hs) if s not in exclude]
    has_ke = any(s in check_stems for s in ke_stems)
    b6 = not has_ke

    # B7：G8 财星不超标（财 = 化神所克）
    # 财 = 化神所克：木克土(戊己)、火克金(庚辛)、土克水(壬癸)、金克木(甲乙)、水克火(丙丁)
    cai_map = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
    cai_wx = cai_map.get(hx, "")
    cai_stems = [s for s in "甲乙丙丁戊己庚辛壬癸" if WUXING.get(s) == cai_wx]
    # 财透数量（排除日干和合化之干，只查年/月/时三干，且排除合神）
    other_stems = [ys, ms, hs]
    exclude = {ds, g}
    tou_cai = [s for s in other_stems if (s in cai_stems) and (s not in exclude)]
    # 财根深：地支有财五行本气
    cai_roots = sum(1 for b in br if WUXING.get(b) == cai_wx)
    # 超标条件：财透两位，或财透一位但根深(>=2)
    if len(tou_cai) >= 2:
        b7 = False
    elif len(tou_cai) == 1 and cai_roots >= 2:
        b7 = False
    else:
        b7 = True

    # B4：无破 = 无克化神透干(b6) and 财星不超标(b7)
    b4 = b6 and b7

    # B8：G7 日主有根→降档（不是硬闸，是减项）
    # 日主在地支见本气根（含库中余气）→ 化得不彻底→降MID
    # 注意：日干原五行=化神五行时不算（如甲己化土，日干己土，化神也是土，见土根是化神有根，不是日主有根）
    day_wx = WUXING.get(ds, "")
    if day_wx != hx:
        # 迁到root_qi.py单点真相源
        from spec.root_qi import calc_root_qi
        stems_list = [ys, ms, ds, hs]
        branches_list = list(br)
        root_qi = calc_root_qi(ds, branches_list, stems_list)
        b8 = root_qi > 0  # True=有根→降档
    else:
        b8 = False  # 日干五行=化神五行，不存在"日主有根不降"的问题

    # 纯布尔枚举: 直接判定, 不用score
    is_xiuqi = (b1a or b1b) and b2 and b4 and b6 and b7

    root = f"一行成象·{hx_to_ge(hx)}" if hx else None

    return XiuqiResult(root, "化气型", ds, b1a, b1b, b2, b3, b4, b5, b6, b7, b8, is_xiuqi, list(gate_debug))
