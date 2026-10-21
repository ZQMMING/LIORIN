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
    phase: str = "先天"        # 先天/后天（死断「行后天」限定用）


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
        # 爻位值运：卦不变、只走爻，故本段 6 步共用同一卦名。
        # 2026-10-06：原先在循环内逐次调用 _lines_to_hexagram(lines)，6 次结果恒同，
        # 提到循环外算一次（两段共省 10 次无谓换算）。
        upper, lower, name = _lines_to_hexagram(lines)
        # 从元堂起自下而上共 6 爻
        for step in range(6):
            idx = (yuantang + step) % 6
            nature = "阳" if lines[idx] == 1 else "阴"
            span = 9 if lines[idx] == 1 else 6
            age_end = age + span - 1
            seq.append(DayunLiyaoEntry(
                age_start=age, age_end=age_end,
                hexagram_name=name, upper=upper, lower=lower,
                line_index=idx, line_nature=nature, lines=list(lines),
                phase=gua_name,
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
    seg: Optional[DayunLiyaoEntry] = None  # 当前大运段

    for age in range(age_from, age_to + 1):
        year = birth_year + age - 1
        ganzhi = f"{_year_gan(year)}{BRANCHES[(year - 4) % 12]}"
        yang = _is_yang_year(year)
        rule = ""

        # 找所属大运段。2026-10-06：原为每年对 seq 线性扫（O(年龄×段数)）。
        # 大运段按 age 单调不重叠排列且 age 递增，故用游标顺推即可，O(1)。
        if seg is None or age > seg.age_end:
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



# 起日卦「阳位/阴位」（原典 L390：初三五为阳位，二四上为阴位）
_LIURI_YANG_POS = (0, 2, 4)   # 初、三、五
_LIURI_YIN_POS = (1, 3, 5)    # 二、四、上
_LIURI_DAYS_PER_MONTH = 30    # 「六爻俱变毕，则满三十日」


def liuri_day_positions(yue_yao_index: int) -> list[int]:
    """起日卦 30 日**逐日**爻位（原典 L390「挨次而变，不容紊也」）。

    自月卦居位爻的下一爻起（原文「进一爻起」），
    阳日（奇数日）只在阳位（初/三/五）取，阴日（偶数日）只在阴位（二/四/上）取，
    逐日顺推不回头。

    该式同时满足原典「每一爻管五日」：30 日内每爻恰出现 5 次。

    原典实例（乾九二居位 → start=三爻）：
        初一(阳)→三爻 履六三 ｜ 初二(阴)→四爻 中孚六四
        初三(阳)→五爻 损六五 ｜ 初四(阴)→上爻 临上六
        初五(阳)→初爻 师初六
    """
    pos = (yue_yao_index + 1) % 6
    out: list[int] = []
    for d in range(1, _LIURI_DAYS_PER_MONTH + 1):
        pool = _LIURI_YANG_POS if d % 2 == 1 else _LIURI_YIN_POS
        for step in range(6):
            cand = (pos + step) % 6
            if cand in pool:
                pos = cand
                break
        out.append(pos)
    return out


def liuri_day_lines(yue_lines: list[int], yue_yao_index: int) -> list[tuple[int, list[int]]]:
    """起日卦 30 日**逐日链式累变**（原典 L390）。

    原典不是「月卦各翻一爻」，而是**每日自前一日卦继续翻下一爻**：

        初一日当在三爻，变为履六三
        初二日变履九四为中孚六四        ← 自「履」的九四翻，非自月卦乾
        初三日变中孚九五为损六五        ← 自「中孚」的九五翻
        初四日变损上九为临上六
        初五日变临初九为师初六

    乾初爻居位实测五日（卦名 + 变爻名）逐字吻合：
        履六三 / 中孚六四 / 损六五 / 临上六 / 师初六
    若改成「月卦单爻翻转」则得 履 / 小畜 / 大有 / 夬 / 姤，与原典 4/5 不符。

    第二处独立佐证（起例卷之上·小象行年卦气末段，流年版）：
        「假如同人六二爻为元堂，则一变为乾九二，再变为履六三，三变为中孚六四，
          四变为损六五，五变为临上六，六变为师初六，一年变一爻为一卦」
    与本节五日实例**逐字同序**。起日卦与流年小象两章共用同一条链式规则。

    2026-10-07 据此改正。此前实现（2026-09-12 考证裁定，文档亦作「另画一乾卦
    ……非链式」）与原典实例冲突，以原典为准。

    Returns:
        30 组 ``(爻位, 该日卦六爻)``；第 0 日即 ``liuri_day_positions[0]``。
    """
    out: list[tuple[int, list[int]]] = []
    cur = list(yue_lines)
    for pos in liuri_day_positions(yue_yao_index):
        cur = _flip_line(cur, pos)
        out.append((pos, cur))
    return out


def _lines_to_hexagram_name(lines: list[int]) -> tuple[str, str, str]:
    u, lo, name = _lines_to_hexagram(lines)
    return u, lo, name


def compute_liuri(
    yue_lines: list[int],
    yue_yao_index: int,
    jie_datetime: str | None = None,
    next_jie_datetime: str | None = None,
    align_dates: bool = False,
    rule: str = "hou5",
) -> LiuRiResult:
    """
    流日卦（《河洛真数·起例卷之上·起日卦例》万历二十年李学诗刻本）。

    规则（原典 L390 口径，2026-10-07 复核定案）：
      1. 自月卦居位爻的**下一爻**起，逐日翻一爻，**自前一日卦继续翻**
         （链式累变）。原文：「挨次而变，不容紊也」，并逐日点名
         「初二日变**履**九四为中孚六四」——明言自前一日卦而变。
      2. 阳日（初、三、五等奇数日）只在阳位（初/三/五爻）取爻，
         阴日只在阴位（二/四/上爻）取爻。原文：「阳日寻阳爻位，
         （初三五为阳位。）阴日寻阴爻位。（二四上为阴位。）」
      3. 「每一爻管五日」+「六爻俱变毕，则满三十日」：30 日内每爻恰 5 次。
      4. 「进一爻起」：居位爻的下一爻为初一之位。此读法与原文两处实例
         （乾初爻居位初一日在三爻、乾二爻居位初一日亦在三爻）**同时吻合**；
         首句「以流月卦前一爻为初一日」与之矛盾，登记为异文，不据此造规则。

      例（乾初爻居位，原文五日实例逐字复现）：
        初一 翻三爻 → 天泽履 六三
        初二 翻四爻 → 风泽中孚 六四
        初三 翻五爻 → 山泽损 六五
        初四 翻上爻 → 地泽临 上六
        初五 翻初爻 → 地水师 初六

    异文记录：2026-09-12 曾据「另画一乾卦」一句定为「各段以月卦为本独立变
      对应爻位（非链式）」，并据晚出约 40 年的《河洛理数》卷二下
      「除此一爻不变…每管六日…自下爻行至上爻」取 5 爻×6 日口径。
      **两说均与 L390 逐日实例冲突**（单变则初二得小畜、初三得大有，
      原文明作中孚、损），2026-10-07 依原典实例定案为链式 6 爻×5 日，
      前说废止；晚出本异文仅备查。

    节气对齐（《河洛真数》："日卦行起必须按月卦节气方不误"）：
      若提供 jie_datetime（当月"节"的精确时刻，如 2024-08-07 08:09）且
      ``align_dates=True``，各段标注真实起止日期 date_from/date_to。
      2026-10-06 起 align_dates 默认 **False**：全仓无人消费 date_from/date_to，
      而每段多算 2 个日期串 + 一次 strptime，实测占单盘载荷的大头。
      仍可由调用方显式开启，不丢能力。
    """
    positions = liuri_day_positions(yue_yao_index)
    day_lines = liuri_day_lines(yue_lines, yue_yao_index)
    n_seg = 6 if rule == "hou5" else 5
    seg_len = 5 if rule == "hou5" else 6
    # H10b：给了节与下节时刻即按实际间隔均匀切分（自动对齐），
    # 不必再显式开 align_dates。
    _align = align_dates or bool(jie_datetime and next_jie_datetime)
    base = _parse_datetime(jie_datetime) if (jie_datetime and _align) else None
    nxt = _parse_datetime(next_jie_datetime) if (next_jie_datetime and _align) else None
    days = []
    for k in range(n_seg):
        seg_days = positions[k * seg_len:k * seg_len + seg_len]
        flip_idx = seg_days[0]          # 段首爻位（保留旧键语义=该段第一日）
        seg_lines = day_lines[k * seg_len][1]
        u, lo, name = _lines_to_hexagram(seg_lines)
        # 段内五日逐日各有一卦（原典「挨次而变」），不共一卦
        day_items = []
        for j, pos in enumerate(seg_days):
            dl = day_lines[k * seg_len + j][1]
            du, dlo, dname = _lines_to_hexagram(dl)
            item = {
                "day": k * seg_len + j + 1,
                "polarity": "阳日" if (k * seg_len + j) % 2 == 0 else "阴日",
                "flip_index": pos,
                "day_yao_index": pos,   # 原典「变为履六三」的「三」即当日变爻
                "name": dname, "upper": du, "lower": dlo, "lines": dl,
            }
            if base is not None:
                try:
                    from datetime import timedelta
                    item["date"] = (base + timedelta(days=k * seg_len + j)).strftime("%Y-%m-%d")
                except Exception as exc:
                    item["date_align_error"] = f"节气日期对齐失败：{exc}"
            day_items.append(item)
        entry = {
            "segment": k + 1, "day_from": k * seg_len + 1, "day_to": k * seg_len + seg_len,
            "flip_index": flip_idx,
            "name": name, "upper": u, "lower": lo, "lines": seg_lines,
            "day_items": day_items,
        }
        if base is not None and nxt is not None and nxt > base:
            # H10b 节气为界均匀分配：段边界 = 节时刻 + k*(下节-节)/N，
            # 按实际节气间隔（含时刻）切分，不机械固定每段日数
            try:
                from datetime import timedelta
                span = (nxt - base).total_seconds()
                seg_sec = span / n_seg
                b0 = base + timedelta(seconds=k * seg_sec)
                b1 = base + timedelta(seconds=(k + 1) * seg_sec)
                entry["day_from"] = int((b0.date() - base.date()).days) + 1
                entry["day_to"] = int((b1.date() - base.date()).days)
                if k == n_seg - 1:
                    entry["day_to"] = int((nxt.date() - base.date()).days) + 1  # 末段至下一节
                entry["date_from"] = b0.strftime("%Y-%m-%d %H:%M")
                entry["date_to"] = b1.strftime("%Y-%m-%d %H:%M")
                entry["jie_span_days"] = round(span / 86400.0, 4)  # 实际节气间隔（天）
            except Exception as exc:
                entry["jie_align_error"] = f"节气均匀分配失败：{exc}"
        elif base is not None:
            # 节气对齐：段k覆盖节起第(k*5+1)~第(k*5+5)天
            try:
                from datetime import timedelta
                entry["date_from"] = (base + timedelta(days=k * 5)).strftime("%Y-%m-%d")
                entry["date_to"] = (base + timedelta(days=k * 5 + 4)).strftime("%Y-%m-%d")
            except Exception as exc:
                # 2026-10-07：原为 pass（静默吞掉），改为留痕。
                # 失败时本段仍保持相对分段 day_from/day_to，可用性不受影响，
                # 但必须能从 payload 看出「日期没对上」，否则调用方无从分辨
                # 「无节气基准」与「有基准但换算失败」。
                entry["date_align_error"] = f"节气日期对齐失败（保留相对分段）：{exc}"
        days.append(entry)
    return LiuRiResult(month=0, days=days)


def compute_liuri_stub(yue_lines: list[int], yue_yao_index: int) -> list[dict]:
    """流日六段的**廉价索引**（含六爻，不含卦名），供全量时间轴按需化使用。

    2026-10-06：四层时间轴只为「命中应期的那一个月」付出卦名换算代价。
    旧实现在 ``_build_timeline`` 里对 93 流年 × 12 月 = 1,116 个月逐月调用
    ``compute_liuri``，每次做 6 次 ``_lines_to_hexagram`` 卦名换算
    （合计 6,696 次），占单盘耗时与载荷的大头；而消费方（guajie）
    每次排盘只查**一个**月。

    本函数保留每段六爻——``_flip_line`` 只是复制一个 6 元 list 并翻转一爻，
    近乎零成本——**只省掉 ``name``/``upper``/``lower`` 三个卦名字符串**，
    那才是耗时与载荷的大头。
    保留 ``lines`` 是刻意取舍：tests/heluo/test_timeline_yun_perf.py 的
    ``TestLazyLiuShi`` 两项断言直接读 ``d["lines"]`` 校验 flip_index，
    保留它即可在**不改任何既有测试**的前提下拿到全部收益。

    ``flip_index`` 即该日/该段的变爻位置（与 ``day_yao_index`` 同值），
    由 :func:`liuri_day_positions` 直接给出。

    2026-10-07 起 ``lines``/``day_lines`` 为**链式累变**结果（见
    :func:`liuri_day_lines`），不再是对月卦的单爻翻转。

    需要卦名时，由调用方对命中的那一个月调 :func:`materialize_month_days` 现算。
    """
    positions = liuri_day_positions(yue_yao_index)
    day_lines = liuri_day_lines(yue_lines, yue_yao_index)
    out = []
    for k in range(6):
        seg_days = positions[k * 5:k * 5 + 5]
        out.append({
            "segment": k + 1,
            "day_from": k * 5 + 1,
            "day_to": k * 5 + 5,
            "flip_index": seg_days[0],
            "lines": day_lines[k * 5][1],
            "day_positions": seg_days,
            "day_lines": [day_lines[k * 5 + j][1] for j in range(5)],
        })
    return out


def materialize_month_days(month: dict) -> list[dict]:
    """把按需化的流月条目的 ``days`` 物化成完整日段（含卦名与六爻）。

    2026-10-06：``canonical._build_timeline`` 只存六段廉价定位字段
    （见 :func:`compute_liuri_stub`），以避免 1,116 个月 × 6 次卦名换算。
    排盘时只有**命中应期的那一个月**需要完整日段，由消费方（guajie）
    调本函数现算。

    Args:
        month: ``_build_timeline`` 产出的单个月份 dict。

    Returns:
        完整日段列表（segment/day_from/day_to/flip_index/name/upper/lower/lines），
        与改造前逐月 ``compute_liuri(...).days`` 的内容逐字一致。
    """
    lines = month.get("lines") or []
    yue_yao = month.get("yue_yao_index")
    if yue_yao is None or not lines:
        return list(month.get("days") or [])
    days = compute_liuri(lines, yue_yao, month.get("jie_datetime")).days
    return days


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
    "liuri_day_positions", "liuri_day_lines",
    "compute_liushi", "LiuShiResult",
]
