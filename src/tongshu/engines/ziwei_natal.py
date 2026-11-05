# -*- coding: utf-8 -*-
"""紫微斗数原生排盘（独立真值层）——不依赖 iztro / 任何第三方库。

建此层的唯一目的：**给"算得准"一个不自洽的对照**。
现有生产路径是 iztro 的 subprocess 包装，用 iztro 生成的数据集来"验证" iztro，
是循环论证。本模块按《紫微斗数全书》通行安星诀逐条实现，可用于：

1. 逐字段对照生产输出（命宫/身宫/五行局/紫微位/十四主星/辅煞/四化/大限）；
2. 反向发现 iztro 与传世口诀不一致处（以口诀为准，不以工具为准）；
3. 未来替换 iztro 依赖，使紫微引擎真正"独立可跑"。

安星诀出处（通行本，与倪海厦《天纪》体系同源）：
- 命宫：寅起正月，顺数至生月，再从该宫起子时逆数至生时。
- 身宫：同起点，起子时顺数至生时。
- 五行局：命宫干支纳音（水二/木三/金四/土五/火六）。
- 紫微：生日除局数；除尽则安商数宫之前一宫；有余数取补数，补数单则逆退、双则顺进。
- 十四主星：紫微逆一机、逆三阳、逆四武、逆五同、逆八廉；天府与紫微寅申对称，
  顺行太阴、贪狼、巨门、天相、天梁、七杀，破军隔三。
- 六吉六煞、禄存天马与 38 颗杂曜，依年干/年支/生月/生时/生日安（见各类上方口诀）。
- 闰月：前半月（1–15 日）按本月、后半月按次月（晚子时不折算）。
- 四组十二神：长生（五行局长生位起）、博士（禄存起）、将前（三合将星起）、岁前（年支起）；
  长生与博士按「阳男阴女顺、阴男阳女逆」，将前/岁前恒顺行。
"""
from __future__ import annotations

from dataclasses import dataclass, field

BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

MAIN_STARS_14 = ["紫微", "天机", "太阳", "武曲", "天同", "廉贞",
                 "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"]

PALACE_NAMES = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                "迁移", "仆役", "官禄", "田宅", "福德", "父母"]

# --- 五虎遁：年干 → 寅宫天干 ------------------------------------------------
_YIN_STEM_BY_YEAR_STEM = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}

# --- 六十甲子纳音五行（30 组，按甲子/乙丑 起顺序）-----------------------------
_NAYIN_ELEMENTS = [
    "金", "火", "木", "土", "金", "火", "水", "土", "金", "木",
    "水", "土", "火", "木", "水", "金", "火", "木", "土", "金",
    "火", "水", "土", "金", "木", "水", "土", "火", "木", "水",
]
_JU_BY_ELEMENT = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}

# --- 四化（通行本 / 与倪海厦体系同）：禄 权 科 忌 ------------------------------
SIHUA_BY_STEM = {
    0: ("廉贞", "破军", "武曲", "太阳"),   # 甲
    1: ("天机", "天梁", "紫微", "太阴"),   # 乙
    2: ("天同", "天机", "文昌", "廉贞"),   # 丙
    3: ("太阴", "天同", "天机", "巨门"),   # 丁
    4: ("贪狼", "太阴", "右弼", "天机"),   # 戊
    5: ("武曲", "贪狼", "天梁", "文曲"),   # 己
    6: ("太阳", "武曲", "太阴", "天同"),   # 庚
    7: ("巨门", "太阳", "文曲", "文昌"),   # 辛
    8: ("天梁", "紫微", "左辅", "武曲"),   # 壬
    9: ("破军", "巨门", "太阴", "贪狼"),   # 癸
}

# --- 年干起例 ----------------------------------------------------------------
_TIANKUI_TIANYUE = {  # (魁, 钺)
    0: (1, 7), 4: (1, 7), 6: (1, 7),      # 甲戊庚：丑未
    1: (0, 8), 5: (0, 8),                 # 乙己：子申
    2: (11, 9), 3: (11, 9),               # 丙丁：亥酉
    8: (3, 5), 9: (3, 5),                 # 壬癸：卯巳
    7: (6, 2),                            # 辛：午寅
}
_LUCUN = {0: 2, 1: 3, 2: 5, 3: 6, 4: 5, 5: 6, 6: 8, 7: 9, 8: 11, 9: 0}

