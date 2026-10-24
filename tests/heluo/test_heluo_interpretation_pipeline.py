# -*- coding: utf-8 -*-
"""解读层**接线**守卫（2026-10-24 新增）。

背景
----
解读层六模块（``interpretation`` / ``guidance`` / ``diagnosis_rule_graph`` /
``metrics_v2`` / ``hexagram_state`` / ``canonical_signals``）此前在 ``src/`` 内
**零生产调用方** —— 逻辑与单测都在，但生产链从不产出它们的输出。
本守卫钉死「已接线」这件事，并防止接线过程中**复活已作废的自拟分数**。

三条硬纪律
----------
1. **六模块产出齐备** —— 任一子块缺失即为接线回退；
2. **降级必须留痕** —— 子块失败写 ``warnings``，不得静默；
3. **不复活自拟分数** —— ``hexagram_state.calculate_hexagram_state`` /
   ``get_base_factors`` / ``calculate_element_modifier`` /
   ``interpretation._hexagram_base_score`` / ``_year_cycle_factor``
   均已作废（无原典依据），源码里**不得**出现对它们的调用；
   六项判据只给 **吉/凶/不判**，**不给 0–1 分数**。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine.adapter import HeluoAdapter  # noqa: E402
from heluo_engine.engines.heluo.diagnosis_rule_graph import HELUO_RULES  # noqa: E402
from heluo_engine.engines.heluo.dimensions import DIM_TO_RULE  # noqa: E402

CASES = [
    ((1975, 11, 22, 1), "male", "2026-10-23"),
    ((1980, 6, 22, 10), "male", "2026-09-15"),
]

#: 已作废、**不得复活**的函数（自拟浮点分数，无原典依据）
FORBIDDEN_CALLS = (
    "calculate_hexagram_state(",
    "get_base_factors(",
    "calculate_element_modifier(",
    "_hexagram_base_score(",
    "_year_cycle_factor(",
)


def _results():
    ad = HeluoAdapter()
    for solar, gender, tgt in CASES:
        r = ad.compute(solar, gender=gender, target_date=tgt)
        yield tgt, r


class TestPipelineWired:
    """六模块确实接在生产链上。"""

    def test_result_carries_interpretation(self):
        for tgt, r in _results():
            assert r.interpretation is not None, f"{tgt} 结果未挂解读层输出"
            assert isinstance(r.interpretation, dict)

    def test_all_six_blocks_present_and_non_empty(self):
        required = ("platform_signals", "interpretation", "diagnosis",
                    "guidance", "metrics", "hexagram_state")
        for tgt, r in _results():
            it = r.interpretation
            for key in required:
                assert key in it, f"{tgt} 解读层缺子块 {key}"
                assert it[key], f"{tgt} 解读层子块 {key} 为空（接线回退？）"

    def test_no_silent_downgrade(self):
        """正常盘**不应**有降级留痕；有则说明某子块没跑通。"""
        for tgt, r in _results():
            w = r.interpretation.get("warnings") or []
            assert not w, f"{tgt} 解读层有降级留痕：{w}"

    def test_dimension_view_reused(self):
        """维度视图应与判词层一致（不是另算一份）。"""
        for tgt, r in _results():
            assert r.interpretation.get("dimension_view") == (
                (r.guajie or {}).get("by_dimension") or {})
            assert r.interpretation.get("dimension_coverage") == (
                (r.guajie or {}).get("dimension_coverage") or {})


class TestDiagnosisGraphWiring:
    """诊断规则图：证据 → 机制节点。"""

    def test_assertions_cover_evidence(self):
        """每条判据证据都应进图（判据证据数 = 断言数，不多不少）。"""
        for tgt, r in _results():
            it = r.interpretation
            diag = it.get("diagnosis") or {}
            evs = it.get("dimension_view") or {}
            n_evidence = sum(n.get("count", 0) for n in evs.values()
                             if n.get("id") not in ("PROCESS", "UNCLASSIFIED"))
            n_assert = len(diag.get("assertions") or [])
            assert n_assert >= n_evidence, (
                f"{tgt} 断言数 {n_assert} < 判据证据数 {n_evidence}（证据丢图了）")

    def test_assertion_rule_ids_registered(self):
        """图上出现的**河洛机制节点**必须在注册表内（授权面）。

        ⚠ 图上还有**事件信号派生**的断言（``EVE_*`` 前缀，来自平台信号层），
        它们不是河洛机制节点，不在此校验范围内。
        """
        for tgt, r in _results():
            for a in (r.interpretation.get("diagnosis") or {}).get("assertions") or []:
                rid = str(a.get("assertion_id") or "")
                if not rid.startswith("HE_LUO_"):
                    continue
                base = rid[len("HE_LUO_"):]
                assert base in HELUO_RULES, (
                    f"{tgt} 断言引用了未注册规则：{base}")

    def test_dim_to_rule_targets_are_registered(self):
        """维度→机制映射里的 rule_id 必须已注册（否则证据会被丢弃）。"""
        for dim, rid in DIM_TO_RULE.items():
            if not rid:
                continue
            assert rid in HELUO_RULES, f"维度 {dim} 映射到未注册规则 {rid}"

    def test_every_registered_rule_has_a_dimension_mapping(self):
        """注册表里的每条规则都该有维度映射（否则该机制永远收不到证据）。

        ⚠ ``HL_HUA_GONG`` 例外：它的断言由 **FrozenState（化工状态）**补充，
        不走 EngineEvidence ⇒ 无需维度映射。
        """
        mapped = {r for r in DIM_TO_RULE.values() if r}
        missing = sorted(set(HELUO_RULES) - mapped - {"HL_HUA_GONG"})
        assert not missing, f"这些已注册规则没有任何维度映射：{missing}"


class TestNoResurrectedFabricatedScores:
    """★ 不复活已作废的自拟分数。"""

    def test_source_does_not_call_forbidden_functions(self):
        """源码**不得调用**已作废的自拟分数函数。

        ⚠ 判据用 **AST**（不是文本搜索）：作废函数本身还留在源码里
        （作为「显式拒绝点」，防止后人复活），且 docstring 里会**提到**它们 ——
        文本搜索会把这两种合法出现误判成「调用」。
        """
        import ast
        banned = {fn.rstrip("(") for fn in FORBIDDEN_CALLS}
        hits = []
        for p in (_REPO / "src" / "heluo_engine").rglob("*.py"):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                name = (fn.id if isinstance(fn, ast.Name)
                        else fn.attr if isinstance(fn, ast.Attribute) else "")
                if name in banned:
                    hits.append(f"{p.name}:{node.lineno}: {name}()")
        assert not hits, "源码调用了已作废的自拟分数函数：\n  " + "\n  ".join(hits)

    def test_liu_ju_has_no_numeric_scores(self):
        """六项判据只给 **吉/凶/不判**，不得给 0–1 分数。"""
        for tgt, r in _results():
            hs = r.interpretation.get("hexagram_state") or {}
            for name, item in (hs.get("liu_ju") or {}).items():
                assert "score" not in item, f"{tgt} 六项判据「{name}」含分数"
                assert item.get("passed") in (True, False, None), (
                    f"{tgt} 六项判据「{name}」的 passed 不是吉/凶/不判："
                    f"{item.get('passed')!r}")
                assert item.get("basis"), f"{tgt} 六项判据「{name}」缺原典依据"

    def test_element_state_is_named_not_numeric(self):
        """五行旺衰给**名目**（王/相/休/囚/死），不给数值。"""
        for tgt, r in _results():
            els = (r.interpretation.get("hexagram_state") or {}).get("element_state") or {}
            assert els, f"{tgt} 五行旺衰为空"
            for el, v in els.items():
                assert isinstance(v, str), f"{tgt} 五行 {el} 给的是数值 {v!r}（应为名目）"


def test_pipeline_module_is_importable_standalone():
    """解读层编排不得依赖主仓（独立包可跑）。"""
    from heluo_engine.engines.heluo.interpretation_pipeline import build_interpretation
    assert callable(build_interpretation)
