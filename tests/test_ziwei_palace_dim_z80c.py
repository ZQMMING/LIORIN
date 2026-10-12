# -*- coding: utf-8 -*-
"""Z80-C → Z80-D: 十二宫 → 维度归位修正与结构缺桶彻底解决测试。

演进脉络
--------
Z80-C（文献核对修归位）:
  修前 answer_layer._PALACE_DIM 有 5 处归位错误，根因是「8 维桶数
  （8）< 十二宫数（12）」，多个宫被迫挤进同一议题桶：
    · 兄弟/子女/父母/仆役 → 挤「性格」   · 迁移 → 挤「事业」
  参见 docs/audit/ZIWEI_PALACE_DIM_VERIFICATION_20261012.md

Z80-D（彻底解决结构缺桶）:
  放弃「按议题切 8 桶」的口径，改为「按宫位切 12 桶 + 3 议题桶 = 15 维」，
  与 interpretation 的 12 维**同构**（一宫一维）。
  于是 _PALACE_DIM 退化为**恒等映射**（宫名 = 维名），
  多宫挤一桶的结构性缺陷从根上消失，_PALACE_DIM_PROVISIONAL 亦清空。

覆盖：
  - 15 维体系定义与顺序
  - 一宫一维恒等归位（逐宫断言）
  - 结构性缺桶已消失（15 桶全部有内容、无溢出）
  - 3 议题维仍存在且可归位
  - 12 宫位维 ↔ 12 维（interpretation）1:1 桥接完整
  - 未登记宫位不再静默降级
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.answer_layer import (
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


class TestDimensionSystem15:
    """15 维体系定义。"""

    def test_fifteen_dimensions(self):
        """Z80-D：维度体系为 12 宫位维 + 3 议题维。"""
        assert len(DIMENSIONS_15) == 15
        assert PALACE_DIMENSIONS + TOPIC_DIMENSIONS == DIMENSIONS_15

    def test_palace_dimensions_are_twelve(self):
        """12 宫位维须与十二宫一致。"""
        assert len(PALACE_DIMENSIONS) == 12
        assert set(PALACE_DIMENSIONS) == _CANONICAL_PALACES

    def test_topic_dimensions_are_three(self):
        """3 议题维（无宫位对应）须显式声明。"""
        assert TOPIC_DIMENSIONS == ["格局", "应期", "四化体用"]

    def test_legacy_dimensions_still_exported(self):
        """兼容旧名：DIMENSIONS 保留，指向原 8 维（不破坏旧 import）。"""
        assert DIMENSIONS == [
            "性格", "格局", "事业", "婚姻", "财运", "健康", "应期", "四化体用",
        ]

    def test_legacy_map_covers_palace_dims(self):
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
        """Z80-D 核心：每宫归位到同名维度（一宫一维）。"""
        for palace in _CANONICAL_PALACES:
            assert _PALACE_DIM[palace] == palace, (
                f"{palace} 归位错误: {_PALACE_DIM[palace]}"
            )

    def test_alias_maps_to_servant(self):
        """「交友」为「仆役」的兼容别名。"""
        assert _PALACE_DIM["交友"] == "仆役"

    def test_all_values_are_valid_dimensions(self):
        """归位目标必须是 15 维之一。"""
        invalid = {k: v for k, v in _PALACE_DIM.items() if v not in DIMENSIONS_15}
        assert not invalid, f"归位到不存在的维度: {invalid}"

    def test_no_more_marriage_pollution(self):
        """Z80-D：兄弟/子女宫各自独立成桶，不再挤婚姻。"""
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


class TestStructuralBucketFix:
    """结构性缺桶彻底解决：15 桶全部存在、无溢出。"""

    def _build(self):
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        return build_answer(chart)

    def test_answer_has_fifteen_keys(self):
        """build_answer 输出须含全部 15 维键。"""
        ans = self._build()
        assert ans["dimensions"] == DIMENSIONS_15
        assert set(ans["answer"].keys()) == set(DIMENSIONS_15)

    def test_no_overflow_bucket(self):
        """除 4 化体用（真·兜底维）外，不得有维度键越界。"""
        ans = self._build()
        assert set(ans["answer"].keys()) - set(DIMENSIONS_15) == set()

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

    def test_topic_dims_have_content(self):
        """3 议题维仍须产出（不受扩容影响）。"""
        ans = self._build()
        assert ans["answer"]["格局"], "格局维为空"
        assert ans["answer"]["应期"], "应期维为空"
        assert ans["answer"]["四化体用"], "四化体用维为空"

    def test_summary_dimension_counts(self):
        """summary.dimension_counts 须与 15 维对齐。"""
        ans = self._build()
        counts = ans["summary"]["dimension_counts"]
        assert set(counts.keys()) == set(DIMENSIONS_15)
        for d in DIMENSIONS_15:
            assert counts[d] == len(ans["answer"][d])


class TestBridge1to1:
    """15 维 → 12 维 1:1 桥接。"""

    def test_palace_bridge_is_bijection(self):
        """12 宫位维 → 12 维须为 1:1 双射。"""
        assert len(PALACE_DIM_TO_READING) == 12
        assert len(set(PALACE_DIM_TO_READING.values())) == 12
        assert set(PALACE_DIM_TO_READING.values()) == set(DIMENSION_ORDER)

    def test_cross_keys_are_topic_dims(self):
        """跨维池键须恰为 3 议题维。"""
        assert set(CROSS_DIMENSION_KEYS) == set(TOPIC_DIMENSIONS)

    def test_alignment_covers_all_twelve(self):
        """对齐后 12 维须全覆盖、无空维。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        al = align_answer_to_dimensions(ans)
        assert al.coverage["reading_dimensions_empty"] == []
        assert set(al.coverage["reading_dimensions_covered"]) == set(DIMENSION_ORDER)

    def test_alignment_no_unmapped(self):
        """15 维全部有归宿（宫位维投射、议题维入跨维池）。"""
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
                assert it["from_answer_dimension"] in DIMENSIONS_15

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
