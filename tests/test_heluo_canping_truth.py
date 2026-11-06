# -*- coding: utf-8 -*-
"""河洛·卷十参评层（金锁银匙歌）原典起数真值。

真值来源：诗断秘诀卷 / 参评数转录（data/heluo/canping/raw_shici_*.json 与
data/heluo/算法原文对照核证表.md 所记原文数字），不是引擎自证。

原典三例（canping.py docstring 逐字记录）：
  1. 戌日寅时，乙卯（纳音水）顺数：2000+500+14+27+1 = 2542（原文"二千五百四十二"）
  2. 戌日寅时逆数（乙卯水）：2000+900+14+27+1 = 2942（原文"二千九百四十二"）
  3. 申日申时，戊午（纳音火）：2000+1300+18+27+2 = 3347（原文"三千三百四十七"）
"""
from __future__ import annotations

import pytest

from tongshu.engines.heluo import canping


@pytest.mark.parametrize(
    "day_zhi,hour_zhi,element,direction,expected",
    [
        ("戌", "寅", "水", "顺", 2542),
        ("戌", "寅", "水", "逆", 2942),
        ("申", "申", "火", "顺", 3347),
    ],
)
def test_qishu_original_text_numbers(day_zhi, hour_zhi, element, direction, expected):
    got = canping.qishu(day_zhi, hour_zhi, element, direction)
    assert got["total"] == expected, got


def test_qishu_steps_are_explainable():
    """起数必须给出可复核的四段步骤（千/百/十/零 位各一段）。"""
    got = canping.qishu("戌", "寅", "水", "顺")
    assert len(got["steps"]) == 5
    joined = " | ".join(got["steps"])
    assert "二千" in joined and "百" in joined and "零" in joined


def test_poem_lookup_original_lines():
    """原典诗断三例首句必须能在参评库中按行定位（页码/列位与转录记录一致）。"""
    expect = {
        "掌中秋月扇": (29, "丑酉"),
        "玉壺無別物": (34, "辰宾"),
        "道是無形光": (53, "未未"),
    }
    for line, (page, col) in expect.items():
        hits = canping.search_raw_poem(line)
        assert hits, f"未定位到诗断行：{line}"
        assert any(h[0] == page and h[1] == col for h in hits), (line, hits[:3])


def test_canping_raw_data_is_loaded():
    rows = canping.load_raw_shici_jintu()
    assert len(rows) >= 100
    for r in rows[:5]:
        assert isinstance(r["page"], int)
        assert isinstance(r["lines"], list) and r["lines"]
