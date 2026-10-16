# -*- coding: utf-8 -*-
"""Z28: 身宫论断（《秘传紫微·骨髓赋问答》原著）测试"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.interpretation import NihaiAssertionResolver


def _chart():
    engine = ZiweiEngine()
    return engine.full_chart((1983, 9, 29), 11, "male")


class TestShenGong:
    def test_shengong_assertions_present(self):
        """1983 案例：身宫论断 ≥3 条"""
        entries = NihaiAssertionResolver().resolve(_chart())
        sg = [e for e in entries if e.category == "身宫论断"]
        assert len(sg) >= 3

    def test_shengong_total_rule(self):
        """身宫关贵贱总论（骨髓赋问答原著）"""
        entries = NihaiAssertionResolver().resolve(_chart())
        sg = [e for e in entries if e.category == "身宫论断"]
        assert any("身宫关贵贱" in e.text for e in sg)

    def test_shengong_priority_rule(self):
        """身命为先，福德为次"""
        entries = NihaiAssertionResolver().resolve(_chart())
        sg = [e for e in entries if e.category == "身宫论断"]
        assert any("身命为先" in e.text for e in sg)

    def test_shengong_star_hint(self):
        """身宫之星曜（七杀）主后天发展重点"""
        entries = NihaiAssertionResolver().resolve(_chart())
        sg = [e for e in entries if e.category == "身宫论断"]
        assert any("七杀" in e.text for e in sg)

    def test_shengong_source(self):
        """出处为《秘传紫微·骨髓赋问答》"""
        entries = NihaiAssertionResolver().resolve(_chart())
        sg = [e for e in entries if e.category == "身宫论断"]
        assert all("骨髓赋" in e.source for e in sg)

    def test_shen_name_located(self):
        """1983 身宫=命宫（辰）"""
        chart = _chart()
        soul_br = chart.soul_earthly_branch
        shen = [n for n, pd in chart.palaces.items() if pd.get("branch") == soul_br]
        assert shen == ["命宫"]


class TestGenderNvmingJue:
    """Z54: 女命诀 gender 过滤（星曜坐身宫诀：紫微/天府仅女命触发）"""

    def _resolve_sg(self, gender):
        engine = ZiweiEngine()
        chart = engine.full_chart((1983, 9, 29), 11, gender)
        entries = NihaiAssertionResolver().resolve(chart)
        return [e for e in entries if e.source == "《紫微斗数全书》星曜诀"]

    def test_male_no_nvming_jue(self):
        """男命：紫微/天府女命诀不触发（1983 案例身宫无紫微天府 → 0 条）"""
        sg = self._resolve_sg("male")
        assert all(e.star not in ("紫微", "天府") for e in sg)

    def test_female_chart_has_gender(self):
        """女命盘 chart.gender == female（字段已补）"""
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "female")
        assert chart.gender == "female"
        assert chart.to_dict()["gender"] == "female"

    def test_roundtrip_gender(self):
        """to_dict/from_dict roundtrip 保留 gender"""
        chart = ZiweiEngine().full_chart((1983, 9, 29), 11, "female")
        c2 = chart.from_dict(chart.to_dict())
        assert c2.gender == "female"
