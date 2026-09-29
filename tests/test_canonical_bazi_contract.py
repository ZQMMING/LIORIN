"""P0-FNDR-10 (R-15 ⑭ BaziChart 契约 audit fix): CanonicalBaziChart contract test.

User 裁决 (2026-09-10): ⑭ = 🟡 CONDITIONAL PASS.
目标: 证明八字排盘引擎输出给下游的 Canonical State 是
  完整 / 确定 / 可冻结 / 无辨层污染.

本测试锁死 CanonicalBaziChart (models/canonical_bazi.py) 的契约:
  1. 明确保留字段 (4柱 + day_master + gender + start_age + birth_datetime)
  2. 明确剥离字段 (spouse_star* / officer_mixed / branch_*_map / 五行 / 空亡...)
  3. birth_datetime 必须保留 (下游高精度起运依赖)
  4. frozen / 不可变性锁定
  5. 禁止下游重新计算 — 只能经 from_bazi_chart() 构造
  6. P2 辨层字段权威性标注 (NOT_AUTHORIZED / AUXILIARY_SIGNAL)

本轮只补测试 + 权威标注, 不删除/不迁移生产结构 (User 收紧范围).
"""

from __future__ import annotations

import dataclasses
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datetime import datetime
from zoneinfo import ZoneInfo

from tongshu.engines.bazi_engine import (
    BaziEngine,
    calc_spouse_star_authority_status,
    calc_spouse_star_role,
    calc_spouse_star_strength_authority_status,
    calc_spouse_star_strength_role,
    calc_officer_mixed_authority_status,
    calc_officer_mixed_role,
)
from tongshu.models.canonical_bazi import (
    CanonicalBaziChart,
    is_factory_provenance,
    provenance_of,
    assert_canonical_gate,
    CANONICAL_PROVENANCE_FACTORY,
    CANONICAL_PROVENANCE_DIRECT,
)