# --- 年干起例（杂曜）：天官 / 天福 / 天厨 / 截路 / 空亡 --------------------------
# 天官诀：甲喜羊鸡乙龙猴，丙年蛇鼠一窝谋。丁虎擒猪戊玉兔，
#        己鸡居然与虎俦。庚猪马辛鸡蛇走，壬犬马癸马蛇游。
_TIANGUAN = (7, 4, 5, 2, 3, 9, 11, 9, 10, 6)   # 未辰巳寅卯酉亥酉戌午
_TIANFU_AUX = (9, 8, 0, 11, 3, 2, 6, 5, 6, 5)  # 酉申子亥卯寅午巳午巳
# 天厨诀：甲丁食蛇口，乙戊辛马方。丙从鼠口得，己食于猴房。庚食虎头上，壬鸡癸猪堂。
_TIANCHU = (5, 6, 0, 5, 6, 8, 2, 6, 9, 11)     # 巳午子巳午申寅午酉亥
# 截路空亡（截空）：甲己之年申酉，乙庚午未，丙辛辰巳，丁壬寅卯，戊癸子丑。
_JIELU = (8, 6, 4, 2, 0)
_KONGWANG = (9, 7, 5, 3, 1)

# --- 年支起例 ----------------------------------------------------------------
_TIANMA = {0: 2, 4: 2, 8: 2, 2: 8, 6: 8, 10: 8, 5: 11, 9: 11, 1: 11, 11: 5, 3: 5, 7: 5}
_HUOLING_BASE = {0: 2, 4: 2, 8: 2,    # 申子辰 → 寅
                 2: 1, 6: 1, 10: 1,   # 寅午戌 → 丑
                 5: 3, 9: 3, 1: 3,    # 巳酉丑 → 卯
                 11: 9, 3: 9, 7: 9}   # 亥卯未 → 酉
_LINGXING_BASE = {0: 10, 4: 10, 8: 10,   # 申子辰 → 戌
                  2: 3, 6: 3, 10: 3,     # 寅午戌 → 卯
                  5: 10, 9: 10, 1: 10,   # 巳酉丑 → 戌
                  11: 10, 3: 10, 7: 10}  # 亥卯未 → 戌
# 华盖：子辰申在辰，丑巳酉在丑，寅午戍在戍，卯未亥在未（三合墓库）
_HUAGAI = {0: 4, 4: 4, 8: 4, 5: 1, 9: 1, 1: 1, 2: 10, 6: 10, 10: 10, 11: 7, 3: 7, 7: 7}
# 咸池：子辰申在酉，丑巳酉在午，寅午戍在卯，卯未亥在子（三合沐浴）
_XIANCHI = {0: 9, 4: 9, 8: 9, 5: 6, 9: 6, 1: 6, 2: 3, 6: 3, 10: 3, 11: 0, 3: 0, 7: 0}
# 孤辰寡宿：寅卯辰安巳丑，巳午未安申辰，申酉戍安亥未，亥子丑安寅戍。
_GUCHEN = {2: 5, 3: 5, 4: 5, 5: 8, 6: 8, 7: 8, 8: 11, 9: 11, 10: 11, 11: 2, 0: 2, 1: 2}
_GUASU = {2: 1, 3: 1, 4: 1, 5: 4, 6: 4, 7: 4, 8: 7, 9: 7, 10: 7, 11: 10, 0: 10, 1: 10}
# 破碎：子午卯酉年安巳，寅申巳亥年安酉，辰戍丑未年安丑。
_POSUI = {b: (5, 1, 9)[b % 3] for b in range(12)}
# 蜚廉：子丑寅年在申酉戍，卯辰巳年在巳午未，午未申年在寅卯辰，酉戍亥年在亥子丑。
_FEILIAN = (8, 9, 10, 5, 6, 7, 2, 3, 4, 11, 0, 1)
# 年解：解神从戌上起子，逆数至当生年太岁。
_NIANJIE = (10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 11)
# 月解：正二在申，三四在戍，五六在子，七八在寅，九十在辰，十一十二在午。
_YUEJIE = (8, 10, 0, 2, 4, 6)     # 按 month_index//2
# 阴煞：正七月在寅，二八在子，三九在戍，四十在申，五十一在午，六十二在辰。
_YINSHA = (2, 0, 10, 8, 6, 4)     # 按 month_index%6
# 天月：一犬二蛇三在龙，四虎五羊六兔宫。七猪八羊九在虎，十马冬犬腊寅中。
_TIANYUE = (10, 5, 4, 2, 7, 3, 11, 7, 2, 6, 10, 2)
# 天巫：正五九月在巳，二六十月在申，三七十一在寅，四八十二在亥。
_TIANWU = (5, 8, 2, 11)           # 按 month_index%4

