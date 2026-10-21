#!/usr/bin/env python3
"""Unit tests for Heluo context extraction and rule matching."""
import sys
sys.path.insert(0, "src")

from tongshu.engines.heluo.canonical import HeluoCanonical
from tongshu.reasoning.signal_engine import extract_heluo_context, build_rule_context
from tongshu.reasoning.matcher import RuleMatcher
from pathlib import Path


def test_extract_heluo_fields():
    """Test that extract_heluo_context returns all expected fields."""
    canonical = HeluoCanonical()
    # 许家印八字
    bazi_cn = [("戊", "戌"), ("壬", "戌"), ("己", "未"), ("乙", "亥")]
    result = canonical.calculate(bazi=bazi_cn, gender="male", birth_hour="亥", era="zhong")

    # Mock bazi with month_pillar (戌月)
    class MockPillar:
        def __init__(self, branch):
            self.earthly_branch = branch
    class MockBazi:
        def __init__(self):
            self.month_pillar = MockPillar("XU")
            self.five_element_balance = {"WOOD": 0.1, "FIRE": 0.1, "EARTH": 0.5, "METAL": 0.2, "WATER": 0.1}
    mock_bazi = MockBazi()

    fields = extract_heluo_context(result, mock_bazi)
    print("Extracted fields:")
    for k, v in sorted(fields.items()):
        print(f"  {k} = {v}")

    # 验证关键字段存在
    assert "heluo_benming_guawuxing" in fields, "缺少本命卦五行"
    assert "heluo_wuxing_imbalance" in fields, "缺少五行失衡"
    assert "heluo_dishu_youyu" in fields, "缺少地数有余"
    assert "heluo_birth_season_unfavorable" in fields, "缺少不利时节"
    assert "heluo_benming_gong" in fields, "缺少本命卦宫位"
    assert "heluo_benming_guaming" in fields, "缺少本命卦名"
    assert "heluo_yuantang" in fields, "缺少元堂爻"
    assert "heluo_yuantang_index" in fields, "缺少元堂爻位"
    assert "heluo_houtian_guaming" in fields, "缺少后天卦名"

    # 验证值合理
    assert fields["heluo_benming_guawuxing"] in ("金", "木", "水", "火", "土")
    assert fields["heluo_wuxing_imbalance"] in ("over", "under", "none")
    assert isinstance(fields["heluo_dishu_youyu"], bool)
    assert isinstance(fields["heluo_birth_season_unfavorable"], bool)
    assert fields["heluo_yuantang_index"] in range(6)
    print("\n✅ All field assertions passed")


def test_heluo_rules_load():
    """Test that HL rule files are valid JSON and reference known fields."""
    import json, glob
    rules = []
    for f in sorted(glob.glob("data/rules/HL-*.json")):
        with open(f, encoding="utf-8") as fh:
            r = json.load(fh)
        rules.append(r)
    assert len(rules) >= 21, f"Expected >=21 HL rules, got {len(rules)}"
    # Verify all condition fields are in FIELD_SPECS
    from tongshu.reasoning.matcher import FIELD_SPECS
    for r in rules:
        for cond in r["conditions"].get("all", []):
            field = cond.get("field")
            assert field in FIELD_SPECS, f"{r['rule_id']}: unknown field '{field}'"
    print(f"\n✅ {len(rules)} HL rules validated, all fields in FIELD_SPECS")


def test_timeline_structure():
    """Test that timeline produces yearly/monthly/daily hexagrams."""
    canonical = HeluoCanonical()
    bazi_cn = [("戊", "戌"), ("壬", "戌"), ("己", "未"), ("乙", "亥")]
    result = canonical.calculate(bazi=bazi_cn, gender="male", birth_hour="亥", era="zhong")

    assert result.timeline is not None, "timeline should not be None"
    yearly = result.timeline.yearly_hexagrams
    assert len(yearly) > 0, "should have yearly hexagrams"

    first_year = yearly[0]
    print(f"\nFirst year: age={first_year['age']}, year={first_year['year']}, hexagram={first_year['hexagram']}")
    assert "hexagram" in first_year
    assert "months" in first_year
    assert len(first_year["months"]) == 12, "should have 12 months"

    first_month = first_year["months"][0]
    print(f"First month: month={first_month['month']}, name={first_month['name']}")
    assert "days" in first_month
    assert len(first_month["days"]) == 6, "should have 6 day segments（《河洛真数》起日卦例：六爻俱变毕，则满三十日）"

    # yi_signal should be present
    assert "yi_signal" in first_year, "should have yi_signal"
    yi = first_year["yi_signal"]
    print(f"yi_signal: hexagram={yi['hexagram']}, confidence={yi['confidence']:.2f}")
    assert "evidence" in yi
    assert len(yi["evidence"]) > 0
    print("✅ Timeline structure verified")


if __name__ == "__main__":
    test_extract_heluo_fields()
    test_heluo_rules_load()
    test_timeline_structure()
    print("\n" + "=" * 50)
    print("ALL HELUO TESTS PASSED ✅")
