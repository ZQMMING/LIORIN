# -*- coding: utf-8 -*-
"""叶/不叶在生月未知时必须「不判」，不得落到「不叶凶象」（D-016）。

原典（河洛真数·卦头）：叶/不叶的判据是「生月得时」+「年干支在纳甲」，
生月是必要前提。旧实现以 birth_month=0 直接比较卦气月，必然得出
「生月0月 ≠ 卦气月 → 不叶（凶象）」，属无中生有。
"""

from __future__ import annotations

from tongshu.engines.heluo.guajie import judge_ye_buye


def test_unknown_birth_month_is_not_judged():
    r = judge_ye_buye("乾", 0, "甲子")
    assert r is not None
    assert r.judged is False
    assert r.ye is False
    assert r.buye is False
    assert any("不判" in e for e in r.evidence)
    assert any("生月未知" in e for e in r.evidence)


def test_unknown_birth_month_does_not_use_negative_month_compare():
    """不得出现「生月0月 ≠ 卦气月」这类越界比较。"""
    r = judge_ye_buye("乾", 0, "甲子")
    assert all("生月0月 ≠" not in e for e in r.evidence)


def test_known_month_still_judges():
    r = judge_ye_buye("乾", 4, "甲子")
    assert r is not None and r.judged is True
    assert r.ye is True  # 乾卦气属四月 + 甲子在本命纳甲
    assert r.najia_hit is True
