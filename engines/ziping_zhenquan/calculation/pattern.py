"""PZZQ 月令取格派生（《子平真诠·论用神》· 引擎自有 Derived Facts，§65）。

依据原著原文（精校稿第24页）：
- 「八字用神，專求月令。以日干配月令地支，而生剋不同，格局分為財官印食。
   煞傷刃劫，此用神之不善而逆用之者也。」
- 「然亦有月令無用神者，如木生寅卯，月與日同，本身不可為用……
   是建祿月劫之格，非用而即用神也。」

第二层实现（透干取格，《论用神变化》第27页）：
- 本气透出天干 → 本气定格（「格成正財，正官乃其兼格」：变而不失本格）
- 本气不透、余/中气透出 → 透出者作主（「不透甲而透丙，則同知得以作主」）
- 多透次序：原著未明示。注家口径（《八格外格》「支藏两神并透，斟酌其一，
  以有力而无克合者为上」；今人「本气优先、先取月令再取月令外」）→ 暂定
  「月干>时干>年干」（月干透出紧贴月令最有力）；「有力/克合」细化待 Human 裁定

第三层实现（会支化局，《论用神变化》第27-28页）：
- 「丁生亥月，本為正官，支全卯未，則化為印」→ 月支参与三合局 → 以局五行×日干定格
- 「癸生寅月，藏甲透丙，會午會戌，則化傷為財」「乙生寅月，透戊為財，會午會戌，
  則月劫化為食傷」「丙生申月，本屬偏財，藏庚透壬，會子會辰，則化為煞」
- 本气透而化局 → 仍本格（「丙生寅月，午戌會劫，而又或透甲…仍為印而格不破」），
  化局作兼格标注（bureau_effect 含「不失本格」）

不重排盘：只消费日干/月支/月支藏干静态表/四柱天干地支。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from shared_types.fail_closed import FailClosedReason, FailClosedError

# 人元司令藏干表（L0 hidden_stems 若提供则优先）
# 2026-09-30: 改为读 LIORIN vendor，消除第二数据源。
#   原硬编码的 巳=["丙","庚","戊"] 中/余气颠倒（应 丙(本) 戊(中) 庚(余)），
#   会在 L0 未传 hidden 时静默给出错误本气。此处不再独立维护副本。
from engines.l0_paipan import branch_hidden_stems as _branch_hidden_stems

BRANCH_HIDDEN = _branch_hidden_stems()

STEM_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
STEM_YINYANG = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
}

# 阳干帝旺（阳刃）位
YANG_REN_POS = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}

# 十神 → 格局名（原著八格）
PATTERN_NAME = {
    "正官": "正官格", "七殺": "七煞格",
    "正財": "財格", "偏財": "財格",
    "正印": "印格", "偏印": "印格",
    "食神": "食神格", "傷官": "傷官格",
}

# 三合局（《论用神变化》会支化局；月支须参与）
SANHE: Dict[frozenset, str] = {
    frozenset(["申", "子", "辰"]): "水",
    frozenset(["亥", "卯", "未"]): "木",
    frozenset(["寅", "午", "戌"]): "火",
    frozenset(["巳", "酉", "丑"]): "金",
}

_PRODUCE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROL = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _ten_god(day_stem: str, target_stem: str) -> str:
    """标准十神（同我/我生/我克/克我/生我 × 阴阳）。"""
    d_el, d_yy = STEM_ELEMENT[day_stem], STEM_YINYANG[day_stem]
    t_el, t_yy = STEM_ELEMENT[target_stem], STEM_YINYANG[target_stem]
    same_yy = (d_yy == t_yy)
    if d_el == t_el:
        return "比肩" if same_yy else "劫財"
    if _PRODUCE[d_el] == t_el:      # 我生
        return "食神" if same_yy else "傷官"
    if _CONTROL[d_el] == t_el:      # 我克
        return "偏財" if same_yy else "正財"
    if _PRODUCE[t_el] == d_el:      # 生我
        return "偏印" if same_yy else "正印"
    if _CONTROL[t_el] == d_el:      # 克我
        return "七殺" if same_yy else "正官"
    raise FailClosedError(FailClosedReason.CONTRACT_INVALID,
                          f"十神判定失败: {day_stem}/{target_stem}")


def _pattern_by_ten_god(day_stem: str, tg: str, month_branch: str) -> str:
    """十神 → 格局名（含建祿/月劫/陽刃特殊位）。"""
    if tg == "比肩":
        return "建祿月劫格"          # 月與日同（建祿）
    if tg == "劫財":
        if YANG_REN_POS.get(day_stem) == month_branch:
            return "陽刃格"
        return "建祿月劫格"          # 月劫
    return PATTERN_NAME.get(tg, tg + "格")


def _bureau_element(branches: List[str], month_branch: str) -> Optional[str]:
    """月支参与的三合局五行；未成局返回 None。"""
    if not branches:
        return None
    bset = set(b for b in branches if b)
    for trio, el in SANHE.items():
        if month_branch in trio and trio <= bset:
            return el
    return None


def _pattern_by_element(day_stem: str, element: str) -> str:
    """局五行 × 日干 → 化局格局名（原文用词：印/財/煞/劫/食傷）。"""
    d_el = STEM_ELEMENT[day_stem]
    if element == d_el:
        return "劫財格"              # 「化為劫」
    if _PRODUCE[element] == d_el:
        return "印格"                # 局生我「化為印」
    if _PRODUCE[d_el] == element:
        return "食傷格"              # 我生局「化為食傷」
    if _CONTROL[d_el] == element:
        return "財格"                # 我克局「化為財」
    if _CONTROL[element] == d_el:
        return "七煞格"              # 局克我「化為煞」
    raise FailClosedError(FailClosedReason.CONTRACT_INVALID,
                          f"化局判定失败: {day_stem}/{element}")


def derive_pattern(day_stem: str, month_branch: str,
                   hidden: dict | None = None,
                   transparent_stems: list | None = None,
                   branches: list | None = None,
                   base: dict | None = None,
                   l0_chart: dict | None = None) -> Dict[str, Any]:
    """月令取格 → 格局（透干第二层 + 会支第三层 + 本气第一层）。

    hidden: L0 hidden_stems 若提供则优先（键=支，值=藏干列表，首干为本气）。
    transparent_stems: 四柱天干（年/月/时），用于透干判定。
    branches: 四柱地支（年/月/日/时），用于三合化局判定。

    返回 dict（§65 派生字段）：
    - pattern: 最终格局（化局时返回化局格局）
    - bureau: 三合局五行（未成局 None）
    - bureau_effect: 原文化局效果（含「不失本格」标注）
    - transparent_ten_gods: 四柱天干（年/月/时）→ 十神 映射（judgment 消费）
    """
    if not day_stem or not month_branch:
        raise FailClosedError(FailClosedReason.INPUT_FORBIDDEN, "取格需要 day_stem/month_branch")
    hd = hidden or {}
    stems = hd.get(month_branch) or BRANCH_HIDDEN.get(month_branch)
    if not stems:
        raise FailClosedError(FailClosedReason.CONTRACT_INVALID, f"未知月支: {month_branch}")
    benqi = stems[0]
    bureau_el = _bureau_element(branches or [], month_branch)
    effect = None
    # 四柱天干十神映射（十神为标准定义；L0 shishen 缺失时 judgment 亦可用）
    transparent_tg: Dict[str, str] = {}
    for s in (transparent_stems or []):
        if s:
            transparent_tg[s] = _ten_god(day_stem, s)

    # 本气透 → 本格定格（化局作兼，不失本格）
    if transparent_stems and benqi in [s for s in transparent_stems if s in stems]:
        pat = _pattern_by_ten_god(day_stem, _ten_god(day_stem, benqi), month_branch)
        if bureau_el:
            effect = f"會{bureau_el}局而不失本格（本气{benqi}透）"
        return {"pattern": pat, "bureau": bureau_el, "bureau_effect": effect,
                "transparent_ten_gods": transparent_tg}

    # 本气不透 + 月支参与三合成局 → 化局定格（优先于透余气，原文例「乙生寅月透戊會午戌→食傷」）
    if bureau_el:
        hua = _pattern_by_element(day_stem, bureau_el)
        return {"pattern": hua, "bureau": bureau_el,
                "bureau_effect": f"化為{hua.replace('格', '')}（{month_branch}會{bureau_el}局）",
                "transparent_ten_gods": transparent_tg}

    # 本气不透、无化局、余/中气透 → 透出者作主
    if transparent_stems:
        transparent = [s for s in transparent_stems if s in stems]
        if transparent:
            # 多透次序（月干 > 时干 > 年干）属《论用神变化》未明示处，待 Human 裁定
            picked = next((s for s in (transparent_stems[1:2] + transparent_stems[2:3] + transparent_stems[0:1])
                           if s in transparent), transparent[0])
            return {"pattern": _pattern_by_ten_god(day_stem, _ten_god(day_stem, picked), month_branch),
                    "bureau": None, "bureau_effect": None,
                    "transparent_ten_gods": transparent_tg}

    # 不透 → 本气定格（第一层：財官印食煞傷刃劫 + 建祿/月劫/陽刃）
    return {"pattern": _pattern_by_ten_god(day_stem, _ten_god(day_stem, benqi), month_branch),
            "bureau": bureau_el, "bureau_effect": effect,
            "transparent_ten_gods": transparent_tg}