# --- 命主 / 身主 --------------------------------------------------------------
_SOUL_STAR_BY_BRANCH = {0: "贪狼", 1: "巨门", 11: "巨门", 2: "禄存", 10: "禄存",
                        3: "文曲", 9: "文曲", 4: "廉贞", 8: "廉贞", 5: "武曲",
                        7: "武曲", 6: "破军"}
_BODY_STAR_BY_BRANCH = {0: "火星", 6: "火星", 1: "天相", 7: "天相", 2: "天梁",
                        8: "天梁", 3: "天同", 9: "天同", 4: "文昌", 10: "文昌",
                        5: "天机", 11: "天机"}


def _mod(v: int, n: int = 12) -> int:
    return v % n


def jiazi_index(stem: int, branch: int) -> int:
    """干支 → 六十甲子序（0=甲子）。"""
    for k in range(60):
        if k % 10 == stem and k % 12 == branch:
            return k
    raise ValueError(f"非法干支: {STEMS[stem]}{BRANCHES[branch]}")


def nayin_element(stem: int, branch: int) -> str:
    return _NAYIN_ELEMENTS[jiazi_index(stem, branch) // 2]


def palace_stem(year_stem: int, branch: int) -> int:
    """五虎遁：寅宫天干起，寅卯…亥子丑 顺序轮天干（到子丑要绕回，不能按 10 取模）。"""
    return _mod(_YIN_STEM_BY_YEAR_STEM[year_stem] + _mod(branch - 2), 10)


def soul_branch(month: int, hour_index: int) -> int:
    """命宫：寅起正月顺数生月，再起子时逆数生时。month=1..12, hour_index 0=子时。"""
    return _mod(2 + (month - 1) - hour_index)


def body_branch(month: int, hour_index: int) -> int:
    """身宫：同起点，起子时顺数生时。"""
    return _mod(2 + (month - 1) + hour_index)


def five_ju(month: int, hour_index: int, year_stem: int) -> int:
    s = soul_branch(month, hour_index)
    return _JU_BY_ELEMENT[nayin_element(palace_stem(year_stem, s), s)]


def ziwei_branch(five_elements_ju: int, day: int) -> int:
    """安紫微星诀（子平/紫微通行本）：

    以生日除局数，商数宫 = 寅起顺数商数（商 0 即寅）；除得尽（余 0）即安商数宫之前一宫；
    有余数则取补数 = 局数 − 余数，补数为单则从商数宫逆退补数宫，补数为双则顺进补数宫。

    实测校核：与 iztro 的 (局,日)→紫微 全表 150/150 一致（150 格无一冲突）。
    """
    q, r = divmod(day, five_elements_ju)
    if r == 0:
        return _mod(2 + q - 1)
    complement = five_elements_ju - r
    base = 2 + q
    if complement % 2 == 1:
        return _mod(base - complement)
    return _mod(base + complement)


def fourteen_main_stars(zw: int) -> dict[str, int]:
    zi = {
        "紫微": zw, "天机": _mod(zw - 1), "太阳": _mod(zw - 3),
        "武曲": _mod(zw - 4), "天同": _mod(zw - 5), "廉贞": _mod(zw - 8),
    }
    fu = _mod(4 - zw)
    fu_system = {
        "天府": fu, "太阴": _mod(fu + 1), "贪狼": _mod(fu + 2), "巨门": _mod(fu + 3),
        "天相": _mod(fu + 4), "天梁": _mod(fu + 5), "七杀": _mod(fu + 6),
        "破军": _mod(fu + 10),
    }
    return {**zi, **fu_system}


def aux_stars(month_index: int, day_index: int, hour_index: int, year_stem: int,
              year_branch: int, soul_branch: int, body_branch: int) -> dict[str, int]:
    """六吉 + 六煞 + 禄存天马 + 38 杂曜的宫位。

    month_index: 0=正月（寅月起算，闰月已按「前半月本月/后半月次月」折算）
    day_index:  生日序（平日 = day-1；晚子时按 day，见安三台八座诀）
    """
    lc = _LUCUN[year_stem]
    kui, yue = _TIANKUI_TIANYUE[year_stem]
    zuo = _mod(4 + month_index)
    you = _mod(10 - month_index)
    chang = _mod(10 - hour_index)
    qu = _mod(4 + hour_index)
    out = {
        # 六吉
        "左辅": zuo, "右弼": you, "文昌": chang, "文曲": qu,
        "天魁": kui, "天钺": yue,
        # 禄存与羊陀
        "禄存": lc, "擎羊": _mod(lc + 1), "陀罗": _mod(lc - 1),
        # 六煞
        "火星": _mod(_HUOLING_BASE[year_branch] + hour_index),
        "铃星": _mod(_LINGXING_BASE[year_branch] + hour_index),
        "地劫": _mod(11 + hour_index), "地空": _mod(11 - hour_index),
        # 天马
        "天马": _TIANMA[year_branch],
        # 日系
        "三台": _mod(zuo + day_index), "八座": _mod(you - day_index),
        "恩光": _mod(chang + day_index - 1), "天贵": _mod(qu + day_index - 1),
        # 时系
        "台辅": _mod(6 + hour_index), "封诰": _mod(2 + hour_index),
        # 年支系
        "红鸾": _mod(3 - year_branch), "天喜": _mod(3 - year_branch + 6),
        "华盖": _HUAGAI[year_branch], "咸池": _XIANCHI[year_branch],
        "孤辰": _GUCHEN[year_branch], "寡宿": _GUASU[year_branch],
        "破碎": _POSUI[year_branch], "蜚廉": _FEILIAN[year_branch],
        "龙池": _mod(4 + year_branch), "凤阁": _mod(10 - year_branch),
        "天哭": _mod(6 - year_branch), "天虚": _mod(6 + year_branch),
        "年解": _NIANJIE[year_branch],
        "天才": _mod(soul_branch + year_branch), "天寿": _mod(body_branch + year_branch),
        # 天伤在仆役、天使在疾厄（宫位按地支顺行编号：命0 父母1 … 仆役5 … 疾厄7）
        "天伤": _mod(soul_branch + 5), "天使": _mod(soul_branch + 7),
        "天空": _mod(year_branch + 1),
        "天德": _mod(9 + year_branch), "月德": _mod(5 + year_branch),
        # 年干系
        "天官": _TIANGUAN[year_stem], "天福": _TIANFU_AUX[year_stem],
        "天厨": _TIANCHU[year_stem],
        "截路": _JIELU[year_stem % 5], "空亡": _KONGWANG[year_stem % 5],
        "旬空": _xunkong_branch(year_stem, year_branch),
        # 月系
        "天刑": _mod(9 + month_index), "天姚": _mod(1 + month_index),
        "解神": _YUEJIE[month_index // 2], "阴煞": _YINSHA[month_index % 6],
        "天月": _TIANYUE[month_index], "天巫": _TIANWU[month_index % 4],
    }
    return out


def _xunkong_branch(year_stem: int, year_branch: int) -> int:
    """旬空：以年支起算，癸干为旬末；再按年支阴阳校正宫位奇偶。"""
    palace = _mod((year_branch - 2) + (9 - year_stem) + 1)
    if year_branch % 2 != palace % 2:
        palace = _mod(palace + 1)
    return _mod(palace + 2)


# --- 四组十二神 ----------------------------------------------------------------
# 长生十二神：水二局长生在申、木三局在亥、金四局在巳、土五局在申、火六局在寅；
# 阳男阴女顺行、阴男阳女逆行。
_CS12_START = {2: 8, 3: 11, 4: 5, 5: 8, 6: 2}   # 局 → 长生支（申/亥/巳/申/寅）
CS12 = ("长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养")
# 博士十二神：从禄存起，同长生十二神顺逆方向。
BOSHI12 = ("博士", "力士", "青龙", "小耗", "将军", "奏书", "飞廉", "喜神", "病符", "大耗", "伏兵", "官府")
# 将前十二神：寅午戌将星午、申子辰将星子、巳酉丑将星酉、亥卯未将星卯，顺行。
_JIANGXING_START = {2: 6, 6: 6, 10: 6, 0: 0, 4: 0, 8: 0, 5: 9, 9: 9, 1: 9, 11: 3, 3: 3, 7: 3}
JIANGQIAN12 = ("将星", "攀鞍", "岁驿", "息神", "华盖", "劫煞", "灾煞", "天煞",
               "指背", "咸池", "月煞", "亡神")
# 岁前十二神：年支起岁建，顺行。
SUIQIAN12 = ("岁建", "晦气", "丧门", "贯索", "官符", "小耗", "大耗", "龙德",
             "白虎", "天德", "吊客", "病符")


def twelve_gods(ju: int, year_stem: int, year_branch: int, gender: str,
                lu_branch: int) -> dict[str, dict[int, str]]:
    """四组十二神（按地支 → 神名）。顺逆：阳男阴女顺、阴男阳女逆。"""
    yang_year = year_stem % 2 == 0
    forward = (yang_year and gender == "male") or (not yang_year and gender == "female")

    out: dict[str, dict[int, str]] = {"changsheng": {}, "boshi": {}, "jiangqian": {}, "suiqian": {}}
    start = _CS12_START[ju]
    for i, name in enumerate(CS12):
        out["changsheng"][_mod(start + i if forward else start - i)] = name
    for i, name in enumerate(BOSHI12):
        out["boshi"][_mod(lu_branch + i if forward else lu_branch - i)] = name
    jq = _JIANGXING_START[year_branch]
    for i, name in enumerate(JIANGQIAN12):
        out["jiangqian"][_mod(jq + i)] = name
    for i, name in enumerate(SUIQIAN12):
        out["suiqian"][_mod(year_branch + i)] = name
    return out


# 十四辅煞（iztro 归为 minorStars 的那一组）
MINOR_STARS_14 = ("左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存",
                  "擎羊", "陀罗", "火星", "铃星", "地空", "地劫", "天马")


def hour_to_time_index(hour: int) -> int:
    """24h 时钟 → iztro timeIndex（0=早子 … 11=亥 … 12=晚子）。"""
    if hour == 23:
        return 12
    if hour in (0, 24):
        return 0
    return (hour + 1) // 2 % 12


def native_raw_chart(lunar_date, hour: int, gender: str = "male",
                     leap_mode: str = "half_month") -> dict:
    """原生排盘 → 与 iztro raw 同构的盘面 dict（供 ZiweiEngine 走同一后处理）。

    lunar_date 为 (年, 月, 日)，月为负数表示闰月（与 ZiweiEngine 惯例一致）。
    leap_mode: "half_month"（默认，与 iztro 一致）/ "classic"（原典闰月整体作次月）。
    输出字段与 `ZiweiEngine.full_chart` 中 JS 侧一致，便于共用
    `postprocess_natal_palaces` 与字段映射——这是「脱离 iztro 也能出盘」的接口。
    """
    year, month, day = lunar_date
    is_leap = month < 0
    month = abs(month)
    ti = hour_to_time_index(hour)
    ch = build_natal_chart(year, month, day, ti, gender, is_leap=is_leap,
                           month_days=lunar_month_days(year, month, is_leap),
                           leap_mode=leap_mode)

    palaces: dict[str, dict] = {}
    for name, p in ch.palaces.items():
        br = p["branch_index"]
        dx = ch.decadal.get(p["branch"], {})
        mins = [s for s in p["minor"] if s in MINOR_STARS_14]
        adjs = [s for s in p["minor"] if s not in MINOR_STARS_14]
        palaces[name] = {
            "stem": p["stem"],
            "branch": p["branch"],
            "major": list(p["major"]),
            "minor": mins,
            "adjective": adjs,
            "decadalRange": [dx.get("start_age"), dx.get("end_age")] if dx else [],
            "decadalStem": p["stem"],
            "decadalBranch": p["branch"],
            "starDetail": (
                [{"name": s, "kind": "major", "brightness": "", "mutagen": ch.sihua.get(s, "")}
                 for s in p["major"]]
                + [{"name": s, "kind": "minor", "brightness": "", "mutagen": ch.sihua.get(s, "")}
                   for s in mins]
            ),
            "changsheng12": ch.twelve_gods["changsheng"].get(br, ""),
            "boshi12": ch.twelve_gods["boshi"].get(br, ""),
            "jiangqian12": ch.twelve_gods["jiangqian"].get(br, ""),
            "suiqian12": ch.twelve_gods["suiqian"].get(br, ""),
            "isBody": br == ch.body,
            "isOriginal": False,
            "ages": [],
        }

    return {
        "fiveElementsClass": {2: "水二局", 3: "木三局", 4: "金四局",
                              5: "土五局", 6: "火六局"}[ch.ju],
        "soulPalaceBranch": BRANCHES[ch.soul],
        "bodyPalaceBranch": BRANCHES[ch.body],
        "natalYearStem": STEMS[ch.year_stem],
        "soulStar": ch.soul_star,
        "bodyStar": ch.body_star,
        "solarDate": "",
        "lunarDateText": f"农历{year}年{month}月{day}日" + ("（闰）" if is_leap else ""),
        "timeText": f"第{ti}时",
        "timeRange": "",
        "sign": "",
        "zodiac": "",
        "palaces": palaces,
        "source": "native",
    }


@dataclass
class NatalChart:
    lunar_year: int
    year_stem: int
    year_branch: int
    month: int
    day: int
    hour_index: int
    gender: str
    soul: int
    body: int
    ju: int
    ziwei: int
    main_stars: dict[str, int] = field(default_factory=dict)
    aux: dict[str, int] = field(default_factory=dict)
    sihua: dict[str, str] = field(default_factory=dict)   # 星 → 禄/权/科/忌
    palaces: dict[str, dict] = field(default_factory=dict)
    decadal: dict[str, dict] = field(default_factory=dict)
    twelve_gods: dict[str, dict[int, str]] = field(default_factory=dict)
    soul_star: str = ""
    body_star: str = ""

    def to_dict(self) -> dict:
        return {
            "lunar_year": self.lunar_year,
            "year_stem": STEMS[self.year_stem],
            "year_branch": BRANCHES[self.year_branch],
            "month": self.month, "day": self.day, "hour_index": self.hour_index,
            "gender": self.gender,
            "soul_branch": BRANCHES[self.soul], "body_branch": BRANCHES[self.body],
            "five_elements_ju": self.ju,
            "ziwei_branch": BRANCHES[self.ziwei],
            "soul_star": self.soul_star, "body_star": self.body_star,
            "palaces": self.palaces,
            "decadal": self.decadal,
            "twelve_gods": {
                kind: {BRANCHES[b]: v for b, v in row.items()}
                for kind, row in self.twelve_gods.items()
            },
            "sihua": self.sihua,
        }


def lunar_month_days(year: int, month: int, is_leap: bool = False) -> int:
    """农历当月天数（晚子时换日用）。优先 lunar_python，缺库时回退 30。"""
    try:
        from lunar_python import LunarYear
        m = LunarYear.fromYear(year).getMonth(-month if is_leap else month)
        return int(m.getDayCount())
    except Exception:  # noqa: BLE001
        return 30


def build_natal_chart(lunar_year: int, month: int, day: int,
                      hour_index: int, gender: str = "male",
                      is_leap: bool = False, month_days: int = 30,
                      leap_mode: str = "half_month") -> NatalChart:
    """hour_index: 0=子 … 11=亥（12 表示晚子时）。

    闰月口径两种，显式可切换（不再混用）：
    - `leap_mode="half_month"`（默认，与 iztro `fixLeap=true` 同）：
      闰月前半月（1–15 日）按本月算，后半月（16 日起）按次月算；
      晚子时（timeIndex 12）不作次月折算。
    - `leap_mode="classic"`（原典口径，《紫微斗数全书》原文）：
      「又若闰月正月生者要在二月内起安身命，凡有闰月具要依此为例」
      → 闰月**整体作次月**，不分上下半月。

    晚子时：紫微安星按「次日」的日数（超出当月天数则回绕），
    而三台/八座等日系星仍用当日日数（与 iztro `fixLunarDayIndex` 一致）。
    """
    hour_raw = hour_index
    ti = 0 if hour_raw == 12 else hour_raw
    if not 1 <= month <= 12:
        raise ValueError("month 必须 1-12")
    if not 1 <= day <= 30:
        raise ValueError("day 必须 1-30")
    if gender not in ("male", "female"):
        raise ValueError("gender 必须 male/female")
    if leap_mode not in ("half_month", "classic"):
        raise ValueError("leap_mode 必须 half_month/classic")

    ys = (lunar_year - 4) % 10
    yb = (lunar_year - 4) % 12

    month_index = month - 1
    if is_leap and leap_mode == "classic":
        month_index = _mod(month_index + 1)
    elif is_leap and day > 15 and hour_raw != 12:
        month_index = _mod(month_index + 1)
    day_index = day if hour_raw >= 12 else day - 1

    soul = _mod(2 + month_index - ti)
    body = _mod(2 + month_index + ti)
    ju = _JU_BY_ELEMENT[nayin_element(palace_stem(ys, soul), soul)]
    zw_day = day + 1 if hour_raw == 12 else day
    if zw_day > month_days:
        zw_day -= month_days
    zw = ziwei_branch(ju, zw_day)
    mains = fourteen_main_stars(zw)
    aux = aux_stars(month_index, day_index, ti, ys, yb, soul, body)
    gods = twelve_gods(ju, ys, yb, gender, _LUCUN[ys])

    sihua = {}
    for star, kind in zip(SIHUA_BY_STEM[ys], ("禄", "权", "科", "忌")):
        sihua[star] = kind

    soul_star = _SOUL_STAR_BY_BRANCH[soul]
    body_star = _BODY_STAR_BY_BRANCH[yb]

    # 十二宫：命宫起，逆时针排（命宫→兄弟→夫妻… 沿地支逆序）
    palaces: dict[str, dict] = {}
    for offset, name in enumerate(PALACE_NAMES):
        br = _mod(soul - offset)
        palaces[name] = {
            "branch": BRANCHES[br],
            "branch_index": br,
            "stem": STEMS[palace_stem(ys, br)],
            "major": [s for s, b in mains.items() if b == br],
            "minor": [s for s, b in aux.items() if b == br],
        }

    # 大限：五行局数起限，阳男阴女顺、阴男阳女逆
    yang = ys % 2 == 0
    forward = (yang and gender == "male") or (not yang and gender == "female")
    decadal: dict[str, dict] = {}
    for i, name in enumerate(PALACE_NAMES):
        order = i if forward else -i
        br = _mod(soul + order)
        start = ju + 10 * i
        decadal[BRANCHES[br]] = {
            "palace": PALACE_NAMES[order % 12],
            "start_age": start, "end_age": start + 9,
        }

    return NatalChart(
        lunar_year=lunar_year, year_stem=ys, year_branch=yb, month=month, day=day,
        hour_index=hour_raw, gender=gender, soul=soul, body=body, ju=ju, ziwei=zw,
        main_stars=mains, aux=aux, sihua=sihua, palaces=palaces, decadal=decadal,
        twelve_gods=gods,
        soul_star=soul_star, body_star=body_star,
    )
