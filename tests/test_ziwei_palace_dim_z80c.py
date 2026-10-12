# -*- coding: utf-8 -*-
"""Z80-C: 十二宫 → 八维归位修正测试。

背景缺陷（文献核对：docs/audit/ZIWEI_PALACE_DIM_VERIFICATION_20261012.md）：
  answer_layer._PALACE_DIM 有 5 处归位错误：
    · 兄弟 婚姻 → 性格   （文献：兄弟宫主兄弟姊妹/合伙人/知心朋友）
    · 子女 婚姻 → 性格   （子女宫主子女缘/下属/合伙，桃花仅延伸角色）
    · 迁移 应期 → 事业   （迁移是空间场域，非时间维度）
    · 仆役 应期 → 性格   （仆役主朋友/下属/助力，属人际）
    · 父母 性格 → 性格   （保持，但属"暂居"）
  并新增 _PALACE_DIM_PROVISIONAL 显式声明"8 维无对应、暂居他桶"的宫位。

覆盖：
  - 归位正确性（逐宫断言）
  - 「婚姻」维度不再被兄弟/子女宫污染
  - 暂居集合声明完整
  - 8 维契约不被破坏（仍是 8 个维度）
  - 未登记宫位不再静默降级
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.answer_layer import (
    DIMENSIONS,
    _PALACE_DIM,
    _PALACE_DIM_PROVISIONAL,
    build_answer,
)

_LUNAR = (1980, 5, 10)
_HOUR = 12
_GENDER = "male"

# 十二宫规范名单（iztro 侧名称）
_CANONICAL_PALACES = {
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "仆役", "官禄", "田宅", "福德", "父母",
}


class TestPalaceDimMapping:
    """归位表逐宫正确性。"""

    def test_all_twelve_palaces_registered(self):
        """十二宫必须全部登记（防新增宫位静默落入默认桶）。"""
        missing = _CANONICAL_PALACES - set(_PALACE_DIM)
        assert not missing, f"未登记的宫位: {sorted(missing)}"

    def test_no_extra_palace(self):
        """不得有十二宫之外的键（防脏数据）。"""
        extra = set(_PALACE_DIM) - _CANONICAL_PALACES
        assert not extra, f"多余的宫位键: {sorted(extra)}"

    def test_all_values_are_valid_dimensions(self):
        """归位目标必须是 8 维之一。"""
        invalid = {k: v for k, v in _PALACE_DIM.items() if v not in DIMENSIONS}
        assert not invalid, f"归位到不存在的维度: {invalid}"

    def test_sibling_not_marriage(self):
        """Z80-C 核心：兄弟宫不得归「婚姻」。"""
        assert _PALACE_DIM["兄弟"] != "婚姻", "兄弟宫仍被归入婚姻维度"
        assert _PALACE_DIM["兄弟"] == "性格"

    def test_children_not_marriage(self):
        """Z80-C 核心：子女宫不得归「婚姻」。"""
        assert _PALACE_DIM["子女"] != "婚姻", "子女宫仍被归入婚姻维度"
        assert _PALACE_DIM["子女"] == "性格"

    def test_marriage_palace_is_marriage(self):
        """夫妻宫仍归「婚姻」（唯一正确归位）。"""
        assert _PALACE_DIM["夫妻"] == "婚姻"

    def test_migration_not_yingqi(self):
        """Z80-C：迁移宫不得归「应期」（迁移是空间场域，非时间维）。"""
        assert _PALACE_DIM["迁移"] != "应期", "迁移宫仍被归入应期维度"
        assert _PALACE_DIM["迁移"] == "事业"

    def test_servant_not_yingqi(self):
        """Z80-C：仆役宫不得归「应期」（仆役属人际）。"""
        assert _PALACE_DIM["仆役"] != "应期", "仆役宫仍被归入应期维度"
        assert _PALACE_DIM["仆役"] == "性格"

    def test_parent_not_pure_character(self):
        """Z80-C：父母宫虽归性格，但须在暂居集合中标注。"""
        assert _PALACE_DIM["父母"] == "性格"
        assert "父母" in _PALACE_DIM_PROVISIONAL

    def test_correct_assignments_unchanged(self):
        """本来正确的归位不得被改动。"""
        assert _PALACE_DIM["命宫"] == "性格"
        assert _PALACE_DIM["财帛"] == "财运"
        assert _PALACE_DIM["田宅"] == "财运"
        assert _PALACE_DIM["疾厄"] == "健康"
        assert _PALACE_DIM["官禄"] == "事业"
        assert _PALACE_DIM["福德"] == "性格"


class TestProvisionalDeclaration:
    """暂居维度声明完整性。"""

    def test_provisional_subset_of_mapping(self):
        """暂居集合必须是归位表的子集。"""
        assert _PALACE_DIM_PROVISIONAL <= set(_PALACE_DIM)

    def test_provisional_covers_five_palaces(self):
        """5 个"8 维无对应"的宫位必须全部声明。"""
        expected = {"兄弟", "子女", "父母", "迁移", "仆役"}
        assert _PALACE_DIM_PROVISIONAL == expected

    def test_provisional_is_frozenset(self):
        """暂居集合须为不可变（防运行期被改写）。"""
        assert isinstance(_PALACE_DIM_PROVISIONAL, frozenset)


class TestContractUnbroken:
    """8 维契约不被破坏。"""

    def test_dimensions_still_eight(self):
        """8 维数量与顺序不变。"""
        assert DIMENSIONS == [
            "性格", "格局", "事业", "婚姻", "财运", "健康", "应期", "四化体用",
        ]

    def test_build_answer_keys_unchanged(self):
        """build_answer 顶层键不变。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        assert set(ans.keys()) == {"dimensions", "answer", "summary"}
        assert list(ans["dimensions"]) == DIMENSIONS


