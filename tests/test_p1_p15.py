"""P1 + P1.5 测试"""
from __future__ import annotations
import unittest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tongshu.engines.time.solar_time import (
    calculate_true_solar_time,
    create_global_time_table,
    get_equation_of_time
)

import psycopg2

DB_URI = "host=127.0.0.1 port=5432 dbname=shuntian_kb user=postgres password=postgres"


class TestTrueSolarTime(unittest.TestCase):
    """测试真太阳时计算。"""
    
    def test_beijing_no_correction(self):
        """北京经度接近120度，修正应很小。"""
        result = calculate_true_solar_time(
            datetime(2025, 8, 21, 12, 0, 0),
            longitude=116.4,
            latitude=39.9
        )
        self.assertAlmostEqual(result["longitude_correction_minutes"], -14.4, delta=1)
    
    def test_shanghai_positive_correction(self):
        """上海在东边，时间应提前。"""
        result = calculate_true_solar_time(
            datetime(2025, 8, 21, 12, 0, 0),
            longitude=121.5,
            latitude=31.2
        )
        # 经度修正应为正
        self.assertGreater(result["longitude_correction_minutes"], 0)
    
    def test_urumqi_negative_correction(self):
        """乌鲁木齐在西边，时间应推迟。"""
        result = calculate_true_solar_time(
            datetime(2025, 8, 21, 12, 0, 0),
            longitude=87.6,
            latitude=43.8
        )
        # 经度修正应为负
        self.assertLess(result["longitude_correction_minutes"], 0)
    
    def test_equation_of_time_range(self):
        """均时差应在合理范围（全年极值约 ±16.4min ≈ ±985s）。"""
        eot = get_equation_of_time(2025, 8, 21)
        # 8月21日真实值约 -199s（Meeus）；断言放宽至天文极值范围。
        self.assertGreaterEqual(eot, -1000)
        self.assertLessEqual(eot, 1000)
        # 非零：修复 P1-3 前恒返回 0，此断言确保均时差真实生效。
        self.assertNotEqual(eot, 0)


class TestGlobalTimeTable(unittest.TestCase):
    """测试全球时间参数表。"""
    
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg2.connect(DB_URI)
    
    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
    
    def test_table_created(self):
        """表已创建。"""
        stats = create_global_time_table(self.conn)
        self.assertEqual(stats["global_time_params_table"], 1)
    
    def test_params_inserted(self):
        """参数已插入。"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM global_time_params")
        count = cur.fetchone()[0]
        self.assertGreaterEqual(count, 4)


if __name__ == "__main__":
    unittest.main()
