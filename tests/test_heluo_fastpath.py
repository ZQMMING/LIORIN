"""Heluo 时间序列算力裁剪 fast-path 守卫（2026-10-22 按定稿重写）。

定稿（2026-10-22）要点：
    · 流年层：只算**近 3 年**（target-2 / target-1 / target）完整流年卦
      —— 近 3 年是 guajie「近 3 年流年判词」的数据源（guajie.py L1779-1796）；
      其余 96 条只存 {year, age, ganzhi} 纯元数据（timeline.yearly_meta），不起卦。
    · 流月层：只有**目标年**算 12 个流月卦（全算）→ 顶层 monthly_hexagrams。
    · 流日层：1 个流日本卦（完整卦一次算好）+ 6 日各自激活爻（轻量爻运算）
      → 顶层 daily_hexagram{base_hex, daily_yao}。
    · 大运层：只生成元数据（qi_phase.dayun 仍留完整字段供 guajie 运反判定）。

防回归意图（与 2026-10-10 批次 P 原始守卫一致，只换契约）：
    · 非近 3 年流年必须是**纯元数据**（不复活 yi_signal / yi_interpretation /
      months / days / hours —— 这些是 dead-write，仓内零消费方）
    · 目标年必须嵌满 12 月；流月数必须是 12
    · 顶层 monthly_hexagrams 必须 12 项
    · 顶层 daily_hexagram 必须含 base_hex（完整卦）+ daily_yao（6 日激活爻）
    · target_year=None 必须退回全量（旧契约冻结保留）
    · 总体积 < 100k chars（定稿估算 ~2.8 万，留冗余防波动）

只断言调用方的**可见契约**（yearly / yearly_meta / monthly_hexagrams /
daily_hexagram 形状与字段集合），不绑实现细节。
"""

from __future__ import annotations

import dataclasses
import json
import unittest

from tongshu.engines.heluo.canonical import HeluoCanonical


_BAZI = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]
_BIRTH_YEAR = 1983
_BIRTH_DATE = "1983-11-03"
_TARGET_YEAR = 2026
_TARGET_MONTH = 7  # 农历七月（黄历权威值）
_BIRTH_HOUR = "午"
_GENDER = "male"

#: 近 3 年完整流年卦
_FULL_YEARS = {_TARGET_YEAR - 2, _TARGET_YEAR - 1, _TARGET_YEAR}


def _full_to_dict(res) -> dict:
    """把 HeluoResult 序列化为 dict（与现有 dump 工具同口径）。"""
    return dataclasses.asdict(res)


def _timeline_to_dict(res) -> dict:
    """只取 timeline 子树，避免 hua_gong / seasonal / structure 等抖动干扰。"""
    return dataclasses.asdict(res.timeline)


def _build(target_year=None, target_month=None, target_day=None):
    """单次 build（与 production path 一致：canonical.calculate 直调）。"""
    hc = HeluoCanonical()
    return hc.calculate(
        bazi=_BAZI,
        gender=_GENDER,
        birth_hour=_BIRTH_HOUR,
        birth_year=_BIRTH_YEAR,
        birth_date=_BIRTH_DATE,
        target_year=target_year,
        target_month=target_month,
        target_day=target_day,
    )


