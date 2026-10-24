# -*- coding: utf-8 -*-
"""平台 17 类**候选证据**守卫（2026-10-24 新增）。

纪律
----
河洛侧**只**给 L5 事件类型的**候选证据**；**L1/L2 与 L5 的最终裁定属平台**，
河洛不得臆造跨引擎语义、**不得自定方向**。

⇒ 本守卫钉死：
  1. 镜像的 17 类本体与**域分布**必须与平台一致（4/5/5/3）；
  2. 每条候选必须带：平台默认方向、**河洛侧有据方向**、证据条目、判据出处；
  3. 河洛侧方向**判不出就 UNKNOWN** —— 不给「看起来有结果」的猜测；
  4. 强度**不得**是 0–1 分数（原典只给吉凶不给数值）；
  5. 「无候选」必须被**显式报出**（能力缺口可见，不得静默）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine.adapter import HeluoAdapter  # noqa: E402
from heluo_engine.engines.heluo.dimensions import (  # noqa: E402
    DIM_TO_EVENT, EVENT_TYPES, heluo_direction,
)

VALID_DIRECTIONS = {"POSITIVE", "NEGATIVE", "CHANGE", "NEUTRAL", "UNKNOWN"}

#: 河洛判词层**当前未产出**候选证据的平台事件类型（能力缺口，逐条钉死）
#:
#: 逐条理由（改动此处须同时更新理由）：
#:   EXAM           —— 河洛无「考试」判据（学历类断语无对应爻象依据）
#:   GRADUATION    —— 同上（「毕业」无独立原典判据；DEGREE 已覆盖学位）
#:   JOB_CHANGE    —— 河洛判的是「官禄/位阶」，**不区分**换不换岗（方向亦随卦变）
#:   RESIGNATION   —— 同上（「去官/离职」无独立原典判据）
#:   DEMOTION      —— 同上（「降职」无独立原典判据）
#:   FAMILY_HARMONY—— 河洛有「琴瑟不和」（→DIVORCE），但**无**「和谐」的正向判据
#:   LEGAL_ISSUE   —— 河洛判词层**无**官非/诉讼类判据（三刑六列原典有载、引擎未实现）
KNOWN_GAPS = {
    "EXAM", "GRADUATION", "JOB_CHANGE", "RESIGNATION", "DEMOTION",
    "FAMILY_HARMONY", "LEGAL_ISSUE",
}


class TestEventOntologyMirror:
    """镜像表本身。"""

    def test_seventeen_types_with_platform_domain_distribution(self):
        assert len(EVENT_TYPES) == 17, f"平台 17 类，实测 {len(EVENT_TYPES)}"
        dist = {}
        for v in EVENT_TYPES.values():
            dist[v["domain"]] = dist.get(v["domain"], 0) + 1
        assert dist == {"EDUCATION": 4, "CAREER": 5, "FAMILY": 5,
                        "LIFE_EVENT": 3}, f"域分布与平台不一致：{dist}"

    def test_default_directions_valid(self):
        for eid, v in EVENT_TYPES.items():
            assert v["default_direction"] in VALID_DIRECTIONS, (
                f"{eid} 的默认方向非法：{v['default_direction']}")

    def test_dim_to_event_targets_are_known_types(self):
        bad = {d: e for d, es in DIM_TO_EVENT.items()
               for e in es if e not in EVENT_TYPES and e != "ALL"}
        assert not bad, f"维度映射到了不存在的平台事件类型：{bad}"

    def test_every_event_type_is_reachable_or_declared_gap(self):
        """每类要么有维度映射，要么在**钉死的缺口清单**里。

        ⚠ 缺口清单**逐条钉死**（不是阈值）—— 覆盖变化必须是刻意的：
        新增一类候选 ⇒ 改这张清单；少一类 ⇒ 说明能力回退，也必须改。
        """
        mapped = {e for es in DIM_TO_EVENT.values() for e in es} - {"ALL"}
        gap = set(EVENT_TYPES) - mapped
        assert gap == KNOWN_GAPS, (
            "平台事件类型的候选覆盖变了 —— 缺口清单须同步更新：\n"
            f"  现在无候选：{sorted(gap)}\n"
            f"  清单声明：{sorted(KNOWN_GAPS)}")


class TestHeluoDirectionIsGrounded:
    """河洛侧方向必须**有据**，判不出就 UNKNOWN。"""

    def test_unknown_when_no_guajie(self):
        d, basis = heluo_direction({})
        assert d == "UNKNOWN"
        assert basis

    def test_positive_from_yuan_qi(self):
        d, basis = heluo_direction({"yuan_qi_hit": True})
        assert d == "POSITIVE"
        assert "元气" in basis

    def test_negative_from_shu_xiong(self):
        d, basis = heluo_direction({"shu_xiong": {"shu_xiong": True}})
        assert d == "NEGATIVE"
        assert "数凶" in basis

    def test_si_duan_gives_no_definite_direction(self):
        """死断是**条件式**立断（阴骘两支并陈）⇒ 不得给出确定方向。"""
        d, basis = heluo_direction({"si_duan": ["…到此必死…"]})
        assert d == "UNKNOWN"
        assert "条件式" in basis

    def test_conflicting_judgements_give_unknown(self):
        d, basis = heluo_direction({"yuan_qi_hit": True,
                                    "shu_xiong": {"shu_xiong": True}})
        assert d == "UNKNOWN"
        assert "相冲" in basis


class TestEventCandidatesOutput:
    """引擎实际产出的候选块。"""

    @pytest.fixture(scope="class")
    def out(self):
        r = HeluoAdapter().compute((1975, 11, 22, 1), gender="male",
                                   target_date="2026-10-23")
        return r.interpretation

    def test_block_present(self, out):
        ec = out.get("event_candidates")
        assert ec, "解读层未产出 event_candidates"
        for key in ("candidates", "coverage", "heluo_direction"):
            assert key in ec, f"event_candidates 缺 {key}"

    def test_candidates_carry_grounded_fields(self, out):
        cands = out["event_candidates"]["candidates"]
        assert cands, "未产出任何事件候选"
        for et, c in cands.items():
            assert c["event_type"] == et
            assert c["platform_default_direction"] in VALID_DIRECTIONS
            assert c["heluo_direction"] in VALID_DIRECTIONS
            assert c["heluo_direction_basis"], f"{et} 缺方向依据"
            assert c["dimensions"], f"{et} 缺维度来源"
            assert c["items"], f"{et} 缺证据条目"
            assert "分数" in c["strength_note"], f"{et} 的强度说明未声明不给分数"

    def test_no_numeric_strength(self, out):
        """候选里**不得**出现 0–1 强度分数（原典只给吉凶不给数值）。"""
        blob = repr(out["event_candidates"])
        assert not re.search(r'"strength"\s*:\s*0?\.\d+', blob), (
            "事件候选里出现了浮点强度分数（原典只给吉凶不给数值）")

    def test_coverage_reports_gaps(self, out):
        cov = out["event_candidates"]["coverage"]
        assert cov["event_types_total"] == 17
        assert "event_types_without_candidate" in cov
        assert "能力缺口" in cov["note"]


def test_candidate_event_types_are_subset_of_platform():
    """候选的事件类型**必须**是平台 17 类之内的（河洛不得自造事件类型）。"""
    for es in DIM_TO_EVENT.values():
        for e in es:
            assert e in EVENT_TYPES or e == "ALL", f"自造事件类型：{e}"
