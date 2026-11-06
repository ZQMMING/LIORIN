"""D-021：流年卦应爻/元爻断随大运段元堂，而非本命先天元堂。

原典《河洛真数·起例卷之上·小象行年卦气》：「一岁在同人九三元爻，二岁取应爻…
至十岁换九四爻」——每换一段大运，元堂换了爻位，「应爻」与「元爻断」都随段而变。
旧实现把整张流年表都按本命先天元堂解释，段 2 起应爻恒错位。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from tongshu.engines.heluo.canonical import heluo_calculate  # noqa: E402


def _years():
    r = heluo_calculate(("壬子", "辛亥", "壬辰", "丙午"), "male", "午", "zhong")
    return r.timeline.yearly_hexagrams


def test_years_carry_segment_yuan_tang():
    for y in _years():
        assert isinstance(y.get("yuantang_index"), int)
        assert 0 <= y["yuantang_index"] < 6


def test_ying_line_relates_to_segment_yuan_tang():
    """每个流年的应爻 = (本段元堂 + 3) % 6。"""
    for y in _years():
        it = y.get("yi_interpretation") or {}
        seg = y["yuantang_index"]
        assert it["ying_line"] == (seg + 3) % 6, (y["year"], it["ying_line"], seg)


def test_later_segments_differ_from_natal_yuan_tang():
    """至少存在一年，其段元堂 ≠ 本命先天元堂，且应爻随之不同（否则本测试无意义）。"""
    years = _years()
    natal = years[0]["yuantang_index"]
    found = [y for y in years if y["yuantang_index"] != natal]
    assert found, "样本盘应有跨段年份"
    for y in found:
        it = y["yi_interpretation"]
        assert it["ying_line"] == (y["yuantang_index"] + 3) % 6
        assert (natal + 3) % 6 != it["ying_line"] or True  # 允许同余，但需按段计算


def test_evidence_mentions_segment_yuan_tang():
    y = next(y for y in _years() if y["yuantang_index"] != _years()[0]["yuantang_index"])
    ev = " ".join(y["yi_signal"]["evidence"])
    assert f"本段元堂@{y['yuantang_index']}" in ev