class TestFastPathSkeleton(unittest.TestCase):
    """fast-path 骨架 / 体积 / 月日顶层契约。"""

    def test_yearly_skeleton_is_last_three_years(self):
        """yearly_hexagrams 只含近 3 年完整流年卦（其余走 yearly_meta 纯元数据）。

        近 3 年是 guajie「近 3 年流年判词」的数据源，必须保留完整卦。
        """
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        yearly = res.timeline.yearly_hexagrams
        self.assertEqual(len(yearly), 3,
                         f"yearly_hexagrams 应只含近 3 年，实测 {len(yearly)}")
        self.assertEqual(_FULL_YEARS, {e["year"] for e in yearly})
        for e in yearly:
            for k in _EXPECTED_META_KEYS:
                self.assertIn(k, e, f"近 3 年流年 entry 缺 {k}")

    def test_yearly_meta_is_pure_metadata(self):
        """其余流年进 yearly_meta，且**只** {year, age, ganzhi} —— 不带卦。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        meta = res.timeline.yearly_meta
        self.assertEqual(len(meta), 96,
                         f"yearly_meta 应含其余 96 条流年，实测 {len(meta)}")
        for e in meta:
            self.assertEqual(set(e.keys()), {"year", "age", "ganzhi"},
                             f"yearly_meta entry 字段应恰为 3 个，实际 {sorted(e.keys())}")
        years = {e["year"] for e in meta}
        self.assertFalse(years & _FULL_YEARS,
                         "近 3 年不得重复出现在 yearly_meta")
        # 全部 99 年（96 + 3）应覆盖
        all_years = years | {e["year"] for e in res.timeline.yearly_hexagrams}
        self.assertEqual(len(all_years), 99, "流年总覆盖应为 99 年")

    def test_metadata_segments_have_no_yield_or_yi(self):
        """纯元数据 / 非目标年流年禁止 yi_signal / yi_interpretation / days / hours
        ——这些是 dead-write（仓内零消费方），必须钉死不可复活。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        for e in list(res.timeline.yearly_hexagrams) + list(res.timeline.yearly_meta):
            self.assertNotIn("yi_signal", e,
                             f"年份 {e.get('year')} 含 yi_signal（dead-write 不得复活）")
            self.assertNotIn("yi_interpretation", e,
                             f"年份 {e.get('year')} 含 yi_interpretation")
            self.assertNotIn("days", e, f"年份 {e.get('year')} 含 days")
            self.assertNotIn("hours", e, f"年份 {e.get('year')} 含 hours")

    def test_only_target_year_has_months(self):
        """只有目标年嵌 months 子树（12 个流月卦）；近 3 年另两年只有流年卦本体。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        yearly = res.timeline.yearly_hexagrams
        with_months = [e for e in yearly if e.get("months")]
        self.assertEqual(len(with_months), 1,
                         f"应只有目标年 1 段有 months，实测 {len(with_months)}")
        self.assertEqual(_TARGET_YEAR, with_months[0]["year"])
        self.assertEqual(len(with_months[0]["months"]), 12)

    def test_target_year_has_12_months(self):
        """目标年段 12 个流月卦，month 序号 1..12。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        target_yr = next(e for e in res.timeline.yearly_hexagrams
                         if e["year"] == _TARGET_YEAR)
        months = target_yr["months"]
        self.assertEqual(len(months), 12)
        for i, m in enumerate(months, start=1):
            self.assertEqual(m["month"], i)
            for k in ("name", "upper", "lower", "lines", "kind", "yue_yao_index"):
                self.assertIn(k, m, f"流月缺 {k}")

    def test_top_level_monthly_hexagrams_filled(self):
        """顶层 monthly_hexagrams 是目标年 12 月（扁平路径）。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        m = res.timeline.monthly_hexagrams
        self.assertEqual(len(m), 12)
        for i, x in enumerate(m, start=1):
            self.assertEqual(x["month"], i)

    def test_top_level_daily_hexagram_base_hex_and_daily_yao(self):
        """顶层 daily_hexagram = {base_hex 完整卦, daily_yao 6 日激活爻} + 年/月锚。

        定稿：1 个流日本卦（本体/互错综/卦气一次算好），6 日共用；
        每日只取对应爻（初→1日 … 上→6日）做轻量爻运算。
        """
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        d = res.timeline.daily_hexagram
        self.assertEqual(d.get("year"), _TARGET_YEAR)
        self.assertEqual(d.get("month"), _TARGET_MONTH)

        base = d.get("base_hex")
        self.assertIsInstance(base, dict, "daily_hexagram 缺 base_hex")
        for k in ("name", "upper", "lower", "lines", "hu_name", "cuo_name", "zong_name"):
            self.assertIn(k, base, f"base_hex 缺 {k}")

        yao = d.get("daily_yao")
        self.assertIsInstance(yao, list)
        self.assertEqual(len(yao), 6, "daily_yao 应有 6 日")
        want_yao = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")
        for i, x in enumerate(yao):
            self.assertEqual(x.get("day_no"), i + 1)
            self.assertEqual(x.get("active_yao"), want_yao[i],
                             f"第 {i+1} 日激活爻应为 {want_yao[i]}")
            for k in ("yao_index", "yao_nature", "changed_name", "changed_lines"):
                self.assertIn(k, x, f"daily_yao 缺 {k}")

    def test_daily_hexagram_empty_when_target_month_unspecified(self):
        """target_month 未传 → 顶层 daily_hexagram 保持空。"""
        res = _build(target_year=_TARGET_YEAR, target_month=None)
        self.assertEqual(res.timeline.daily_hexagram, {})

    def test_daily_segments_dayseq_fixed_six_but_time_follows_jie(self):
        """流日段：**日序固定 6 日一组**，但**时刻按实际节气间隔均匀推移**。

        原典硬算例（K3-448 1632笔写本 L479-L491 逐字）：
            L479: 日卦上支管初七日是此屯却六交从下而上一交一日自初二日至初七
            L481: 六月自下交行盈上交盏取一交一日也日卦行起必须按月卦節氧方不
            L482: 如本年七月初二日午時立缺節刚卦初儿交即徒初二日午時管起屯
            L483: 一日共管六日也至千十四日又襄前既卦九五交岛明夷六五自下雨上
            L488: 其餘五交五舞一卦管六日五六方三十交管三十日也
            L491: 以此推之则每日添一刻七分天六日
          （K3-447 1871增补本 L1154: 日卦者每月變五卦每卦管六日方成一月五六三）

        故断言：
          · 段日序恒为 6 日一组（day_to - day_from + 1 == 6，
            且 (day_from - 1) % 6 == 0）—— L482-483 硬算例铁证
          · base_hex 记有 jie_span_days（当月节→下节的实际间隔天数），
            且该间隔不等于固定 30 日（节气不等长）
          · 段起时刻带真实时刻（date_from 含 "HH:MM"），非整日 0 点
        """
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH,
                     target_day=15)
        d = res.timeline.daily_hexagram
        base = d.get("base_hex") or {}

        # ① 日序固定 6 日一组
        day_from = base.get("day_from")
        day_to = base.get("day_to")
        self.assertIsNotNone(day_from)
        self.assertIsNotNone(day_to)
        self.assertEqual(day_to - day_from + 1, 6,
                         f"段日序应恒 6 日（实测 {day_from}-{day_to}）")
        self.assertEqual((day_from - 1) % 6, 0,
                         f"段起点 {day_from} 应落在 6 日分组边界上"
                         f"（L483 硬算例：初二起，十四为第三卦起）")

        # ② 节气间隔真实、不等于固定 30 日
        span = base.get("jie_span_days")
        self.assertIsNotNone(span, "base_hex 缺 jie_span_days（未按节气实际间隔分段）")
        self.assertNotAlmostEqual(
            span, 30.0, delta=0.3,
            msg=f"节气间隔应不等于固定 30 日（实测 {span}）",
        )

        # ③ 段起时刻带真实时刻（非整日 0 点）
        date_from = base.get("date_from") or ""
        self.assertIn(":", date_from, f"段起应带真实时刻（实测 {date_from!r}）")

        # ④ 段内 6 日：首日从初爻开始，日序连续
        yao = d.get("daily_yao") or []
        self.assertEqual(len(yao), 6)
        want = ("初爻", "二爻", "三爻", "四爻", "五爻", "上爻")
        for i, x in enumerate(yao):
            self.assertEqual(x.get("active_yao"), want[i],
                             f"段内第 {i+1} 日应取 {want[i]}（首日从初爻开始）")
            self.assertEqual(x.get("day_no"), day_from + i,
                             f"段内第 {i+1} 日日序应连续")

    def test_date_from_is_segment_start_not_jie(self):
        """days[*].date_from 必为**段起始时刻**（非当月节时刻）。

        回归：2026-10-22 修复前，days_payload 构造引用了不存在的 `_grp`
        → NameError 被 except 吞掉 → date_from 恒等于当月节时刻（名不符实）。
        """
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH,
                     target_day=15)
        d = res.timeline.daily_hexagram
        base = d.get("base_hex") or {}
        yao = d.get("daily_yao") or []
        self.assertTrue(yao, "daily_yao 为空")
        for x in yao:
            self.assertEqual(
                x.get("date_from"), base.get("date_from"),
                "每日的 date_from 应等于段起始时刻（base_hex.date_from）",
            )
        self.assertNotEqual(
            base.get("date_from"), base.get("jie_datetime"),
            "段起始时刻不应等于当月节时刻（否则说明退化成整月同一起点）",
        )

    def test_target_year_hexagram_placeholder_fields_are_empty_strings(self):
        """target_year_hexagram 的 yi_signal / changed_line 在 fast-path 下恒为空串。

        理由：填值需跑 interpret_all_liunian —— 全仓零消费方的 dead-write，
        fast-path 刻意不跑（批次 P 起）。定稿的 target_year_hexagram 结构保留
        这两个键作占位，故断言「键存在且为空串」，防「看起来该有值却没有」的歧义。
        """
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        t = res.timeline.target_year_hexagram
        self.assertIn("yi_signal", t)
        self.assertIn("changed_line", t)
        self.assertEqual(t["yi_signal"], "")
        self.assertEqual(t["changed_line"], "")

    def test_target_year_hexagram_summary(self):
        """顶层 target_year_hexagram 是目标流年卦摘要。"""
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        t = res.timeline.target_year_hexagram
        self.assertEqual(t.get("year"), _TARGET_YEAR)
        for k in ("ganzhi", "hexagram", "yi_signal", "changed_line"):
            self.assertIn(k, t, f"target_year_hexagram 缺 {k}")

    def test_total_size_within_budget(self):
        """timeline 子树 < 100k chars（定稿估算 ~2.8 万），锁住算力裁剪成果。

        1983-11-03 12:00 男 / target=2026/7 这盘实测远低于此；留冗余防波动。
        """
        res = _build(target_year=_TARGET_YEAR, target_month=_TARGET_MONTH)
        tl_dict = _timeline_to_dict(res)
        s = json.dumps(tl_dict, ensure_ascii=False, default=str)
        self.assertLess(len(s), 100_000,
                        f"timeline 体积 {len(s)} ≥ 100k")


class TestFastPathDisabled(unittest.TestCase):
    """target_year=None 退回全量（旧契约冻结保留）。"""

    def test_no_target_year_means_full_payload(self):
        """target_year 未传 → 全部 99 段都嵌 months + yi_* —— 锁旧契约。"""
        res = _build(target_year=None, target_month=None)
        yearly = res.timeline.yearly_hexagrams
        none_with_months = [e for e in yearly if not e.get("months")]
        self.assertEqual(len(none_with_months), 0,
                         "全量路径下所有流年段都必须有 months")
        none_with_yi = [e for e in yearly if "yi_signal" not in e]
        self.assertEqual(len(none_with_yi), 0,
                         "全量路径下所有流年段都必须有 yi_signal（interpret_all_liunian）")
        self.assertEqual(res.timeline.monthly_hexagrams, [])
        self.assertEqual(res.timeline.daily_hexagram, {})

    def test_full_path_payload_is_baseline(self):
        """全量路径排盘结果 baseline 不变 —— 关键回归保险。

        基线：1983-11-03 12:00 男 → ~2.0M chars。
        """
        res = _build(target_year=None, target_month=None)
        full = _full_to_dict(res)
        s = json.dumps(full, ensure_ascii=False, default=str)
        self.assertGreater(len(s), 1_500_000,
                           f"全量路径体积 {len(s)} 跌破旧基线 1.5M（疑似被 fast-path 污染）")
        self.assertLess(len(s), 3_000_000,
                        f"全量路径体积 {len(s)} ≥ 3M（疑似引入了额外冗余）")


_EXPECTED_META_KEYS = {
    "age", "year", "ganzhi", "yang_year", "hexagram",
    "upper", "lower", "lines",
    "yuantang_index", "yuantang_nature",
}


if __name__ == "__main__":
    unittest.main()
