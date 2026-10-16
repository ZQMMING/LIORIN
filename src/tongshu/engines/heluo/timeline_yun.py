"""河洛理数应期链：大运（爻位值运）+ 流年卦 + 流月卦 + 流日卦

算法依据：《河洛理数·卷之四/五》（陈抟著、邵雍述）
冻结规则依据：Architecture Freeze V1.0 + 古籍原文

本模块解决此前 `temporal.py`（占位）与 `time_sequence.py`（只算干支）的缺口：
将八字 → 先天卦 → 元堂 → 后天卦 的基础上，进一步推演出：
  - 大运（爻位值运：阳爻九年、阴爻六年，自元堂起行完先天再行后天）
  - 流年卦（逐岁推演，分元堂阳爻/阴爻两种规则）
  - 流月卦（以流年卦为本，变元堂下一爻起逐爻 → 阳月卦，取应爻 → 阴月卦）
  - 流日卦（以月卦为本，变月爻下一爻起六爻，每爻管五日，节气对齐，用阴历）

六爻表示：1 = 阳爻，-1 = 阴爻；index 0-5（0=初爻 ... 5=上爻）
应爻关系：一四应、二五应、三六应 → 应爻 index = (i + 3) % 6
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .numbers import get_hexagram_name, build_six_lines, TRIGRAM_LINES

# ═══════════════════════════════════════════════════════════════════
# 基础工具
# ═══════════════════════════════════════════════════════════════════

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
YANG_STEMS = set("甲丙戊庚壬")  # 阳年


def _flip_line(six_lines: list[int], idx: int) -> list[int]:
    """翻转指定爻（1 ↔ -1），返回新卦。"""
    out = list(six_lines)
    out[idx % 6] = -out[idx % 6]
    return out


def _lines_to_hexagram(six_lines: list[int]) -> tuple[str, str, str]:
    """六爻 → (上卦, 下卦, 卦名)。下卦=lines[0:3]，上卦=lines[3:6]。"""
    lower = "".join("1" if l == 1 else "0" for l in six_lines[0:3])
    upper = "".join("1" if l == 1 else "0" for l in six_lines[3:6])
    rev = {"111": "乾", "110": "兑", "101": "离", "100": "震",
           "011": "巽", "010": "坎", "001": "艮", "000": "坤"}
    lower_name = rev[lower]
    upper_name = rev[upper]
    return upper_name, lower_name, get_hexagram_name(upper_name, lower_name)


def _year_gan(year: int) -> str:
    """公元年份 → 年干。1984=甲子。"""
    return STEMS[(year - 4) % 10]


def _is_yang_year(year: int) -> bool:
    """该流年是否为阳年（年干甲丙戊庚壬）。"""
    return _year_gan(year) in YANG_STEMS


# ═══════════════════════════════════════════════════════════════════
# 一、大运（爻位值运）
# ═══════════════════════════════════════════════════════════════════
@dataclass
class DayunLiyaoEntry:
    """单步大运（一个爻位值运段）。"""
    age_start: int            # 虚岁起始
    age_end: int              # 虚岁结束
    hexagram_name: str        # 所在卦（先天/后天）
    upper: str
    lower: str
    line_index: int           # 爻位 0-5
    line_nature: str          # 阳/阴
    lines: list[int]          # 该步卦象六爻


@dataclass
class DayunResult:
    """大运（爻位值运）结果。"""
    sequence: list[DayunLiyaoEntry] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def compute_dayun_liyao(
    prenatal_lines: list[int],
    prenatal_yuantang: int,
    postnatal_lines: list[int],
    postnatal_yuantang: int,
) -> DayunResult:
    """
    爻位值运大运：阳爻九年、阴爻六年。

    规则（《河洛理数·卷之四》论大运）：
      1. 从先天命卦元堂爻起，自下而上（index 递增，行完上爻回到初爻），
         直到行完六爻（最后到元堂前一爻），先天卦走完。
      2. 再从后天命卦元堂起，同样行六爻。
      3. 阳爻值运 9 年，阴爻值运 6 年。
    """
    seq: list[DayunLiyaoEntry] = []
    notes = []

    def _walk(gua_name: str, lines: list[int], yuantang: int, age_start: int) -> int:
        age = age_start
        # 从元堂起自下而上共 6 爻
        for step in range(6):
            idx = (yuantang + step) % 6
            nature = "阳" if lines[idx] == 1 else "阴"
            span = 9 if lines[idx] == 1 else 6
            age_end = age + span - 1
            upper, lower, name = _lines_to_hexagram(lines)
            seq.append(DayunLiyaoEntry(
                age_start=age, age_end=age_end,
                hexagram_name=name, upper=upper, lower=lower,
                line_index=idx, line_nature=nature, lines=list(lines),
            ))
            age = age_end + 1
        return age

    notes.append(f"先天卦元堂@{prenatal_yuantang} 起运")
    age = _walk("先天", prenatal_lines, prenatal_yuantang, 1)
    notes.append(f"先天卦行毕于{age - 1}岁，接后天卦元堂@{postnatal_yuantang}")
    _walk("后天", postnatal_lines, postnatal_yuantang, age)

    return DayunResult(sequence=seq, notes=notes)


# ═══════════════════════════════════════════════════════════════════
# 二、流年卦（逐岁推演）
# ═══════════════════════════════════════════════════════════════════
@dataclass
class LiuNianYear:
    """某岁的流年卦。"""
    age: int                  # 虚岁
    year: int                 # 公历年份
    ganzhi: str               # 流年干支
    yang_year: bool           # 是否阳年
    hexagram_name: str
    upper: str
    lower: str
    lines: list[int]
    rule: str                 # 采用的规则说明
    yuantang_index: int = -1  # 本岁所属大运段的元堂爻位（流月卦据此起）


@dataclass
class LiuNianResult:
    """流年卦序列。"""
    birth_year: int
    years: list[LiuNianYear] = field(default_factory=list)


def compute_liunian(
    prenatal_lines: list[int],
    prenatal_yuantang: int,
    postnatal_lines: list[int],
    postnatal_yuantang: int,
    birth_year: int,
    age_from: int = 1,
    age_to: int = 100,
) -> LiuNianResult:
    """
    逐岁推演流年卦（《河洛真数》小象行年卦气，按大运爻分段）。

    大运爻值运（阳爻9年、阴爻6年，先天6爻行毕转后天6爻）。每个大运段内，
    以该段大运爻为元堂，重新走小象循环：
      - 段内第1年：段首阳年不变 / 段首阴年变元堂
      - 段内第2年：变元堂应爻
      - 段内第3年：变元堂爻
      - 段内第4年起：自元堂下一爻起逐爻自下而上回绕
    阴爻大运段：自本爻起逐爻自下而上回绕（一年变一爻）。

    应爻关系：一四应、二五应、三六应 → 应爻 index = (yuantang + 3) % 6。
    """
    result = LiuNianResult(birth_year=birth_year)
    dayun = compute_dayun_liyao(
        prenatal_lines, prenatal_yuantang, postnatal_lines, postnatal_yuantang
    )
    seq = dayun.sequence

    cur_seg_id: Optional[int] = None
    prev1: Optional[list[int]] = None  # 段内上一卦
    n = 0  # 段内第N年

    for age in range(age_from, age_to + 1):
        year = birth_year + age - 1
        ganzhi = f"{_year_gan(year)}{BRANCHES[(year - 4) % 12]}"
        yang = _is_yang_year(year)
        rule = ""

        # 找所属大运段
        seg = None
        for s in seq:
            if s.age_start <= age <= s.age_end:
                seg = s
                break
        if seg is None:
            continue

        # 段切换时重置段内状态
        if cur_seg_id != id(seg):
            cur_seg_id = id(seg)
            prev1 = None
            n = 1
            seg_first_yang = _is_yang_year(birth_year + seg.age_start - 1)
        else:
            n += 1

        seg_yt = seg.line_index
        seg_yang_line = (seg.lines[seg_yt] == 1)

        if seg_yang_line:
            # 阳爻大运段（9年）：段内小象循环
            if n == 1:
                if seg_first_yang:
                    cur = list(seg.lines)
                    rule = "段首阳年不变"
                else:
                    cur = _flip_line(seg.lines, seg_yt)
                    rule = "段首阴年变元堂"
            elif n == 2:
                base = prev1 if prev1 is not None else list(seg.lines)
                cur = _flip_line(base, (seg_yt + 3) % 6)
                rule = "变元堂应爻"
            elif n == 3:
                base = prev1 if prev1 is not None else list(seg.lines)
                cur = _flip_line(base, seg_yt)
                rule = "变元堂"
            else:
                base = prev1 if prev1 is not None else list(seg.lines)
                flip_idx = (seg_yt + (n - 3)) % 6
                cur = _flip_line(base, flip_idx)
                rule = f"自元堂下爻逐爻(变{flip_idx})"
        else:
            # 阴爻大运段（6年）：自本爻起逐爻自下而上回绕
            base = prev1 if prev1 is not None else list(seg.lines)
            flip_idx = (seg_yt + (n - 1)) % 6
            cur = _flip_line(base, flip_idx)
            rule = f"阴爻段自本爻逐爻(变{flip_idx})"

        upper, lower, name = _lines_to_hexagram(cur)
        result.years.append(LiuNianYear(
            age=age, year=year, ganzhi=ganzhi, yang_year=yang,
            hexagram_name=name, upper=upper, lower=lower,
            lines=cur, rule=rule, yuantang_index=seg_yt,
        ))
        prev1 = cur

    return result


# ═══════════════════════════════════════════════════════════════════
# 三、流月卦
# ═══════════════════════════════════════════════════════════════════
@dataclass
class LiuYueResult:
    """某年的流月卦序列（正月~十二月）。"""
    year: int
    liunian_name: str
    months: list[dict] = field(default_factory=list)  # {month, name, upper, lower, lines, kind(阳/阴月)}


def compute_liuyue(liunian_lines: list[int], liunian_yuantang: int) -> LiuYueResult:
    """
    流月卦（《河洛真数》论月卦从世上起例）。

    正统算法（古籍观卦上九元堂示例，逐爻累积）：
      1. 从年卦"元堂下一爻"起，逐爻累积变 → 阳月卦（子寅辰午申戌）。
         - 子月：年卦变元堂下一爻
         - 寅月：再变下一爻（在上月结果上累积）
         - ...逐爻自下而上
      2. 每个阳月卦取"月爻之应爻"变化 → 阴月卦（丑卯巳未酉亥）。

    应爻关系：一四应、二五应、三六应 → 应爻 index = (月爻 + 3) % 6。

    注：古籍月卦之法"悉从二十四气，非从朔望"，从子月（冬至）起，故
    "前以正月起者，非"。此处月份按 1-12 标注（阳月=奇数月、阴月=偶数月），
    卦序与古籍子月起始的逐爻累积完全一致。
    """
    start = (liunian_yuantang + 1) % 6
    months = []
    cur = list(liunian_lines)  # 累积基准（逐年卦逐爻累积）
    for k in range(6):
        flip_idx = (start + k) % 6
        cur = _flip_line(cur, flip_idx)  # 逐爻累积变
        ying = (flip_idx + 3) % 6
        yin_lines = _flip_line(cur, ying)
        for kind, lines, month, yue_yao in (
            ("阳月", cur, 2 * k + 1, flip_idx),
            ("阴月", yin_lines, 2 * k + 2, ying),
        ):
            u, lo, name = _lines_to_hexagram(lines)
            months.append({
                "month": month, "name": name, "upper": u, "lower": lo,
                "lines": lines, "kind": kind, "yue_yao_index": yue_yao,
            })
    months.sort(key=lambda m: m["month"])
    return LiuYueResult(year=0, liunian_name="", months=months)


# ═══════════════════════════════════════════════════════════════════
# 四、流日卦
# ═══════════════════════════════════════════════════════════════════
@dataclass
class LiuRiResult:
    """某月的流日卦（分六段，每段五天）。"""
    month: int
    days: list[dict] = field(default_factory=list)


def compute_liuri(
    yue_lines: list[int],
    yue_yao_index: int,
    jie_datetime: str | None = None,
) -> LiuRiResult:
    """
    流日卦（《河洛真数·起例卷之上·起日卦例》万历二十年李学诗刻本）。

    规则（按现存最早刻本口径，2026-09-12 考证裁定）：
      1. 以当月月卦为本，从月卦居位爻的下一爻起，自下而上变六爻
         （绕一圈回到居位爻为止），即"六爻俱变毕，则满三十日"。
      2. "每一爻管五日"：六爻各管五日，共三十日。
      3. "另画一乾卦"：各段以月卦为本独立变对应爻位（非链式）。
      例（乾九二居位）：九三→履、九四→小畜、九五→大有、
         上九→夬、初九→姤、九二（居位）→同人。

    异文记录：《河洛理数》卷二下（国图藏史应选校订明刊本，晚出约40年）
      "除此一爻不变…每管六日…自下爻行至上爻"为 5 爻×6 日口径
      （不含居位爻），按"最早书籍为准"原则不采用，保留为异文。

    节气对齐（《河洛真数》："日卦行起必须按月卦节气方不误"）：
      若提供 jie_datetime（当月"节"的精确时刻，如 2024-08-07 08:09），
      则第1段从"节"当日开始管起，各段标注真实起止日期；
      否则退化为相对分段（第1-5天、第6-10天...），兼容旧调用。
    """
    start = (yue_yao_index + 1) % 6
    days = []
    for k in range(6):
        flip_idx = (start + k) % 6
        seg_lines = _flip_line(yue_lines, flip_idx)
        u, lo, name = _lines_to_hexagram(seg_lines)
        entry = {
            "segment": k + 1, "day_from": k * 5 + 1, "day_to": k * 5 + 5,
            "name": name, "upper": u, "lower": lo, "lines": seg_lines,
        }
        if jie_datetime:
            # 节气对齐：段k覆盖节起第(k*5+1)~第(k*5+5)天
            try:
                base = _parse_datetime(jie_datetime)
                from datetime import timedelta
                day_from_dt = base + timedelta(days=k * 5)
                day_to_dt = base + timedelta(days=k * 5 + 4)
                entry["date_from"] = day_from_dt.strftime("%Y-%m-%d")
                entry["date_to"] = day_to_dt.strftime("%Y-%m-%d")
            except Exception:
                pass  # 解析失败则保持相对分段
        days.append(entry)
    return LiuRiResult(month=0, days=days)


def _parse_datetime(s: str):
    """解析 'YYYY-MM-DD HH:MM' 或 'YYYY-MM-DD' → datetime"""
    from datetime import datetime
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析时间: {s}")


# ═══════════════════════════════════════════════════════════════════
# 五、流时卦（《河洛真数·起例卷之上·起时卦例》）
# ═══════════════════════════════════════════════════════════════════
@dataclass
class LiuShiResult:
    """某流日卦的十二时卦（子~亥）。"""
    day_name: str = ""
    hours: list[dict] = field(default_factory=list)


def compute_liushi(day_lines: list[int], day_yao_index: int) -> LiuShiResult:
    """
    流时卦（《河洛真数·起例卷之上·起时卦例》万历二十年李学诗刻本）。

    原文："凡起时卦，于日中寻时，就值日卦上从前一爻起，子丑寅卯辰巳六时，
           主进数变去；值日卦后一爻起，午未申酉戌亥六时，主退数变去。
           假如得乾卦初爻值日，则从二爻变起。
           又云：日卦变时卦，与年卦变月卦同。但子寅辰午申戌居左，变爻用点，
           丑卯巳未酉亥居右取应，变爻不同点。"

    规则（与年卦变月卦同，逐爻累积；进/退两分支各自从值日卦起）：
      1. 以值日卦（流日卦）为本。
      2. 前六时（子丑寅卯辰巳）进数：从值日爻下一爻起，阳时子寅辰逐爻累积变
         （+1,+2,+3），阴时丑卯巳取阳时变爻之应爻。
      3. 后六时（午未申酉戌亥）退数：**重新从值日卦起**，从值日爻上一爻退，
         阳时午申戌逐爻累积变（-1,-2,-3），阴时未酉亥取应。
      例：乾初爻值日 → 子时变二爻（天火同人），午时变上爻（泽天夬）。
    """
    u, lo, name = _lines_to_hexagram(list(day_lines))
    hours = []

    def _push(hour_kind_prefix, flips, hour_base):
        nonlocal hours
        cur = list(day_lines)  # 分支各自从值日卦起
        for k, flip in enumerate(flips):
            flip_idx = (day_yao_index + flip) % 6
            cur = _flip_line(cur, flip_idx)  # 阳时（逐爻累积）
            yang_lines = list(cur)
            ying = (flip_idx + 3) % 6
            yin_lines = _flip_line(cur, ying)  # 阴时取应
            for kind, lines, shi, yue_yao in (
                ("阳时", yang_lines, hour_base + 2 * k, flip_idx),
                ("阴时", yin_lines, hour_base + 2 * k + 1, ying),
            ):
                u2, lo2, name2 = _lines_to_hexagram(lines)
                hours.append({
                    "hour": shi, "name": name2, "upper": u2, "lower": lo2,
                    "lines": lines, "kind": kind, "shi_yao_index": yue_yao,
                })

    # 前六时（子~巳）：进数 +1,+2,+3（阳时子寅辰）
    _push("前", (1, 2, 3), 1)
    # 后六时（午~亥）：退数 -1,-2,-3（阳时午申戌），重新从值日卦起
    _push("后", (-1, -2, -3), 7)
    hours.sort(key=lambda h: h["hour"])
    return LiuShiResult(day_name=name, hours=hours)


__all__ = [
    "compute_dayun_liyao", "DayunResult", "DayunLiyaoEntry",
    "compute_liunian", "LiuNianResult", "LiuNianYear",
    "compute_liuyue", "LiuYueResult",
    "compute_liuri", "LiuRiResult",
    "compute_liushi", "LiuShiResult",
]
