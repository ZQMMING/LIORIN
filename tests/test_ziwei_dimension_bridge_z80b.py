# -*- coding: utf-8 -*-
"""Z80-B: 八维/十二维对齐桥测试。

覆盖 dimension_bridge.py：
  - 映射表完整性（8 维全部有归宿）
  - 一对多投射正确性
  - 跨维池（格局/应期/四化体用）
  - 不丢信息（未声明维度进跨维池而非静默丢弃）
  - 12 维契约不被污染
  - 与 build_life_reading 的接线（answer_alignment 非 None）

背景缺陷：answer_layer（8 维）在 src/ 内零调用方，
interpretation（12 维）独立重算维度体系，两者互为孤岛。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.answer_layer import DIMENSIONS, build_answer
from tongshu.engines.ziwei.rules.dimension_bridge import (
    ANSWER_TO_READING_DIMENSION,
    CROSS_DIMENSION_KEYS,
    align_answer_to_dimensions,
)
from tongshu.engines.ziwei.rules.interpretation import (
    DIMENSION_ORDER,
    build_life_reading,
)
from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals

_LUNAR = (1983, 9, 29)
_HOUR = 12
_GENDER = "female"


def _answer():
    eng = ZiweiEngine()
    chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
    return build_answer(chart), chart


class TestMappingTable:
    """映射表契约。"""

    def test_every_answer_dimension_has_destination(self):
        """8 维必须全部有归宿（映射目标 或 跨维池）。"""
        declared = set(ANSWER_TO_READING_DIMENSION) | set(CROSS_DIMENSION_KEYS)
        assert set(DIMENSIONS) == declared, (
            f"未归位的 8 维: {set(DIMENSIONS) - declared}"
        )

    def test_mapping_targets_are_valid_reading_dimensions(self):
        """映射目标必须是合法 12 维名。"""
        for ans_dim, targets in ANSWER_TO_READING_DIMENSION.items():
            for t in targets:
                assert t in DIMENSION_ORDER, (
                    f"{ans_dim} 映射到非法 12 维名 {t}"
                )

    def test_cross_dimension_keys_have_no_mapping(self):
        """跨维池的维度不得同时出现在映射表中（避免语义重复）。"""
        for k in CROSS_DIMENSION_KEYS:
            assert k not in ANSWER_TO_READING_DIMENSION

    def test_no_reading_dimension_orphaned_by_mapping(self):
        """映射表覆盖的 12 维必须真实存在。"""
        covered = set()
        for targets in ANSWER_TO_READING_DIMENSION.values():
            covered.update(targets)
        assert covered <= set(DIMENSION_ORDER)


class TestAlignment:
    """投射行为。"""

    def test_alignment_runs(self):
        ans, _ = _answer()
        al = align_answer_to_dimensions(ans)
        assert al.by_dimension
        assert al.coverage["answer_dimensions"] == 8

    def test_no_unmapped_dimensions(self):
        """8 维必须全部归位，不得有 unmapped。"""
        ans, _ = _answer()
        al = align_answer_to_dimensions(ans)
        assert al.coverage["unmapped_dimensions"] == [], (
            f"未归位维度: {al.coverage['unmapped_dimensions']}"
        )

    def test_items_mapped(self):
        """应有条目被投射（非空跑）。"""
        ans, _ = _answer()
        al = align_answer_to_dimensions(ans)
        assert al.coverage["mapped_items"] > 0
        assert al.coverage["cross_items"] > 0

    def test_by_dimension_keys_are_reading_dimensions(self):
        ans, _ = _answer()
        al = align_answer_to_dimensions(ans)
        for d in al.by_dimension:
            assert d in DIMENSION_ORDER

    def test_cross_dimension_holds_three_keys(self):
        """格局/应期/四化体用 应进跨维池。"""
        ans, _ = _answer()
        al = align_answer_to_dimensions(ans)
        got = {c.dimension for c in al.cross_dimension}
        assert set(CROSS_DIMENSION_KEYS) <= got, (
            f"跨维池缺少: {set(CROSS_DIMENSION_KEYS) - got}"
        )

    def test_source_preserved(self):
        """投射条目必须保留来源派别（可审计）。"""
        ans, _ = _answer()
        al = align_answer_to_dimensions(ans)
        all_items = [it for v in al.by_dimension.values() for it in v]
        assert all_items
        for it in all_items:
            assert "source" in it
            assert "from_answer_dimension" in it
            assert it["from_answer_dimension"] in DIMENSIONS


class TestNoInfoLoss:
    """不丢信息：未声明维度须进跨维池，不得静默丢弃。"""

    def test_unknown_dimension_goes_to_cross(self):
        fake = {
            "answer": {
                "性格": [{"source": "sanhe", "rule_id": "X1",
                          "text": "t1", "evidence_grade": 1}],
                "玄学新维": [{"source": "qintian", "rule_id": "X2",
                              "text": "t2", "evidence_grade": 1}],
            }
        }
        al = align_answer_to_dimensions(fake)
        assert "玄学新维" in al.coverage["unmapped_dimensions"]
        got = {c.dimension for c in al.cross_dimension}
        assert "玄学新维" in got, "未声明的维度被静默丢弃"

    def test_one_to_many_projection(self):
        """一对多：性格 → 性情禀赋 + 福德精神，两边都应收到。"""
        fake = {
            "answer": {
                "性格": [{"source": "sanhe", "rule_id": "P1",
                          "text": "性格文本", "evidence_grade": 1}],
            }
        }
        al = align_answer_to_dimensions(fake)
        for tgt in ANSWER_TO_READING_DIMENSION["性格"]:
            texts = [it["text"] for it in al.by_dimension[tgt]]
            assert "性格文本" in texts, f"{tgt} 未收到投射"

    def test_projection_does_not_mutate_source(self):
        """投射须深拷贝，不得改写原 8 维条目。"""
        fake = {
            "answer": {
                "性格": [{"source": "sanhe", "rule_id": "P1",
                          "text": "原文", "evidence_grade": 1}],
            }
        }
        al = align_answer_to_dimensions(fake)
        # 改写投射结果，原 answer 不受影响
        al.by_dimension["性情禀赋"][0]["text"] = "被改写"
        assert fake["answer"]["性格"][0]["text"] == "原文"


class TestWiring:
    """接线：build_life_reading 必须产出 answer_alignment。"""

    def test_alignment_attached_to_reading(self):
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        reading = build_life_reading(
            chart, compute_multi_method_signals(chart), target_year=2026
        )
        assert reading.answer_alignment is not None, (
            "reading.answer_alignment 为 None —— 8 维/12 维对齐桥未接入"
        )

    def test_alignment_in_to_dict(self):
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        reading = build_life_reading(
            chart, compute_multi_method_signals(chart), target_year=2026
        )
        d = reading.to_dict()
        assert "answer_alignment" in d
        assert d["answer_alignment"] is not None
        assert "by_dimension" in d["answer_alignment"]

    def test_twelve_dimension_contract_unchanged(self):
        """12 维自有产出不得因桥接而改变。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        reading = build_life_reading(
            chart, compute_multi_method_signals(chart), target_year=2026
        )
        assert len(reading.dimensions) == 12
        empty = [d.dimension for d in reading.dimensions
                 if not (d.conclusion or "").strip()]
        assert not empty, f"12 维断语出现空值: {empty}"

    def test_subpackage_exports(self):
        """子包统一入口应导出三层便捷入口。"""
        import tongshu.engines.ziwei as Z
        for name in ("compute_multi_method_signals", "build_life_reading",
                     "build_answer", "build_domain_readings"):
            assert name in Z.__all__, f"子包未导出 {name}"
            assert hasattr(Z, name), f"子包导出 {name} 但属性不存在"
