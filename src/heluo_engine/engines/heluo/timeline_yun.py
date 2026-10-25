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

from .numbers import get_hexagram_name

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
    #: 本岁所属**大运段**的元堂爻位（0-5）。
    #:
    #: ⚠ 命名警示（2026-10-24）：本字段**不是本命元堂**，也**不是行年爻**。
    #:   - 本命元堂 = `YuanTang.yuantang_index`（出生时先天卦的元堂，全程唯一）；
    #:   - 大运段元堂 = 本字段（每换一段大运变一次，段内恒定）；
    #:   - 行年爻 = `xingnian_yao_index`（本字段下方，逐年挨次变）。
    #:   三者曾共用「yuantang_index」一名，导致「该取行年爻却取了大运段爻」
    #:   的静默错判（2026-10-24 修复流年断爻、流月起卦基准时各踩一次）。
    #:   故流年层一律用 `dayun_seg_yuantang_index` 明确指称本字段。
    dayun_seg_yuantang_index: int = -1
    #: 本年「小象行年爻」= 该年小象变出的那一爻（原典起例卷之上·小象行年卦气：
    #: 「一岁在同人九三（阳）爻；二岁取应爻变，同人上九为革上六；三岁复取应爻变，
    #:  革九三为随六三；然后自下而上，四岁变随九四为屯六四……」）。
    #: -1 = 本年未变（行年爻仍取元堂爻）。
    #: 2026-10-24 新增：此前只把该爻位写进 rule 字符串，下游取不到 ——
    #: 导致流年断爻恒取「年卦的元堂爻」（= 大运段爻，同段内恒定），
    #: 而非原典的「逐年挨次变」之行年爻。
    xingnian_yao_index: int = -1


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
    dayun: DayunResult | None = None,
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
    # 2026-10-22 B6：调用方（canonical）已算好 dayun，传入复用，避免算两遍。
    dayun = dayun if dayun is not None else compute_dayun_liyao(
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
        # ⚠ 2026-10-24：本年「小象行年爻」= 该年小象变出的那一爻
        #   （原典起例卷之上·小象行年卦气：「一岁在同人九三（阳）爻；二岁取应爻变，
        #   同人上九为革上六；三岁复取应爻变，革九三为随六三；然后自下而上，
        #   四岁变随九四为屯六四……」—— 括号/主语里的那个爻即行年爻）。
        #   原先只把 flip_idx 写进 rule 字符串，下游取不到；此处显式落字段。
        flip_idx: Optional[int] = None

        if seg_yang_line:
            # 阳爻大运段（9年）：段内小象循环
            if n == 1:
                if seg_first_yang:
                    cur = list(seg.lines)
                    rule = "段首阳年不变"
                    # 一岁不动 → 行年爻仍是元堂爻本身
                    flip_idx = seg_yt
                else:
                    cur = _flip_line(seg.lines, seg_yt)
                    rule = "段首阴年变元堂"
                    flip_idx = seg_yt
            elif n == 2:
                base = prev1 if prev1 is not None else list(seg.lines)
                flip_idx = (seg_yt + 3) % 6
                cur = _flip_line(base, flip_idx)
                rule = "变元堂应爻"
            elif n == 3:
                base = prev1 if prev1 is not None else list(seg.lines)
                flip_idx = seg_yt
                cur = _flip_line(base, flip_idx)
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
            lines=cur, rule=rule, dayun_seg_yuantang_index=seg_yt,
            xingnian_yao_index=flip_idx,
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

    应爻基准（已裁定，见 tests/heluo/test_heluo_original_cases.py
    TestCase12HeLuoLiShuYueGua）：双月所取之应爻，是**当月阳月居位变爻**的
    隔三位应爻，不是元堂之应爻。依据为《河洛理数》卷五「月卦」四组显式
    逐月对拍（K3-448 修正版 L469-L471；K3-447 修正版 L1132-L1146）：
      「五月是小畜三爻，六月则取小畜应爻上九」
      「七月是乾九四，八月则取乾卦应爻初九」
      「大有六五……取大有应爻……离卦六二」
      「十一月是大壮上爻，则十二月取大壮应爻……归妹六三」
    若按元堂取应爻，六个月双月将同变一爻，与上述实证冲突。
    《河洛真数》同段时卦例「日卦变时卦，与年卦变月卦同……子时其应爻则丑时也」
    同一基准（取刚变之爻），可互为佐证。

    ⚠ 2026-10-24 **订正本段原引文**（原典查无实据，且与原典相反）：
      原 docstring 曾写「古籍月卦之法『悉从二十四气，非从朔望』，从子月（冬至）起，
      故『前以正月起者，非』」—— 经全底本检索（《河洛真数——原著.txt》20158 行、
      《河洛理数》K3-448/K3-447/K3-449/续修四库本），**这三句引文原典无载**，
      且「前以正月起者，非」与原典**直接相反**。若照它推演，会把月卦序列
      的锚点从「正月」挪到「子月」，整体错位两个月 —— 本函数的实现是**对的**
      （锚点=正月），错的只是这段说明。现按原典改写：

      · 锚点 = **正月**：《河洛真数·起例卷之上》L384（包内切片 L127）
        「凡起月卦…秘决云：此例亦是，但**要从所生之月准正月起**，如起日卦一般，
         **数至十二月毕**。若正月则是下年正月也。**此说方合节气**。」
      · 月序 = **农历月序号**（建寅：正月=寅月=立春月、七月=申月=立秋月）——
        「此说方合节气」即指与节气同源；引擎既有
        `_jie_datetime_for_lunar_month(year, lm)` 的 lm↔节 表即此口径
        （lm=1 立春 / lm=7 立秋 / lm=12 小寒）。
      · 阴阳月 = 奇偶月：L133（包内切片 L402）
        「但**子寅辰午申戌居左**，变爻用点，**丑卯巳未酉亥居右**取应」
        —— 阳月（居左、变爻用点）配子寅辰午申戌 = 建寅下的奇数月；
        阴月（居右、取应爻）配丑卯巳未酉亥 = 偶数月 ⇒ 阳月=奇、阴月=偶 ✓
        （与本实现 ``2*k+1`` 阳月 / ``2*k+2`` 阴月 逐月对应）。
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


#: gua6 的**变爻序**：**爻位顺序，跳过居位爻**（月卦各变一爻，不累变）。
#:
#: 依据：《河洛理数》日卦定式（K3-448 1632笔写本 L464-L491 / K3-447 1871增补本
#: L1149-L1159）：
#:   · 「日卦者每月變五卦，每卦管六日，方成一月」—— 每月 5 卦 × 6 日 = 30 日。
#:   · 「假如七月月得既濟六二爻，**除此一爻不變**」—— 五卦是月卦**各变一爻**
#:     （不是链式累变），**居位爻不动**。
#:   · 硬算例（万历二十三年七月，七月初二日午时立秋）：
#:       段1 變既濟九三 → **屯卦**（管初二~初七；「屯卦六爻從下而上一爻一日」）
#:       段2 變既濟六四 → **革卦**（L477「至初八日又變…為革卦，此一卦自下而上」；
#:                             初八 = 初二 + 6 = 段2 起点 ✓）
#:       段3 變既濟九五 → **明夷**（L483「至十四日…明夷六五」；
#:                             十四 = 初二 + 12 = 段3 起点 ✓）
#:       段4 變既濟上六 → **家人**（K3-447 L1158「再將月卦上六爻變為家人，管六日」）
#:       段5 變既濟初九 → **蹇**（余下唯一未变之爻，由「除此一爻不變」排除法定）
#:     ⇒ 变爻序 = **三、四、五、上、初**（居位=二爻时）＝ 爻位顺序跳过居位。
#:
#: ⚠ 诚实标注：段1/段2/段3 的**卦名与段序**有两处日算互证（初八、十四）；
#: 段4（家人）由底本可辨名 + 段序由余位推定；段5（蹇）为排除法定。
_GUA6_FLIP_ORDER: tuple[int, ...] = (2, 3, 4, 5, 0)


def liuri_gua6_bases(yue_lines: list[int], yue_yao_index: int) -> list[list[int]]:
    """gua6 的 **5 个段本卦**：月卦逐爻变（**居位爻不动**）。

    原典（《河洛理数》日卦定式）：「日卦者每月變五卦，每卦管六日，方成一月」，
    「假如七月月得既濟六二爻，除此一爻不變」—— 五卦是月卦**各变一爻**（不累变），
    变爻序为**爻位顺序跳过居位爻**（见 :data:`_GUA6_FLIP_ORDER` 的引文链）。

    ⚠ 2026-10-22 修正：原实现取链式累变的 ``day_lines[k*6]``（那是《河洛真数》
    hou5 的链），在 gua6 口径下产出**退化序列**（既济/居位二爻 → 屯、鼎、屯、鼎、屯），
    与原典的「屯、革、明夷、家人、蹇」不符。
    """
    order = [(yue_yao_index + k) % 6 for k in range(1, 6)]
    return [_flip_line(list(yue_lines), idx) for idx in order]


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
      对应爻位（非链式）」，并据晚出约 40 年的《河洛理数》「每管六日」一系口径
      取 5 段×6 日。当时**该「每管六日」引文本地无源**（data/ 全库检索
      「每管六日|一爻一日|一卦六日|除此一爻|自下爻行至上爻|六日一变」= 0 命中，
      《河洛理数》起例卷原文未入库），故登记为**待取证**，不作已证依据。
      2026-10-07 依《河洛真数》L129 逐日实例定案为链式 6 爻×5 日（hou5）。

    ✅ 2026-10-22 **已取证**：《河洛理数》日卦起例卷原文已切片入库
      （heluo_engine/orig/河洛理数_日卦起例卷.txt，18 条 / 271 行逐字原文；
      校记见同目录 河洛理数_日卦起例卷_校记.md）。关键条文：
        · K3-447 L1154「日卦者每月變五卦每卦管六日方成一月五六三」
        · K3-448 L488「其餘五爻五變 一卦管六日 …」
        · K3-448 L479「日卦上支管初七日…從下而上一交一日」
        · K3-448 L481「日卦行起必須按月卦節氣方不誤」
        · K3-448 L491「以此推之則每日添一刻七分天 六日」
      故流日层**生产口径为 gua6**（一卦管 6 日、一爻一日、首日从初爻），
      与 fast path 一致（见 ``compute_daily_base_hex`` 与
      ``tests/test_heluo_liuri_rule_consistency.py``）。
      hou5（《河洛真数》L390 每爻管五日）作为**原典变体**保留，
      仅供原典对拍（``rule="hou5"``），不是生产口径。
      ⚠ 两书口径并存且原文未言取舍，见校记「原文层面未解决问题」第 ① 条。

    节气对齐（《河洛真数·起例卷之上》L129「假如乾九二居位，**进一爻起节气**。
      假如正月节气在十二月小尽二十八日，立春就从二十八日起数是也」+ L127
      「但要从人所生之月准正月起，如起日卦一般…**此说方合节气**」）：
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


def compute_daily_base_hex(
    yue_lines: list[int],
    yue_yao_index: int,
    target_day: int = 1,
    jie_datetime: str | None = None,
    next_jie_datetime: str | None = None,
    rule: str = "gua6",
) -> tuple[dict, list[dict]]:
    """流日层（定稿 2026-10-22）：一卦管 6 日、一爻一日，**段边界按节气实际间隔均匀分配**。

    原典依据（用户 2026-10-22 引）：
      · 「六日一变」的卦气系统：同样从节气开始，但六天更换一卦，**首日从初爻开始**。
      · 「日卦的起算必须严格遵循各月节气交接的具体时刻，而不能机械地固定每卦六日。
        因为节气长度并非完全均等（或不足 30 日，或超过 30 日），所以需要根据实际
        时刻来『均匀』分配，不可执定『卦六日』的死板规则。」

    原著硬算例（K3-448 1632笔写本 L479-L491 逐字）：
        L479: 日卦上支管初七日是此屯却六交从下而上一交一日自初二日至初七
        L480: 卦二交管初盈日屯卦三交管初四日卦四交管初五日世卦五交管初六
        L481: 六月自下交行盈上交盏取一交一日也日卦行起必须按月卦節氧方不
        L482: 如本年七月初二日午時立缺節刚卦初儿交即徒初二日午時管起屯
        L483: 一日共管六日也至千十四日又襄前既卦九五交岛明夷六五自下雨上
        L488: 其餘五交五舞一卦管六日五六方三十交管三十日也随其文称宾吉色
        L491: 以此推之则每日添一刻七分天六日
      （K3-447 1871增补本 L1154: 日卦者每月變五卦每卦管六日方成一月五六三）

    落码：
      · **日序固定 6 日一组**：每月 5 卦 × 6 日 = 30 日（L1154 / L475 / L483
        「一日共管六日也」）。L482-483 硬算例：七月「初二日午时」立秋起，
        第一卦管初二~初七，「至十四日」第三卦起 —— 初二 + 12 = 十四，
        **日序恒 6 日一组**，铁证。
      · **时刻按实际节气间隔均匀推移**（L491「每日添一刻七分天 六日」）：
        第 k 段起时刻 = T0 + k*(T1-T0)/5。节气非 30 日时，每日多/少推一点，
        整月从节到节对齐 —— 这才是「不可执定『卦六日』的死板规则」的含义：
        **六日仍是六日，但六日所跨的时刻随实际节气间隔变**。
      · 每段 1 个流日本卦（本体/互/错/综/卦气一次算好），6 日共用
      · 段内每日只取对应爻位（**首日从初爻开始**），做轻量爻运算
      · 段间推进：**月卦逐爻变**（第 k 段本卦 = 月卦变第 k 个未变之爻，
        居位爻不动 —— 《河洛理数》日卦定式：「日卦者每月變五卦，每卦管六日」
        「除此一爻不變」；变爻序与硬算例见 :func:`liuri_gua6_bases`）
        ⚠ 2026-10-22 修正：原实现误取《河洛真数》hou5 的链式 `day_lines[k*6]`，
        在 gua6 口径下产出退化序列（屯、鼎、屯、鼎、屯），与原典「屯、革、明夷、
        家人、蹇」不符。

    与 hou5（原典 L129「每一爻管五日、挨次而变」）**不可兼容**。

    Returns:
        ``(base_hex, daily_yao)``
        - ``base_hex``   目标日所在段的完整卦字典
        - ``daily_yao`` 该段 6 日：每日激活爻 + 轻量运算结果
    """
    from .hexagram import (  # 权威单一来源：不自造互错综与五行表
        TRIGRAM_ELEMENT, compute_cuo_gua, compute_hu_gua, compute_zong_gua,
    )
    from datetime import timedelta

    n_seg = 5
    seg_len = 6
    # 2026-10-22 B4：positions 算完从不使用（30 次外循环 + 内层扫描 ≈ 90 步/盘）
    # ——只需 day_lines 的链式结果 → 删死算。
    day_lines = liuri_day_lines(yue_lines, yue_yao_index)

    base_dt = _parse_datetime(jie_datetime) if jie_datetime else None
    nxt_dt = _parse_datetime(next_jie_datetime) if next_jie_datetime else None
    _uniform = base_dt is not None and nxt_dt is not None and nxt_dt > base_dt

    # ── 段边界：日序固定 6 日一组；时刻按实际节气间隔均匀推移 ──
    #   日序固定  ← K3-447 L1154「每月變五卦每卦管六日」+ K3-448 L483 硬算例
    #   时刻均匀  ← K3-448 L491「以此推之则每日添一刻七分天 六日」
    segs: list[dict] = []
    for k in range(n_seg):
        d_from = k * seg_len + 1
        d_to = (k + 1) * seg_len
        date_from = ""
        date_to = ""
        jie_span_days = None
        if _uniform:
            span = (nxt_dt - base_dt).total_seconds()
            seg_sec = span / n_seg
            b0 = base_dt + timedelta(seconds=k * seg_sec)
            b1 = base_dt + timedelta(seconds=(k + 1) * seg_sec)
            date_from = b0.strftime("%Y-%m-%d %H:%M")
            date_to = b1.strftime("%Y-%m-%d %H:%M")
            jie_span_days = round(span / 86400.0, 4)
        segs.append({
            "segment": k + 1, "day_from": d_from, "day_to": d_to,
            "date_from": date_from, "date_to": date_to,
            "jie_span_days": jie_span_days,
        })

    # ── 定位目标日所在段 ──
    _td = int(target_day or 1)
    k = next((i for i, sg in enumerate(segs)
              if sg["day_from"] <= _td <= sg["day_to"]), None)
    if k is None:
        k = max(0, min(n_seg - 1, (_td - 1) // seg_len))
    seg = segs[k]

    # ── 该段本卦：gua6 = 月卦逐爻变（liuri_gua6_bases）；hou5 = 链式 day_lines ──
    if rule == "hou5":
        base_lines = list(day_lines[k * seg_len][1])
    else:
        base_lines = list(liuri_gua6_bases(yue_lines, yue_yao_index)[k])
    u, lo, name = _lines_to_hexagram(base_lines)

    base_hex = {
        "name": name, "upper": u, "lower": lo, "lines": list(base_lines),
        "hu_name": compute_hu_gua(base_lines),
        "cuo_name": compute_cuo_gua(u, lo),
        "zong_name": compute_zong_gua(u, lo),
        "element": TRIGRAM_ELEMENT.get(u, "") or TRIGRAM_ELEMENT.get(lo, ""),
        "yue_yao_index": yue_yao_index,
        "segment": seg["segment"],
        "day_from": seg["day_from"], "day_to": seg["day_to"],
        "date_from": seg["date_from"],
        "jie_span_days": seg["jie_span_days"],
        "jie_datetime": jie_datetime or "",
        "next_jie_datetime": next_jie_datetime or "",
        "rule": rule,
    }

    # ── 段内 6 日：固定本卦，每日取对应爻位（首日从初爻开始）──
    yao_names = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")
    daily_yao: list[dict] = []
    # ⚠ 2026-10-24 新增：每日的**真实时刻**（原典 L491「以此推之则每日添一刻七分天」）。
    #   推法：第 n 日的时刻 = 节时刻 + (n-1) × (节气间隔 / 30) ——
    #   与段边界「节 + k×(间隔/5)」**逐位自洽**
    #   （第 6k+1 日 = 节 + 6k×间隔/30 = 节 + k×间隔/5 ✓）。
    #   此前 daily_yao 只带「段首时刻」(date_from)，导致：
    #     ① 黄历标注显示的是**段首日**而非目标日（目标 10-23 却标 10-20）；
    #     ② 平台层 DAILY 信号按**段首日**发（canonical_signals 取
    #        liuri_lunar.solar_date 的日号）⇒ 事件落在错误的日期上。
    _day_sec = (nxt_dt - base_dt).total_seconds() / 30.0 if _uniform else None
    for d in range(seg_len):
        idx = d  # 首日从初爻开始，依次初/二/三/四/五/上
        changed = _flip_line(list(base_lines), idx)
        cu, clo, cname = _lines_to_hexagram(changed)
        _no = seg["day_from"] + d
        _day_dt = ""
        if _day_sec is not None:
            _day_dt = (base_dt + timedelta(seconds=(_no - 1) * _day_sec)
                       ).strftime("%Y-%m-%d %H:%M")
        daily_yao.append({
            "day_no": _no,
            "day_in_seg": d + 1,
            "active_yao": yao_names[idx],
            "yao_index": idx,
            "yao_nature": "阳" if base_lines[idx] else "阴",
            "date_from": seg["date_from"],
            # 该日的**真实时刻**（原典 L491「每日添一刻七分天」）；
            # date_from 仍保留**段首时刻**（旧消费方按段读，不改语义）。
            "date": _day_dt,
            "changed_name": cname,
            "changed_upper": cu,
            "changed_lower": clo,
            "changed_lines": list(changed),
            "changed_element": TRIGRAM_ELEMENT.get(cu, "") or TRIGRAM_ELEMENT.get(clo, ""),
        })
    # 目标日本身的时刻（平台层按目标日发信号，不按段首日）
    if _day_sec is not None:
        base_hex["target_date"] = (
            base_dt + timedelta(seconds=(_td - 1) * _day_sec)
        ).strftime("%Y-%m-%d %H:%M")
        base_hex["target_day_no"] = _td
    return base_hex, daily_yao

def compute_liuri_stub(
    yue_lines: list[int],
    yue_yao_index: int,
    rule: str = "gua6",
) -> list[dict]:
    """流日层的**廉价索引**（含六爻，不含卦名），供全量时间轴按需化使用。

    2026-10-22（口径统一）：默认 **gua6**（定稿口径 —— 一卦管 6 日、
    一爻一日、首日从初爻起）。此前默认 hou5（每爻管 5 日），导致
    **全量路径与 fast path 对同一 (年,月,日) 给出不同的流日卦名与动爻**
    （实测：升/九三 vs 损/初九），已统一为 gua6。

    ``rule="hou5"`` 保留《河洛真数》L390 原典变体（每爻管 5 日、
    阳日寻阳位/阴日寻阴位、链式累变），**仅供原典对拍**，不是生产口径。

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

    ``flip_index`` 即该日/该段的变爻位置（与 ``day_yao_index`` 同值）：
      · gua6：段内日序 0-5（首日=初爻）
      · hou5：由 :func:`liuri_day_positions` 直接给出（阳/阴位交替）

    需要卦名时，由调用方对命中的那一个月调 :func:`materialize_month_days` 现算。
    """
    if rule == "hou5":
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
                "rule": "hou5",
            })
        return out

    # ── gua6（《河洛理数》日卦定式）：一个月 5 卦 × 6 日 ──
    #   段本卦 = **月卦逐爻变**（居位爻不动，见 liuri_gua6_bases）；
    #   段内第 d 日 = 段本卦翻第 d 爻（自下而上，一爻一日）。
    bases = liuri_gua6_bases(yue_lines, yue_yao_index)
    out = []
    for k in range(5):
        base = list(bases[k])
        out.append({
            "segment": k + 1,
            "day_from": k * 6 + 1,
            "day_to": k * 6 + 6,
            "flip_index": 0,          # 段首日 = 初爻
            "lines": base,
            "day_positions": [0, 1, 2, 3, 4, 5],
            "day_lines": [_flip_line(base, d) for d in range(6)],
            "rule": "gua6",
        })
    return out


def materialize_month_days(month: dict, rule: str | None = None) -> list[dict]:
    """把流月条目的 ``days`` 物化成完整日段（定稿口径：gua6）。

    定稿流日结构：**一个月 30 日 = 5 组 × 6 日**（一卦管 6 日、一爻一日）——
        · 每组 1 个流日本卦（本体/互错综/卦气一次算好）
        · 组内 6 日共用该本卦，每日只取对应爻位（初→1日 … 上→6日）做轻量爻运算
        · 组间链式推进

    2026-10-22 口径统一：本函数原先靠**嗅探 payload 里有没有 ``day_no``**
    来分流（gua6 逐日条目 vs hou5 段索引），这是隐式契约 —— 同一份数据
    因形状不同走两套算法，产出**不同的流日卦名与动爻**。现改为：
      1. 先看显式 ``rule`` 参数 → 再看 month 里的 ``liuri_rule`` 标注；
      2. 都没有才回退到形状嗅探（仅为兼容旧 payload）。

    本函数对外仍返回 **hou5 兼容形态**（day_from/day_to/segment/flip_index/
    name/upper/lower/lines/day_items/date_from），使下游 guajie 的既有读法
    （d_from/d_to 区间 + day_items 逐日取卦）不需改动。

    Args:
        month: ``_build_timeline`` 产出的单个月份 dict。
        rule: 显式口径（``"gua6"`` / ``"hou5"``）；None 则取 month 里的
            ``liuri_rule``，再无则按形状嗅探。

    Returns:
        完整日段列表（每条对应一日）。
    """
    _days = list(month.get("days") or [])
    _rule = rule or month.get("liuri_rule") or ""
    if not _rule:
        # 兼容旧 payload：优先看日段自带的 rule 标记；都没有才按形状嗅探
        _seg_rules = {d.get("rule") for d in _days if d.get("rule")}
        if len(_seg_rules) == 1:
            _rule = _seg_rules.pop()
        elif _days and any(d.get("day_no") is not None for d in _days):
            _rule = "gua6"
        else:
            _rule = "hou5"

    if _rule == "hou5":
        # 《河洛真数》L390 原典变体（每爻管 5 日）：旧法现算
        lines = month.get("lines") or []
        yue_yao = month.get("yue_yao_index")
        if yue_yao is None or not lines:
            return _days
        return compute_liuri(lines, yue_yao, month.get("jie_datetime")).days

    # ── gua6 ──
    if _days and any(d.get("day_no") is not None for d in _days):
        # 已预置的**逐日**条目（fast path 目标月：1 本卦 + 6 日激活爻）
        _date_from = _days[0].get("date_from", "")
        return [_gua6_day_to_compat(_d, _date_from) for _d in _days]

    if _days:
        # 段索引（全量路径）→ 展开为逐日
        out: list[dict] = []
        for seg in _days:
            out.extend(_gua6_segment_to_days(seg))
        return out

    # 无预置日段（fast path 的非目标月）→ 按同一口径现算
    lines = month.get("lines") or []
    yue_yao = month.get("yue_yao_index")
    if yue_yao is None or not lines:
        return _days
    out = []
    for seg in compute_liuri_stub(lines, yue_yao, rule="gua6"):
        out.extend(_gua6_segment_to_days(seg))
    return out


def _gua6_segment_to_days(seg: dict) -> list[dict]:
    """gua6 段索引 → 逐日条目（hou5 兼容形态）。

    段内每日激活爻：**首日从初爻起**，依次初/二/三/四/五/上（定稿口径）。
    段本卦 = **月卦逐爻变**（居位爻不动，见 :func:`liuri_gua6_bases`）——
    与 ``compute_liuri_stub`` / ``compute_daily_base_hex`` 同一算法，
    故本函数与 fast path 的预置结果**逐字一致**。

    ⚠ 2026-10-24 订正：本 docstring 原写「段本卦 = 链式 day_lines[k*6]」——
      那是 2026-10-22 修正**之前**的旧口径（hou5 的链式累变），已在
      commit 7a5ce148 改为「月卦逐爻变」。此处描述滞后于实现，
      会误导后来者以为链式仍是 gua6 的正确口径 —— 现予订正。
      （实测：链式在 gua6 下产出退化序列 屯/鼎/屯/鼎/屯，
        与原典「屯、革、明夷、家人、蹇」不符。）
    """
    _dls = seg.get("day_lines") or []
    _first = int(seg.get("day_from") or 1)
    _date_from = seg.get("date_from", "") or ""
    out: list[dict] = []
    for d in range(len(_dls)):
        changed = _dls[d]
        cu, clo, cname = _lines_to_hexagram(changed)
        day_no = _first + d
        out.append({
            "day": day_no,
            "day_no": day_no,
            "segment": seg.get("segment", day_no),
            "day_from": day_no,
            "day_to": day_no,
            "flip_index": d,
            "day_yao_index": d,
            "name": cname, "upper": cu, "lower": clo,
            "lines": list(changed),
            "date_from": _date_from,
            "day_items": [{
                "day": day_no,
                "polarity": "阳日" if d % 2 == 0 else "阴日",
                "flip_index": d,
                "day_yao_index": d,
                "name": cname, "upper": cu, "lower": clo,
                "lines": list(changed),
                "date": _date_from[:10] if _date_from else "",
            }],
        })
    return out


def _gua6_day_to_compat(d: dict, date_from: str = "") -> dict:
    """gua6 日条目 → hou5 兼容形态（day_from/day_to/segment/day_items/...）。"""
    _no = d.get("day_no")
    _f = _no if _no is not None else d.get("day_from", 1)
    _t = _no if _no is not None else d.get("day_to", 6)
    _lines = d.get("changed_lines") or d.get("lines") or []
    _name = d.get("changed_name") or d.get("name", "")
    _upper = d.get("changed_upper") or d.get("upper", "")
    _lower = d.get("changed_lower") or d.get("lower", "")
    _flip = d.get("yao_index")
    if _flip is None:
        _flip = d.get("day_yao_index", d.get("flip_index", 0))
    # ⚠ 2026-10-24：优先用**该日自己的时刻**（原典 L491「每日添一刻七分天」
    #   推出的逐日时刻）；缺失时退回段首时刻（旧行为）。
    _day_date = d.get("date") or d.get("date_from", date_from)
    return {
        "day": _no if _no is not None else d.get("day", _f),
        "day_no": _no,
        "segment": d.get("segment", _no),
        "day_from": _f,
        "day_to": _t,
        "flip_index": _flip,
        "day_yao_index": d.get("day_yao_index", _flip),
        "name": _name,
        "upper": _upper,
        "lower": _lower,
        "lines": list(_lines),
        "date_from": d.get("date_from", date_from),
        "date": _day_date,
        "day_items": [{
            "day": _no if _no is not None else d.get("day", _f),
            "polarity": "阳日" if _flip % 2 == 0 else "阴日",
            "flip_index": _flip,
            "day_yao_index": _flip,
            "name": _name, "upper": _upper, "lower": _lower,
            "lines": list(_lines),
            "date": _day_date[:10] if _day_date else "",
        }],
    }

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


#: 流时卦的两法（《河洛真数》起时卦例末句「**二法皆通，前法为优**」）。
LIUSHI_METHOD_QIAN = "qian"      # 前法（生产口径）
LIUSHI_METHOD_HOU = "hou"        # 后法（留档，与年卦变月卦同）


def compute_liushi(
    day_lines: list[int],
    day_yao_index: int,
    method: str = LIUSHI_METHOD_QIAN,
) -> LiuShiResult:
    """流时卦（《河洛真数·起例卷之上·起时卦例》）。

    原文（逐字）：
      「凡起时卦，于日中寻时，就值日卦上从前一爻起，子丑寅卯辰巳六时，
        主进数变去；值日卦后一爻起，午未申酉戌亥六时，主退数变去。
        假如得乾卦初爻值日，则从二爻变起。
        又云，日卦变时卦，与年卦变月卦同。但子寅辰午申戌居左，变爻用点，
        丑卯巳未酉亥居右取应，变爻不同点。凡居位进一爻起，子时其应爻则丑时也。
        假令乾卦初九居位，进一爻起数。自下而上挨次变去，取变卦应爻变之。
        **二法皆通，前法为优，学者详之。**」

    两法（``method``）：

    * **前法**（默认，生产口径）：子…巳 自值日爻的下一爻起**进数**（+1…+6）
      逐时累积变；午…亥 自值日爻的后一爻起**退数**（-1…-6）逐时累积变
      （后六时重新从值日卦起）。**十二时皆为变爻，不取应爻。**
    * **后法**（留档）：与「年卦变月卦」同 —— 阳时（子寅辰午申戌）链式逐爻变，
      阴时（丑卯巳未酉亥）取对应阳时的应爻。

    ⚠ 2026-10-22 修正：原实现把两法**混用**（前六时用后法的阴阳时分配，
    后六时用「退数 + 阴时取应」的第三种组合），十二时中只有子、午两时与原典
    前法相符 —— 既不是前法，也不是后法。已按「前法为优」更正。

    ⚠ **生产链不启用本层**（用户 2026-10-22 裁决：「不要算流时卦，到流日就可以」）：
    流时层自 2026-10-06 起整段剥离（见 guajie.build_guajie_from_result），
    本函数**只作为算法本体保留**，不被生产链调用。保留它且按原典更正，是为了
    不在代码里留一颗「看着能用、实则两法混用」的地雷；将来若要启用，
    口径已是前法（= 原典「前法为优」），可直接接回。

    原典实例（乾初爻值日）：子时变二爻（天火同人）、午时变上爻（泽天夬）。
    """
    u, lo, name = _lines_to_hexagram(list(day_lines))
    hours: list[dict] = []

    def _emit(hour_no: int, lines: list[int], yao: int, kind: str) -> None:
        u2, lo2, name2 = _lines_to_hexagram(lines)
        hours.append({
            "hour": hour_no, "name": name2, "upper": u2, "lower": lo2,
            "lines": list(lines), "kind": kind, "shi_yao_index": yao,
        })

    if method == LIUSHI_METHOD_HOU:
        # 后法：阳时（子寅辰午申戌）链式变爻；阴时（丑卯巳未酉亥）取应
        yangs: list[tuple[list[int], int]] = []
        cur = list(day_lines)
        for k in range(6):
            idx = (day_yao_index + 1 + k) % 6
            cur = _flip_line(cur, idx)
            yangs.append((list(cur), idx))
        for k, (lines, idx) in enumerate(yangs):
            _emit(2 * k + 1, lines, idx, "阳时")
        for k, (lines, idx) in enumerate(yangs):
            ying = (idx + 3) % 6
            _emit(2 * k + 2, _flip_line(list(lines), ying), ying, "阴时")
        hours.sort(key=lambda h: h["hour"])
        return LiuShiResult(day_name=name, hours=hours)

    # 前法（生产口径）：前六时进数、后六时退数，十二时皆变爻
    cur = list(day_lines)
    for k in range(6):                       # 子丑寅卯辰巳
        idx = (day_yao_index + 1 + k) % 6
        cur = _flip_line(cur, idx)
        _emit(k + 1, cur, idx, "变爻")
    cur = list(day_lines)                    # 后六时重新从值日卦起
    for k in range(6):                       # 午未申酉戌亥
        idx = (day_yao_index - 1 - k) % 6
        cur = _flip_line(cur, idx)
        _emit(7 + k, cur, idx, "变爻")
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
