"""QTBJ 穷通调候派生测试（《窮通寶鑑》· 引擎自有 Derived Facts，§65）。

覆盖：
- 单月规则：甲木正月「先用丙癸」（原文 QTBJ-003-002）
- 合论月规则：己土巳午未「取癸為要，次用丙火」（原文 QTBJ-058-001）
- 三冬丁火「甲木為尊，庚金佐之」（原文 QTBJ-046-001，亥子丑合论）
- 无此组合 → 空 dict（不臆造）
- 缺参 → FAIL_CLOSED
"""

from __future__ import annotations

import pytest

from shared_types.fail_closed import FailClosedError, FailClosedReason
from engines.qiongtong_baojian.calculation.medicine import (
    _load_index, derive_medicine,
)


def test_matrix_index_loaded():
    idx = _load_index()
    # 10 干 × 12 月全覆盖（合论月为 in 列表）
    assert len(idx) >= 109


def test_single_month_jiayin():
    out = derive_medicine("甲", "寅")
    assert out["local_requirement"] == "先用丙癸（得丙癸透，無丙癸平常人）"
    assert out["local_requirement_rule"].startswith("CAND-QTBJ-")


def test_merged_summer_ji_branch():
    """三夏己土合论：巳午未同用「取癸為要，次用丙火」（QTBJ-058-001）。"""
    for mb in ("巳", "午", "未"):
        out = derive_medicine("己", mb)
        assert out["local_requirement"] == "取癸為要，次用丙火", mb


def test_merged_winter_ding_branch():
    """三冬丁火合论：亥子丑「甲木為尊，庚金佐之」（QTBJ-046-001）。"""
    for mb in ("亥", "子", "丑"):
        out = derive_medicine("丁", mb)
        assert "甲木為尊" in out["local_requirement"], mb


def test_known_rule_sample_richness():
    """抽样原文关键句（正二月戊土、三秋己土）。"""
    assert "丙" in derive_medicine("戊", "寅")["local_requirement"]
    assert "癸" in derive_medicine("戊", "卯")["local_requirement"]
    assert "癸" in derive_medicine("己", "申")["local_requirement"]


def test_missing_combination_empty():
    """原书无组合（矩阵外）→ 不产出。"""
    # 构造不在索引内的日干（非法会 FAIL_CLOSED；这里测合法但无记录的场景）
    idx = _load_index()
    covered = set()
    for (ds, months) in idx:
        for mb in months:
            covered.add((ds, mb))
    import itertools
    allc = set(itertools.product("甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"))
    missing = allc - covered
    if missing:
        ds, mb = sorted(missing)[0]
        assert derive_medicine(ds, mb) == {}


def test_fail_closed_on_missing_args():
    with pytest.raises(FailClosedError) as ei:
        derive_medicine(None, "寅")
    assert ei.value.reason == FailClosedReason.INPUT_FORBIDDEN
    with pytest.raises(FailClosedError) as ei:
        derive_medicine("甲", None)
    assert ei.value.reason == FailClosedReason.INPUT_FORBIDDEN
