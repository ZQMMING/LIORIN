"""H11: 节候卦计算测试

覆盖：24节气节候卦映射、动爻位置、原典一致性
原典依据：《河洛真数》起例卷下·定节候卦说
"""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from tongshu.engines.heluo.jiehhou import (
    SOLAR_TERMS,
    JIEHOU_GUA,
    JIEHOU_GUA_NAME,
    get_seasonal_hexagram,
    get_qi_phase,
    get_current_jieqi_info,
    SeasonalHexagram,
)


class TestSolarTerms(unittest.TestCase):
    """24节气名称顺序验证"""

    def test_24_terms_count(self):
        self.assertEqual(len(SOLAR_TERMS), 24)

    def test_24_terms_order(self):
        expected = [
            "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
            "春分", "清明", "谷雨", "立夏", "小满", "芒种",
            "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
            "秋分", "寒露", "霜降", "立冬", "小雪", "大雪",
        ]
        self.assertEqual(SOLAR_TERMS, expected)


class TestSeasonalHexagram(unittest.TestCase):
    """节候卦映射验证"""

    def test_all_24_coverage(self):
        """24节气全覆盖，无缺失"""
        for i in range(24):
            info = get_seasonal_hexagram(i)
            self.assertEqual(info.jq_name, SOLAR_TERMS[i])
            self.assertIn(info.main_gua, JIEHOU_GUA_NAME.values())

    def test_dongzhi_yi_fu(self):
        """冬至：颐六四动→复（原典）"""
        info = get_seasonal_hexagram(0)
        self.assertEqual(info.jq_name, "冬至")
        self.assertEqual(info.main_gua, "山雷颐")
        self.assertEqual(info.moving_line, 4)
        self.assertEqual(info.result_gua, "地雷复")

    def test_lichun_jie(self):
        """立春：泰三动→解（原典）"""
        info = get_seasonal_hexagram(3)
        self.assertEqual(info.result_gua, "雷水解")

    def test_chunfen_duogua(self):
        """春分：夬二动→损"""
        info = get_seasonal_hexagram(6)
        self.assertEqual(info.result_gua, "山泽损")

    def test_xiazhi_shi_pou(self):
        """夏至：师五动→剥"""
        info = get_seasonal_hexagram(12)
        self.assertEqual(info.result_gua, "山地剥")

    def test_qiufen_dun(self):
        """秋分：丰四动→遁"""
        info = get_seasonal_hexagram(18)
        self.assertEqual(info.result_gua, "天山遁")

    def test_invalid_index_raises(self):
        """越界应抛出 ValueError"""
        with self.assertRaises(ValueError):
            get_seasonal_hexagram(-1)
        with self.assertRaises(ValueError):
            get_seasonal_hexagram(24)

    def test_evidence_chain(self):
        """证据链包含原典引用"""
        info = get_seasonal_hexagram(0)
        self.assertTrue(any("河洛真数" in e for e in info.evidence))


class TestQiPhase(unittest.TestCase):
    """卦气阶段测试"""

    def test_sizheng_gua(self):
        """四正卦分管的节气（冬至/春分/夏至/秋分）"""
        sizheng_indices = {0, 6, 12, 18}
        for i in sizheng_indices:
            phase = get_qi_phase(2026, i)
            self.assertTrue(phase.is_sizheng)
            self.assertFalse(phase.six_day_seven_method)

    def test_bi_gua_monthly(self):
        """辟卦月份对应的节气"""
        li_chun = get_qi_phase(2026, 3)
        self.assertTrue(li_chun.is_bi_gua)

    def test_six_day_seven(self):
        """非四正卦节气适用六日七分法"""
        phase = get_qi_phase(2026, 1)  # 小寒
        self.assertTrue(phase.six_day_seven_method)


class TestCurrentJieqiInfo(unittest.TestCase):
    """当前节气查询测试（回归：修复非节气日返回 None 的 bug）"""

    def test_non_jieqi_date_returns_past_jieqi(self):
        """非节气日的出生日期必须返回最近的已过节气（修复前为 None）"""
        info = get_current_jieqi_info(2026, 9, 4)  # 处暑(8/23)之后、白露(9/7)之前
        self.assertIsNotNone(info)
        self.assertEqual(info.jq_name, "处暑")
        self.assertEqual(info.jq_index, 16)

    def test_1983_11_03_shuangjiang(self):
        """1983-11-03 立冬前 → 霜降"""
        info = get_current_jieqi_info(1983, 11, 3)
        self.assertIsNotNone(info)
        self.assertEqual(info.jq_name, "霜降")
        self.assertEqual(info.jq_index, 20)

    def test_2000_12_25_dongzhi(self):
        """2000-12-25 冬至后 → 冬至（2000-12-21）"""
        info = get_current_jieqi_info(2000, 12, 25)
        self.assertIsNotNone(info)
        self.assertEqual(info.jq_name, "冬至")
        self.assertEqual(info.jq_index, 0)

    def test_jieqi_day_itself(self):
        """出生当天恰为节气日 → 返回当天节气"""
        info = get_current_jieqi_info(2026, 12, 7)  # 大雪日
        self.assertIsNotNone(info)
        self.assertEqual(info.jq_name, "大雪")
        self.assertEqual(info.jq_index, 23)

    def test_cross_year_boundary(self):
        """跨年边界：2026-02-03 立春前一天 → 大寒（去冬节气周期）"""
        info = get_current_jieqi_info(2026, 2, 3)
        self.assertIsNotNone(info)
        self.assertEqual(info.jq_name, "大寒")
        self.assertEqual(info.jq_index, 2)

    def test_january_cross_year(self):
        """2027-01-15 → 小寒（2027 年初，节气周期仍属去冬）"""
        info = get_current_jieqi_info(2027, 1, 15)
        self.assertIsNotNone(info)
        self.assertEqual(info.jq_name, "小寒")
        self.assertEqual(info.jq_index, 1)

    def test_returned_is_seasonal_hexagram(self):
        """返回类型必须是 SeasonalHexagram 且含原典证据链"""
        info = get_current_jieqi_info(2026, 9, 4)
        self.assertIsInstance(info, SeasonalHexagram)
        self.assertTrue(any("河洛真数" in e for e in info.evidence))
        self.assertIn(info.main_gua, JIEHOU_GUA_NAME.values())


class TestJiehhouDataIntegrity(unittest.TestCase):
    """节候卦数据完整性"""

    def test_jiehou_gua_dict_has_24_entries(self):
        self.assertEqual(len(JIEHOU_GUA), 24)

    def test_jiehou_gua_name_matches(self):
        """JIEHOU_GUA_NAME 与 JIEHOU_GUA 一致"""
        for idx, (main, _, _) in JIEHOU_GUA.items():
            self.assertEqual(JIEHOU_GUA_NAME[idx], main)


if __name__ == "__main__":
    unittest.main()