class TestNoMarriagePollution:
    """「婚姻」维度不得被兄弟/子女宫内容污染。"""

    def _marriage_rule_ids(self):
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        return [it["rule_id"] for it in ans["answer"].get("婚姻", [])]

    def test_no_sibling_rule_in_marriage(self):
        """兄弟宫规则不得出现在婚姻维度。"""
        rids = self._marriage_rule_ids()
        bad = [r for r in rids if r.endswith("-兄弟")]
        assert not bad, f"兄弟宫规则仍在婚姻维度: {bad}"

    def test_no_children_palace_rule_in_marriage(self):
        """子女宫规则不得出现在婚姻维度。"""
        rids = self._marriage_rule_ids()
        bad = [r for r in rids if r.endswith("-子女")]
        assert not bad, f"子女宫规则仍在婚姻维度: {bad}"

    def test_marriage_dimension_has_content(self):
        """婚姻维度仍应有夫妻宫内容（不得修成空）。"""
        rids = self._marriage_rule_ids()
        assert any(r.endswith("-夫妻") for r in rids), (
            f"婚姻维度缺少夫妻宫内容，实际: {rids}"
        )


class TestProvisionalAnnotation:
    """暂居宫位在输出中可审计。"""

    def test_provisional_palace_annotated(self):
        """暂居宫位的条目 qualifier 应含 [暂居维度] 标注。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        # 兄弟宫在八维中属暂居，其条目应带标注
        found = False
        for dim, items in ans["answer"].items():
            for it in items:
                if it["rule_id"].endswith("-兄弟"):
                    found = True
                    assert "[暂居维度]" in it.get("qualifier", ""), (
                        f"兄弟宫条目缺少暂居标注: {it}"
                    )
        assert found, "未找到兄弟宫条目，无法验证标注"

    def test_direct_palace_not_annotated(self):
        """真属此维的宫位（如财帛）不应带暂居标注。"""
        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        ans = build_answer(chart)
        for it in ans["answer"].get("财运", []):
            if it["rule_id"].endswith("-财帛"):
                assert "[暂居维度]" not in it.get("qualifier", ""), (
                    f"财帛宫被误标暂居: {it}"
                )
