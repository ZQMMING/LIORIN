# -*- coding: utf-8 -*-
"""Z80-H/W1 经典细则层（classical_detail）回归。

验收点：
1. 九出口形状 + 计数自洽；
2. `_PATTERN_SPEC` 与 pattern_rules.ALL_PATTERNS 1:1（无缺项、无孤儿）；
3. 假命中防护：未实现判据（空亡/反背/运限）不产出 hit；含星曜组合的
   PF/PD 条文只作参考条文（hit=False）；
4. 真值：1990-03-01 午时男 命宫戌 → PF-11/PD-08 条文命中 + NOB-19/20/21 格局命中；
5. 女命盘 nvming 出口有定义、男命盘空置；
6. 运限事实与 temporal_facts.py 口径一致（2026 丙午）。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.ziwei.rules.classical_detail import (  # noqa: E402
    _PATTERN_SPEC,
    build_classical_detail,
)
from tongshu.engines.ziwei.rules.pattern_rules import (  # noqa: E402
    ALL_PATTERNS,
    PALACE_DEPRIVATION_RULE,
    PALACE_FORTUNE_RULE,
)
from tongshu.engines.ziwei.rules.temporal_facts import (  # noqa: E402
    small_limit_branch,
    taisui_branch,
)
from tongshu.engines.ziwei_engine import ZiweiEngine  # noqa: E402

NINE_KEYS = (
    "palace_jue",
    "classical_patterns",
    "nvming",
    "child_limit",
    "limit_advanced",
    "temporal_rules",
    "aux_verdicts",
    "temporal_facts",
    "summary",
)


def _engine() -> ZiweiEngine:
    return ZiweiEngine(node_modules_dir=Path("__no_iztro__"), backend="native")


def _male_chart():
    return _engine().full_chart((1990, 3, 1), 12, "male", flow_year=2026)


def _female_chart():
    return _engine().full_chart((1990, 2, 5), 5, "female")


def test_nine_keys_present_and_summary_consistent():
    detail = build_classical_detail(_male_chart())
    for key in NINE_KEYS:
        assert key in detail, key
    summary = detail["summary"]
    assert summary["palace_jue"] == len(detail["palace_jue"])
    assert summary["classical_patterns"] == len(detail["classical_patterns"])
    assert summary["nvming"] == len(detail["nvming"])
    assert summary["temporal_rules"] == len(detail["temporal_rules"])
    assert summary["aux_verdicts"] == len(detail["aux_verdicts"])
    assert summary["data_issues"], "未实现判据必须显式登记"


def test_pattern_spec_is_one_to_one_with_mother_table():
    rules = ALL_PATTERNS.values() if isinstance(ALL_PATTERNS, dict) else ALL_PATTERNS
    ids = {r.get("pattern_id") for r in rules}
    assert set(_PATTERN_SPEC) == ids
    for pid, spec in _PATTERN_SPEC.items():
        assert spec["all"] or spec["any"], f"{pid} 无任何谓词"


def test_no_fake_hit_on_unimplemented_judges():
    detail = build_classical_detail(_male_chart())
    unevaluated = {e["pattern_id"] for e in detail["summary"]["unevaluated"]}
    hits = {p["pattern_id"] for p in detail["classical_patterns"]}
    expected = {"POV-01", "POV-02", "POV-03", "POV-04"}
    expected |= {f"MISC-0{i}" for i in range(1, 9)}
    assert unevaluated == expected
    assert not (unevaluated & hits)
    for entry in detail["summary"]["unevaluated"]:
        assert entry["reason"]


def test_jue_entries_are_reference_only():
    detail = build_classical_detail(_male_chart())
    assert detail["palace_jue"], "命宫戌应有 PF-11 / PD-08 条文"
    assert {e["rule_id"] for e in detail["palace_jue"]} == {"PF-11", "PD-08"}
    for entry in detail["palace_jue"]:
        assert entry["evaluated"] is False
        assert entry["hit"] is False
        assert entry["reason"]
        verbatim = entry["verbatim"]
        assert verbatim in {r["verbatim"] for r in PALACE_FORTUNE_RULE + PALACE_DEPRIVATION_RULE}


def test_known_chart_hits_structured_patterns():
    chart = _male_chart()
    assert chart.soul_earthly_branch == "戌"
    detail = build_classical_detail(chart)
    hits = {p["pattern_id"] for p in detail["classical_patterns"]}
    assert {"NOB-19", "NOB-20", "NOB-21"} <= hits
    # 日月不夹命（命宫戌 两邻 酉空宫 / 亥太阴），不得命中 NOB-01
    assert "NOB-01" not in hits
    for entry in detail["classical_patterns"]:
        assert entry["hit"] is True
        assert entry["evidence"], f"{entry['pattern_id']} 命中必须带证据"


def test_nvming_female_only():
    female = build_classical_detail(_female_chart())
    assert female["nvming"], "女命盘应产出女命条文"
    assert len(female["nvming_definitions"]) == 6
    assert female["nvming_note"] == ""
    for entry in female["nvming"]:
        assert entry["evidence"]

    male = build_classical_detail(_male_chart())
    assert male["nvming"] == []
    assert male["nvming_note"] == "男命盘，本出口空置"


def test_temporal_facts_match_temporal_module():
    detail = build_classical_detail(_male_chart())
    facts = detail["temporal_facts"]
    assert facts["flow_year"] == 2026
    assert facts["nominal_age"] == 37
    assert facts["taisui_branch"] == taisui_branch(2026) == "午"
    assert facts["birth_year_branch"] == "午"
    assert facts["small_limit_branch"] == small_limit_branch("午", "男", 37)
    assert facts["flow_year_stem"] == "丙"
    # 丙年：流禄在巳、流羊在午、流陀在辰
    assert (facts["flow_lu"], facts["flow_yang"], facts["flow_tuo"]) == ("巳", "午", "辰")
    assert facts["taisui_palace"] == detail["temporal_rules"][0]["palace_name"]


def test_child_limit_after_first_limit_is_not_applied():
    detail = build_classical_detail(_male_chart())
    fact = detail["child_limit"][-1]["computed"]
    assert fact["evaluated"] is False
    assert "起限岁数" in fact["reason"]


def test_empty_chart_returns_same_shape():
    class _Empty:
        palaces = {}
        soul_earthly_branch = ""

    detail = build_classical_detail(_Empty())
    for key in NINE_KEYS:
        assert key in detail
    assert detail["classical_patterns"] == []
    assert detail["summary"]["classical_patterns"] == 0
