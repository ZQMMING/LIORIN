# -*- coding: utf-8 -*-
"""Z29: 夹宫/身前三奇断言（《秘传紫微·骨髓赋问答》原著）测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.interpretation import NihaiAssertionResolver


def _chart():
    engine = ZiweiEngine()
    return engine.full_chart((1983, 9, 29), 11, "male")


class TestJiaSanqi:
    def test_no_false_positive_1983(self):
        """1983：羊陀不夹命/身（羊在子女、陀在疾厄），身前三奇不中 → 0 条不误报"""
        entries = NihaiAssertionResolver().resolve(_chart())
        jia = [e for e in entries if e.category == "夹宫论断"]
        assert jia == []

    def test_yangtuo_positions(self):
        """1983 羊陀位置：擎羊在子女(丑)、陀罗在疾厄(亥)"""
        chart = _chart()
        pos = {}
        for name, pd in chart.palaces.items():
            for s in pd.get("minor", []):
                if s in ("擎羊", "陀罗"):
                    pos[s] = name
        assert pos.get("擎羊") == "子女"
        assert pos.get("陀罗") == "疾厄"

    def test_resolve_method_exists(self):
        """夹宫/三奇方法可调用（返回 list）"""
        r = NihaiAssertionResolver()
        out = r._resolve_jia_sanqi_assertions(_chart())
        assert isinstance(out, list)
