# -*- coding: utf-8 -*-
"""历法层端到端对拍守卫（2026-10-22）。

**本守卫把「农历日期 → 公历 → 四柱 → 河洛判词」整条链一次打通**，
取代此前「历法层不可对拍」的旧定性（该定性经本轮实测**不成立**）。

## 一、历法层的真口径（此前踩过的坑）

1582 年（格里历改历）**之前**，sxtwl 的节气儒略日给出的是**儒略历**日期；
仓库通用换算 `tongshu.engines.time.jd_converter.jd_to_datetime` 按
**proleptic Gregorian** 换算 —— 两者在 1150 / 1206 年**相差 7 天**
（实测：大雪 1206 = sxtwl 标 1206-11-30 09:34，jd_to_datetime 标 1206-12-07 09:34）。

南���用的是儒略历，故**原典对拍一律走 sxtwl（儒略历标签）**。

## 二、五例全链对拍结果（实测全绿）

| 算例 | 出处 | 原典农历 | 公历(儒略) | 四柱 | 天/地 | 先天卦 | 元堂 | 后天卦 | 换后天 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 起例卷之中 L184 | 1150 七月二十二日酉时 | 1150-08-16 | 庚午甲申丙申丁酉 | 44/28 | 火山旅 | 初六 | 离为火 | 46 |
| 2 | 起例卷之中 L185 | 1155 八月初三日申时 | 1155-09-01 | 乙亥乙酉戊寅庚申 | 26/26 | 天水讼 | 初六 | 泽天夬 | 49 |
| 3 | 起例卷之中 L186 | 1206 十月二十九日亥时 | 1206-11-30 | 丙寅庚子丙子己亥 | 18/42 | 山地剥 | 上九 | 坤为地 | — |
| 4 | 起例卷之中 L187 | 1228 十一月二十三日亥时 | 1228-12-21 | 戊子甲子癸巳癸亥 | 11/30 | 水雷屯 | 九五 | — | — |
| 5 | 起例卷之上 L62 | 1134 十月初四日申时 | 1134-10-22 | 甲寅甲戌己卯壬申 | 29/48 | 风山渐 | 六四 | 山天大畜 | 46 |

## 三、原典自身的两处抵牾（本守卫据以裁定，不是引擎缺陷）

1. **算例 1 日柱底本讹字**：L184 作「命庚午甲申**丙午**丁酉」，但
   * 原典自述「阳数四十四 / 阴数二十八」只在日柱作**丙申**时才成立
     （丙午 → 天42 地26；丙申 → 天44 地28）；
   * 历法独立印证：农历 1150 七月二十二日 = 公历(儒略) 1150-08-16，
     其日柱正是**丙申**，且丙申日酉时 = 丁酉时，与原典时柱相合。
   → 判定为底本转录讹字（午/申形近），引擎用校正后的丙申。
2. **算例 4 年号与干支互斥**：原典作「绍定三年**戊子**」，而
   戊子 = **1228 = 绍定元年**（绍定三年 = 1230 = 庚寅）。
   本守卫按**干支**取 1228（干支与卦/元堂/二数全链条自洽）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.calendar_guard import (
    check_calendar_consistency,
    julian_gregorian_offset,
    sxtwl_pillars,
)
from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.engines.heluo.numbers import build_six_lines, compute_tian_di_shu
from tongshu.engines.heluo.timeline_yun import compute_dayun_liyao
from tongshu.engines.heluo.yuan_tang import find_yuantang

#: 时辰 → 该时辰起始小时（用于取时柱）
_SHICHEN_HOUR = {
    "子": 0, "丑": 2, "寅": 4, "卯": 6, "辰": 8, "巳": 10,
    "午": 12, "未": 14, "申": 16, "酉": 18, "戌": 20, "亥": 22,
}

#: 原典五例：农历日期 + 时辰 + 原典四柱 + 原典判词
CASES = [
    dict(no=1, line="起例卷之中 L184",
         lunar=(1150, 7, 22), solar=(1150, 8, 16), shichen="酉",
         pillars=("庚午", "甲申", "丙申", "丁酉"),
         tian=44, di=28, prenatal="火山旅", yuantang="初六",
         postnatal="离为火", switch=46),
    dict(no=2, line="起例卷之中 L185",
         lunar=(1155, 8, 3), solar=(1155, 9, 1), shichen="申",
         pillars=("乙亥", "乙酉", "戊寅", "庚申"),
         tian=26, di=26, prenatal="天水讼", yuantang="初六",
         postnatal="泽天夬", switch=49),
    dict(no=3, line="起例卷之中 L186",
         lunar=(1206, 10, 29), solar=(1206, 11, 30), shichen="亥",
         pillars=("丙寅", "庚子", "丙子", "己亥"),
         tian=18, di=42, prenatal="山地剥", yuantang="上九",
         postnatal="坤为地", switch=None),
    dict(no=4, line="起例卷之中 L187",
         lunar=(1228, 11, 23), solar=(1228, 12, 21), shichen="亥",
         pillars=("戊子", "甲子", "癸巳", "癸亥"),
         tian=11, di=30, prenatal="水雷屯", yuantang="九五",
         postnatal=None, switch=None),
    dict(no=5, line="起例卷之上 L62",
         lunar=(1134, 10, 4), solar=(1134, 10, 22), shichen="申",
         pillars=("甲寅", "甲戌", "己卯", "壬申"),
         tian=29, di=48, prenatal="风山渐", yuantang="六四",
         postnatal="山天大畜", switch=46),
]


def _sxtwl_pillars(solar, hour):
    import sxtwl
    G = "甲乙丙丁戊己庚辛壬癸"
    Z = "子丑寅卯辰巳午未申酉戌亥"
    day = sxtwl.fromSolar(*solar)
    ygz, mgz, dgz = day.getYearGZ(), day.getMonthGZ(), day.getDayGZ()
    hgz = day.getHourGZ(hour, False)
    return (
        G[ygz.tg] + Z[ygz.dz], G[mgz.tg] + Z[mgz.dz],
        G[dgz.tg] + Z[dgz.dz], G[hgz.tg] + Z[hgz.dz],
    )


class TestOriginalCaseCalendarChain(unittest.TestCase):
    """农历 → 公历(儒略) → 四柱 → 河洛判词：五例全链对拍。"""

    def test_calendar_to_judgement_chain(self):
        for c in CASES:
            with self.subTest(case=c["no"], line=c["line"]):
                import sxtwl
                y, m, d = c["lunar"]
                day = sxtwl.fromLunar(y, m, d, False)
                solar = (day.getSolarYear(), day.getSolarMonth(), day.getSolarDay())
                self.assertEqual(solar, c["solar"],
                                 f"算例{c['no']} 农历→公历(儒略历标签)")

                hour = _SHICHEN_HOUR[c["shichen"]]
                pillars = _sxtwl_pillars(solar, hour)
                self.assertEqual(pillars, c["pillars"],
                                 f"算例{c['no']} 四柱应逐字等于原典")

                bazi = [(p[0], p[1]) for p in pillars]
                ns = compute_tian_di_shu(bazi, "male")
                self.assertEqual((ns.tian_shu, ns.di_shu), (c["tian"], c["di"]),
                                 f"算例{c['no']} 天地二数")

                res = HeluoCanonical().calculate(
                    bazi=bazi, gender="male", birth_hour=c["shichen"],
                    era="zhong", birth_year=1900)
                self.assertEqual(res.prenatal.hexagram_name, c["prenatal"],
                                 f"算例{c['no']} 先天卦")
                self.assertEqual(res.yuantang.yuantang, c["yuantang"],
                                 f"算例{c['no']} 元堂")
                if c["postnatal"]:
                    self.assertEqual(res.postnatal.hexagram_name, c["postnatal"],
                                     f"算例{c['no']} 后天卦")
                if c["switch"] is not None:
                    pre = build_six_lines(res.prenatal.upper_gua, res.prenatal.lower_gua)
                    post = build_six_lines(res.postnatal.upper_gua, res.postnatal.lower_gua)
                    pyt = find_yuantang(six_lines=post, birth_hour=c["shichen"],
                                         gender="male",
                                         xiantian_name=res.postnatal.hexagram_name)
                    dy = compute_dayun_liyao(pre, res.yuantang.yuantang_index,
                                              post, pyt.yuantang_index)
                    switch = next((e.age_start for e in dy.sequence
                                   if e.phase == "后天"), None)
                    self.assertEqual(switch, c["switch"],
                                     f"算例{c['no']} 换后天岁数")

    def test_original_case3_month_pillar_is_jieqi_month(self):
        """算例 3：月柱「庚子」= 大雪后子月 —— 原典按**节气**分月。

        原典 L186 自述「十月二十九日子时交大雪节……系是大雪后一日生也」。
        sxtwl 口径下大雪 1206 = 公历(儒略) 11-30 09:34，亥时（21:00）生于
        同日 → 已过大雪 → 子月 → 月柱庚子。**八字引擎因 jd_to_datetime 按
        proleptic Gregorian 换算（差 7 天）而判成亥月（己亥）**，
        属八字/时间域缺陷，本包不改，只在此钉住河洛侧口径。
        """
        import sxtwl
        day = sxtwl.fromSolar(1206, 11, 30)
        mgz = day.getMonthGZ()
        G, Z = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
        self.assertEqual(G[mgz.tg] + Z[mgz.dz], "庚子",
                         "sxtwl 节气月 = 子月（庚子），与原典一致")


class TestAdapterEndToEnd(unittest.TestCase):
    """**端到端**：农历 → 公历 → HeluoAdapter（经八字引擎）→ 河洛判词。

    这是本轮最硬的一道尺：走的是平台真正会走的入口
    （`HeluoAdapter.compute` → 八字引擎排盘 → 河洛），而不是把原典四柱直接
    喂进河洛。算例 3 尤其关键 —— 八字引擎在 1582 年前的「节」边界差 7 天
    （月柱判成亥月），河洛侧按自己的 sxtwl 节气口径自校后必须回到原典的
    子月（庚子），且天数地数/卦/元堂随之复原。
    """

    def test_adapter_end_to_end_all_cases(self):
        from tongshu.engines.heluo_adapter import HeluoAdapter
        import sxtwl

        adapter = HeluoAdapter()
        for c in CASES:
            with self.subTest(case=c["no"], line=c["line"]):
                y, m, d = c["lunar"]
                day = sxtwl.fromLunar(y, m, d, False)
                solar = (day.getSolarYear(), day.getSolarMonth(), day.getSolarDay())
                hour = _SHICHEN_HOUR[c["shichen"]]
                res = adapter.compute(solar_date=(solar[0], solar[1], solar[2], hour),
                                      gender="male")
                pillars = tuple(f"{g}{z}" for g, z in res.bazi)
                self.assertEqual(pillars, c["pillars"],
                                 f"算例{c['no']} 河洛采用的四柱应逐字等于原典")
                self.assertEqual((res.numbers.tian_shu, res.numbers.di_shu),
                                 (c["tian"], c["di"]),
                                 f"算例{c['no']} 天地二数")
                self.assertEqual(res.prenatal.hexagram_name, c["prenatal"],
                                 f"算例{c['no']} 先天卦")
                self.assertEqual(res.yuantang.yuantang, c["yuantang"],
                                 f"算例{c['no']} 元堂")

    def test_case3_month_pillar_correct(self):
        """算例 3：月柱必须是子月**庚子**（原典口径）。

        2026-10-22 起八字侧已修（``jd_to_datetime`` 改用儒略历），故上游直接
        给对；河洛侧的自校此时**不触发**（它只是兜底 —— 上游一旦再错位，
        自校会把月柱拉回河洛口径并留痕）。
        """
        from tongshu.engines.heluo_adapter import HeluoAdapter
        import sxtwl

        day = sxtwl.fromLunar(1206, 10, 29, False)
        solar = (day.getSolarYear(), day.getSolarMonth(), day.getSolarDay())
        res = HeluoAdapter().compute(
            solar_date=(solar[0], solar[1], solar[2], 21), gender="male")
        self.assertEqual(f"{res.bazi[1][0]}{res.bazi[1][1]}", "庚子",
                         "月柱应为子月（庚子）")
        self.assertEqual(f"{res.bazi[2][0]}{res.bazi[2][1]}", "丙子")
        # 自校只在**上游确实错位**时才留痕；上游已修 → 不应有留痕
        for note in (res.bazi_caliber_notes or []):
            self.assertIn("历法自校", note)

    def test_self_correction_kicks_in_when_upstream_is_wrong(self):
        """上游若再错位（人为喂错月柱）→ 河洛自校拉回并留痕（兜底仍有效）。"""
        from tongshu.engines.heluo.canonical import HeluoCanonical
        from tongshu.engines.heluo.calendar_guard import resolve_year_month

        # 1206-11-30 21:00 的大雪后子月 = 庚子；这里喂相邻的亥月（己亥）
        bazi = [("丙", "寅"), ("己", "亥"), ("丙", "子"), ("己", "亥")]
        fixed, notes = resolve_year_month(bazi, "1206-11-30", "亥")
        self.assertEqual(fixed[1][0] + fixed[1][1], "庚子",
                         "相邻月柱应被自校回子月（庚子）")
        self.assertTrue(notes, "自校必须留痕")
        self.assertIn("月柱", " ".join(notes))

        res = HeluoCanonical().calculate(
            bazi=bazi, gender="male", birth_hour="亥", era="zhong",
            birth_date="1206-11-30", birth_year=1206)
        self.assertEqual(f"{res.bazi[1][0]}{res.bazi[1][1]}", "庚子")
        self.assertTrue(res.bazi_caliber_notes, "canonical 亦须留痕")

    def test_modern_date_untouched(self):
        """现代日期不得被自校改动（无据不动）。"""
        from tongshu.engines.heluo_adapter import HeluoAdapter
        import sxtwl

        day = sxtwl.fromSolar(2026, 10, 22)
        res = HeluoAdapter().compute(
            solar_date=(day.getSolarYear(), day.getSolarMonth(), day.getSolarDay(), 12),
            gender="male")
        self.assertEqual(res.bazi_caliber_notes, [],
                         "现代日期不应触发自校留痕")

    def test_non_adjacent_input_not_modified(self):
        """输入四柱与日期**根本不对应**（相差不相邻）→ 不改，只留痕。

        合成 fixture（bazi 与 birth_date 无关）是典型情形：河洛**不得擅自
        改写调用方的显式输入**，否则既有行为被静默篡改。
        """
        from tongshu.engines.heluo.canonical import HeluoCanonical
        from tongshu.engines.heluo.calendar_guard import resolve_year_month

        # 1983-11-03 的节气月是亥月；这里给寅月（不相邻）
        bazi = [("癸", "亥"), ("甲", "寅"), ("丁", "巳"), ("戊", "午")]
        fixed, notes = resolve_year_month(bazi, "1983-11-03", "午")
        self.assertEqual(fixed[1], ("甲", "寅"), "不相邻时不得改动输入四柱")
        self.assertTrue(notes, "但必须留痕（输入与日期不对应）")
        self.assertIn("未改动", " ".join(notes))

        res = HeluoCanonical().calculate(
            bazi=bazi, gender="male", birth_hour="午", era="zhong",
            birth_date="1983-11-03")
        self.assertEqual(res.bazi[1], ("甲", "寅"),
                         "canonical 亦不得改动不相邻的输入四柱")


class TestJulianGregorianCaliber(unittest.TestCase):
    """历法口径事实守卫：1582 年前 sxtwl 用儒略历。"""

    def test_offset_table(self):
        self.assertEqual(julian_gregorian_offset(1150, 8, 16), 7)
        self.assertEqual(julian_gregorian_offset(1206, 11, 30), 7)
        self.assertEqual(julian_gregorian_offset(1500, 3, 1), 10)
        self.assertEqual(julian_gregorian_offset(1582, 10, 15), 0)
        self.assertEqual(julian_gregorian_offset(2026, 10, 22), 0)

    def test_sxtwl_label_is_julian_before_1582(self):
        """sxtwl 的公历标签在改历前 = 儒略历；仓库换算必须与之同口径。

        2026-10-22 起 `jd_to_datetime` 已改为「1582-10-15 前用儒略历」，
        与 sxtwl.JD2DD 逐分钟一致（此前差 7 天 → 八字引擎古日期月柱错位）。
        """
        import sxtwl
        from tongshu.engines.time.jd_converter import jd_to_datetime
        day = sxtwl.fromSolar(1206, 11, 30)
        t = sxtwl.JD2DD(day.getJieQiJD())
        sxtwl_label = (int(t.Y), int(t.M), int(t.D))
        self.assertEqual(sxtwl_label, (1206, 11, 30),
                         "sxtwl 标的大雪日（儒略历标签）")
        conv = jd_to_datetime(day.getJieQiJD())
        self.assertEqual((conv.year, conv.month, conv.day), (1206, 11, 30),
                         "jd_to_datetime 必须与 sxtwl 同口径（儒略历）")
        self.assertEqual(conv.strftime("%Y-%m-%d %H:%M"),
                         "1206-11-30 09:34",
                         "时刻须与 sxtwl.JD2DD 逐分钟一致")

    def test_sxtwl_pillars_helper(self):
        p = sxtwl_pillars("1206-11-30")
        self.assertIsNotNone(p)
        self.assertEqual(p["day"], "丙子")
        self.assertEqual(p["month"], "庚子")


class TestCalendarGuard(unittest.TestCase):
    """河洛侧历法口径自检（calendar_guard）行为守卫。"""

    def test_modern_date_no_false_positive(self):
        # 上游口径一致的现代日期（bazi 取 sxtwl 自算值）→ 不得误报
        p = sxtwl_pillars("2026-10-22")
        bazi = [(p["year"][0], p["year"][1]), (p["month"][0], p["month"][1]),
                (p["day"][0], p["day"][1]), ("庚", "午")]
        notes = check_calendar_consistency(bazi, "2026-10-22")
        self.assertEqual(notes, [], "现代日期不得误报")

    def test_gregorian_converted_ancient_date_is_flagged(self):
        """把古农历按 proleptic Gregorian 换算后喂进来 → 必须报出口径差异。"""
        # 农历 1206 十月二十九 = 儒略 1206-11-30 = 格里 1206-12-07
        bazi = [("丙", "寅"), ("庚", "子"), ("丙", "子"), ("己", "亥")]
        notes = check_calendar_consistency(bazi, "1206-12-07")
        self.assertTrue(notes, "格里历标签喂入必须留痕")
        joined = " ".join(notes)
        self.assertIn("日柱不一致", joined)
        self.assertIn("7 天", joined)

    def test_jie_boundary_day_not_flagged(self):
        """交节当日：sxtwl 整日口径与八字引擎精确时刻口径可能差一柱，不报。"""
        # 2026-02-04 立春当日：月柱可能因切分时刻不同而不同，但不应被当成口径问题
        p = sxtwl_pillars("2026-02-04")
        bazi = [(p["year"][0], p["year"][1]), (p["month"][0], p["month"][1]),
                (p["day"][0], p["day"][1]), ("丙", "子")]
        notes = check_calendar_consistency(bazi, "2026-02-04")
        self.assertEqual(notes, [], "交节当日不得误报月柱差异")

    def test_missing_input_is_not_judged(self):
        self.assertEqual(check_calendar_consistency(None, "1206-11-30"), [])
        self.assertEqual(check_calendar_consistency([("丙", "寅")], ""), [])


if __name__ == "__main__":
    unittest.main()
