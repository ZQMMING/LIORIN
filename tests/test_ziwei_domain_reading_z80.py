# -*- coding: utf-8 -*-
"""Z80: 维度断语层测试 — 十二宫逐宫综合解读 + 领域聚合。

覆盖 domain_reading.py（此前零测试覆盖）：
  - 十二宫逐宫解读结构与必填字段
  - 领域聚合（DOMAIN_PALACES 映射完整性，十二宫全归属）
  - 自化解读通路（zihua_map 消费）
  - 空宫借对宫处理
  - 对宫冲击解读
  - 关键概念抽取
  - 新增领域：子女 / 父母

另附 interpretation 接线回归：_synthesize_dimension_conclusion 的
chart 入参必须生效，自化解读不得再恒空（Z80 接线缺陷防回归）。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.domain_reading import (
    DOMAIN_PALACES,
    MINOR_STAR_BY_PALACE,
    OPPOSITE_IMPACT,
    PALACE_ALIAS,
    PALACE_DIM_MAP,
    ZIHUA_BY_PALACE,
    build_domain_readings,
)

# 固定样本盘：1983-09-29 巳时男（项目内既有测试基准盘）
_LUNAR = (1983, 9, 29)
_HOUR = 11
_GENDER = "male"

_DOMAINS = {
    "健康", "学业", "事业", "财运", "人际", "婚恋",
    "子女", "父母",
}

# 十二宫规范名（iztro 口径）
_CANONICAL_PALACES = {
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "官禄", "田宅", "福德", "父母", "仆役",
}


def _engine():
    return ZiweiEngine()


def _chart():
    return _engine().full_chart(_LUNAR, _HOUR, _GENDER)


def _readings():
    eng = _engine()
    chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
    zihua_map = eng.get_all_zihua(chart)
    return build_domain_readings(chart, zihua_map), zihua_map


class TestDomainReadingContracts:
    """表结构契约：映射表完整性。"""

    def test_domain_palaces_keys(self):
        assert set(DOMAIN_PALACES) == _DOMAINS

    def test_domain_palaces_values_nonempty(self):
        for domain, palaces in DOMAIN_PALACES.items():
            assert palaces, f"{domain} 无关联宫位"
            for p in palaces:
                assert p in PALACE_DIM_MAP, f"{domain} 引用了未登记宫位 {p}"

    def test_palace_alias_table(self):
        """别名表：交友/仆役 必须互认。"""
        assert PALACE_ALIAS.get("交友") == "仆役"
        assert PALACE_ALIAS.get("仆役") == "仆役"

    def test_declared_palaces_resolvable(self):
        """声明宫位必须可在标准十二宫名中解析（直连或经别名）。"""
        canonical = set(PALACE_DIM_MAP)
        for domain, palaces in DOMAIN_PALACES.items():
            for p in palaces:
                resolved = p if p in canonical else PALACE_ALIAS.get(p)
                assert resolved in canonical, (
                    f"{domain} 的宫位 {p} 无法解析为规范宫名"
                )

    def test_opposite_impact_covers_twelve(self):
        """对宫冲击表覆盖十二宫（允许 12 键，仆役/交友兼容）。"""
        assert len(OPPOSITE_IMPACT) >= 12

    def test_zihua_table_covers_twelve(self):
        """自化解读表覆盖十二宫。"""
        assert len(ZIHUA_BY_PALACE) >= 12

    def test_minor_star_table_covers_key_palaces(self):
        """辅星解读表至少覆盖命/财/官三主宫。"""
        for p in ("命宫", "财帛", "官禄"):
            assert p in MINOR_STAR_BY_PALACE


class TestPalaceReadings:
    """十二宫逐宫解读。"""

    def test_twelve_palaces(self):
        out, _ = _readings()
        assert len(out.palace_readings) == 12

    def test_palace_names_unique_and_known(self):
        out, _ = _readings()
        names = [pr.palace for pr in out.palace_readings]
        assert len(set(names)) == 12
        for n in names:
            assert n in PALACE_DIM_MAP, f"未知宫位 {n}"

    def test_every_palace_has_conclusion(self):
        """每宫必须有综合断语段落（不可为空）。"""
        out, _ = _readings()
        empty = [pr.palace for pr in out.palace_readings if not pr.conclusion.strip()]
        assert not empty, f"以下宫位断语为空: {empty}"

    def test_dimension_mapped(self):
        out, _ = _readings()
        for pr in out.palace_readings:
            assert pr.dimension == PALACE_DIM_MAP[pr.palace]

    def test_stars_field_is_list(self):
        out, _ = _readings()
        for pr in out.palace_readings:
            assert isinstance(pr.stars, list)

    def test_conclusion_contains_interpretation_fragments(self):
        """综合断语应由主星/辅星/四化/自化/对宫等片段组成。"""
        out, _ = _readings()
        for pr in out.palace_readings:
            fragments = [
                pr.major_interpretation, pr.minor_interpretation,
                pr.sihua_interpretation, pr.zihua_interpretation,
                pr.opposite_interpretation,
            ]
            assert any(f for f in fragments), f"{pr.palace} 无任何解读片段"


class TestDomainReadings:
    """领域聚合（Z80 修复后由六大领域扩为八大领域）。"""

    def test_domain_count(self):
        out, _ = _readings()
        assert len(out.domain_readings) == len(_DOMAINS)

    def test_domain_names(self):
        out, _ = _readings()
        assert {dr.domain for dr in out.domain_readings} == _DOMAINS

    def test_all_twelve_palaces_covered_by_domains(self):
        """Z80 修复防回归：十二宫必须全部归属至少一个领域。

        历史缺陷：子女/父母两宫未纳入任何领域聚合，领域层无法覆盖这两条人生线。
        """
        covered = set()
        for palaces in DOMAIN_PALACES.values():
            for p in palaces:
                covered.add(PALACE_ALIAS.get(p, p))
        missing = _CANONICAL_PALACES - covered
        assert not missing, f"以下宫位未归属任何领域: {sorted(missing)}"

    def test_every_domain_has_conclusion(self):
        out, _ = _readings()
        empty = [dr.domain for dr in out.domain_readings if not dr.conclusion.strip()]
        assert not empty, f"以下领域断语为空: {empty}"

    def test_related_palaces_match_table(self):
        """related_palaces 应与 DOMAIN_PALACES 声明一致（经别名解析后）。

        注：盘内宫名以 iztro 为准（仆役），声明表亦已收敛为「仆役」，
        故此处应逐字相等；若未来声明表改回「交友」，PALACE_ALIAS 会兜底。
        """
        out, _ = _readings()
        for dr in out.domain_readings:
            expected = [
                PALACE_ALIAS.get(p, p) for p in DOMAIN_PALACES[dr.domain]
            ]
            assert dr.related_palaces == expected

    def test_no_declared_palace_silently_dropped(self):
        """Z80 缺陷防回归：声明宫位不得因命名差异被静默丢弃。

        历史缺陷：DOMAIN_PALACES 写「交友」而盘内为「仆役」，导致
        学业/人际两领域各丢一宫（related 长度小于声明长度）。
        """
        out, _ = _readings()
        for dr in out.domain_readings:
            declared = DOMAIN_PALACES[dr.domain]
            assert len(dr.related_palaces) == len(declared), (
                f"领域[{dr.domain}] 声明 {declared}，"
                f"实际解析 {dr.related_palaces} —— 有宫位被丢弃"
            )

    def test_risk_and_suggestions_are_lists(self):
        out, _ = _readings()
        for dr in out.domain_readings:
            assert isinstance(dr.risk_points, list)
            assert isinstance(dr.suggestions, list)


class TestZihuaPassthrough:
    """自化解读通路：zihua_map 必须被消费到。"""

    def test_zihua_map_nonempty_for_sample(self):
        """样本盘应存在自化宫位（否则本测试无意义）。"""
        _, zihua_map = _readings()
        assert zihua_map, "样本盘无自化数据，测试前提不成立"

    def test_zihua_lands_in_palace_reading(self):
        """凡 zihua_map 命中的宫位，其 zihua_interpretation 必须非空。"""
        out, zihua_map = _readings()
        by_palace = {pr.palace: pr for pr in out.palace_readings}
        for pname in zihua_map:
            if pname not in by_palace:
                continue
            pr = by_palace[pname]
            assert pr.zihua_interpretation, (
                f"{pname} 在 zihua_map 中有自化 ({zihua_map[pname]})，"
                f"但 zihua_interpretation 为空"
            )

    def test_zihua_absent_when_map_empty(self):
        """不传 zihua_map 时，自化解读应整体为空（不臆造）。"""
        chart = _chart()
        out = build_domain_readings(chart, {})
        assert all(not pr.zihua_interpretation for pr in out.palace_readings)


class TestEdgeCases:
    """边界：空宫、对宫、兼容键。"""

    def test_opposite_interpretation_present(self):
        out, _ = _readings()
        got = [pr for pr in out.palace_readings if pr.opposite_interpretation]
        assert got, "无任何宫位产出对宫冲击解读"

    def test_borrowed_palace_not_empty(self):
        """空宫（无主星）也应产出断语（借对宫/辅星路径）。"""
        out, _ = _readings()
        empty_major = [pr for pr in out.palace_readings
                       if not pr.major_interpretation or pr.major_interpretation == "无主星"]
        for pr in empty_major:
            assert pr.conclusion.strip(), f"空宫 {pr.palace} 结论为空"

    def test_servant_palace_alias(self):
        """仆役/交友 兼容：任一写法都应能取到辅星表。"""
        has_servant = "仆役" in PALACE_DIM_MAP
        has_friend = "交友" in PALACE_DIM_MAP
        assert has_servant or has_friend

    def test_to_dict_serializable(self):
        """输出可序列化（下游文章层消费）。"""
        import json
        out, _ = _readings()
        d = out.to_dict()
        assert len(d["palace_readings"]) == 12
        assert len(d["domain_readings"]) == len(_DOMAINS)
        json.dumps(d, ensure_ascii=False)  # 不抛异常即通过


class TestNewDomains:
    """Z80 新增领域：子女 / 父母。"""

    def test_children_domain_nonempty(self):
        out, _ = _readings()
        dr = next(d for d in out.domain_readings if d.domain == "子女")
        assert dr.related_palaces, "子女领域无关联宫位"
        assert dr.conclusion.strip(), "子女领域断语为空"

    def test_parent_domain_nonempty(self):
        out, _ = _readings()
        dr = next(d for d in out.domain_readings if d.domain == "父母")
        assert dr.related_palaces, "父母领域无关联宫位"
        assert dr.conclusion.strip(), "父母领域断语为空"

    def test_children_domain_mentions_children_palace(self):
        """子女领域结论必须含子女宫内容。"""
        out, _ = _readings()
        dr = next(d for d in out.domain_readings if d.domain == "子女")
        assert "子女宫" in dr.conclusion

    def test_parent_domain_mentions_parent_palace(self):
        """父母领域结论必须含父母宫内容。"""
        out, _ = _readings()
        dr = next(d for d in out.domain_readings if d.domain == "父母")
        assert "父母宫" in dr.conclusion


class TestInterpretationZihuaWiring:
    """Z80 接线缺陷防回归。

    历史缺陷：_synthesize_dimension_conclusion 内 chart_dict 依赖不存在的
    state._chart_ref，恒为 {"palaces": {}}，导致自化解读在综合断语中 100% 丢失。
    本测试固定该缺陷不再出现。
    """

    def test_zihua_appears_in_dimension_conclusion(self):
        from tongshu.engines.ziwei.rules.interpretation import build_life_reading
        from tongshu.engines.ziwei.rules.multi_method import (
            compute_multi_method_signals,
        )

        eng = ZiweiEngine()
        chart = eng.full_chart(_LUNAR, _HOUR, _GENDER)
        reading = build_life_reading(
            chart, compute_multi_method_signals(chart), target_year=2024
        )
        dims = reading.dimensions
        assert len(dims) == 12

        # 全部维度必须有断语
        empty = [d.dimension for d in dims if not (d.conclusion or "").strip()]
        assert not empty, f"以下维度断语为空: {empty}"

        # 自化解读不得再恒空
        with_zihua = [d for d in dims if "自化" in (d.conclusion or "")]
        assert with_zihua, (
            "12 维断语中无任何自化解读 —— Z80 接线缺陷回归"
            "（检查 _synthesize_dimension_conclusion 的 chart 入参是否生效）"
        )

    def test_synthesize_accepts_chart_param(self):
        """签名契约：chart 必须为可传参（而非依赖 state 私有字段）。"""
        import inspect
        from tongshu.engines.ziwei.rules.interpretation import (
            ZiweiLifeReadingBuilder,
        )

        sig = inspect.signature(
            ZiweiLifeReadingBuilder._synthesize_dimension_conclusion
        )
        assert "chart" in sig.parameters, "缺少 chart 入参"

    def test_synthesize_without_chart_still_safe(self):
        """chart=None 时不得抛异常（向后兼容旧调用方）。"""
        from tongshu.engines.ziwei.rules.interpretation import (
            ZiweiDimensionState,
            ZiweiLifeReadingBuilder,
        )

        eng = ZiweiEngine()
        builder = ZiweiLifeReadingBuilder(eng)
        state = ZiweiDimensionState(
            dimension="性情禀赋", palace="命宫", natal_stars=["紫微"]
        )
        # 不传 chart，应正常返回字符串
        r = builder._synthesize_dimension_conclusion(
            "命宫", "性情禀赋", ["紫微"], state, {}, {}, None
        )
        assert isinstance(r, str)

    def test_exing_star_expresses_independence(self):
        """规则补缺防回归：七杀/破军在命宫须表达「独立要强」语义。

        缺口来源：覆盖率审计（ziwei_coverage_audit.py）报出
        [命宫] 独立要强，不喜受人支配 → GAP，真实规则缺口。
        """
        from tongshu.engines.ziwei.rules.interpretation import PALACE_STAR_RULES

        xing = PALACE_STAR_RULES["性情禀赋"]["七杀"]
        texts = "".join(r["text"] for r in xing)
        assert "要强" in texts, "七杀命宫断语缺少「要强」语义"
        assert "不喜受人支配" in texts, "七杀命宫断语缺少「不喜受人支配」语义"

    def test_palace_dimension_map_defined_once(self):
        """Z80 修复防回归：PALACE_DIMENSION_MAP 不得重复定义。

        历史缺陷：interpretation.py 内该表被定义两次（后定义静默覆盖前定义），
        属高危重复，一旦两处不一致将产生难以定位的映射错误。
        """
        import re
        from pathlib import Path
        import tongshu.engines.ziwei.rules.interpretation as interp

        src = Path(interp.__file__).read_text(encoding="utf-8")
        n_map = len(re.findall(r"^PALACE_DIMENSION_MAP\s*=", src, re.M))
        n_order = len(re.findall(r"^DIMENSION_ORDER\s*=", src, re.M))
        assert n_map == 1, f"PALACE_DIMENSION_MAP 定义了 {n_map} 次（应为 1）"
        assert n_order == 1, f"DIMENSION_ORDER 定义了 {n_order} 次（应为 1）"

    def test_dimension_map_values_match_order(self):
        """PALACE_DIMENSION_MAP 值域必须与 DIMENSION_ORDER 一致。"""
        from tongshu.engines.ziwei.rules.interpretation import (
            DIMENSION_ORDER,
            PALACE_DIMENSION_MAP,
        )

        assert set(PALACE_DIMENSION_MAP.values()) == set(DIMENSION_ORDER)
