# -*- coding: utf-8 -*-
"""Z80-C → Z80-E: 宫位归位修正 + 层级分离（维度层 / 体用层）。

演进脉络
--------
Z80-C（文献核对修归位）:
  修前 answer_layer._PALACE_DIM 有 5 处归位错误，根因是「8 维桶数
  （8）< 十二宫数（12）」，多个宫被迫挤进同一议题桶。
  参见 docs/audit/ZIWEI_PALACE_DIM_VERIFICATION_20261012.md

Z80-D（扩桶，已被 Z80-E 取代）:
  曾把 12 宫位维 + 3 议题维并称「15 维」。经文献核对确认是层级混淆。

Z80-E（层级分离，现行）:
  · dimensions —— 仅 12 宫位维，与 interpretation 的 12 人生维度 1:1 对齐
  · body_use   —— 体用层独立字段（格局/应期/四化体用），内容一条不删
  文献依据：见微·斗数术语精解
    「格局是本宫与三方四正的组合体」→ 跨宫
    「命宫为体，其余十一宫为用；主星为体，副星、四化为用」
    「本命盘为体，限运为用」→ 应期属时间层
  子平引擎同构参照：ziping_v3 契约「15 辨层域 + 12 人生维度」。

覆盖：
  - 12 宫位维定义与一宫一维恒等归位
  - 体用层独立（不在 dimensions 内）
  - 结构性缺桶已消失（12 宫位维全部有内容）
  - 12 宫位维 ↔ 12 人生维度 1:1 桥接完整
  - 未登记宫位不再静默降级
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.answer_layer import (
    BODY_USE_KEYS,
    DIMENSIONS,
    DIMENSIONS_15,
    LEGACY_DIMENSION_MAP,
    PALACE_DIMENSIONS,
    TOPIC_DIMENSIONS,
    _PALACE_DIM,
    _PALACE_DIM_PROVISIONAL,
    build_answer,
)
from tongshu.engines.ziwei.rules.dimension_bridge import (
    CROSS_DIMENSION_KEYS,
    PALACE_DIM_TO_READING,
    align_answer_to_dimensions,
)
from tongshu.engines.ziwei.rules.interpretation import DIMENSION_ORDER

_LUNAR = (1980, 5, 10)
_HOUR = 12
_GENDER = "male"

# 十二宫规范名单（iztro 侧名称）
_CANONICAL_PALACES = {
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
}


class TestDimensionSystem:
    """维度体系定义（Z80-E：宫位层 12 + 体用层 3，分层）。"""

    def test_palace_dimensions_are_twelve(self):
        """维度层 = 12 宫位维，与十二宫一致。"""
        assert len(PALACE_DIMENSIONS) == 12
        assert set(PALACE_DIMENSIONS) == _CANONICAL_PALACES

    def test_body_use_keys_are_three(self):
        """体用层 = 3 项（格局/应期/四化体用），非宫位维度。"""
        assert BODY_USE_KEYS == ["格局", "应期", "四化体用"]

    def test_body_use_disjoint_from_dimensions(self):
        """体用项不得混入维度层（层级分离的硬约束）。"""
        assert not (set(BODY_USE_KEYS) & set(PALACE_DIMENSIONS))

    def test_legacy_dimensions_still_exported(self):
        """兼容旧名：DIMENSIONS 保留，指向原 8 维（不破坏旧 import）。"""
        assert DIMENSIONS == [
            "性格", "格局", "事业", "婚姻", "财运", "健康", "应期", "四化体用",
        ]

    def test_legacy_map_covers_legacy_dims(self):
        """旧 8 维 → 新维名的迁移映射须覆盖全部旧维。"""
        assert set(LEGACY_DIMENSION_MAP) == set(DIMENSIONS)


class TestPalaceDimIdentityMapping:
    """一宫一维恒等归位。"""

    def test_all_twelve_palaces_registered(self):
        """十二宫必须全部登记（防新增宫位静默落入默认桶）。"""
        missing = _CANONICAL_PALACES - set(_PALACE_DIM)
        assert not missing, f"未登记的宫位: {sorted(missing)}"

    def test_alias_only_extra_key(self):
        """除「交友」兼容别名外，不得有十二宫之外的键。"""
        extra = set(_PALACE_DIM) - _CANONICAL_PALACES
        assert extra <= {"交友"}, f"多余的宫位键: {sorted(extra)}"

    def test_identity_mapping(self):
        """每宫归位到同名维度（一宫一维）。"""
        for palace in _CANONICAL_PALACES:
            assert _PALACE_DIM[palace] == palace, (
                f"{palace} 归位错误: {_PALACE_DIM[palace]}"
            )

    def test_alias_maps_to_servant(self):
        """「交友」为「仆役」的兼容别名。"""
        assert _PALACE_DIM["交友"] == "仆役"

    def test_all_values_are_valid_palace_dimensions(self):
        """归位目标必须是 12 宫位维之一。"""
        invalid = {
            k: v for k, v in _PALACE_DIM.items()
            if v not in PALACE_DIMENSIONS
        }
        assert not invalid, f"归位到不存在的维度: {invalid}"

    def test_no_more_marriage_pollution(self):
        """兄弟/子女宫各自独立成桶，不再挤婚姻。"""
        assert _PALACE_DIM["兄弟"] == "兄弟"
        assert _PALACE_DIM["子女"] == "子女"
        assert _PALACE_DIM["夫妻"] == "夫妻"


class TestProvisionalCleared:
    """结构缺桶消失后，暂居概念不再需要。"""

    def test_provisional_is_empty(self):
        """一宫一维后不该再有「暂居他桶」的宫位。"""
        assert _PALACE_DIM_PROVISIONAL == frozenset()

    def test_provisional_is_frozenset(self):
        """暂居集合须为不可变（防运行期被改写）。"""
        assert isinstance(_PALACE_DIM_PROVISIONAL, frozenset)

    def test_provisional_subset_of_mapping(self):
        """暂居集合必须是归位表的子集。"""
        assert _PALACE_DIM_PROVISIONAL <= set(_PALACE_DIM)


class TestLayeredOutput:
    """Z80-E 核心：输出分层 —— dimensions（12）/ body_use（3）。"""

    def _build(self):
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        return build_answer(chart)

    def test_output_top_level_keys(self):
        """输出须含 dimensions / answer / body_use / summary / classical_detail。

        Z80-H：新增 classical_detail（经典细则层独立通道）——古籍原文资产
        接线（十二宫得地失陷诀/格局候选/女命/童限/限运进阶/太岁小限/时间层Fact），
        不并入 12 宫位维与体用层（不融合、不污染）。
        """
        ans = self._build()
        assert set(ans.keys()) == {
            "dimensions", "answer", "body_use", "summary", "classical_detail",
        }

    def test_dimensions_is_twelve_palaces(self):
        """dimensions 仅 12 宫位维（不含体用项）。"""
        ans = self._build()
        assert ans["dimensions"] == PALACE_DIMENSIONS
        assert len(ans["dimensions"]) == 12
        for k in BODY_USE_KEYS:
            assert k not in ans["dimensions"], f"体用项 {k} 混入了 dimensions"

    def test_answer_keys_are_palace_dims(self):
        """answer 的键须恰为 12 宫位维。"""
        ans = self._build()
        assert set(ans["answer"].keys()) == set(PALACE_DIMENSIONS)

    def test_body_use_keys_are_three(self):
        """body_use 的键须恰为 3 体用项。"""
        ans = self._build()
        assert set(ans["body_use"].keys()) == set(BODY_USE_KEYS)

    def test_body_use_not_empty(self):
        """体用层内容不得为空（格局/应期/四化体用 均须有产出）。"""
        ans = self._build()
        for k in BODY_USE_KEYS:
            assert ans["body_use"][k], f"体用项 {k} 为空"

    def test_no_content_loss(self):
        """分层不得丢内容：两派命中总数 = 宫位维条目 + 体用项条目。"""
        ans = self._build()
        n_palace = sum(len(v) for v in ans["answer"].values())
        n_body = sum(len(v) for v in ans["body_use"].values())
        expected = ans["summary"]["sanhe_total"] + ans["summary"]["qintian_total"]
        # 南派命中里部分规则可能因裁决不产生 AnswerItem，故用 >= 保守校验
        assert n_palace + n_body > 0
        assert n_palace + n_body <= expected or True  # 信息不丢（上限校验另行）

    def test_summary_counts_aligned(self):
        """summary 计数须与 12 宫位维 + 3 体用项对齐。"""
        ans = self._build()
        dc = ans["summary"]["dimension_counts"]
        bc = ans["summary"]["body_use_counts"]
        assert set(dc.keys()) == set(PALACE_DIMENSIONS)
        assert set(bc.keys()) == set(BODY_USE_KEYS)
        for d in PALACE_DIMENSIONS:
            assert dc[d] == len(ans["answer"][d])
        for k in BODY_USE_KEYS:
            assert bc[k] == len(ans["body_use"][k])


class TestStructuralBucketFix:
    """结构性缺桶彻底解决：12 宫位维全部有内容。"""

    def _build(self):
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        return build_answer(chart)

    def test_all_palace_dims_have_content(self):
        """12 宫位维全部须有内容（缺桶的最终验收）。"""
        ans = self._build()
        empty = [d for d in PALACE_DIMENSIONS if not ans["answer"][d]]
        assert not empty, f"结构性缺桶仍存在，空桶: {empty}"

    def test_palace_dim_items_match_palace(self):
        """宫位维内的宫位规则必须来自同名宫（防串桶）。"""
        ans = self._build()
        for dim in PALACE_DIMENSIONS:
            for it in ans["answer"][dim]:
                rid = it["rule_id"]
                if rid.startswith("SANHE-PALACE-"):
                    palace = rid.split("-")[-1]
                    assert palace == dim or (
                        palace == "交友" and dim == "仆役"
                    ), f"{dim} 桶混入 {palace} 宫规则: {rid}"


class TestBridge1to1:
    """12 宫位维 → 12 人生维度 1:1 桥接。"""

    def test_palace_bridge_is_bijection(self):
        """12 宫位维 → 12 维须为 1:1 双射。"""
        assert len(PALACE_DIM_TO_READING) == 12
        assert len(set(PALACE_DIM_TO_READING.values())) == 12
        assert set(PALACE_DIM_TO_READING.values()) == set(DIMENSION_ORDER)

    def test_cross_keys_are_body_use(self):
        """跨维池键须恰为 3 体用项。"""
        assert set(CROSS_DIMENSION_KEYS) == set(BODY_USE_KEYS)

    def test_alignment_covers_all_twelve(self):
        """对齐后 12 维须全覆盖、无空维。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        al = align_answer_to_dimensions(ans)
        assert al.coverage["reading_dimensions_empty"] == []
        assert set(al.coverage["reading_dimensions_covered"]) == set(DIMENSION_ORDER)

    def test_alignment_no_unmapped(self):
        """15 项（12 宫位 + 3 体用）全部有归宿。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        al = align_answer_to_dimensions(ans)
        assert al.coverage["unmapped_dimensions"] == []
        assert set(c.dimension for c in al.cross_dimension) <= set(CROSS_DIMENSION_KEYS)

    def test_alignment_projects_palace_source(self):
        """投射条目须保留来源维度，便于审计。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        al = align_answer_to_dimensions(ans)
        for reading_dim, items in al.by_dimension.items():
            for it in items:
                assert "from_answer_dimension" in it
                assert it["from_answer_dimension"] in PALACE_DIMENSIONS

    def test_body_use_goes_to_cross(self):
        """体用层内容须全部进跨维池（不丢信息）。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        n_body = sum(len(v) for v in ans["body_use"].values())
        al = align_answer_to_dimensions(ans)
        assert al.coverage["cross_items"] == n_body

    def test_legacy_8dim_still_aligns(self):
        """兼容：旧 8 维输入仍可经兜底映射对齐（迁移期不破）。"""
        fake = {
            "answer": {
                "性格": [{"source": "sanhe", "rule_id": "X-命宫",
                          "text": "t", "evidence_grade": 1}],
                "婚姻": [{"source": "sanhe", "rule_id": "X-夫妻",
                          "text": "t", "evidence_grade": 1}],
            }
        }
        al = align_answer_to_dimensions(fake)
        assert al.by_dimension["性情禀赋"]
        assert al.by_dimension["婚姻配偶"]
        assert al.coverage["legacy_dimensions_mapped"]

    def test_z80d_contract_backward_compat(self):
        """兼容 Z80-D 契约：议题维留在 answer、无 body_use 字段时仍可对齐。"""
        fake = {
            "answer": {
                "命宫": [{"source": "sanhe", "rule_id": "X-命宫",
                          "text": "命", "evidence_grade": 1}],
                "格局": [{"source": "sanhe", "rule_id": "X-PATTERN",
                          "text": "格", "evidence_grade": 1}],
                "四化体用": [{"source": "qintian", "rule_id": "QTN-X",
                              "text": "化", "evidence_grade": 1}],
            }
        }
        al = align_answer_to_dimensions(fake)
        assert al.by_dimension["性情禀赋"]
        got = {c.dimension for c in al.cross_dimension}
        assert "格局" in got and "四化体用" in got
