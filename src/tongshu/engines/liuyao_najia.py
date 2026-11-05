# -*- coding: utf-8 -*-
"""六爻纳甲装卦核心（京房纳甲法）。

本模块只做「装卦」这一层，全部规则来自通行京房纳甲体系（《火珠林》一脉）：

1. 八卦纳甲（天干与地支）：
   - 乾内甲子寅辰、外壬午申戌；坤内乙未巳卯、外癸丑亥酉
   - 震内庚子寅辰、外庚午申戌；巽内辛丑亥酉、外辛未巳卯
   - 坎内戊寅辰午、外戊申戌子；离内己卯丑亥、外己酉未巳
   - 艮内丙辰午申、外丙戌子寅；兑内丁巳卯丑、外丁亥酉未
2. 八宫卦序（京房八宫）：本宫八卦、一世、二世、三世、四世、五世、游魂、归魂
3. 世应：本宫世在六爻，一世在初爻……游魂在四爻、归魂在三爻；应爻恒与世爻相隔三位
4. 六亲：以本宫五行为「我」——生我者父母、我生者子孙、克我者官鬼、我克者妻财、比和者兄弟
5. 六神：按日干起——甲乙青龙、丙丁朱雀、戊勾陈、己螣蛇、庚辛白虎、壬癸玄武，自初爻向上顺排
6. 伏神：本卦六爻缺某六亲时，取本宫首卦（八纯卦）中该六亲之爻为伏神
7. 旬空：按日柱所在旬取空亡二支
8. 月建/日辰旺衰：旺相休囚死（当令旺、令生相、生令休、克令囚、令克死）

纪律：
- 不引入任何断语文案，只产出可机读的装卦结构；
- 所有表都是显式常量，便于逐表校验（tests/test_liuyao_najia.py 逐表核对）；
- 无法确定的项不猜：缺六亲就给伏神，伏神也缺则标记 ``无法立用神``。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# 基础常量
# ---------------------------------------------------------------------------

STEM_ORDER: Tuple[str, ...] = tuple("甲乙丙丁戊己庚辛壬癸")
BRANCH_ORDER: Tuple[str, ...] = tuple("子丑寅卯辰巳午未申酉戌亥")

# 地支五行
BRANCH_ELEMENT: Dict[str, str] = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 八卦五行（本宫五行）
TRIGRAM_ELEMENT: Dict[str, str] = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 八卦符号（自下而上，1=阳爻，0=阴爻）
TRIGRAM_LINES: Dict[str, Tuple[int, int, int]] = {
    "乾": (1, 1, 1), "兑": (1, 1, 0), "离": (1, 0, 1), "震": (1, 0, 0),
    "巽": (0, 1, 1), "坎": (0, 1, 0), "艮": (0, 0, 1), "坤": (0, 0, 0),
}

# 八卦纳甲：内卦（初二三爻）与外卦（四五六爻）的 (天干, 三支)
NAJIA: Dict[str, Dict[str, Tuple[str, Tuple[str, str, str]]]] = {
    "乾": {"内": ("甲", ("子", "寅", "辰")), "外": ("壬", ("午", "申", "戌"))},
    "坤": {"内": ("乙", ("未", "巳", "卯")), "外": ("癸", ("丑", "亥", "酉"))},
    "震": {"内": ("庚", ("子", "寅", "辰")), "外": ("庚", ("午", "申", "戌"))},
    "巽": {"内": ("辛", ("丑", "亥", "酉")), "外": ("辛", ("未", "巳", "卯"))},
    "坎": {"内": ("戊", ("寅", "辰", "午")), "外": ("戊", ("申", "戌", "子"))},
    "离": {"内": ("己", ("卯", "丑", "亥")), "外": ("己", ("酉", "未", "巳"))},
    "艮": {"内": ("丙", ("辰", "午", "申")), "外": ("丙", ("戌", "子", "寅"))},
    "兑": {"内": ("丁", ("巳", "卯", "丑")), "外": ("丁", ("亥", "酉", "未"))},
}

# 六十四卦：下卦/上卦 → 卦名
HEXAGRAM_NAME: Dict[Tuple[str, str], str] = {
    ("乾", "乾"): "乾为天", ("坤", "坤"): "坤为地", ("震", "震"): "震为雷",
    ("巽", "巽"): "巽为风", ("坎", "坎"): "坎为水", ("离", "离"): "离为火",
    ("艮", "艮"): "艮为山", ("兑", "兑"): "兑为泽",
    ("乾", "坤"): "天地否", ("坤", "乾"): "地天泰",
    ("乾", "震"): "天雷无妄", ("震", "乾"): "雷天大壮",
    ("乾", "坎"): "天水讼", ("坎", "乾"): "水天需",
    ("乾", "艮"): "天山遁", ("艮", "乾"): "山天大畜",
    ("乾", "巽"): "天风姤", ("巽", "乾"): "风天小畜",
    ("乾", "离"): "天火同人", ("离", "乾"): "火天大有",
    ("乾", "兑"): "天泽履", ("兑", "乾"): "泽天夬",
    ("坤", "震"): "地雷复", ("震", "坤"): "雷地豫",
    ("坤", "坎"): "地水师", ("坎", "坤"): "水地比",
    ("坤", "艮"): "地山谦", ("艮", "坤"): "山地剥",
    ("坤", "巽"): "地风升", ("巽", "坤"): "风地观",
    ("坤", "离"): "地火明夷", ("离", "坤"): "火地晋",
    ("坤", "兑"): "地泽临", ("兑", "坤"): "泽地萃",
    ("震", "坎"): "雷水解", ("坎", "震"): "水雷屯",
    ("震", "艮"): "雷山小过", ("艮", "震"): "山雷颐",
    ("震", "巽"): "雷风恒", ("巽", "震"): "风雷益",
    ("震", "离"): "雷火丰", ("离", "震"): "火雷噬嗑",
    ("震", "兑"): "雷泽归妹", ("兑", "震"): "泽雷随",
    ("坎", "艮"): "水山蹇", ("艮", "坎"): "山水蒙",
    ("坎", "巽"): "水风井", ("巽", "坎"): "风水涣",
    ("坎", "离"): "水火既济", ("离", "坎"): "火水未济",
    ("坎", "兑"): "水泽节", ("兑", "坎"): "泽水困",
    ("离", "艮"): "火山旅", ("艮", "离"): "山火贲",
    ("离", "巽"): "火风鼎", ("巽", "离"): "风火家人",
    ("离", "兑"): "火泽睽", ("兑", "离"): "泽火革",
    ("艮", "巽"): "山风蛊", ("巽", "艮"): "风山渐",
    ("艮", "兑"): "山泽损", ("兑", "艮"): "泽山咸",
    ("巽", "兑"): "风泽中孚", ("兑", "巽"): "泽风大过",
}

# 京房八宫：每宫八卦（本宫、一世、二世、三世、四世、五世、游魂、归魂）
PALACE_HEXAGRAMS: Dict[str, Tuple[str, ...]] = {
    "乾": ("乾为天", "天风姤", "天山遁", "天地否", "风地观", "山地剥", "火地晋", "火天大有"),
    "兑": ("兑为泽", "泽水困", "泽地萃", "泽山咸", "水山蹇", "地山谦", "雷山小过", "雷泽归妹"),
    "离": ("离为火", "火山旅", "火风鼎", "火水未济", "山水蒙", "风水涣", "天水讼", "天火同人"),
    "震": ("震为雷", "雷地豫", "雷水解", "雷风恒", "地风升", "水风井", "泽风大过", "泽雷随"),
    "巽": ("巽为风", "风天小畜", "风火家人", "风雷益", "天雷无妄", "火雷噬嗑", "山雷颐", "山风蛊"),
    "坎": ("坎为水", "水泽节", "水雷屯", "水火既济", "泽火革", "雷火丰", "地火明夷", "地水师"),
    "艮": ("艮为山", "山火贲", "山天大畜", "山泽损", "火泽睽", "天泽履", "风泽中孚", "风山渐"),
    "坤": ("坤为地", "地雷复", "地泽临", "地天泰", "雷天大壮", "泽天夬", "水天需", "水地比"),
}

# 八宫卦序对应的世爻位置（1..6）
PALACE_SHI_POSITION: Dict[str, Tuple[int, ...]] = {
    "乾": (6, 1, 2, 3, 4, 5, 4, 3),
    "兑": (6, 1, 2, 3, 4, 5, 4, 3),
    "离": (6, 1, 2, 3, 4, 5, 4, 3),
    "震": (6, 1, 2, 3, 4, 5, 4, 3),
    "巽": (6, 1, 2, 3, 4, 5, 4, 3),
    "坎": (6, 1, 2, 3, 4, 5, 4, 3),
    "艮": (6, 1, 2, 3, 4, 5, 4, 3),
    "坤": (6, 1, 2, 3, 4, 5, 4, 3),
}

# 六亲
SIX_KIN = ("父母", "兄弟", "子孙", "妻财", "官鬼")

# 六神（自青龙起顺排）
SIX_SPIRITS: Tuple[str, ...] = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")
SPIRIT_START_BY_STEM: Dict[str, int] = {
    "甲": 0, "乙": 0,  # 青龙
    "丙": 1, "丁": 1,  # 朱雀
    "戊": 2,           # 勾陈
    "己": 3,           # 螣蛇
    "庚": 4, "辛": 4,  # 白虎
    "壬": 5, "癸": 5,  # 玄武
}

# 五行生克
ELEMENT_GENERATES: Dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
ELEMENT_CONTROLS: Dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _relation(this_el: str, other_el: str) -> str:
    """this 与 other 的五行关系（站在 this 的角度）。"""
    if this_el == other_el:
        return "同"
    if ELEMENT_GENERATES[other_el] == this_el:
        return "生我"
    if ELEMENT_GENERATES[this_el] == other_el:
        return "我生"
    if ELEMENT_CONTROLS[other_el] == this_el:
        return "克我"
    if ELEMENT_CONTROLS[this_el] == other_el:
        return "我克"
    return "无"


def six_kin_of(palace_element: str, branch: str) -> str:
    """本宫五行与爻支五行定六亲。"""
    rel = _relation(palace_element, BRANCH_ELEMENT[branch])
    return {
        "生我": "父母",
        "同": "兄弟",
        "我生": "子孙",
        "克我": "官鬼",
        "我克": "妻财",
    }.get(rel, "未知")


def _palace_of(hex_name: str) -> str:
    for palace, names in PALACE_HEXAGRAMS.items():
        if hex_name in names:
            return palace
    raise KeyError(f"卦名不在八宫表：{hex_name}")


def _index_in_palace(hex_name: str) -> int:
    palace = _palace_of(hex_name)
    return PALACE_HEXAGRAMS[palace].index(hex_name)


def _trigrams_of(hex_name: str) -> Tuple[str, str]:
    """卦名 → (上卦, 下卦)。卦名表以「上卦+下卦」为键（如天地否=上乾下坤）。"""
    for (upper, lower), name in HEXAGRAM_NAME.items():
        if name == hex_name:
            return upper, lower
    raise KeyError(f"未知卦名：{hex_name}")


def hexagram_lines(hex_name: str) -> Tuple[int, ...]:
    """六爻阴阳（自下而上，1=阳，0=阴）。"""
    upper, lower = _trigrams_of(hex_name)
    return TRIGRAM_LINES[lower] + TRIGRAM_LINES[upper]


def _najia_stem_branch(lower: str, upper: str) -> List[Tuple[str, str]]:
    """六爻纳甲（初爻至上爻的 (天干, 地支)）。"""
    li, lb = NAJIA[lower]["内"]
    ui, ub = NAJIA[upper]["外"]
    return [(li, b) for b in lb] + [(ui, b) for b in ub]


def shi_ying(hex_name: str) -> Tuple[int, int]:
    """世爻、应爻位置（1..6）。应爻恒与世爻相隔三位。"""
    palace = _palace_of(hex_name)
    shi = PALACE_SHI_POSITION[palace][_index_in_palace(hex_name)]
    ying = shi + 3 if shi <= 3 else shi - 3
    return shi, ying


@dataclass
class Line:
    """一爻的装卦结果。"""
    position: int          # 1..6（初爻=1）
    yin_yang: int          # 1=阳 0=阴（本卦）
    moving: bool           # 是否动爻
    stem: str              # 纳甲天干
    branch: str            # 纳甲地支
    element: str           # 地支五行
    six_kin: str           # 六亲
    spirit: str            # 六神
    is_shi: bool = False   # 是否世爻
    is_ying: bool = False  # 是否应爻
    kong: bool = False     # 是否旬空
    changed_stem: str = ""  # 变爻纳甲天干（动爻才有）
    changed_branch: str = ""  # 变爻纳甲地支
    changed_element: str = ""
    changed_six_kin: str = ""
    to_line: str = ""      # 回头生/回头克/无


@dataclass
class LiuYaoChart:
    """六爻装卦盘。"""
    hexagram: str
    palace: str
    palace_element: str
    lower: str
    upper: str
    shi: int
    ying: int
    lines: List[Line] = field(default_factory=list)
    moving_positions: List[int] = field(default_factory=list)
    changed_hexagram: str = ""      # 变卦名（有动爻时）
    fu_shen: List[Line] = field(default_factory=list)  # 伏神
    day_stem: str = ""
    day_branch: str = ""
    month_branch: str = ""
    xun_kong: Tuple[str, ...] = ()
    missing_kin: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def by_position(self, position: int) -> Optional[Line]:
        for ln in self.lines:
            if ln.position == position:
                return ln
        return None

    def kin_lines(self, kin: str) -> List[Line]:
        return [ln for ln in self.lines if ln.six_kin == kin]

    def to_dict(self) -> dict:
        return {
            "hexagram": self.hexagram,
            "palace": self.palace,
            "palace_element": self.palace_element,
            "lower": self.lower,
            "upper": self.upper,
            "shi": self.shi,
            "ying": self.ying,
            "moving_positions": list(self.moving_positions),
            "changed_hexagram": self.changed_hexagram,
            "xun_kong": list(self.xun_kong),
            "missing_kin": list(self.missing_kin),
            "notes": list(self.notes),
            "lines": [
                {
                    "position": ln.position,
                    "yin_yang": ln.yin_yang,
                    "moving": ln.moving,
                    "stem": ln.stem,
                    "branch": ln.branch,
                    "element": ln.element,
                    "six_kin": ln.six_kin,
                    "spirit": ln.spirit,
                    "is_shi": ln.is_shi,
                    "is_ying": ln.is_ying,
                    "kong": ln.kong,
                    "changed_stem": ln.changed_stem,
                    "changed_branch": ln.changed_branch,
                    "changed_element": ln.changed_element,
                    "changed_six_kin": ln.changed_six_kin,
                    "to_line": ln.to_line,
                }
                for ln in self.lines
            ],
            "fu_shen": [
                {
                    "position": ln.position,
                    "yin_yang": ln.yin_yang,
                    "stem": ln.stem,
                    "branch": ln.branch,
                    "element": ln.element,
                    "six_kin": ln.six_kin,
                }
                for ln in self.fu_shen
            ],
            "day_stem": self.day_stem,
            "day_branch": self.day_branch,
            "month_branch": self.month_branch,
        }


def xun_kong_of(day_stem: str, day_branch: str) -> Tuple[str, str]:
    """由日柱求旬空二支。"""
    si = STEM_ORDER.index(day_stem)
    bi = BRANCH_ORDER.index(day_branch)
    # 日柱在六十甲子中的序号：满足 stem/branch 同余
    # 甲子=0；六十甲子序 n 满足 n%10==si 且 n%12==bi
    for n in range(60):
        if n % 10 == si and n % 12 == bi:
            break
    else:  # pragma: no cover - 合法干支必能找到
        raise ValueError(f"非法日柱：{day_stem}{day_branch}")
    head = (n // 10) * 10  # 旬首序号
    kb1 = BRANCH_ORDER[(head + 10) % 12]
    kb2 = BRANCH_ORDER[(head + 11) % 12]
    return kb1, kb2


def _changed_hexagram(hex_name: str, moving: Sequence[int]) -> str:
    """动爻反转后的变卦名。"""
    lines = list(hexagram_lines(hex_name))
    for pos in moving:
        lines[pos - 1] = 1 - lines[pos - 1]
    lower = _trigram_from_lines(tuple(lines[:3]))
    upper = _trigram_from_lines(tuple(lines[3:]))
    return HEXAGRAM_NAME[(upper, lower)]


def _trigram_from_lines(lines: Sequence[int]) -> str:
    for name, pattern in TRIGRAM_LINES.items():
        if tuple(lines) == pattern:
            return name
    raise ValueError(f"三爻不成卦：{lines}")


def _changed_relation(changed_element: str, original_element: str) -> str:
    # 站在动爻（原卦之爻）角度：
    # 变爻生原爻 = 回头生；变爻克原爻 = 回头克；原爻生变爻 = 回头泄；原爻克变爻 = 回头耗
    rel = _relation(changed_element, original_element)
    return {
        "我生": "回头生",   # changed 生 original
        "我克": "回头克",   # changed 克 original
        "生我": "回头泄",   # original 生 changed
        "克我": "回头耗",   # original 克 changed
    }.get(rel, "比和")


def build_liuyao_chart(
    day_stem: str,
    day_branch: str,
    month_branch: str,
    moving: Iterable[int],
    hex_name: Optional[str] = None,
    *,
    lower: Optional[str] = None,
    upper: Optional[str] = None,
) -> LiuYaoChart:
    """装一卦。

    参数：
        day_stem/day_branch: 起卦日干支（六神、旬空用）
        month_branch: 月建地支（旺衰用，可留空）
        moving: 动爻位置集合（1..6）
        hex_name: 本卦名；或用 lower/upper 指定上下卦
    """
    if hex_name is None:
        if lower is None or upper is None:
            raise ValueError("必须给 hex_name 或 lower+upper")
        hex_name = HEXAGRAM_NAME[(upper, lower)]
    if hex_name not in [n for names in PALACE_HEXAGRAMS.values() for n in names]:
        raise KeyError(f"未知卦名：{hex_name}")

    moving_set = {int(m) for m in moving}
    bad = [m for m in moving_set if not 1 <= m <= 6]
    if bad:
        raise ValueError(f"动爻位置必须在 1..6：{bad}")

    palace = _palace_of(hex_name)
    palace_element = TRIGRAM_ELEMENT[palace]
    upper_t, lower_t = _trigrams_of(hex_name)
    shi, ying = shi_ying(hex_name)
    stems_branches = _najia_stem_branch(lower_t, upper_t)
    yin_yang = hexagram_lines(hex_name)

    spirit_start = SPIRIT_START_BY_STEM[day_stem]
    kong_branches = xun_kong_of(day_stem, day_branch) if (day_stem or day_branch) else ()

    changed_name = _changed_hexagram(hex_name, moving_set) if moving_set else ""
    changed_sb: List[Tuple[str, str]] = []
    changed_yy: Tuple[int, ...] = ()
    changed_palace_element = ""
    if changed_name:
        cu, cl = _trigrams_of(changed_name)
        changed_sb = _najia_stem_branch(cl, cu)
        changed_yy = hexagram_lines(changed_name)
        changed_palace_element = TRIGRAM_ELEMENT[_palace_of(changed_name)]

    lines: List[Line] = []
    for i in range(6):
        pos = i + 1
        stem, branch = stems_branches[i]
        element = BRANCH_ELEMENT[branch]
        kin = six_kin_of(palace_element, branch)
        spirit = SIX_SPIRITS[(spirit_start + i) % 6]
        moving = pos in moving_set
        ln = Line(
            position=pos,
            yin_yang=yin_yang[i],
            moving=moving,
            stem=stem,
            branch=branch,
            element=element,
            six_kin=kin,
            spirit=spirit,
            is_shi=(pos == shi),
            is_ying=(pos == ying),
            kong=(branch in kong_branches),
        )
        if moving and changed_sb:
            cstem, cbranch = changed_sb[i]
            ln.changed_stem = cstem
            ln.changed_branch = cbranch
            ln.changed_element = BRANCH_ELEMENT[cbranch]
            ln.changed_six_kin = six_kin_of(changed_palace_element, cbranch)
            ln.to_line = _changed_relation(ln.changed_element, element)
        lines.append(ln)

    # 伏神：本卦六爻缺六亲时，取本宫首卦同六亲之爻
    present = {ln.six_kin for ln in lines}
    missing = [k for k in SIX_KIN if k not in present]
    fu_shen: List[Line] = []
    if missing:
        pure = PALACE_HEXAGRAMS[palace][0]
        p_upper, p_lower = _trigrams_of(pure)
        p_sb = _najia_stem_branch(p_lower, p_upper)
        p_yy = hexagram_lines(pure)
        p_shi, _ = shi_ying(pure)
        for i, (pstem, pbranch) in enumerate(p_sb):
            pkin = six_kin_of(palace_element, pbranch)
            if pkin in missing:
                fu_shen.append(
                    Line(
                        position=i + 1,
                        yin_yang=p_yy[i],
                        moving=False,
                        stem=pstem,
                        branch=pbranch,
                        element=BRANCH_ELEMENT[pbranch],
                        six_kin=pkin,
                        spirit="",  # 伏神不配六神
                        is_shi=(i + 1 == p_shi),
                    )
                )
        for k in missing:
            if k not in {f.six_kin for f in fu_shen}:
                fu_shen.append(
                    Line(
                        position=0, yin_yang=-1, moving=False, stem="", branch="",
                        element="", six_kin=k, spirit="",
                    )
                )

    notes: List[str] = []
    if fu_shen:
        notes.append("本卦缺 " + "/".join(missing) + "，已按本宫首卦取伏神")
    if not month_branch:
        notes.append("未给月建，旺衰未判")
    if not day_stem or not day_branch:
        notes.append("未给日柱，六神/旬空未判")

    return LiuYaoChart(
        hexagram=hex_name,
        palace=palace,
        palace_element=palace_element,
        lower=lower_t,
        upper=upper_t,
        shi=shi,
        ying=ying,
        lines=lines,
        moving_positions=sorted(moving_set),
        changed_hexagram=changed_name,
        fu_shen=fu_shen,
        day_stem=day_stem,
        day_branch=day_branch,
        month_branch=month_branch,
        xun_kong=kong_branches,
        missing_kin=missing,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# 旺衰（月建 / 日辰）
# ---------------------------------------------------------------------------

WANG_LEVELS: Tuple[str, ...] = ("旺", "相", "休", "囚", "死")


def branch_wangshuai(line_element: str, month_element: str) -> str:
    """按「当令旺、令生相、生令休、克令囚、令克死」判旺衰。

    参数为爻之五行与月建之五行。
    """
    rel = _relation(month_element, line_element)
    return {
        "同": "旺",      # 当令
        "我生": "相",    # 月建生爻
        "生我": "休",    # 爻生月建
        "克我": "囚",    # 爻克月建（克令）
        "我克": "死",    # 月建克爻（令克）
    }.get(rel, "未知")


def day_influence(line_branch: str, day_branch: str) -> str:
    """日辰对爻的直接影响：日建（同支）、日冲（相隔六位）、日合（六合）、日生克。"""
    bi = BRANCH_ORDER.index(line_branch)
    di = BRANCH_ORDER.index(day_branch)
    if line_branch == day_branch:
        return "日建"
    if (bi + 6) % 12 == di:
        return "日冲"
    if BRANCH_LIUHE.get(line_branch) == day_branch:
        return "日合"
    rel = _relation(BRANCH_ELEMENT[day_branch], BRANCH_ELEMENT[line_branch])
    return {
        "我生": "日生",   # 日辰生爻
        "我克": "日克",   # 日辰克爻
        "生我": "日泄",   # 爻生日辰
        "克我": "日耗",   # 爻克日辰
    }.get(rel, "无")


BRANCH_LIUHE: Dict[str, str] = {
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午",
}


def month_break(line_branch: str, month_branch: str) -> bool:
    """月破：爻支与月建相冲。"""
    bi = BRANCH_ORDER.index(line_branch)
    mi = BRANCH_ORDER.index(month_branch)
    return (bi + 6) % 12 == mi


def select_yong_shen(chart: LiuYaoChart, kin: str) -> List[Line]:
    """取用神：按六亲取本卦之爻；若缺则以伏神；仍缺则返回空并由调用方标「无法立用神」。"""
    hits = chart.kin_lines(kin)
    if hits:
        return hits
    return [ln for ln in chart.fu_shen if ln.six_kin == kin]


def yong_shen_status(chart: LiuYaoChart, kin: str) -> dict:
    """用神状态（只做可机读的旺衰/空破/动变，不做断语）。"""
    ys = select_yong_shen(chart, kin)
    if not ys:
        return {"six_kin": kin, "found": False, "reason": "本卦与伏神俱无此六亲，无法立用神"}
    out = []
    month_el = BRANCH_ELEMENT.get(chart.month_branch, "")
    for ln in ys:
        rec = {
            "position": ln.position,
            "stem_branch": f"{ln.stem}{ln.branch}",
            "element": ln.element,
            "from_fu_shen": ln.position == 0 or ln in chart.fu_shen,
            "kong": ln.branch in chart.xun_kong,
            "month_break": month_break(ln.branch, chart.month_branch) if chart.month_branch else False,
            "wangshuai": branch_wangshuai(ln.element, month_el) if month_el else "",
            "day_influence": day_influence(ln.branch, chart.day_branch) if chart.day_branch else "",
            "moving": ln.moving,
            "changed": f"{ln.changed_stem}{ln.changed_branch}" if ln.changed_branch else "",
            "to_line": ln.to_line,
        }
        out.append(rec)
    return {"six_kin": kin, "found": True, "lines": out}
