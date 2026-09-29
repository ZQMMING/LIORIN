"""P0-FNDR-08.5: ⑫ 起运增量整改 ORACLE-001.

User 裁决要求补:
  1. ORACLE-001: 1983-11-03 12:00:00 公历 男 完整命例 Oracle, start_age = 8.432623
  2. Negative Oracle: 算法绝不能选霜降 (idx=20, 是气不是节), 否则 ≈ 3.39 岁
  3. _is_jie() 节/气分类独立验证 (24 节气全覆盖)

这是补完 ⑫ 起运 CLOSED 之前的最后验证.
"""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from tongshu.engines.bazi_engine import BaziEngine, is_jie


class TestStartAgeOracle19831103Noon(unittest.TestCase):
    """ORACLE-001: 1983-11-03 12:00 公历 男 完整命例端到端验证.

    精确数据 (基于 sxtwl getJieQiByYear(1983)):
      出生:        1983-11-03 12:00:00 +08:00 (公历, 男)
      年干:        GUI (癸) = 阴
      性别:        男
      顺逆:        REVERSE (阴男逆排)
      上一节:      寒露 1983-10-09 04:51:04.210524 +08:00 (idx=19, 节)
      下一节:      立冬 1983-11-08 07:52:11.604767 +08:00 (idx=21, 节)
      Delta:       25.297868 天 (= 25 天 7 小时 8 分 56 秒)
      Start Age:   25.297868 / 3 = 8.432623 岁

      如果错误选霜降 (idx=20, 气):
        霜降 1983-10-24 07:54:16.766510
        Delta = 9.18 天, Start Age = 3.06 岁
    """

    def setUp(self):
        self.engine = BaziEngine()

    def test_oracle_001_full_lifecycle(self):
        """ORACLE-001: 1983-11-03 12:00 公历 男, 完整端到端验证.

        验证 5 个独立信号:
          1. 年柱 = GUI 癸亥 (R-04 Solar Year Boundary)
          2. 月柱 = 壬戌 (寒露后, 立冬前)
          3. 日柱 = 乙未
          4. 时柱 = 壬午 (12:00 = 午时, 甲己日 壬午起)
          5. start_age ≈ 8.432623 (精确到小数点后 6 位)
        """
        tz = ZoneInfo("Asia/Shanghai")
        bd = datetime(1983, 11, 3, 12, 0, 0, tzinfo=tz)
        chart = self.engine.compute(
            (1983, 11, 3, 12),
            gender="male",
            birth_datetime=bd,
        )

        # 1. 年柱 = GUI 癸亥
        self.assertEqual(chart.year_pillar.heavenly_stem, "GUI")
        self.assertEqual(chart.year_pillar.earthly_branch, "HAI")

        # 2. 月柱 = 壬戌
        self.assertEqual(chart.month_pillar.heavenly_stem, "REN")
        self.assertEqual(chart.month_pillar.earthly_branch, "XU")

        # 3. 日柱 = 乙未
        self.assertEqual(chart.day_pillar.heavenly_stem, "YI")
        self.assertEqual(chart.day_pillar.earthly_branch, "WEI")

        # 4. 时柱 = 壬午 (12:00 = 午时, 甲己日 壬午起)
        self.assertEqual(chart.hour_pillar.heavenly_stem, "REN")
        self.assertEqual(chart.hour_pillar.earthly_branch, "WU")

        # 5. 起运岁数 = 8.432623... 岁 (精确)
        # 与 sxtwl 寒露 1983-10-09 04:51:04.210524 对齐
        # Delta = 25.297868 天 / 3
        self.assertAlmostEqual(
            chart.start_age, 8.432623, places=6,
            msg=f"ORACLE-001: start_age={chart.start_age} should be ≈ 8.432623",
        )

    def test_oracle_001_negative_no_shuangjiang(self):
        """NEGATIVE ORACLE: 算法绝不能选霜降 (idx=20, 是气不是节).

        如果算法错误选霜降, start_age ≈ 3.06 岁 (Delta = 9.18 天 / 3).
        我们的 assertAlmostEqual(..., places=6) 期望 8.432623,
        如果选霜降, 实际 ≈ 3.06, 差 5.37, places=6 必 fail.

        显式 negative 断言: 选中的节 ≠ 霜降 1983-10-24 07:54:16.
        """
        tz = ZoneInfo("Asia/Shanghai")
        bd = datetime(1983, 11, 3, 12, 0, 0, tzinfo=tz)
        chart = self.engine.compute(
            (1983, 11, 3, 12),
            gender="male",
            birth_datetime=bd,
        )

        # Negative assertion: start_age 不能等于"如果选霜降"的值
        # 霜降 1983-10-24 07:54:16 - 1983-11-03 12:00:00 = 10.17 天 / 3 ≈ 3.39
        SHUANGJIANG_BUG_VALUE = 3.39
        self.assertNotAlmostEqual(
            chart.start_age, SHUANGJIANG_BUG_VALUE, places=1,
            msg=f"算法不应选霜降! 选霜降 start_age ≈ {SHUANGJIANG_BUG_VALUE}",
        )

        # 进一步: start_age 应远大于 3.39 (因为寒露距 25 天, 起运 8.43)
        self.assertGreater(
            chart.start_age, 5.0,
            msg=f"起运 8.43 岁应 > 5.0 (排除霜降 3.39 岁错误)",
        )

    def test_oracle_001_sxtwl_direct_verification(self):
        """ORACLE-001 终极验证: 用 sxtwl 直接计算 start_age 与生产代码对比.

        P0-FNDR-08.6 (User 裁决最后一项):
          Oracle 必须独立于项目 facts 层, 不再 import DAYS_PER_YEAR_OF_START_AGE.
          3天=1岁换算规则是经典命理基础常识, Oracle 中硬编码 / 3.0 作为独立外部参考值.
          这一步通过后, ⑫ 起运正式 CLOSED.

        不依赖 BaziEngine._calc_start_age, 用 sxtwl.getJieQiByYear 直接查寒露时刻
        自己实现起运计算, 与生产结果比对. 这是"独立 Oracle 终极测试".
        """
        import sxtwl
        from tongshu.engines.time.jd_converter import jd_to_datetime

        bd = datetime(1983, 11, 3, 12, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

        # 用 sxtwl 查找 1983 寒露 (idx=19, 节)
        hanlu_dt = None
        for jq in sxtwl.getJieQiByYear(1983):
            if jq.jqIndex == 19:  # 寒露
                hanlu_dt = jd_to_datetime(jq.jd)
                break

        self.assertIsNotNone(hanlu_dt, "sxtwl 1983 寒露时刻必须存在")
        self.assertEqual(
            hanlu_dt.year, 1983,
            msg=f"寒露年份应为 1983, 实际 {hanlu_dt.year}",
        )

        # P0-FNDR-08.6: Oracle 独立化 — 不再 import DAYS_PER_YEAR_OF_START_AGE.
        # 3天=1岁换算 (硬编码) — 经典命理基础常识, 作为独立外部参考值.
        # 这与 sxtwl 节气数据并列: 都是"独立外部权威", 不引用项目 facts.
        INDEPENDENT_CANONICAL_DAYS_PER_YEAR = 3
        delta_days = (bd - hanlu_dt).total_seconds() / 86400.0
        oracle_start_age = abs(delta_days) / INDEPENDENT_CANONICAL_DAYS_PER_YEAR

        # 与生产代码对比
        chart = self.engine.compute(
            (1983, 11, 3, 12),
            gender="male",
            birth_datetime=bd,
        )
        self.assertAlmostEqual(
            chart.start_age, oracle_start_age, places=10,
            msg=(
                f"生产代码 ({chart.start_age}) 应与 sxtwl 直接计算 ({oracle_start_age}) 完全一致. "
                f"Oracle 现在使用独立硬编码 / 3.0 (P0-FNDR-08.6), "
                f"不依赖项目 facts 层."
            ),
        )

        # P0-FNDR-08.6 额外验证: Oracle 与项目 facts 数值必须一致 (架构正确性).
        # 这保证"独立 Oracle"与"生产常量"使用同一个换算规则.
        from tongshu.facts.bazi_facts import DAYS_PER_YEAR_OF_START_AGE
        self.assertEqual(
            INDEPENDENT_CANONICAL_DAYS_PER_YEAR, DAYS_PER_YEAR_OF_START_AGE,
            msg=(
                f"Oracle 硬编码 / 3.0 应与项目 facts DAYS_PER_YEAR_OF_START_AGE={DAYS_PER_YEAR_OF_START_AGE} "
                f"保持一致, 否则生产与测试使用不同换算规则."
            ),
        )


class TestIsJieIndependent(unittest.TestCase):
    """P0-FNDR-08.5: _is_jie() 节/气分类独立验证.

    sxtwl 节气索引规律:
      偶数 idx (0/2/4/6/8/10/12/14/16/18/20/22) = 中气
      奇数 idx (1/3/5/7/9/11/13/15/17/19/21/23) = 节
    """

    def test_jie_specific_dates(self):
        """用 sxtwl 直接验证特定日期的节/气分类.

        1983 寒露 10-09 (节), 霜降 10-24 (气), 立冬 11-08 (节).
        1984 立春 02-04 (节), 雨水 02-19 (气).
        """
        import sxtwl

        cases = [
            # (year, month, day, expected_idx, expected_is_jie, description)
            (1983, 10, 9, 19, True, "寒露 1983-10-09"),
            (1983, 10, 24, 20, False, "霜降 1983-10-24"),
            (1983, 11, 8, 21, True, "立冬 1983-11-08"),
            (1984, 2, 4, 3, True, "立春 1984-02-04"),
            (1984, 2, 19, 4, False, "雨水 1984-02-19"),
        ]
        for year, month, day, exp_idx, exp_is_jie, desc in cases:
            day_obj = sxtwl.fromSolar(year, month, day)
            self.assertTrue(day_obj.hasJieQi(), f"{desc} 应该有节气")
            self.assertEqual(
                day_obj.getJieQi(), exp_idx,
                f"{desc} idx 实际 {day_obj.getJieQi()} != 期望 {exp_idx}",
            )
            self.assertEqual(
                is_jie(day_obj), exp_is_jie,
                f"{desc} idx={exp_idx} 应 is_jie={exp_is_jie}",
            )

    def test_jie_24_classification(self):
        """全 24 节气节/气分类覆盖 (5 年 × 24 节气 = 120 个).

        遍历多年所有 24 节气, 验证偶数=气, 奇数=节.
        """
        import sxtwl
        from tongshu.engines.time.jd_converter import jd_to_datetime

        jie_count = 0
        qi_count = 0
        for year in [1983, 1984, 1985, 2024, 2025]:
            for jq in sxtwl.getJieQiByYear(year):
                idx = jq.jqIndex
                # 从 jd 反推日期 (sxtwl.JieQiInfo 无 y/m/d 属性, 仅有 jd)
                jq_dt = jd_to_datetime(jq.jd)
                # 用 jq_dt 的年/月/日 重建 day_obj
                day_obj = sxtwl.fromSolar(jq_dt.year, jq_dt.month, jq_dt.day)
                self.assertTrue(day_obj.hasJieQi(),
                                f"{year} idx={idx} 应该有节气")
                self.assertEqual(day_obj.getJieQi(), idx,
                                 f"{year} idx 实际 {day_obj.getJieQi()} != 期望 {idx}")
                expected_is_jie = (idx % 2 == 1)
                actual_is_jie = is_jie(day_obj)
                self.assertEqual(
                    actual_is_jie, expected_is_jie,
                    f"idx={idx} 应 is_jie={expected_is_jie}, 实际 {actual_is_jie}",
                )
                if expected_is_jie:
                    jie_count += 1
                else:
                    qi_count += 1

        # sxtwl.getJieQiByYear 返回 25 个节气 (包含跨年小寒/大寒),
        # 节 (奇数 idx) 总数 = 13 节 × 5 年 = 65 (跨年立春算 2 次)
        # 气 (偶数 idx) 总数 = 12 气 × 5 年 = 60
        # 但 65+60 = 125, 不等于 5×25. 这是因为 idx=3 (立春) 在跨年时计两次.
        # 实际断言:
        #   - 5 年内每个 idx 应出现 5 次 (除跨年节气)
        #   - 节/气总数比 65:60
        self.assertEqual(jie_count, 65,
                         f"5 年应正好 65 个'节' (含跨年立春), 实际 {jie_count}")
        self.assertEqual(qi_count, 60,
                         f"5 年应正好 60 个'气', 实际 {qi_count}")


if __name__ == "__main__":
    unittest.main()