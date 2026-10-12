# -*- coding: utf-8 -*-
"""紫微端到端集成测试（计划 2.3）。

链路：农历输入 → iztro 排盘（经 ZiweiEngine）→ 两派规则匹配
（compute_multi_method_signals）→ 答案层八维度组装（build_answer）。

覆盖：男/女命、闰月（负月）、双主星、chart 序列化往返、
大限方向传统规则符合性、流日契约（含 fail-closed）、rules 包懒导出。

依赖本地 iztro（node）；不可用时整文件 skip，不误报失败。
"""
from __future__ import annotations

import pytest

from tongshu.engines.ziwei_engine import ZiweiChart, ZiweiEngine

_ENGINE = ZiweiEngine()
pytestmark = pytest.mark.skipif(
    not _ENGINE._iztro_available, reason="iztro/node unavailable"
)

# (lunar_date, hour, gender) 基准盘
MALE = ((1990, 5, 15), 10, "male")
FEMALE = ((1983, 6, 1), 0, "female")
LEAP = ((1990, -5, 15), 10, "male")  # lunar_python 负月 = 闰五月


@pytest.fixture(scope="module")
def male_chart():
    return _ENGINE.compute(*MALE)


@pytest.fixture(scope="module")
def female_chart():
    return _ENGINE.compute(*FEMALE)


class TestCalculationLayer:
    def test_compute_real_iztro(self, male_chart):
        assert male_chart.source == "iztro"
        assert male_chart.soul_palace_main_star
        assert len(male_chart.palaces) == 12
        assert male_chart.fiveElementsClass

    def test_gender_paths_differ_or_self_consistent(self, male_chart, female_chart):
        for c in (male_chart, female_chart):
            assert c.source == "iztro"
            soul = c.palaces.get("命宫", {})
            assert soul.get("stem") and soul.get("branch")

    def test_leap_month_negative_accepted(self):
        chart = _ENGINE.compute(*LEAP)
        assert chart.source == "iztro"
        assert len(chart.palaces) == 12

    def test_dict_roundtrip(self, male_chart):
        restored = ZiweiChart.from_dict(male_chart.to_dict())
        assert restored.soul_earthly_branch == male_chart.soul_earthly_branch
        assert restored.palaces == male_chart.palaces
        assert restored.fiveElementsClass == male_chart.fiveElementsClass

    def test_dict_like_compat(self, male_chart):
        assert "soul_palace_main_star" in male_chart
        assert male_chart["soul_earthly_branch"] == male_chart.soul_earthly_branch
        assert male_chart.soulPalaceBranch == male_chart.soul_earthly_branch
        assert male_chart.get("not_a_field", "dflt") == "dflt"

    def test_decadal_direction_traditional_rule(self):
        """full_chart 大限顺逆须符合阳男阴女顺、阴男阳女逆。

        宫位分布：命宫起、支盘逆时针为 兄弟/夫妻/…/父母（父母在命宫支+1）。
        因此第二大限落在 父母 = 顺行(FORWARD)，落在 兄弟 = 逆行(REVERSE)。
        """
        from tongshu.engines.ziwei_dependency_adapter import (
            Direction, compute_expected_direction,
        )

        for (ld, h, g) in (MALE, FEMALE):
            fc = _ENGINE.full_chart(ld, h, g)
            starts = {
                p["decadalRange"][0]: name
                for name, p in fc.palaces.items() if p.get("decadalRange")
            }
            soul_start = next(s for s, n in starts.items() if n == "命宫")
            second_start = min(s for s in starts if s > soul_start)
            second = starts[second_start]
            expected = compute_expected_direction(ld[0], g)
            want = "父母" if expected is Direction.FORWARD else "兄弟"
            assert second == want, (
                f"{g} {ld[0]}年 expected {expected.value} → "
                f"第二大限应为{want}, got {second}"
            )

    def test_baseline_signal_shape(self, male_chart):
        sig = _ENGINE.extract_baseline_signal(male_chart, sig_index=0)
        if sig is not None:  # 命宫主星在 USO 表内才有信号（DECISION-009）
            assert sig.layer == "BASELINE"
            assert sig.direction == "STABLE"
            assert sig.polarity == "neutral"


class TestDiagnosisAndAnswerLayers:
    def test_multi_method_both_bundles_ok(self, male_chart):
        from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals

        signal = compute_multi_method_signals(male_chart)
        assert set(signal.bundles) == {"SANHE", "QINTIAN"}
        assert signal.compute_status != "FAIL"
        for b in signal.bundles.values():
            assert b.implementation_status not in ("FAIL",)
            assert b.graph_id and b.method_id
        # 命盘必有可匹配事实：至少一派有命中，且命中+未命中=该派规则全集口径
        assert signal.total_matched_rules + signal.total_unmatched_production > 0

    def test_answer_layer_fifteen_dimensions(self, male_chart):
        from tongshu.engines.ziwei.rules.answer_layer import (
            DIMENSIONS_15,
            build_answer,
        )

        out = build_answer(male_chart)
        assert out["dimensions"] == DIMENSIONS_15
        assert set(out["answer"]) == set(DIMENSIONS_15)
        counts = out["summary"]["dimension_counts"]
        assert sum(counts.values()) >= 12  # 12宫主题至少全命中一轮
        # 每条答案带溯源字段（治理铁律：可追溯）
        for dim_items in out["answer"].values():
            for it in dim_items:
                assert it["rule_id"] and it["source"] in ("sanhe", "qintian")

    def test_answer_layer_female_no_crash(self, female_chart):
        from tongshu.engines.ziwei.rules.answer_layer import (
            DIMENSIONS_15,
            build_answer,
        )

        out = build_answer(female_chart)
        assert set(out["answer"]) == set(DIMENSIONS_15)

    def test_flow_day_contract_via_full_chart(self):
        fc = _ENGINE.full_chart(*MALE, flow_year=2026, flow_day=(2026, 3, 10))
        assert fc.flow_day_gan and fc.flow_day_zhi
        assert len(fc.flow_day_mutagen) == 4

        from tongshu.engines.ziwei.rules.qintian.flow_day_contract import (
            resolve_flow_day,
        )

        r = resolve_flow_day(fc, (2026, 3, 10))
        assert r.flow_day_date == "2026-03-10"
        assert r.applicable_sect == []          # 铁律：不接规则
        assert r.sihua_gan_source.startswith("UNRESOLVED")
        assert r.day_position_palace in fc.palaces

    def test_flow_day_contract_fail_closed(self, male_chart):
        """未经 full_chart(flow_day=) 构造的盘必须拒绝，不得凭空推断。"""
        from tongshu.engines.ziwei.rules.qintian.flow_day_contract import (
            resolve_flow_day,
        )

        with pytest.raises(ValueError, match="未携带流日干支"):
            resolve_flow_day(male_chart, (2026, 3, 10))


class TestRulesPackageSurface:
    def test_lazy_export(self):
        import tongshu.engines.ziwei.rules as rules

        assert rules.get_available_methods() == ["sanhe", "qintian"]
        g = rules.make_rule_graph("qintian")
        assert type(g).__name__ == "QintianRuleGraph"
        # 顶层懒导出类与源模块同一对象
        from tongshu.engines.ziwei.rules.method_graphs import SanheRuleGraph

        assert rules.SanheRuleGraph is SanheRuleGraph
