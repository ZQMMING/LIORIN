"""阳月令 / 阴月令判定 —— 原典十二月卦气表逐月对照（2026-10-07）

**起因**：原实现 `yang_month = birth_month in (1,2,3,4,5,6)` 被判为错误。
原典 L854–L914 逐月给出卦气与阴阳消长，**无需推断，只须读表**：

    正月 雨水 → 泰   「三阳出于寅」
    二月 春分 → 大壮 「四阳生于卯」
    三月 谷雨 → 夬   「五阳生于辰」
    四月 小满 → 乾   「六阳终于巳……乃纯阳之月」
    五月 夏至 → 姤   「一阴始生于午」    ← 阴令起点
    六月 大暑 → 遁   「二阴生于未」
    七月 处暑 → 否   「三阴生于申」
    八月 秋分 → 观   「四阴生于酉」
    九月 霜降 → 剥   「五阴生于戌」
    十月       → 坤   「六阴生于亥……乃纯阴之时」
    十一月 冬至 → 复 「一阳生于子」      ← 阳令起点
    十二月 大寒 → 临 「二阳生于丑」

即：阳气自十一月冬至一阳生，至四月小满六阳俱备（纯乾）；
    阴气自五月夏至一阴生，至十月六阴俱纯（纯坤）。
→ 阳月令 = 11、12、1、2、3、4；阴月令 = 5~10。

旧口径把 5、6、11、12 四个月判反——尤其 11、12 月（冬至一阳生）
被当作阴月令，会漏判生死大凶。

**本文件 24 项守卫**：十二个月逐月钉死 + 结构断言，
变异（退回 1-6 月简化法）后必红。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from heluo_engine.engines.heluo.guajie import (
    GUA_QI_MONTH_TABLE,
    YIN_YUE_LING,
    YANG_YUE_LING,
    judge_shu_xiong,
)

# 原典逐月判定的字面期望（节令）：True=阳月令，False=阴月令
# 按 1~12 月排列。来源见本文件头部引用。
EXPECTED_YANG_BY_MONTH = {
    1: True, 2: True, 3: True, 4: True,          # 三阳→六阳，纯阳之月
    5: False, 6: False, 7: False,                 # 一阴→三阴
    8: False, 9: False, 10: False,                # 四阴→六阴，纯阴之时
    11: True, 12: True,                           # 一阳、二阳
}


def _is_yang(month: int) -> bool:
    return month in YANG_YUE_LING


class TestYangYueLingLiteral(unittest.TestCase):
    """逐月钉死十二个月的月令阴阳（12 项）。"""

    def test_each_month_literal(self):
        for m in range(1, 13):
            self.assertEqual(_is_yang(m), EXPECTED_YANG_BY_MONTH[m],
                             f"{m}月的月令阴阳判定不符原典十二月卦气表")


class TestYangYueLingStructure(unittest.TestCase):
    """结构断言：阴阳两令必须完整覆盖十二月，且与卦气进退严格对应。"""

    def test_partition_is_total_and_disjoint(self):
        self.assertEqual(len(YANG_YUE_LING | YIN_YUE_LING), 12,
                         "阳月令与阴月令必须恰好覆盖十二个月")
        self.assertEqual(YANG_YUE_LING & YIN_YUE_LING, frozenset(),
                         "阳月令与阴月令不得重叠")

    def test_yang_months_are_six(self):
        self.assertEqual(len(YANG_YUE_LING), 6)
        self.assertEqual(len(YIN_YUE_LING), 6)

    def test_yang_solstice_to_pure_yang_is_contiguous(self):
        """阳月令自十一月（冬至）起、至四月（纯阳）止，跨年连续。"""
        ordered = [11, 12, 1, 2, 3, 4]
        self.assertEqual(sorted(YANG_YUE_LING), sorted(ordered),
                         "阳月令应为跨年连续的十一月~四月")
        self.assertEqual(YANG_YUE_LING, frozenset(ordered))

    def test_yin_months_are_may_to_october(self):
        self.assertEqual(sorted(YIN_YUE_LING), [5, 6, 7, 8, 9, 10],
                         "阴月令应为夏至后连续的五月~十月")

    def test_old_simplification_is_explicitly_wrong(self):
        """反证：旧口径（1~6 月为阳）必须在 5、6、11、12 四个月上判反。"""
        old = {m for m in range(1, 13) if m in (1, 2, 3, 4, 5, 6)}
        wrong = {m for m in range(1, 13) if (m in old) != EXPECTED_YANG_BY_MONTH[m]}
        self.assertEqual(wrong, {5, 6, 11, 12},
                         "旧口径的判反月份若变了，说明原典表或裁决被改动")


class TestGuaQiMonthTableLiteral(unittest.TestCase):
    """原典十二月卦气表本身（12 项）—— 卦名不得改。"""

    EXPECTED_GUA = {
        1: "泰", 2: "大壮", 3: "夬", 4: "乾",
        5: "姤", 6: "遁", 7: "否",
        8: "观", 9: "剥", 10: "坤", 11: "复", 12: "临",
    }

    def test_每卦与原典一致(self):
        for m, (_, gua, _) in GUA_QI_MONTH_TABLE.items():
            self.assertEqual(gua, self.EXPECTED_GUA[m],
                             f"{m}月卦气应为 {self.EXPECTED_GUA[m]}")

    def test_每节气与原典一致(self):
        expect_jq = {1: "雨水", 2: "春分", 3: "谷雨", 4: "小满",
                     5: "夏至", 6: "大暑", 7: "处暑",
                     8: "秋分", 9: "霜降", 10: "—",
                     11: "冬至", 12: "大寒"}
        for m, (jq, _, _) in GUA_QI_MONTH_TABLE.items():
            self.assertEqual(jq, expect_jq[m], f"{m}月节气不符原典")


class TestShuXiongRespectsYueLing(unittest.TestCase):
    """端到端：数凶判定须随月令阴阳变化（生产链路行为守卫）。"""

    # 以弱敌强：地数>=30 且 天数<=24 → 阳月令才主灭顶之凶（L1073）
    TIAN, DI = 20, 40

    def test_yang_month_is_xiong(self):
        for m in sorted(YANG_YUE_LING):
            r = judge_shu_xiong(self.TIAN, self.DI, m)
            self.assertTrue(r.shu_xiong,
                            f"{m}月为阳月令，「以弱敌强」逢之应主凶（L1073）")

    def test_yin_month_is_not_xiong(self):
        """原典 L1073：「阴月令逢之，尚庶几」——阴月令不判凶。"""
        for m in sorted(YIN_YUE_LING):
            r = judge_shu_xiong(self.TIAN, self.DI, m)
            self.assertFalse(r.shu_xiong,
                             f"{m}月为阴月令，原典称「尚庶几」，不应判凶")

    def test_evidence_records_yue_ling(self):
        r = judge_shu_xiong(self.TIAN, self.DI, 11)
        self.assertTrue(any("阳月" in e for e in r.evidence),
                        f"十一月应留痕阳月令：{r.evidence}")
        r2 = judge_shu_xiong(self.TIAN, self.DI, 5)
        self.assertTrue(any("阴月" in e for e in r2.evidence),
                        f"五月应留痕阴月令：{r2.evidence}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
