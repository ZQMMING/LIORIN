"""流时卦接线回归（D-020）：流日链式累积后，六段都必须挂上流时卦。

D-015 把流日卦改为链式累积（段 k 与月卦相差 k+1 爻），而 canonical 旧的流时接线
用「段与月卦单爻差」找值日爻，导致第 2 段起 diffs 长度 >1 而静默跳过流时卦。
改为直接用段内 flip_index（本段所变之位=值日爻）。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from tongshu.engines.heluo.canonical import heluo_calculate  # noqa: E402
from tongshu.engines.heluo.timeline_yun import (  # noqa: E402
    compute_liuri,
    compute_liushi,
)

PILLARS = ("壬子", "辛亥", "壬辰", "丙午")


def _first_month_days():
    r = heluo_calculate(PILLARS, "male", "午", "zhong")
    year = r.timeline.yearly_hexagrams[0]
    assert year["months"], "流月卦不应为空"
    return year["months"][0]


def test_all_six_day_segments_have_hours():
    month = _first_month_days()
    days = month["days"]
    assert len(days) == 6
    for d in days:
        hours = d.get("hours")
        assert hours, f"第 {d['segment']} 段缺流时卦（D-020 回归）"
        assert len(hours) == 12


def test_hours_follow_segment_flip_index():
    """流时卦以值日卦为本、值日爻=该段 flip_index，子时应起于其后一位。"""
    month = _first_month_days()
    for d in month["days"]:
        hours = d["hours"]
        first = hours[0]
        assert first["hour"] == 1, "首条应为子时（hour 以 1=子 编列）"
        # 子时（进数）应变为值日爻的下一位
        expect = (d["flip_index"] + 1) % 6
        assert first["shi_yao_index"] == expect
        changed = [i for i in range(6)
                   if first["lines"][i] != d["lines"][i]]
        assert changed == [expect], (d["segment"], changed, expect)


def test_compute_liushi_matches_manual_for_segment_six():
    month = _first_month_days()
    last = month["days"][-1]
    manual = compute_liushi(last["lines"], last["flip_index"])
    assert [h["name"] for h in manual.hours] == [h["name"] for h in last["hours"]]
