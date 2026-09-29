"""P0-FNDR-10 (R-15 ⑭ BaziChart 契约 audit fix): to_dict() contract test.

User 裁决 (2026-09-10) — ⑭b to_dict() 收紧范围:
  * 明确 birth_datetime 的处理 (当前: 不序列化)
  * 明确 day_master_element 是派生输出, 不是 Canonical 字段
  * 不要求为"字段数量完全对称"重构整个 to_dict()
  * 真正需要冻结的是 CanonicalBaziChart → 下游 Engine Adapter 边界
    (已锁在 test_canonical_bazi_contract.py)

本测试只把 to_dict() 的当前契约行为锁死, 防止回归:
  1. to_dict() 是 BaziChart 内部 debug/日志 dict, 非下游 Canonical 接口
  2. birth_datetime 当前不在 to_dict (下游高精度起运走 CanonicalBaziChart, 它保留)
  3. day_master_element 是 to_dict 动态注入的派生 key, 非 dataclass 字段
  4. 四柱/大运嵌套展开正确
"""

from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datetime import datetime
from zoneinfo import ZoneInfo

from tongshu.engines.bazi_engine import BaziEngine, BaziChart


def _make_chart():
    engine = BaziEngine()
    bd = datetime(1983, 11, 3, 12, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    chart = engine.compute((1983, 11, 3, 12), gender="male", birth_datetime=bd)
    return chart, bd


class TestToDictContract(unittest.TestCase):
    """to_dict() 当前契约行为的锁定 (非 1:1, 仅防止回归漂移)."""

    def test_to_dict_is_not_downstream_canonical_interface(self):
        """to_dict() 是内部 debug dict — 下游权威消费走 CanonicalBaziChart.

        锁定: CanonicalBaziChart 保留 birth_datetime, 而 BaziChart.to_dict() 当前不保留.
        这是已知的、被接受的契约差异 (不是 bug), 本测试防止未来有人
        "顺手让 to_dict 1:1 对称" 时误以为该改 Canonical 面.
        """
        chart, bd = _make_chart()
        from tongshu.models.canonical_bazi import CanonicalBaziChart
        canonical = CanonicalBaziChart.from_bazi_chart(chart)
        self.assertIsNotNone(canonical.birth_datetime, "Canonical 必须保留 birth_datetime")
        # to_dict 当前契约: birth_datetime 不序列化
        self.assertNotIn("birth_datetime", chart.to_dict())

    def test_day_master_element_is_derived_not_field(self):
        """day_master_element 是 to_dict 动态注入的派生 key.

        它不是 BaziChart dataclass 字段, 而是 to_dict 里
        STEM_ELEMENT[day_master] 的展开. 锁定这一事实.
        """
        chart, _ = _make_chart()
        dc_fields = {f.name for f in dataclasses.fields(BaziChart)}
        d = chart.to_dict()
        self.assertIn("day_master_element", d)
        self.assertNotIn("day_master_element", dc_fields,
                         "day_master_element 是派生 key, 非 dataclass 字段")
        # 派生值与 day_master 五行一致
        from tongshu.facts.bazi_facts import STEM_ELEMENT
        self.assertEqual(d["day_master_element"], STEM_ELEMENT[chart.day_master])

    def test_pillars_nested_expanded(self):
        """四柱 + 大运在 to_dict 里是展开的 dict (非 Pillar 对象)."""
        chart, _ = _make_chart()
        d = chart.to_dict()
        self.assertIsInstance(d["year_pillar"], dict)
        self.assertIn("heavenly_stem", d["year_pillar"])
        self.assertIn("earthly_branch", d["year_pillar"])
        for lp in d["luck_pillars"]:
            self.assertIsInstance(lp, dict)
            self.assertIn("heavenly_stem", lp)

    def test_to_dict_deterministic(self):
        """同输入两次 to_dict 完全一致 (可日志/可对比)."""
        engine = BaziEngine()
        bd = datetime(1983, 11, 3, 12, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        d1 = engine.compute((1983, 11, 3, 12), gender="male", birth_datetime=bd).to_dict()
        d2 = engine.compute((1983, 11, 3, 12), gender="male", birth_datetime=bd).to_dict()
        self.assertEqual(d1, d2)

    def test_core_facts_in_to_dict(self):
        """to_dict 必须含核心八字事实 (四柱/日主/性别/起运岁/大运)."""
        chart, _ = _make_chart()
        d = chart.to_dict()
        for key in [
            "year_pillar", "month_pillar", "day_pillar", "hour_pillar",
            "day_master", "gender", "start_age", "luck_pillars",
        ]:
            self.assertIn(key, d, f"to_dict 缺核心字段 {key}")


if __name__ == "__main__":
    unittest.main()