def _make_chart():
    engine = BaziEngine()
    bd = datetime(1983, 11, 3, 12, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    return engine.compute((1983, 11, 3, 12), gender="male", birth_datetime=bd), bd


class TestCanonicalRetainedFields(unittest.TestCase):
    """⑭a: CanonicalBaziChart 必须保留的确定性基础事实."""

    RETAINED = [
        "year_pillar", "month_pillar", "day_pillar", "hour_pillar",
        "day_master", "gender", "start_age", "birth_datetime",
    ]

    def test_retained_fields_present(self):
        chart, bd = _make_chart()
        canonical = CanonicalBaziChart.from_bazi_chart(chart)
        for f in self.RETAINED:
            self.assertTrue(
                hasattr(canonical, f),
                f"CanonicalBaziChart 缺少保留字段 {f}",
            )

    def test_birth_datetime_retained(self):
        """birth_datetime 必须保留 — 下游引擎 (盲派/河洛) 高精度起运依赖."""
        chart, bd = _make_chart()
        canonical = CanonicalBaziChart.from_bazi_chart(chart)
        self.assertIsNotNone(canonical.birth_datetime)
        self.assertEqual(canonical.birth_datetime, bd)

    def test_pillar_values_round_trip(self):
        """四柱 + day_master 与源 BaziChart 完全一致 (值不漂移)."""
        chart, _ = _make_chart()
        canonical = CanonicalBaziChart.from_bazi_chart(chart)
        self.assertEqual(canonical.year_pillar, chart.year_pillar)
        self.assertEqual(canonical.month_pillar, chart.month_pillar)
        self.assertEqual(canonical.day_pillar, chart.day_pillar)
        self.assertEqual(canonical.hour_pillar, chart.hour_pillar)
        self.assertEqual(canonical.day_master, chart.day_master)
        self.assertEqual(canonical.gender, chart.gender)
        self.assertEqual(canonical.start_age, chart.start_age)

    def test_deterministic(self):
        """同一 BaziChart 两次 from_bazi_chart 结果完全一致 (可冻结)."""
        chart, _ = _make_chart()
        c1 = CanonicalBaziChart.from_bazi_chart(chart)
        c2 = CanonicalBaziChart.from_bazi_chart(chart)
        self.assertEqual(dataclasses.asdict(c1), dataclasses.asdict(c2))


class TestCanonicalStripsDerivedFields(unittest.TestCase):
    """⑭a: CanonicalBaziChart 必须剥离所有 derived/interpretive 字段.

    这是"无辨层污染"的核心保证 — 下游拿到的 Canonical State 不能
    携带 spouse_star 评分 / branch_map / 五行失衡 等派生或启发信号.
    """

    STRIPPED = [
        # P2 辨层启发字段
        "spouse_star", "spouse_star_attack", "spouse_star_strength",
        "officer_mixed", "peach_blossom",
        # 地支关系图
        "branch_clash_map", "branch_harm_map",
        "branch_he_map", "branch_sanhe_map", "branch_sanxing_map",
        # 空亡 / 五行
        "kong_wang", "five_element_balance", "five_element_imbalance",
        # 大运 / 派生
        "luck_pillars", "day_branch_main_ten_god",
    ]

    def test_derived_fields_absent(self):
        chart, _ = _make_chart()
        canonical = CanonicalBaziChart.from_bazi_chart(chart)
        canonical_field_names = {f.name for f in dataclasses.fields(CanonicalBaziChart)}
        for f in self.STRIPPED:
            self.assertNotIn(
                f, canonical_field_names,
                f"CanonicalBaziChart 不应携带派生/辨层字段 {f} (无辨层污染被破坏)",
            )

    def test_canonical_field_set_exact(self):
        """字段集合 = 保留集, 不多不少 (锁死契约面, 防止未来误加字段)."""
        canonical_field_names = {f.name for f in dataclasses.fields(CanonicalBaziChart)}
        RETAINED = {
            "year_pillar", "month_pillar", "day_pillar", "hour_pillar",
            "day_master", "gender", "start_age", "birth_datetime",
        }
        self.assertEqual(
            canonical_field_names, RETAINED,
            f"CanonicalBaziChart 字段面应为保留集 {sorted(RETAINED)}, "
            f"实际 {sorted(canonical_field_names)}",
        )


class TestCanonicalImmutability(unittest.TestCase):
    """⑭a: frozen / 不可变性锁定."""

    def test_frozen(self):
        chart, _ = _make_chart()
        canonical = CanonicalBaziChart.from_bazi_chart(chart)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            canonical.day_master = "JIA"

    def test_is_dataclass_frozen(self):
        self.assertTrue(dataclasses.fields(CanonicalBaziChart))
        # 类型注解层面确认 frozen=True
        import inspect
        src = inspect.getsource(CanonicalBaziChart)
        self.assertIn("frozen=True", src)


class TestNoRecomputeContract(unittest.TestCase):
    """⑭a: 禁止下游重新计算 — from_bazi_chart 是唯一构造路径."""

    def test_from_bazi_chart_is_only_factory(self):
        """下游契约: CanonicalBaziChart 由 from_bazi_chart(BaziChart) 构造.

        直接验证: 传 BaziChart 得到正确的 canonical; 传非 BaziChart 应报错
        (下游不能绕过 compute() 直接堆 4 柱, 保证"下游 MUST NOT recompute").
        """
        chart, _ = _make_chart()
        canonical = CanonicalBaziChart.from_bazi_chart(chart)
        self.assertIsInstance(canonical, CanonicalBaziChart)
        # 值来源自 BaziChart, 不是下游重算
        self.assertEqual(canonical.day_master, chart.day_master)

    def test_from_bazi_chart_rejects_non_bazi_chart(self):
        """下游误传非 BaziChart → 报错 (fail-closed), 防止绕过计算核心."""
        from tongshu.models.canonical_bazi import CanonicalBaziChart as C
        with self.assertRaises(AttributeError):
            C.from_bazi_chart(None)


class TestP2AuthorityAnnotation(unittest.TestCase):
    """⑭c: P2 辨层字段权威性标注 (NOT_AUTHORIZED / AUXILIARY_SIGNAL).

    User 裁决: 不删除 spouse_star*/officer_mixed, 但必须标注它们
    不是 Bazi Calculation Core 的基础事实, 是子平辨层辅助信号.
    本测试锁死标注存在且值正确, 防止未来某次改动悄悄升级其权威性.
    """

    def test_spouse_star_annotations(self):
        self.assertEqual(calc_spouse_star_authority_status, "NOT_AUTHORIZED")
        self.assertEqual(calc_spouse_star_role, "AUXILIARY_SIGNAL")

    def test_spouse_star_strength_annotations(self):
        self.assertEqual(calc_spouse_star_strength_authority_status, "NOT_AUTHORIZED")
        self.assertEqual(calc_spouse_star_strength_role, "AUXILIARY_SIGNAL")

    def test_officer_mixed_annotations(self):
        self.assertEqual(calc_officer_mixed_authority_status, "NOT_AUTHORIZED")
        self.assertEqual(calc_officer_mixed_role, "AUXILIARY_SIGNAL")

    def test_annotations_not_authorized_semantics(self):
        """标注一致性: 所有 P2 辨层字段必须同为 NOT_AUTHORIZED + AUXILIARY_SIGNAL."""
        statuses = [
            calc_spouse_star_authority_status,
            calc_spouse_star_strength_authority_status,
            calc_officer_mixed_authority_status,
        ]
        roles = [
            calc_spouse_star_role,
            calc_spouse_star_strength_role,
            calc_officer_mixed_role,
        ]
        self.assertTrue(all(s == "NOT_AUTHORIZED" for s in statuses))
        self.assertTrue(all(r == "AUXILIARY_SIGNAL" for r in roles))


class TestProvenanceGate(unittest.TestCase):
    """BZ-FNDR-10.1: 唯一构造路径的可执行 gate (架构加固).

    User 裁决 (2026-09-10): BZ-FNDR-10(B) 遗留的非阻塞缺口 —
    "唯一构造路径"是文档声明而非可机器校验契约. 本轮加固:
      经 from_bazi_chart() 构造的实例可追踪为 factory provenance;
      直接实例化的实例可追踪为 direct;
      下游 Adapter 用 assert_canonical_gate() 消费前 fail-closed 校验.

    注意: 这是软约束 (不阻断语言层直接实例化, 不新增 dataclass 字段),
    把 "MUST NOT recompute" 变成可执行检查.
    """

    def _direct_instance(self, chart, bd):
        """构造一个绕过工厂、直接实例化的 CanonicalBaziChart."""
        return CanonicalBaziChart(
            year_pillar=chart.year_pillar,
            month_pillar=chart.month_pillar,
            day_pillar=chart.day_pillar,
            hour_pillar=chart.hour_pillar,
            day_master=chart.day_master,
            gender=chart.gender,
            start_age=chart.start_age,
            birth_datetime=bd,
        )

    def test_factory_instance_has_factory_provenance(self):
        chart, bd = _make_chart()
        canon = CanonicalBaziChart.from_bazi_chart(chart)
        self.assertTrue(is_factory_provenance(canon))
        self.assertEqual(provenance_of(canon), CANONICAL_PROVENANCE_FACTORY)

    def test_direct_instance_has_direct_provenance(self):
        chart, bd = _make_chart()
        direct = self._direct_instance(chart, bd)
        self.assertFalse(is_factory_provenance(direct))
        self.assertEqual(provenance_of(direct), CANONICAL_PROVENANCE_DIRECT)

    def test_gate_passes_for_factory_instance(self):
        chart, bd = _make_chart()
        canon = CanonicalBaziChart.from_bazi_chart(chart)
        assert_canonical_gate(canon, require_factory=True)  # 不抛错

    def test_gate_fails_closed_for_direct_instance(self):
        chart, bd = _make_chart()
        direct = self._direct_instance(chart, bd)
        with self.assertRaises(ValueError):
            assert_canonical_gate(direct, require_factory=True)

    def test_gate_audit_mode_does_not_block(self):
        chart, bd = _make_chart()
        direct = self._direct_instance(chart, bd)
        # require_factory=False 仅记录 provenance, 不阻断 (审计模式)
        assert_canonical_gate(direct, require_factory=False)  # 不抛错
        self.assertEqual(provenance_of(direct), CANONICAL_PROVENANCE_DIRECT)

    def test_provenance_constants_distinct(self):
        self.assertNotEqual(CANONICAL_PROVENANCE_FACTORY, CANONICAL_PROVENANCE_DIRECT)
        self.assertEqual(CANONICAL_PROVENANCE_FACTORY, "from_bazi_chart")
        self.assertEqual(CANONICAL_PROVENANCE_DIRECT, "direct-construction")


if __name__ == "__main__":
    unittest.main()
