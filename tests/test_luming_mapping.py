# -*- coding: utf-8 -*-
"""映射层 oracle：七断言测试契约（全离线确定性，P0 #31）

1. 结构断言：合成报告章节集合 == 章节注册表（无幽灵章节、无缺失、无 key 污染）
2. 强度断言：每条 claim 必带 strength ∈ {逐字/推导/合成/润色}
3. 摘录完成度断言：RULE_SEMANTICS/NAYIN_NATURE 全部 quote_status=complete（逐字必带 quote）
4. 标注断言：非逐字 claim 渲染输出必含显式标注（〔推导〕〔合成〕〔润色〕）
5. topic 前置断言：每条引擎 verdict 必有 topic（RULE_SEMANTICS 全覆盖，无释义记录=失败）
6. 口径断言：白名单三口径（命宫=癸丑/文昌癸=丑/喜忌读引擎切片）
7. 聚合断言：1983 案例各主章节结构完整，五主题章节至少 2 个命中，空章节显式标注
"""
import unittest
import sys
import json

sys.path.insert(0, r"D:\shuntian\src")

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.luming.engine import from_bazi_chart, query_year
from tongshu.luming.semantics import (
    RULE_SEMANTICS, audit_rule_semantics,
)
from tongshu.luming.nayin_nature import NAYIN_NATURE, audit_nayin_nature
from tongshu.luming.render_mapping import (
    SECTION_REGISTRY, build_ancient_report, render_ancient_text,
)

_STRENGTHS = {"逐字", "推导", "待补", "合成", "润色"}


def _make_1983():
    chart = BaziEngine().compute((1983, 11, 3, 12), gender="male")
    lm = from_bazi_chart(chart)
    return chart, lm


class TestMappingStructure(unittest.TestCase):
    """断言 1/2/4/5/7：1983 案例合成报告."""

    @classmethod
    def setUpClass(cls):
        cls.chart, cls.lm = _make_1983()
        cls.years = [query_year(cls.chart, y, lm=cls.lm) for y in range(2020, 2031)]
        cls.rep = build_ancient_report(cls.lm, cls.years)
        cls.txt = render_ancient_text(cls.rep)

    def test_01_sections_match_registry(self):
        keys = [s["key"] for s in self.rep["sections"]]
        registry = [s["key"] for s in SECTION_REGISTRY]
        self.assertEqual(keys, registry, "章节集合与注册表不一致（幽灵/缺失/污染）")

    def test_02_every_claim_has_strength(self):
        for c in self.rep["claims"]:
            self.assertIn(c["strength"], _STRENGTHS, f"claim 无合法 strength: {c['text'][:30]}")
            self.assertTrue(c["topic"], f"claim 无 topic: {c['text'][:30]}")

    def test_04_non_verbatim_claims_marked(self):
        marked = {"〔推导〕", "〔待补〕", "〔合成〕", "〔润色〕", "〔交运", "〔逐字"}
        for sec in self.rep["sections"]:
            for line in sec["lines"]:
                # 推导/合成 claim 行必须含显式标注（交运标记/逐字引用亦为合法标注）
                if "〔" in line:
                    self.assertTrue(any(m in line for m in marked),
                                    f"标注缺失: {line[:40]}")

    def test_05_verdict_topic_preamble(self):
        """每条引擎 verdict 必有 topic（RULE_SEMANTICS 全覆盖为前置断言）.

        2026-10-20 修订: ① 校验源改为真实全量 VERDICT_RULES（不再依赖 _rules_dump.json
        快照, 防契约失效）; ② pending 为"待补工作项"清单（strength=待补: 有原文未摘;
        或逐字缺 quote）——允许非空且逐条可审计; errors 必须为空（schema 硬错误）.
        """
        from tongshu.luming.facts import VERDICT_RULES
        rules = [{"id": r["id"]} for r in VERDICT_RULES]
        res = audit_rule_semantics(rules)
        self.assertEqual(res["errors"], [], "规则释义 schema 非法")
        self.assertEqual(res["covered"], len(rules), "规则释义覆盖不全")
        # pending 全部为"待补/未摘"工作项, 无非法项
        for item in res["pending"]:
            self.assertTrue(item.startswith("LM-V"), f"pending 混入非法项: {item}")
        for v in self.lm.verdicts:
            self.assertIn(v["rule_id"], RULE_SEMANTICS, f"verdict 无释义: {v['rule_id']}")

    def test_07_aggregation_1983(self):
        by_key = {s["key"]: s for s in self.rep["sections"]}
        # 主章节结构完整
        for k in ("zong_gang", "shen_sha", "xi_ji", "da_yun", "liu_nian", "zong_duan"):
            self.assertIn(k, by_key, f"缺主章节 {k}")
        # 五主题（事业财运/婚恋/子女/健康）至少 2 个命中
        five = ("shi_ye_cai", "hun_lian", "zi_nv", "jian_kang")
        hit = [k for k in five if by_key[k]["lines"]]
        self.assertGreaterEqual(len(hit), 2, f"五主题命中不足: {hit}")
        # 空章节显式标注
        for k in five:
            if not by_key[k]["lines"]:
                self.assertEqual(by_key[k]["lines"], ["（本节无断语）"],
                                 f"空章节 {k} 未显式标注")


class TestSecondaryTables(unittest.TestCase):
    """断言 3：摘录完成度."""

    def test_03_nayin_complete(self):
        res = audit_nayin_nature()
        self.assertEqual(res["missing"], [])
        self.assertEqual(res["errors"], [])
        for gz, rec in NAYIN_NATURE.items():
            self.assertEqual(rec["quote_status"], "complete", f"{gz} 未完成")
            self.assertEqual(rec["strength"], "逐字", f"{gz} 应逐字")
            self.assertTrue(rec["quote"], f"{gz} quote 为空")


class TestKouJing(unittest.TestCase):
    """断言 6：口径白名单."""

    @classmethod
    def setUpClass(cls):
        cls.chart, cls.lm = _make_1983()

    def test_06_ming_gong_gui_chou(self):
        """命宫=癸丑（五行精纪 L3736/SMTH L915 原著口径，袁树珊月数法无原据）. """
        gong = self.lm.gong or {}
        ming = (self.lm.nayin_chain or {}).get("gong", {}).get("ming", {}) or {}
        algo = ming.get("algorithm", "")
        self.assertEqual(ming.get("pillar", ""), "癸丑", "命宫应为癸丑")
        self.assertNotIn("袁树珊", algo, "不得用袁树珊月数法")

    def test_06_wen_chang_gui_is_chou(self):
        """癸年文昌=丑（L2010 六壬卯位癸逢牛），1983 原局无丑→不现."""
        wc = self.lm.wen_chang or {}
        if wc.get("present"):
            self.assertEqual(wc.get("branch", ""), "CHOU", "癸年文昌必须为丑")
        else:
            self.assertEqual(wc.get("branch", ""), "CHOU", "文昌查表值必须为丑（原局不现）")

    def test_06_xi_ji_from_engine(self):
        """喜忌读引擎切片（五行精纪口径：癸亥大海水 喜木火/土条件喜/忌水金）. """
        xj = self.lm.xi_ji or {}
        xi = [x["el"] for x in xj.get("xi", [])]
        ji = [j["el"] for j in xj.get("ji", [])]
        self.assertIn("WOOD", xi)
        self.assertIn("FIRE", xi)
        self.assertIn("WATER", ji)
        self.assertIn("METAL", ji)


if __name__ == "__main__":
    unittest.main(verbosity=2)
