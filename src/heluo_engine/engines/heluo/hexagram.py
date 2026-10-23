"""河洛卦象结构分析模块（Module 7）

负责：卦象的完整结构分析（不依赖计算引擎，纯结构分析）
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .numbers import SIXTY_FOUR_HEXAGRAMS

# 八卦三画 -> 卦名（自下而上编码，'1'=阳）
_LINES_TO_TRIGRAM = {
    '111': '乾', '110': '兑', '101': '离', '100': '震',
    '011': '巽', '010': '坎', '001': '艮', '000': '坤',
}
# 错卦：先天方位对宫 —— 引用单一来源，不再自存一份
from .hexagram_state import QIANXI_DUKONG as _QIANXI_DUKONG


def _lines_to_gua_name(lines: list[int]) -> str:
    """六爻（自下而上）-> 六十四卦名。"""
    lo = _LINES_TO_TRIGRAM[''.join('1' if l == 1 else '0' for l in lines[0:3])]
    up = _LINES_TO_TRIGRAM[''.join('1' if l == 1 else '0' for l in lines[3:6])]
    return SIXTY_FOUR_HEXAGRAMS.get((up, lo), f'{up}{lo}')


def compute_hu_gua(lines: list[int]) -> str:
    """互体（《河洛真数·起例卷之上·互体伏体论》）。

    原文「以正体内外卦除初上二爻，用中四爻，交互成卦，谓之互体」：
      下互 = 二三四爻 = lines[1:4]
      上互 = 三四五爻 = lines[2:5]
    原典例（渐卦）：「九五六四九三互离，六四九三六二互坎，合之为未济」
    → 上互离、下互坎、未济。
    """
    hu_low = _LINES_TO_TRIGRAM[''.join('1' if l == 1 else '0' for l in lines[1:4])]
    hu_up = _LINES_TO_TRIGRAM[''.join('1' if l == 1 else '0' for l in lines[2:5])]
    return SIXTY_FOUR_HEXAGRAMS.get((hu_up, hu_low), f'{hu_up}{hu_low}')


def compute_cuo_gua(upper: str, lower: str) -> str:
    """错卦：上下卦各取对宫（六爻全变）。"""
    return SIXTY_FOUR_HEXAGRAMS.get(
        (_QIANXI_DUKONG.get(upper, upper), _QIANXI_DUKONG.get(lower, lower)),
        '')


#: 三画卦的**倒转**（六爻整体倒转时，三画卦内部也要跟着倒）。
#: 乾☰ 倒转仍乾、坤☷ 仍坤、坎☵ 仍坎、离☲ 仍离；
#: 震☳ 倒转成艮☶、艮☶ 倒转成震☳、巽☴ 倒转成兑☱、兑☱ 倒转成巽☴。
_TRIGRAM_REVERSED = {
    "乾": "乾", "坤": "坤", "坎": "坎", "离": "离",
    "震": "艮", "艮": "震", "巽": "兑", "兑": "巽",
}


def compute_zong_gua(upper: str, lower: str) -> str:
    """综卦（反对）：**六爻整体倒转**。

    原典（起例卷之下 L46-L48「六十四卦反对图」，逐字）：
        L46: 六十四卦反对图
        L47: 上经正卦六，反卦二十四，共用十八卦，成三十卦。
             下经正卦二，反卦三十二，亦用十八卦，成三十四卦。
        L48: 又尝合上下经始终而论之，乾坤天地也，坎离水火也。以体言也……

    「正卦」即**自反卦**（倒转后仍是自己）。原典计数：上经 6 个、下经 2 个，
    合计 **8 个自反卦**。

    ⚠ 2026-10-22 修正：原实现是 ``SIXTY_FOUR_HEXAGRAMS[(lower, upper)]``
    —— 只把上下卦**对调**，三画卦内部没有倒。这既不等于「六爻倒转」，
    也与仓内另一份综卦表（``guajie.ZONG_GUA``，注释明写「六爻倒转」）
    在 **64 卦中 48 卦**上给出不同结果；其自反卦只有 4 个
    （乾坤坎离），与原典「上经正卦六、下经正卦二」对不上。

    正确算法：六爻倒转后，**下卦变上卦、上卦变下卦，且三画卦内部亦倒**
    （震↔艮、巽↔兑；乾坤坎离不变）。
    按此算法，自反卦恰为 8 个 ——
        上经 6 个：乾、坤、坎、离、颐、大过
        下经 2 个：中孚、小过
    与原典计数**逐位吻合**；另两种口径分别得 4/4 与 4/6，均不符。
    """
    new_upper = _TRIGRAM_REVERSED.get(lower, lower)
    new_lower = _TRIGRAM_REVERSED.get(upper, upper)
    return SIXTY_FOUR_HEXAGRAMS.get((new_upper, new_lower), '')


@dataclass(frozen=True)
class HexagramStructure:
    """六十四卦结构分析结果"""
    name: str                # 六十四卦名
    upper: str               # 上卦
    lower: str               # 下卦
    lines: list[int]         # 六爻
    ti_yong: dict            # 体用关系
    sheng_ke: str            # 生克关系
    cheng_cheng: list[str]   # 承关系
    bi: list[str]            # 比关系
    ying: list[str]          # 应关系
    hu_gua: str | None       # 互卦
    cuo_gua: str | None      # 错卦
    zong_gua: str | None     # 综卦


# 八卦五行
TRIGRAM_ELEMENT: dict[str, str] = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 五行生克
SHENG_MAP = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}
KE_MAP = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}

# 六十四卦互卦、错卦、综卦预定义表
# 互卦：取二三四爻为上卦，三四五爻为下卦
# 错卦：阴阳全反
# 综卦：上下翻转（倒过来看）

# 六十四卦完整结构表（保留已有8卦作为缓存，其余自动解析）
HEXAGRAM_STRUCTURES: dict[str, dict] = {
    "乾为天": {"upper": "乾", "lower": "乾", "lines": [1,1,1,1,1,1]},
    "坤为地": {"upper": "坤", "lower": "坤", "lines": [-1,-1,-1,-1,-1,-1]},
    "水雷屯": {"upper": "坎", "lower": "震", "lines": [1,-1,-1,-1,1,-1]},
    "山水蒙": {"upper": "艮", "lower": "坎", "lines": [-1,1,-1,-1,-1,1]},
    "地天泰": {"upper": "坤", "lower": "乾", "lines": [1,1,1,-1,-1,-1]},
    "天雷无妄": {"upper": "乾", "lower": "震", "lines": [1,-1,-1,1,1,1]},
    "天泽履": {"upper": "乾", "lower": "兑", "lines": [1,1,-1,1,1,1]},
    "地风升": {"upper": "坤", "lower": "巽", "lines": [-1,1,1,-1,-1,-1]},
}

# 八卦三爻（从初爻到上爻，从下到上）
# 乾☰三阳, 兑☱上缺, 离☲中虚, 震☳仰盂, 巽☴下断, 坎☵中实, 艮☶覆碗, 坤☷三阴
_TRIGRAM_LINES: dict[str, list[int]] = {
    "乾": [1, 1, 1],
    "兑": [1, 1, -1],
    "离": [1, -1, 1],
    "震": [1, -1, -1],
    "巽": [-1, 1, 1],
    "坎": [-1, 1, -1],
    "艮": [-1, -1, 1],
    "坤": [-1, -1, -1],
}

# 自然象 → 八卦名
_NATURE_TO_TRIGRAM: dict[str, str] = {
    "天": "乾", "泽": "兑", "火": "离", "雷": "震",
    "风": "巽", "水": "坎", "山": "艮", "地": "坤",
}

# 从 yi.core 导入六十四卦映射（打破循环依赖）
from ..yi.core import (
    SIXTY_FOUR_MAP as _SIXTY_FOUR_MAP,
    NAME_TO_TRIGRAMS as _NAME_TO_TRIGRAMS,
    TRIGRAM_LINES as _TRIGRAM_LINES,
    NATURE_TO_TRIGRAM as _NATURE_TO_TRIGRAM,
    compute_ti_yong_relation as _compute_ti_yong,
)


def _parse_hexagram_name(hexagram_name: str) -> tuple[str, str] | None:
    """从卦名解析(上卦, 下卦). 支持三字卦名/四字卦名/单字卦名."""
    # 1. 优先用反向映射表（最准确，覆盖64卦）
    if hexagram_name in _NAME_TO_TRIGRAMS:
        return _NAME_TO_TRIGRAMS[hexagram_name]

    # 2. 三字卦名: 如"水山蹇" = 上(水→坎) + 下(山→艮) + 卦名(蹇)
    if len(hexagram_name) == 3:
        upper_nature = hexagram_name[0]
        lower_nature = hexagram_name[1]
        if upper_nature in _NATURE_TO_TRIGRAM and lower_nature in _NATURE_TO_TRIGRAM:
            return (_NATURE_TO_TRIGRAM[upper_nature], _NATURE_TO_TRIGRAM[lower_nature])

    # 3. 四字卦名: 如"乾为天" = 上下同卦(乾)
    if len(hexagram_name) == 4 and hexagram_name[1:3] == "为":
        trigram = hexagram_name[0]
        if trigram in _TRIGRAM_LINES:
            return (trigram, trigram)

    return None


def _derive_lines(upper: str, lower: str) -> list[int]:
    """从上卦/下卦推导六爻(从初爻到上爻, 即下卦三爻+上卦三爻)."""
    lower_lines = _TRIGRAM_LINES.get(lower, [0, 0, 0])
    upper_lines = _TRIGRAM_LINES.get(upper, [0, 0, 0])
    return lower_lines + upper_lines


def analyze_hexagram(hexagram_name: str) -> HexagramStructure | None:
    """
    分析卦象的完整结构关系。

    输入：六十四卦名
    输出：卦的完整结构分析

    包括：
    - 上下卦
    - 体用生克
    - 承乘比应
    - 互卦/错卦/综卦

    V2: 支持全部64卦（从卦名自动解析上下卦+推导六爻），不再依赖硬编码。
    """
    # 1. 优先查缓存
    if hexagram_name in HEXAGRAM_STRUCTURES:
        struct = HEXAGRAM_STRUCTURES[hexagram_name]
        upper, lower, lines = struct["upper"], struct["lower"], struct["lines"]
    else:
        # 2. 从卦名自动解析
        parsed = _parse_hexagram_name(hexagram_name)
        if parsed is None:
            return None
        upper, lower = parsed
        lines = _derive_lines(upper, lower)
        # 缓存结果
        HEXAGRAM_STRUCTURES[hexagram_name] = {"upper": upper, "lower": lower, "lines": lines}

    # 体用关系：下卦为体，上卦为用
    ti_element = TRIGRAM_ELEMENT.get(lower, "?")
    yong_element = TRIGRAM_ELEMENT.get(upper, "?")

    # 生克关系（V2修复: 原标签全部搞反）
    # SHENG_MAP[x]=y 表示 x生y; KE_MAP[x]=y 表示 x克y
    # 用生体: SHENG_MAP[yong]==ti → 吉
    # 用克体: KE_MAP[yong]==ti → 凶
    # 体生用: SHENG_MAP[ti]==yong → 泄
    # 体克用: KE_MAP[ti]==yong → 耗(中平)
    if SHENG_MAP.get(yong_element) == ti_element:
        sheng_ke = "用生体（吉）"
    elif KE_MAP.get(yong_element) == ti_element:
        sheng_ke = "用克体（凶）"
    elif SHENG_MAP.get(ti_element) == yong_element:
        sheng_ke = "体生用（泄）"
    elif KE_MAP.get(ti_element) == yong_element:
        sheng_ke = "体克用（耗）"
    else:
        sheng_ke = "比和（平）"

    # 体用详情
    ti_yong = {
        "ti": lower,
        "ti_element": ti_element,
        "yong": upper,
        "yong_element": yong_element,
        "relation": sheng_ke,
    }

    # 承乘比应（承/乘/比/应四关系，规则见下）
    cheng_cheng = []
    bi = []
    ying = []

    # 承：阴爻在阳爻之下
    for i in range(5):
        if lines[i] == -1 and lines[i+1] == 1:
            cheng_cheng.append(f"{i+1}承{i+2}")

    # 乘：阴爻在阳爻之上
    for i in range(5):
        if lines[i] == 1 and lines[i+1] == -1:
            cheng_cheng.append(f"{i+1}乘{i+2}")

    # 比：相邻爻同性质
    for i in range(5):
        if lines[i] == lines[i+1]:
            bi.append(f"{i+1}比{i+2}")

    # 应：初/四、二/五、三/上的对应关系
    for pair in [(0, 3), (1, 4), (2, 5)]:
        if lines[pair[0]] == lines[pair[1]]:
            ying.append(f"{pair[0]+1}应{pair[1]+1}")

    return HexagramStructure(
        name=hexagram_name,
        upper=upper,
        lower=lower,
        lines=lines,
        ti_yong=ti_yong,
        sheng_ke=sheng_ke,
        cheng_cheng=cheng_cheng,
        bi=bi,
        ying=ying,
        hu_gua=compute_hu_gua(lines),   # 互体：除初上，取中四爻交互
        cuo_gua=compute_cuo_gua(upper, lower),  # 错卦：六爻全变
        zong_gua=compute_zong_gua(upper, lower),  # 综卦：上下易位
    )


def compute_ti_yong(upper: str, lower: str) -> dict:
    """体用关系分析（V2修复: 原标签全部搞反）"""
    ti_element = TRIGRAM_ELEMENT.get(lower, "?")
    yong_element = TRIGRAM_ELEMENT.get(upper, "?")

    if SHENG_MAP.get(yong_element) == ti_element:
        relation = "用生体（吉）"
    elif KE_MAP.get(yong_element) == ti_element:
        relation = "用克体（凶）"
    elif SHENG_MAP.get(ti_element) == yong_element:
        relation = "体生用（泄）"
    elif KE_MAP.get(ti_element) == yong_element:
        relation = "体克用（耗）"
    else:
        relation = "比和（平）"

    return {
        "ti": lower,
        "ti_element": ti_element,
        "yong": upper,
        "yong_element": yong_element,
        "relation": relation,
    }


def compute_cheng_cheng_bi_ying(lines: list[int]) -> dict:
    """承乘比应关系分析"""
    result = {"cheng": [], "bi": [], "ying": []}

    # 承乘
    for i in range(5):
        if lines[i] == -1 and lines[i+1] == 1:
            result["cheng"].append(f"{i+1}承{i+2}")
        elif lines[i] == 1 and lines[i+1] == -1:
            result["cheng"].append(f"{i+1}乘{i+2}")

    # 比
    for i in range(5):
        if lines[i] == lines[i+1]:
            result["bi"].append(f"{i+1}比{i+2}")

    # 应
    for pair in [(0, 3), (1, 4), (2, 5)]:
        if lines[pair[0]] == lines[pair[1]]:
            result["ying"].append(f"{pair[0]+1}应{pair[1]+1}")

    return result
