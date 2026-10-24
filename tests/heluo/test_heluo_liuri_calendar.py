# -*- coding: utf-8 -*-
"""流日层**日历口径**守卫（2026-10-24 新增）。

背景（真缺陷）：河洛日卦层的内部契约是「**节气月序** + **自节起的日序**」，
而 adapter 层传进来的是**公历**月日 —— 两者口径不同 ⇒ 流日卦取的是**别的月**
的日卦。实测（修复前）：target_date=2026-10-23（寒露后第 16 日，属九月/寒露月）
被算成**十月/立冬月**的段，date_from=2026-11-25，与目标日相差 33 天。

本文件钉死三件事：
  1. **公历 → 节气窗口的换算本身是对的**（含独立第三方库交叉核验、
     全年逐日不重不漏、跨年边界 1/1–1/4）。
  2. **原典硬算例**：节当日即新月第 1 日（K3-448 L482「七月初二日午時立秋節」；
     《河洛真数》L129「立春就从二十八日起数」）。
  3. **端到端**：adapter 出来的流日必须**覆盖目标日**，且用的是**节气月序**
     而不是公历月；结果里的 target_date 必须是**公历原值**。

⚠ 口径声明（本守卫自身的前提，勿改）：
  · 月序 = **农历月序**（建寅）：正月=立春月、七月=立秋月、十一月=大雪月、
    十二月=小寒月。依据《河洛真数》L384「要从所生之月准正月起…此说方合节气」
    + L133「子寅辰午申戌居左…丑卯巳未酉亥居右」（阳月=奇数月）。
  · 日序 = **自节起的日历日序**（1 = 节当日）。
  · 月界取二十四**气**（中气）；引擎内部沿用「节」这一称呼（术语略松，
    取的时刻正确）。
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine.adapter import HeluoAdapter  # noqa: E402
from heluo_engine.engines.heluo.canonical import (  # noqa: E402
    resolve_jieqi_window,
)

# ---------------------------------------------------------------------------
# 独立第三方路径（lunar_python）—— 不复用引擎的 _LUNAR_MONTH_JIE 表，
# 避免「自己验自己」。
# ---------------------------------------------------------------------------
#: 建寅十二**中气**及其月序（正月=立春=1 … 十二月=小寒=12）
MID_QI_MONTH = {
    "小寒": 12, "立春": 1, "惊蛰": 2, "清明": 3, "立夏": 4, "芒种": 5,
    "小暑": 6, "立秋": 7, "白露": 8, "寒露": 9, "立冬": 10, "大雪": 11,
}


def _solar_to_date(s) -> date:
    return date(s.getYear(), s.getMonth(), s.getDay())


def _prev_before(s) -> "object":
    """严格早于 solar 的上一个节气。

    ⚠ lunar_python 的 getPrevJieQi 在**节气当日**会返回它自己，故须
    先退一天再取，避免拿到「同一天」。
    """
    from lunar_python import Solar
    d = _solar_to_date(s) - timedelta(days=1)
    return Solar.fromYmd(d.year, d.month, d.day).getLunar().getPrevJieQi()


def _next_after(s) -> "object":
    """严格晚于 solar 的下一个节气（同上，先进一天再取）。"""
    from lunar_python import Solar
    d = _solar_to_date(s) + timedelta(days=1)
    return Solar.fromYmd(d.year, d.month, d.day).getLunar().getNextJieQi()


def _independent_window(d: date) -> tuple[int, date, date]:
    """用 lunar_python 独立推导 (月序, 窗口起日, 窗口止日)。

    路径与引擎**完全不同**：
      · 用 lunar_python 的 getPrevJieQi / getNextJieQi 取节气前后；
      · 用「节/气交替」的结构回推窗口起点（上一节气若是「节」，其前一节气
        必为「气」= 窗口起点）；
      · 月序由**中气名**查建寅表得到（引擎用的是 sxtwl 的 jqIndex 表，
        两张表互不共用）。

    ⚠ lunar_python 的节气取用是**日历日粒度**（不含时刻），故在
      **中气当日**会与引擎相差一个月：引擎的「节当日即新月第 1 日」是
      **原典口径**（K3-448 L482 / 《河洛真数》L129），由另一条守卫单独钉死。

    ⚠ lunar_python 的 ``JieQi.isJie()`` 标的是**中气**（小寒/立春/惊蛰/…
      奇数位），与「节」的习惯叫法相反 —— 实测确认，非臆断。
    """
    from lunar_python import Solar

    lunar = Solar.fromYmd(d.year, d.month, d.day).getLunar()
    p = lunar.getPrevJieQi()
    q = lunar.getNextJieQi()
    if p.isJie():                       # p 是中气 → 窗口起点即 p
        start_name = p.getName()
        start = _solar_to_date(p.getSolar())
        q2 = _next_after(q.getSolar())
        assert q2.isJie(), f"中气之后应仍为中气，得 {q2.getName()}"
        end = _solar_to_date(q2.getSolar())
    else:                               # p 是节 → 窗口起点是它前面的中气
        pp = _prev_before(p.getSolar())
        assert pp.isJie(), f"节之前应仍为中气，得 {pp.getName()}"
        start_name = pp.getName()
        start = _solar_to_date(pp.getSolar())
        end = _solar_to_date(q.getSolar())
    assert start_name in MID_QI_MONTH, f"未知中气名 {start_name}"
    return MID_QI_MONTH[start_name], start, end


class TestJieqiWindowConversion:
    """公历 → (节气月序, 节后日序) 的换算。"""

    @pytest.mark.parametrize("y", [2020, 2024, 2025, 2026, 2027, 2030])
    def test_every_day_of_year_resolves(self, y):
        """全年逐日都必须命中窗口 —— 不能有「查无此日」的空洞。"""
        d = date(y, 1, 1)
        end = date(y + 1, 1, 1)
        n = 0
        while d < end:
            w = resolve_jieqi_window(d.year, d.month, d.day)
            assert w["ok"], f"{d} 未命中节气窗口：{w['error']}"
            # ⚠ 节气月长度实测 29–32 日（1900–2100：29 日 320 个、30 日 944、
            #   31 日 923、32 日 225）⇒ 日序上限 **32**，不是 30 ——
            #   30 是「卦」的月长（五卦×六日），与日历月的长度不是一回事。
            #   超出 30 的日（每年约 8 天）由引擎归入末段（时间上仍正确），
            #   并有显式留痕，见 test_day_overflow_is_explicit。
            assert 1 <= w["day"] <= 32, f"{d} 日序越界：{w['day']}"
            n += 1
            d += timedelta(days=1)
        assert n in (365, 366)

    @pytest.mark.parametrize("y", [2024, 2026, 2027])
    def test_windows_are_contiguous_and_non_overlapping(self, y):
        """相邻日的窗口只能「相同」或「恰好切换」，且切换时首尾相接。

        这条抓的是**边界错位**：一旦月界取错（如取到朔而非中气），
        相邻日的窗口就会既不重合也不相接。
        """
        d = date(y, 1, 1)
        end = date(y + 1, 1, 1)
        prev = resolve_jieqi_window(d.year, d.month, d.day)
        while d < end:
            d += timedelta(days=1)
            cur = resolve_jieqi_window(d.year, d.month, d.day)
            if (cur["jie_datetime"], cur["month"]) != (prev["jie_datetime"], prev["month"]):
                # 切换了窗口 ⇒ 前窗口的止 = 后窗口的起
                assert prev["next_jie_datetime"] == cur["jie_datetime"], (
                    f"{d} 窗口不首尾相接："
                    f"prev[{prev['month']}] 止={prev['next_jie_datetime']} "
                    f"cur[{cur['month']}] 起={cur['jie_datetime']}")
            prev = cur

    @pytest.mark.parametrize("y", [2024, 2025, 2026, 2027])
    def test_agrees_with_independent_lunar_python(self, y):
        """与 lunar_python 独立推导逐日一致（**中气当日除外**，见下）。"""
        d = date(y, 1, 1)
        end = date(y + 1, 1, 1)
        boundary_days = 0
        checked = 0
        while d < end:
            w = resolve_jieqi_window(d.year, d.month, d.day)
            ind_lm, ind_start, ind_end = _independent_window(d)
            if w["day"] == 1:
                # **中气当日**：引擎按原典把它当作新月第 1 日（节当日起数），
                # lunar_python 按整日归上一窗 ⇒ 此处只校验「跨了一格」。
                boundary_days += 1
                assert w["jie_datetime"][:10] == d.isoformat(), (
                    f"{d} 日序为 1，其节气起点应是当日，实测 {w['jie_datetime']}")
                assert w["month"] in (ind_lm, (ind_lm % 12) + 1), (
                    f"{d} 中气当日月序异常：engine={w['month']} ind={ind_lm}")
            else:
                assert w["month"] == ind_lm, (
                    f"{d} 月序与独立路径不一致：engine={w['month']} ind={ind_lm}")
                assert w["day"] == (d - ind_start).days + 1, (
                    f"{d} 日序与独立路径不一致：engine={w['day']} "
                    f"ind={(d - ind_start).days + 1}")
                checked += 1
            d += timedelta(days=1)
        assert checked > 300, f"交叉核验样本过少：{checked}"
        assert boundary_days == 12, (
            f"中气当日应为每年 12 个，实测 {boundary_days} —— "
            f"交叉核验可能失效（或引擎的月界取错了节气）")

    def test_midqi_day_is_day_one(self):
        """原典硬算例：节当日即新月第 1 日。

        · K3-448 修正版 L482（影印核定）：
          「如本年**七月初二日午時立[秋]節**，刚卦初九爻即从初二日起…」
          ⇒ 七月（立秋月）第 1 日 = 立秋当日。
        · 《河洛真数·起例卷之上》L129：
          「假如正月节气在十二月小尽二十八日，**立春就从二十八日起数**是也。」
          ⇒ 正月（立春月）第 1 日 = 立春当日。
        """
        cases = [
            (2026, 8, 7, 7),     # 立秋 → 七月
            (2026, 12, 7, 11),   # 大雪 → 十一月
            (2026, 1, 5, 12),    # 小寒 → 十二月
            (2026, 2, 4, 1),     # 立春 → 正月
            (2027, 8, 8, 7),     # 立秋（2027）
        ]
        for y, m, d, lm in cases:
            w = resolve_jieqi_window(y, m, d)
            assert w["ok"], f"{y}-{m}-{d} 未命中窗口"
            assert w["month"] == lm, (
                f"{y}-{m}-{d} 应属 {lm} 月，实测 {w['month']}")
            assert w["day"] == 1, (
                f"{y}-{m}-{d} 是节当日，日序应为 1，实测 {w['day']}")

    def test_year_boundary_early_january(self):
        """跨年边界：1/1–1/4 属**上一年的十一月窗口**（大雪 → 小寒）。

        公历年 Y 的 12 个窗口覆盖 [小寒(Y)-01-05, 小寒(Y+1)-01-05)，
        故年初 4 天落在上一年的十一月窗口里 —— 该窗口的节气须取 Y-1 的表。
        """
        for y in (2025, 2026, 2027):
            for d in (1, 2, 3, 4):
                w = resolve_jieqi_window(y, 1, d)
                assert w["ok"]
                assert w["year"] == y - 1, (
                    f"{y}-01-{d:02d} 窗口年应为 {y - 1}，实测 {w['year']}")
                assert w["month"] == 11, (
                    f"{y}-01-{d:02d} 应属十一月窗口，实测 {w['month']}")
                assert w["jie_datetime"].startswith(str(y - 1)), (
                    f"{y}-01-{d:02d} 的节应取自 {y - 1} 年，实测 {w['jie_datetime']}")
            # 1/5 起进入本年十二月窗口（小寒）
            w = resolve_jieqi_window(y, 1, 5)
            assert w["year"] == y and w["month"] == 12, (
                f"{y}-01-05 应属本年十二月窗口，实测 {w['year']}/{w['month']}")

    def test_rejects_invalid_date(self):
        w = resolve_jieqi_window(2026, 2, 30)
        assert not w["ok"]
        assert w["error"]


class TestAdapterUsesJieqiCaliber:
    """端到端：adapter 必须按**节气口径**取流日，且流日覆盖目标日。"""

    ADAPTER = HeluoAdapter()
    BIRTH = (1975, 11, 22, 1)

    @pytest.mark.parametrize("tgt", [
        "2026-10-23",   # 公历 10 月 ≠ 节气九月（寒露月）—— 本缺陷的原始案例
        "2026-11-25",   # 立冬月
        "2026-08-08",   # 立秋月（节后第 2 日）
        "2026-01-03",   # 跨年边界：上一年的十一月窗口
        "2026-01-20",   # 小寒月
        "2026-02-04",   # 立春当日 = 正月第 1 日
        "2026-12-31",   # 大雪月
    ])
    def test_flow_day_covers_target_date(self, tgt):
        """流日段的**实际日期区间必须包含目标日**。

        修复前：target_date=2026-10-23 得到 date_from=2026-11-25（段在目标日之后）
        ⇒ 断言必然失败。这是本缺陷的**行为级**守卫。
        """
        y, m, d = (int(x) for x in tgt.split("-"))
        r = self.ADAPTER.compute(self.BIRTH, gender="male", target_date=tgt)
        base = (r.timeline.daily_hexagram or {}).get("base_hex") or {}
        df = base.get("date_from")
        assert df, f"{tgt} 流日段缺 date_from（节气对齐失效？）"
        seg_start = datetime.strptime(df, "%Y-%m-%d %H:%M")
        # 段长 = 6 日（gua6 口径：一卦管 6 日）
        # ⚠ 比**日历日**而非时刻：段起点时刻会随「每日添一刻七分天」逐日推移
        #   （K3-448 L491），某段的起点时刻可能晚于当日正午 ——
        #   用时刻比会把「同日」误判为「不在段内」。
        seg_end_date = (seg_start + timedelta(days=6)).date()
        assert seg_start.date() <= date(y, m, d) <= seg_end_date, (
            f"{tgt} 不在流日段区间内：段={df} → +6 日，"
            f"目标日={date(y, m, d)} ⇒ 流日取错月/日（节后日序 "
            f"{base.get('day_from')}-{base.get('day_to')}）")

    @pytest.mark.parametrize("tgt", ["2026-10-23", "2026-08-08", "2026-01-03"])
    def test_month_used_is_jieqi_month_not_solar_month(self, tgt):
        """流日所用的月份必须是**节气月序**，不得是公历月。

        三个案例的公历月与节气月**都不相同**（10→9、8→7、1→11），
        公历月口径的实现必然取错月。
        """
        y, m, d = (int(x) for x in tgt.split("-"))
        w = resolve_jieqi_window(y, m, d)
        assert w["month"] != m, (
            f"测试样本 {tgt} 的公历月与节气月相同，无法区分口径 —— 换样本")
        r = self.ADAPTER.compute(self.BIRTH, gender="male", target_date=tgt)
        months = r.timeline.monthly_hexagrams
        filled = [x for x in months if x.get("days")]
        assert len(filled) == 1, f"应只有 1 个月带日段，实测 {len(filled)}"
        assert filled[0]["month"] == w["month"], (
            f"{tgt} 用了 {filled[0]['month']} 月，应为节气月 {w['month']}")
        base = (r.timeline.daily_hexagram or {}).get("base_hex") or {}
        assert base.get("yue_yao_index") == filled[0]["yue_yao_index"]

    def test_result_target_date_keeps_solar_value(self):
        """结果里的 target_date 必须是**公历原值**，且口径标注为 solar。"""
        tgt = "2026-10-23"
        r = self.ADAPTER.compute(self.BIRTH, gender="male", target_date=tgt)
        assert r.target_date == tgt, (
            f"result.target_date 应为公历 {tgt}，实测 {r.target_date}")
        assert r.target_date_caliber == "solar", (
            f"口径标注应为 solar，实测 {r.target_date_caliber!r}")

    def test_jieqi_caliber_not_leaked_into_record(self):
        """内部节气月序**不得**混进公历记录字段。

        修复前 target_date 由 (target_year, 公历月, 公历日) 拼成 —— 一旦
        换算后不另存公历原值，记录里就会出现「2026-09-16」这种伪日期。
        """
        r = self.ADAPTER.compute(self.BIRTH, gender="male", target_date="2026-10-23")
        assert r.target_date == "2026-10-23"
        assert "2026-09-16" not in str(r.target_date)

    def test_day_overflow_is_explicit(self):
        """日序超出 30 日卦月模型时**必须显式留痕**，不得静默夹取。

        节气月实测 29–32 日；第 31/32 日没有对应卦（原典卦月恒 30 日），
        引擎按时间归入末段 —— 属模型外延用，须说明。
        """
        # 2026 惊蛰(03-05) → 清明(04-05) 共 31 日 ⇒ 04-04 是第 31 日
        w = resolve_jieqi_window(2026, 4, 4)
        assert w["ok"] and w["day"] == 31, (
            f"样本前提不成立：2026-04-04 日序应为 31，实测 {w['day']}")
        r = self.ADAPTER.compute(self.BIRTH, gender="male", target_date="2026-04-04")
        gj = r.guajie or {}
        summary = " ".join(gj.get("summary") or [])
        assert "超出" in summary and "30" in summary, (
            f"第 31 日未显式留痕（静默夹取）—— summary: {summary[:200]}")
