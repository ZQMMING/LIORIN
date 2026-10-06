"""河洛四层时间轴：性能改造回归（2026-10-06）

本文件锁定本轮四项性能改造的**行为不变量**，防止优化悄悄改算法口径：

  ① 流时卦按需化：_build_timeline 不再预展开 hours，只留 flip_index；
     guajie 命中 target_hour 时现算，结果须与旧预展开逐条一致。
  ② interpret_all_liunian 顶层浅拷贝：须返回新列表/新顶层对象，且不改原列表。
  ③ sxtwl 惰性单例：缺依赖时只解析一次，失败不反复试探 import。
  ④ 大运 _lines_to_hexagram 提出循环；流年大运段游标查找口径不变。

另锁定 guajie.to_dict() 补发三个应期卦名（修复前被静默丢弃）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.canonical import HeluoCanonical, _get_sxtwl
from tongshu.engines.heluo.timeline_yun import (
    compute_liuri, compute_liushi, compute_dayun_liyao,
)
from tongshu.engines.heluo import yi_interpreter as yi
from tongshu.engines.heluo import guajie as gj

# 纪晓岚 Golden Case：甲辰 辛未 丙戌 甲午 午时 男
BAZI = [("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")]


def _calc():
    return HeluoCanonical().calculate(BAZI, gender="male", birth_hour="午", era="zhong")


class TestLazyLiuShi(unittest.TestCase):
    """① 流时卦按需化"""

    @classmethod
    def setUpClass(cls):
        cls.res = _calc()
        cls.yearly = cls.res.timeline.yearly_hexagrams

    def test_days_carry_flip_index_not_hours(self):
        """日段应带 flip_index，且不再预挂 hours（80,352 条全量载荷的来源）"""
        segs = [d for y in self.yearly for m in y["months"] for d in m["days"]]
        self.assertEqual(len(segs), 6 * len([m for y in self.yearly for m in y["months"]]))
        for d in segs:
            self.assertIn("flip_index", d)
            self.assertNotIn("hours", d, "流时卦应按需现算，不得预展开")

    def test_lazy_hours_reproduces_full_12(self):
        """按 flip_index 现算，须得 12 个时辰（旧预展开的同源结果）"""
        for y in self.yearly[:5]:
            for m in y["months"][:2]:
                for d in m["days"]:
                    hours = compute_liushi(d["lines"], d["flip_index"]).hours
                    self.assertEqual(len(hours), 12, (y["year"], m["month"], d["segment"]))
                    self.assertEqual([h["hour"] for h in hours], list(range(1, 13)))

    def test_flip_index_is_single_line_diff_vs_month(self):
        """flip_index 必须是日段相对月卦唯一变动的爻，否则按需路径无从重建"""
        for y in self.yearly:
            for m in y["months"]:
                ml = m["lines"]
                for d in m["days"]:
                    diffs = [k for k in range(6)
                             if len(d["lines"]) > k and len(ml) > k and d["lines"][k] != ml[k]]
                    if len(diffs) == 1:
                        self.assertEqual(d["flip_index"], diffs[0])

    def test_guajie_hours_layer_stripped_others_intact(self):
        """2026-10-06 流时层剥离：流时恒空，但流年/流月/流日仍须正确定位。"""
        out = gj.build_guajie_from_result(
            self.res, bazi=BAZI, target_year=2026, target_month=6,
            target_day=15, target_hour=7,
        )
        self.assertEqual(out["liushi_hexagram"], "", "流时层应已剥离")
        self.assertIsNone(out["liushi_yao"])
        # 剥离流时不得牵连其余三层
        self.assertEqual(out["liunian_hexagram"], "困")
        self.assertEqual(out["liuyue_hexagram"], "蛊")
        self.assertEqual(out["liuri_hexagram"], "升")

    def test_guajie_all_twelve_hours_uniformly_stripped(self):
        """12 个时辰一律不产流时，且都在 evidence 留痕。"""
        for h in range(1, 13):
            out = gj.build_guajie_from_result(
                self.res, bazi=BAZI, target_year=2026, target_month=6,
                target_day=15, target_hour=h,
            )
            self.assertEqual(out["liushi_hexagram"], "", f"{h} 时仍产流时")
            self.assertIsNone(out["liushi_yao"], f"{h} 时仍产流时爻辞")
            self.assertTrue(any("流时：已剥离" in e for e in out["evidence"]),
                            f"{h} 时未留痕")

    def test_omitting_target_hour_yields_no_liushi(self):
        out = gj.build_guajie_from_result(
            self.res, bazi=BAZI, target_year=2026, target_month=6, target_day=15,
        )
        self.assertFalse(out["liushi_hexagram"])
        self.assertTrue(out["liuri_hexagram"], "不传时辰时流日仍应定位")
        self.assertFalse(any("流时：已剥离" in e for e in out["evidence"]),
                         "未传 target_hour 时无需留剥离痕迹")


class TestGuajieToDictHexagrams(unittest.TestCase):
    """to_dict() 补发三个应期卦名（修复前只发 _yao，卦名被静默丢弃）"""

    @classmethod
    def setUpClass(cls):
        cls.res = _calc()
        cls.out = gj.build_guajie_from_result(
            cls.res, bazi=BAZI, target_year=2026, target_month=6,
            target_day=15, target_hour=7,
        )

    def test_three_live_hexagram_keys_present_and_filled(self):
        """流年/流月/流日三个应期卦名必须发出且非空。"""
        for k in ("liunian_hexagram", "liuyue_hexagram", "liuri_hexagram"):
            self.assertIn(k, self.out, f"{k} 未被 to_dict 发出")
            self.assertTrue(self.out[k], f"{k} 为空")

    def test_liushi_key_still_present_but_empty(self):
        """流时键保留在契约中（前端可稳定读取），但值恒空。"""
        self.assertIn("liushi_hexagram", self.out)
        self.assertEqual(self.out["liushi_hexagram"], "")

    def test_yao_keys_still_present(self):
        """既有键不得受影响"""
        for k in ("liunian_yao", "liuyue_yao", "liuri_yao"):
            self.assertIn(k, self.out)
            self.assertIsInstance(self.out[k], dict)
        self.assertIn("liushi_yao", self.out)
        self.assertIsNone(self.out["liushi_yao"])


class TestInterpretShallowCopy(unittest.TestCase):
    """② interpret_all_liunian 顶层浅拷贝"""

    def test_returns_new_list_and_leaves_input_untouched(self):
        res = _calc()
        # 取真实条目、剥掉已回填的 yi_* 键，模拟"解释前"的输入
        probe = [{k: v for k, v in e.items() if k not in ("yi_signal", "yi_interpretation")}
                 for e in res.timeline.yearly_hexagrams]
        self.assertTrue(probe)
        before = {id(e) for e in probe}

        out = yi.interpret_all_liunian(probe, yuan_tang_index=0, yuan_tang_nature="阳")

        self.assertIsNot(out, probe, "应返回新列表")
        self.assertEqual(len(out), len(probe))
        self.assertFalse(before & {id(e) for e in out}, "顶层元素应为新对象")
        for a, b in zip(probe, out):
            self.assertNotIn("yi_signal", a, "原列表不得被写入")
            self.assertIn("yi_signal", b)
            self.assertIn("yi_interpretation", b)
            # 子树按引用共享（这正是省掉 deepcopy 的前提）
            self.assertIs(a["lines"], b["lines"])
            self.assertIs(a["months"], b["months"])


class TestSxtwlLazySingleton(unittest.TestCase):
    """③ sxtwl 惰性单例

    2026-10-06 修正：本组原先假设「本机无 sxtwl」，装上 sxtwl 后断言反向而失败。
    改为与环境无关——只锁定真正的不变量：解析至多一次、缓存每年只算一次、
    失败状态被记住且不反复试探 import。
    """

    def test_get_sxtwl_is_memoized(self):
        """惰性单例：进程内至多解析一次，重复调用返回同一对象。"""
        import tongshu.engines.heluo.canonical as cn
        a = cn._get_sxtwl()
        b = cn._get_sxtwl()
        self.assertIs(a, b, "重复调用须返回同一对象，不得重新 import")
        if a is None:
            self.assertTrue(cn._SXTWL_FAILED, "无 sxtwl 时应记住失败")

    def test_failed_resolution_is_remembered(self):
        """强制失败态后不得反复走 import 机制（旧实现 1,116 次 ≈ 206 ms）。"""
        import tongshu.engines.heluo.canonical as cn
        saved = (cn._SXTWL, cn._SXTWL_FAILED, cn._jie_cache)
        try:
            cn._SXTWL, cn._SXTWL_FAILED, cn._jie_cache = None, True, {}
            for _ in range(50):
                cn._jie_datetime_for_lunar_month(2026, 6)
            self.assertIsNone(cn._get_sxtwl(), "记住失败后不应再试探 import")
            self.assertIn(2026, cn._jie_cache, "失败也须写缓存，否则每月重试")
            self.assertEqual(cn._jie_cache[2026], {})
            self.assertIsNone(cn._jie_datetime_for_lunar_month(2026, 6))
        finally:
            cn._SXTWL, cn._SXTWL_FAILED, cn._jie_cache = saved

    def test_jie_cache_computed_once_per_year(self):
        """同一年 12 个月只应触发一次 _compute_year_jie。"""
        import tongshu.engines.heluo.canonical as cn
        saved = (cn._jie_cache, cn._compute_year_jie)
        calls = []
        try:
            cn._jie_cache = {}

            def spy(year, sxtwl=None):
                calls.append(year)
                return {}

            cn._compute_year_jie = spy
            for m in range(1, 13):
                cn._jie_datetime_for_lunar_month(2027, m)
            self.assertEqual(calls, [2027], f"应只算一次，实得 {calls}")
        finally:
            cn._jie_cache, cn._compute_year_jie = saved

    def test_jie_cache_hit_skips_compute(self):
        """命中缓存时不得重算。"""
        import tongshu.engines.heluo.canonical as cn
        saved = (cn._jie_cache, cn._compute_year_jie)
        calls = []
        try:
            cn._jie_cache = {2028: {1: "2028-02-04 10:14"}}
            cn._compute_year_jie = lambda y, sxtwl=None: calls.append(y) or {}
            self.assertEqual(cn._jie_datetime_for_lunar_month(2028, 1), "2028-02-04 10:14")
            self.assertIsNone(cn._jie_datetime_for_lunar_month(2028, 2))
            self.assertEqual(calls, [], "命中缓存时不应重算")
        finally:
            cn._jie_cache, cn._compute_year_jie = saved


class TestJieBatchEquivalence(unittest.TestCase):
    """批量取节气路径：与逐日扫描口径必须逐值一致

    ⚠ sxtwl 有两个返回类，方法名不能混用（2026-10-06 实机核正）：
      fromSolar()     → Day        有方法 getJieQi() / getJieQiJD()
      getJieQiByYear() → JieQiInfo  只有属性 .jd / .jqIndex，无上述方法
    _jie_by_batch 初版误按方法取 → 每次抛 AttributeError 被兜底吞掉 → 静默空转。
    本组锁定「batch 真的返回数据且与 dayscan 一致」，防止再次空转。
    """

    @classmethod
    def setUpClass(cls):
        try:
            import sxtwl
        except ImportError:
            raise unittest.SkipTest("本机无 sxtwl，跳过真实数据对拍")
        cls.sxtwl = sxtwl

    def test_batch_returns_data_not_none(self):
        """防回归：batch 不得恒返回 None（那等于优化空转）。"""
        for y in (1984, 1990, 2026):
            b = self._call_batch(y)
            self.assertIsNotNone(b, f"{y} 年 batch 返回 None —— 又空转了？")
            self.assertEqual(len(b), 12, f"{y} 年应得 12 个节，实得 {len(b)}")

    def test_batch_matches_dayscan(self):
        """逐值对拍：批量与逐日扫描必须完全一致。"""
        for y in (1975, 1990, 2024, 2026, 2050):
            b, s = self._call_batch(y), self._call_dayscan(y)
            self.assertEqual(b, s, f"{y} 年批量与逐日结果不一致")

    def test_dayscan_and_batch_cover_all_12_months(self):
        for y in (1990, 2026):
            self.assertEqual(len(self._call_dayscan(y)), 12)

    def _call_batch(self, y):
        from tongshu.engines.heluo.canonical import _jie_by_batch
        return _jie_by_batch(self.sxtwl, y)

    def _call_dayscan(self, y):
        from tongshu.engines.heluo.canonical import _jie_by_dayscan
        return _jie_by_dayscan(self.sxtwl, y)


class TestDayunAndSegmentLookup(unittest.TestCase):
    """④ 大运换算提出循环 + 流年段游标查找口径不变"""

    def test_dayun_walk_hexagram_constant_per_segment(self):
        """爻位值运：卦不变，只走爻 → 每段 6 步同卦名"""
        d = compute_dayun_liyao([1, -1, 1, 1, -1, -1], 0, [-1, 1, -1, -1, 1, 1], 2)
        self.assertEqual(len(d.sequence), 12)
        self.assertEqual(len({e.hexagram_name for e in d.sequence[:6]}), 1)
        self.assertEqual(len({e.hexagram_name for e in d.sequence[6:]}), 1)
        self.assertNotEqual(d.sequence[0].hexagram_name, d.sequence[6].hexagram_name)

    def test_dayun_segments_contiguous_and_ordered(self):
        d = compute_dayun_liyao([1, -1, 1, 1, -1, -1], 0, [-1, 1, -1, -1, 1, 1], 2)
        self.assertEqual(d.sequence[0].age_start, 1)
        for a, b in zip(d.sequence, d.sequence[1:]):
            self.assertEqual(b.age_start, a.age_end + 1, "大运段应首尾相接")

    def test_dayun_line_index_walks_upward_from_yuantang(self):
        d = compute_dayun_liyao([1, -1, 1, 1, -1, -1], 0, [-1, 1, -1, -1, 1, 1], 2)
        self.assertEqual([e.line_index for e in d.sequence[:6]], [0, 1, 2, 3, 4, 5])
        self.assertEqual([e.line_index for e in d.sequence[6:]], [2, 3, 4, 5, 0, 1])

    def test_liunian_years_match_dayun_coverage(self):
        """游标查找口径：流年应恰好覆盖大运全程，不多不少"""
        res = _calc()
        yearly = res.timeline.yearly_hexagrams
        dayun = res.timeline.qi_phase["dayun"]
        self.assertEqual([y["age"] for y in yearly],
                         list(range(dayun[0]["age_start"], dayun[-1]["age_end"] + 1)))


class TestLiuRiAlignDatesSwitch(unittest.TestCase):
    """① date_from/date_to 改按需产出

    2026-10-06：全仓无人消费这两个字段，而每段要多一次 strptime + 2 个日期串。
    实测占单盘耗时 42%、载荷 22%。改为 align_dates 显式开启，默认关闭——
    能力不丢，默认不付费。
    """

    LINES = [1, -1, 1, 1, -1, -1]
    JIE = "1990-02-04 10:14"

    def test_default_omits_dates(self):
        segs = compute_liuri(self.LINES, 3, self.JIE).days
        self.assertEqual(len(segs), 6)
        for d in segs:
            self.assertNotIn("date_from", d)
            self.assertNotIn("date_to", d)

    def test_align_dates_true_restores_dates(self):
        segs = compute_liuri(self.LINES, 3, self.JIE, align_dates=True).days
        self.assertEqual(segs[0]["date_from"], "1990-02-04")
        self.assertEqual(segs[0]["date_to"], "1990-02-08")
        self.assertEqual(segs[5]["date_from"], "1990-03-01")
        self.assertEqual(segs[5]["date_to"], "1990-03-05")

    def test_relative_segments_identical_either_way(self):
        """开不开日期，卦名/爻/日段边界必须完全一致。"""
        a = compute_liuri(self.LINES, 3, self.JIE).days
        b = compute_liuri(self.LINES, 3, self.JIE, align_dates=True).days
        strip = lambda ds: [{k: v for k, v in d.items()
                             if k not in ("date_from", "date_to")} for d in ds]
        self.assertEqual(strip(a), strip(b))

    def test_no_jie_datetime_degrades_to_relative(self):
        for flag in (False, True):
            d = compute_liuri(self.LINES, 3, None, align_dates=flag).days[0]
            self.assertEqual(d["day_from"], 1)
            self.assertNotIn("date_from", d)

    def test_timeline_keeps_days_eagerly(self):
        """流日层仍全量预展开：tests/test_heluo_context.py 断言 len(days)==6（既有契约）。"""
        res = _calc()
        y0 = res.timeline.yearly_hexagrams[0]
        self.assertEqual(len(y0["months"]), 12)
        for m in y0["months"]:
            self.assertEqual(len(m["days"]), 6)
            for d in m["days"]:
                self.assertIn("flip_index", d)
                self.assertNotIn("hours", d)


if __name__ == "__main__":
    unittest.main()
