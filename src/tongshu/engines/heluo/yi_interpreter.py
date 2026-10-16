"""河洛易经解卦层（HELUO × Yijing Interpreter）

职责：将 timeline_yun 产出的流年卦/流月卦 → 易经卦爻辞 → EVENT_SIGNAL
体系隔离：独立模块，不污染 timeline_yun/canonical 的冻结规则
古籍无据不妄断：证据不足输出 NO_EVIDENCE

EVENT_SIGNAL 格式：
{
    "system": "HELUO",
    "rule_id": str,          # e.g. "HL-YN-2021"
    "theme": "EVENT",
    "direction": "POSITIVE|NEGATIVE|NEUTRAL|MIXED|NO_EVIDENCE",
    "strength": "HIGH|MEDIUM|LOW",
    "time_scope": {"year": int, "month": int|None},
    "hexagram": str,          # 流年卦名
    "evidence": [str, ...],   # 可审计证据链
    "confidence": float,       # 0.0~1.0
}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional
import copy

from ..yi.yao_ci_data import YAO_CI, get_yao_ci, get_all_yao_ci
from ..yi.yao_ci_meanings import YAO_CI_MEANINGS
from ..yi.classical_text import get_classical_text

# ═══════════════════════════════════════════════════════════════════
# EVENT_SIGNAL 数据结构
# ═══════════════════════════════════════════════════════════════════

Direction = Literal["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "NO_EVIDENCE"]
Strength = Literal["HIGH", "MEDIUM", "LOW"]


@dataclass(frozen=True)
class EVENT_SIGNAL:
    """统一事件信号格式（河洛易经层）"""
    system: str = "HELUO"
    rule_id: str = ""
    theme: str = "EVENT"
    direction: Direction = "NEUTRAL"
    strength: Strength = "MEDIUM"
    time_scope: dict = field(default_factory=dict)  # {year, month}
    hexagram: str = ""
    evidence: tuple[str, ...] = tuple()
    confidence: float = 0.5

    def to_dict(self) -> dict:
        return {
            "system": self.system,
            "rule_id": self.rule_id,
            "theme": self.theme,
            "direction": self.direction,
            "strength": self.strength,
            "time_scope": self.time_scope,
            "hexagram": self.hexagram,
            "evidence": list(self.evidence),
            "confidence": self.confidence,
        }


# ═══════════════════════════════════════════════════════════════════
# 爻位名称工具
# ═══════════════════════════════════════════════════════════════════

# 爻位索引 → 名称（河洛/周易标准）
_INDEX_TO_POSITION = ["初", "二", "三", "四", "五", "上"]
_YANG_CHAR = "九"
_YIN_CHAR = "六"


def _line_name(line_index: int, is_yang: bool) -> str:
    """六爻索引 + 爻性 → 爻位名称，如 0+阳→"初九"，3+阴→"六四"."""
    pos = _INDEX_TO_POSITION[line_index]
    char = _YANG_CHAR if is_yang else _YIN_CHAR
    if line_index in (0, 5):
        return f"{pos}{char}"
    return f"{char}{pos}"


def _resolve_hexagram(name: str) -> str:
    """解析卦名（支持简称→全称）."""
    # 简称映射
    ALIASES = {
        "乾": "乾为天", "坤": "坤为地", "屯": "水雷屯", "蒙": "山水蒙",
        "需": "水天需", "讼": "天水讼", "师": "地水师", "比": "水地比",
        "小畜": "风天小畜", "履": "天泽履", "泰": "地天泰", "否": "天地否",
        "同人": "天火同人", "大有": "火天大有", "谦": "地山谦", "豫": "雷地豫",
        "随": "泽雷随", "蛊": "山风蛊", "临": "地泽临", "观": "风地观",
        "噬嗑": "火雷噬嗑", "贲": "山火贲", "剥": "山地剥", "复": "地雷复",
        "无妄": "天雷无妄", "大畜": "山天大畜", "颐": "山雷颐", "大过": "泽风大过",
        "坎": "坎为水", "离": "离为火", "咸": "泽山咸", "恒": "雷风恒",
        "遁": "天山遁", "大壮": "雷天大壮", "晋": "火地晋", "明夷": "地火明夷",
        "家人": "风火家人", "睽": "火泽睽", "蹇": "水山蹇", "解": "雷水解",
        "损": "山泽损", "益": "风雷益", "夬": "泽天夬", "姤": "天风姤",
        "萃": "泽地萃", "升": "地风升", "困": "泽水困", "井": "水风井",
        "革": "泽火革", "鼎": "火风鼎", "震": "震为雷", "艮": "艮为山",
        "渐": "风山渐", "归妹": "雷泽归妹", "丰": "雷火丰", "旅": "火山旅",
        "巽": "巽为风", "兑": "兑为泽", "涣": "风水涣", "节": "水泽节",
        "中孚": "风泽中孚", "小过": "雷山小过", "既济": "水火既济", "未济": "火水未济",
    }
    if name in YAO_CI:
        return name
    if name in ALIASES:
        resolved = ALIASES[name]
        if resolved in YAO_CI:
            return resolved
    return name


# ═══════════════════════════════════════════════════════════════════
# 方向判定规则（基于爻辞语义关键词）
# ═══════════════════════════════════════════════════════════════════

# 爻辞吉凶关键词（来自周易原文统计）
_POSITIVE_KEYWORDS = [
    "吉", "亨", "利", "贞吉", "无咎", "无不利", "元吉", "大吉",
    "往吉", "有喜", "有终", "乃吉", "赐福", "受福", "得", "获",
]
_NEGATIVE_KEYWORDS = [
    "凶", "吝", "厉", "悔", "无攸利", "不利", "有眚", "征凶",
    "终凶", "大凶", "小凶", "丧", "失", "凶事", "有灾",
    "蹇",      # 艰难/险阻(水山蹇)
    "困",      # 困顿(泽水困)
    "剥",      # 剥落(山地剥)
    "否",      # 闭塞(天地否)
    "坎",      # 险陷(坎为水)
    "屯",      # 初生艰难(水雷屯)
    "明夷",    # 光明受伤(地火明夷)
    "大过",    # 过甚(泽风大过)
    "遁",      # 退避(天山遁)
]
_MIXED_KEYWORDS = ["厉无咎", "吝无咎", "悔亡", "凶咎", "凶有", "贞厉"]


def _judge_direction(yao_ci_text: str) -> tuple[Direction, float]:
    """
    基于爻辞文本判定吉凶方向。

    Returns:
        (direction, confidence)
    confidence: 0.5=弱证据, 0.7=中证据, 0.9=强证据
    """
    if not yao_ci_text:
        return "NO_EVIDENCE", 0.0

    pos_count = sum(1 for kw in _POSITIVE_KEYWORDS if kw in yao_ci_text)
    neg_count = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in yao_ci_text)

    # 强负面词（即使有"吉"也应综合考虑）
    strong_neg = any(kw in yao_ci_text for kw in ["不利", "蹇", "困", "否", "剥", "明夷", "大过", "征凶", "终凶"])

    # 爻辞本身带有判断词
    if "吉" in yao_ci_text and "凶" not in yao_ci_text:
        # 有吉但也有强负面词 → 混合(吉凶参半)
        if strong_neg and neg_count >= 1:
            return "MIXED", 0.6
        conf = min(0.5 + pos_count * 0.1, 0.95)
        return "POSITIVE", conf
    if "凶" in yao_ci_text:
        conf = min(0.5 + neg_count * 0.1, 0.95)
        return "NEGATIVE", conf
    if "吝" in yao_ci_text or "厉" in yao_ci_text:
        # 有警告但非定凶
        if "无咎" in yao_ci_text:
            return "NEUTRAL", 0.6
        return "MIXED", 0.55

    if pos_count > neg_count:
        return "POSITIVE", min(0.5 + pos_count * 0.1, 0.85)
    if neg_count > pos_count:
        return "NEGATIVE", min(0.5 + neg_count * 0.1, 0.85)

    return "NEUTRAL", 0.5


# ═══════════════════════════════════════════════════════════════════
# 强度判定
# ═══════════════════════════════════════════════════════════════════

def _judge_strength(line_index: int, is_yang: bool, direction: Direction) -> Strength:
    """
    判定强度。
    - 五爻(4)为君位，最强
    - 上爻(5)为终位，高但带过极风险
    - 三爻(2)为显位，中高
    - 初爻(0)为潜位，低
    """
    if direction == "NO_EVIDENCE":
        return "LOW"

    if line_index == 4:  # 九五君位
        return "HIGH"
    if line_index == 5:  # 上爻，过极
        return "MEDIUM"
    if line_index == 2:  # 三爻显位
        return "MEDIUM" if direction in ("POSITIVE", "NEGATIVE") else "LOW"
    if line_index in (1, 3):  # 二四爻中位
        return "MEDIUM"
    return "LOW"  # 初爻潜位


# ═══════════════════════════════════════════════════════════════════
# 核心：计算某年份的动爻索引
# ═══════════════════════════════════════════════════════════════════

def _compute_changed_line_for_year(
    liunian_years: list[dict],
    target_year: int,
) -> Optional[int]:
    """
    计算目标年份的流年卦相比上一年的动爻索引。

    liunian_years: canonical._build_timeline() 产出的 yearly_hexagrams
    target_year: 公历年份

    Returns:
        line_index (0-5) 如果能判定，否则 None
    """
    # 找到目标年和前一年的 hexagram
    target_entry = None
    prev_entry = None
    for i, entry in enumerate(liunian_years):
        if entry["year"] == target_year:
            target_entry = entry
            if i > 0:
                prev_entry = liunian_years[i - 1]
            break

    if target_entry is None:
        return None

    if prev_entry is None:
        return None  # 第一年无上年对比

    target_lines = target_entry["lines"]
    prev_lines = prev_entry["lines"]

    # 找到差异的爻位（只允许一处差异）
    diffs = [i for i in range(6) if target_lines[i] != prev_lines[i]]
    if len(diffs) == 1:
        return diffs[0]

    return None


# ═══════════════════════════════════════════════════════════════════
# 核心解释器
# ═══════════════════════════════════════════════════════════════════

@dataclass
class YiInterpreterResult:
    """单条流年卦解释结果."""
    year: int
    age: int
    hexagram: str
    changed_line: Optional[int]  # 动爻索引（0-5）
    changed_line_name: str
    ying_line: int               # 应爻索引
    ying_line_name: str
    gua_ci: str                  # 卦辞
    gua_ci_source: str
    changed_yao_ci: str          # 动爻爻辞
    changed_yao_source: str
    ying_yao_ci: str             # 应爻爻辞
    ying_yao_source: str
    signal: EVENT_SIGNAL


def interpret_liunian_year(
    hexagram_name: str,
    year: int,
    age: int,
    yuan_tang_index: int,
    yuan_tang_line_nature: str,  # "阳" or "阴"
    liunian_years: Optional[list[dict]] = None,
) -> YiInterpreterResult:
    """
    解释单条流年卦。

    参数:
        hexagram_name: 流年卦名（如"泽雷随"）
        year: 公历年份
        age: 虚岁
        yuan_tang_index: 先天卦元堂索引（0-5）
        yuan_tang_line_nature: 元堂爻性（"阳"/"阴"）
        liunian_years: 可选，用于计算动爻位置

    返回:
        YiInterpreterResult（含 EVENT_SIGNAL）
    """
    resolved = _resolve_hexagram(hexagram_name)

    # ── 卦辞 ────────────────────────────────────────────────────
    ct = get_classical_text(resolved)
    gua_ci = ct.gua_ci or ""
    gua_ci_source = ct.gua_ci_source or ""

    # ── 动爻分析 ─────────────────────────────────────────────────
    changed_line_idx: Optional[int] = None
    changed_line_name = ""
    changed_yao_ci = ""
    changed_yao_source = ""

    if liunian_years is not None:
        changed_line_idx = _compute_changed_line_for_year(liunian_years, year)

    if changed_line_idx is not None:
        is_yang = resolved in YAO_CI and len(YAO_CI.get(resolved, [])) > changed_line_idx
        # 判断爻性（阳爻=1, 阴爻=-1）
        # 从 yao_ci_data 中的 position name 判断
        yao_list = YAO_CI.get(resolved, [])
        if changed_line_idx < len(yao_list):
            _, pos_name, _, _ = yao_list[changed_line_idx]
            changed_line_name = pos_name
            changed_yao_ci, changed_yao_source = get_yao_ci(resolved, pos_name)
    else:
        # 无法精确判定动爻时，使用元堂爻作为主爻
        changed_line_idx = yuan_tang_index
        changed_line_name = _line_name(yuan_tang_index, yuan_tang_line_nature == "阳")
        changed_yao_ci, changed_yao_source = get_yao_ci(resolved, changed_line_name)

    # ── 应爻分析 ─────────────────────────────────────────────────
    ying_idx = (yuan_tang_index + 3) % 6
    # 判断应爻爻性（通过 yao_ci_data 推断）
    yao_list = YAO_CI.get(resolved, [])
    ying_is_yang = False
    if ying_idx < len(yao_list):
        _, ying_pos_name, _, _ = yao_list[ying_idx]
        ying_is_yang = ying_pos_name.startswith("九")
        ying_line_name = ying_pos_name
    else:
        ying_line_name = _line_name(ying_idx, ying_is_yang)

    ying_yao_ci, ying_yao_source = get_yao_ci(resolved, ying_line_name)

    # ── 方向判定 ─────────────────────────────────────────────────
    # 主要依据动爻爻辞，次要参考应爻爻辞
    primary_direction, primary_conf = _judge_direction(changed_yao_ci)
    secondary_direction, secondary_conf = _judge_direction(ying_yao_ci)

    if primary_direction == "NO_EVIDENCE" and secondary_direction != "NO_EVIDENCE":
        final_direction = secondary_direction
        final_conf = secondary_conf * 0.7
    elif primary_direction != "NO_EVIDENCE" and secondary_direction == "NO_EVIDENCE":
        final_direction = primary_direction
        final_conf = primary_conf
    elif primary_direction == secondary_direction:
        final_direction = primary_direction
        final_conf = max(primary_conf, secondary_conf) * 0.9
    elif primary_direction in ("POSITIVE", "NEGATIVE") and secondary_direction in ("POSITIVE", "NEGATIVE"):
        # 冲突：取主爻
        final_direction = primary_direction
        final_conf = primary_conf * 0.8
    else:
        final_direction = "MIXED"
        final_conf = min(primary_conf, secondary_conf) * 0.8

    # 如果卦辞也提供了方向信号，综合判定
    if gua_ci:
        gua_direction, gua_conf = _judge_direction(gua_ci)
        if gua_direction != "NO_EVIDENCE":
            if final_direction in ("NEUTRAL", "NO_EVIDENCE"):
                final_direction = gua_direction
                final_conf = gua_conf * 0.8
            elif gua_direction == final_direction:
                final_conf = min(final_conf + gua_conf * 0.2, 0.95)

    # 强度
    is_changed_yang = changed_line_name.startswith("九") if changed_line_name else (yuan_tang_line_nature == "阳")
    final_strength = _judge_strength(changed_line_idx or yuan_tang_index, is_changed_yang, final_direction)

    # ── 构建证据链 ───────────────────────────────────────────────
    evidence = []
    if gua_ci and gua_ci_source:
        evidence.append(f"卦辞：{gua_ci}（{gua_ci_source}）")
    if changed_yao_ci and changed_yao_source:
        evidence.append(f"动爻{changed_line_name}：{changed_yao_ci}（{changed_yao_source}）")
    if ying_yao_ci and ying_yao_source:
        evidence.append(f"应爻{ying_line_name}：{ying_yao_ci}（{ying_yao_source}）")
    if changed_line_idx is not None:
        evidence.append(f"元堂@{yuan_tang_index}（{yuan_tang_line_nature}爻），动爻{changed_line_idx}，应爻{ying_idx}")

    # ── 白话爻义（YAO_CI_MEANINGS 接入，消除孤儿资产）────────────
    meanings = YAO_CI_MEANINGS.get(resolved, {})
    changed_mean = meanings.get(changed_line_idx)
    if changed_mean:
        if changed_mean.get("meaning"):
            evidence.append(f"动爻解读：{changed_mean['meaning']}")
        if changed_mean.get("guidance"):
            evidence.append(f"行动建议：{changed_mean['guidance']}")
    ying_mean = meanings.get(ying_idx)
    if ying_mean and ying_mean.get("meaning"):
        evidence.append(f"应爻解读：{ying_mean['meaning']}")

    # ── EVENT_SIGNAL ─────────────────────────────────────────────
    signal = EVENT_SIGNAL(
        system="HELUO",
        rule_id=f"HL-YN-{year}",
        theme="EVENT",
        direction=final_direction,
        strength=final_strength,
        time_scope={"year": year, "month": None},
        hexagram=resolved,
        evidence=tuple(evidence),
        confidence=final_conf,
    )

    return YiInterpreterResult(
        year=year,
        age=age,
        hexagram=resolved,
        changed_line=changed_line_idx,
        changed_line_name=changed_line_name,
        ying_line=ying_idx,
        ying_line_name=ying_line_name,
        gua_ci=gua_ci,
        gua_ci_source=gua_ci_source,
        changed_yao_ci=changed_yao_ci,
        changed_yao_source=changed_yao_source,
        ying_yao_ci=ying_yao_ci,
        ying_yao_source=ying_yao_source,
        signal=signal,
    )


def interpret_all_liunian(
    yearly_hexagrams: list[dict],
    yuan_tang_index: int,
    yuan_tang_nature: str = "阳",
) -> list[dict]:
    """
    解释所有流年卦，为 canonical._build_timeline() 的 yearly 元素附加 yi 解释。

    参数:
        yearly_hexagrams: canonical._build_timeline() 产出的 yearly_hexagrams
        yuan_tang_index: 先天卦元堂索引（0-5）
        yuan_tang_nature: 元堂爻性（"阳"/"阴"）

    返回:
        yearly_hexagrams 副本，每个元素额外含 "yi_signal": EVENT_SIGNAL.to_dict()
    """
    result = copy.deepcopy(yearly_hexagrams)
    for entry in result:
        year = entry["year"]
        age = entry["age"]
        hexagram = entry["hexagram"]

        interp = interpret_liunian_year(
            hexagram_name=hexagram,
            year=year,
            age=age,
            yuan_tang_index=yuan_tang_index,
            yuan_tang_line_nature=yuan_tang_nature,
            liunian_years=yearly_hexagrams,
        )
        entry["yi_signal"] = interp.signal.to_dict()
        entry["yi_interpretation"] = {
            "changed_line": interp.changed_line,
            "changed_line_name": interp.changed_line_name,
            "ying_line": interp.ying_line,
            "ying_line_name": interp.ying_line_name,
            "gua_ci": interp.gua_ci,
            "gua_ci_source": interp.gua_ci_source,
            "changed_yao_ci": interp.changed_yao_ci,
            "changed_yao_source": interp.changed_yao_source,
            "ying_yao_ci": interp.ying_yao_ci,
            "ying_yao_source": interp.ying_yao_source,
        }

    return result


# ═══════════════════════════════════════════════════════════════════
# 许家印验证
# ═══════════════════════════════════════════════════════════════════

def verify_xu_jiayin():
    """
    许家印（戊戌 壬戌 己未 乙亥，1958生）关键流年验证：
    - 2021（泽雷随）
    - 2023（火雷噬嗑）
    - 2017（水风井）
    """
    from .canonical import HeluoCanonical

    bazi = [("戊", "戌"), ("壬", "戌"), ("己", "未"), ("乙", "亥")]
    c = HeluoCanonical()
    result = c.calculate(bazi, gender="male", birth_hour="亥", era="zhong", birth_year=1958)

    # 提取关键年份
    key_years = {2021: "泽雷随", 2023: "火雷噬嗑", 2017: "水风井"}
    print("\n=== 许家印 关键流年卦验证 ===")
    print(f"先天卦：{result.prenatal.hexagram_name}，元堂：{result.yuantang.yuantang}（@{result.yuantang.yuantang_index}）")
    print(f"后天卦：{result.postnatal.hexagram_name}")
    print()

    for year, expected_hex in key_years.items():
        entry = next((e for e in result.timeline.yearly_hexagrams if e["year"] == year), None)
        if entry is None:
            print(f"❌ {year}: 未找到流年数据")
            continue

        actual_hex = entry["hexagram"]
        match = "✅" if actual_hex == expected_hex else "❌"
        print(f"{match} {year} ({entry['ganzhi']}): {actual_hex}（期望：{expected_hex}）")

        interp = interpret_liunian_year(
            hexagram_name=actual_hex,
            year=year,
            age=entry["age"],
            yuan_tang_index=result.yuantang.yuantang_index,
            yuan_tang_line_nature=result.yuantang.yao_nature,
            liunian_years=result.timeline.yearly_hexagrams,
        )

        sig = interp.signal
        print(f"   方向：{sig.direction} | 强度：{sig.strength} | 置信度：{sig.confidence:.2f}")
        print(f"   证据：{'；'.join(sig.evidence)}")
        print()


# ═══════════════════════════════════════════════════════════════════

__all__ = [
    "EVENT_SIGNAL",
    "YiInterpreterResult",
    "interpret_liunian_year",
    "interpret_all_liunian",
    "verify_xu_jiayin",
]
