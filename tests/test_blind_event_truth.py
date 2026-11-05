"""盲派应期层真值测试（原书案例资料集明文「某年发生某事」）."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

CASES = json.loads(
    (REPO / "cases" / "truth" / "blind_event_cases.json").read_text(encoding="utf-8")
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_event_case(case):
    from tongshu.engines.bazi_engine import BaziEngine
    from tongshu.engines.blind_yingqi import BlindYingqiEngine

    yq = BlindYingqiEngine(BaziEngine())
    y, m, d, h = case["solar"]
    chart = yq.bazi_engine.compute((y, m, d, h), gender=case["gender"])
    pillars = chart.get_pillars_chinese()
    assert " ".join(pillars[k] for k in ("year", "month", "day", "hour")) == case["pillars"]

    result = yq.analyze((y, m, d, h), case["gender"], target_year=case["event_year"])
    exp = case["expected"]
    hits = [
        e for e in result.yingqi_events
        if e.get("year") == case["event_year"]
        and e.get("domain") == exp["domain"]
        and e.get("direction") == exp["direction"]
        and (not exp.get("event_topic") or e.get("event_topic") == exp["event_topic"])
    ]
    assert hits, (
        f"{case['case_id']} 未命中: {case['event_year']}年 期望 {exp}；实际事件="
        f"{[(e.get('domain'), e.get('event_topic'), e.get('direction'), e.get('mechanism')) for e in result.yingqi_events if e.get('year') == case['event_year']]}"
    )
    if case.get("expected_nominal_age") is not None:
        assert result.nominal_age == case["expected_nominal_age"]
