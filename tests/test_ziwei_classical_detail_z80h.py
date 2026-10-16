# -*- coding: utf-8 -*-
"""Z80-H：经典细则层（classical_detail 接线）+ doujun 收敛 + 资产索引 单测。"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.classical_detail import build_classical_detail
from tongshu.engines.ziwei.rules.answer_layer import build_answer
from tongshu.engines.ziwei.rules import temporal_facts, pattern_rules, nvming_rules
from tongshu.engines.ziwei.rules.asset_index import (
    AssetDisposition, ZIWEI_UNWIRED_ASSETS, asset_inventory,
)

_ENG = ZiweiEngine()
_HAVE_IZTRO = _ENG._iztro_available

# 1983-09-29 12时 女；1990-05-15 08时 男
_CASES = {
    "f1983": ((1983, 9, 29), 12, "female"),
    "m1990": ((1990, 5, 15), 8, "male"),
}


def _chart(key):
    lunar, hour, gender = _CASES[key]
    return _ENG.full_chart(lunar, hour, gender)


@unittest.skipUnless(_HAVE_IZTRO, "iztro 不可用（需 node_modules/iztro）")
class TestClassicalDetail(unittest.TestCase):

    def test_all_sections_present(self):
        d = build_classical_detail(_chart("f1983"))
        for k in ("palace_jue", "classical_patterns", "nvming", "child_limit",
                  "limit_advanced", "temporal_rules", "aux_verdicts",
                  "temporal_facts", "summary"):
            self.assertIn(k, d)

    def test_aux_verdicts_reachable_and_real(self):
        """辅煞杂曜断语：非空，且命中星确在本盘（此前 102 键不可达）。"""
        ch = _chart("f1983")
        d = build_classical_detail(ch)
        self.assertTrue(d["aux_verdicts"])
        present = set()
        for p in ch.palaces.values():
            present |= set(p.get("major", []) or [])
            present |= set(p.get("minor", []) or [])
            present |= set(p.get("adjective", []) or [])
        for ent in d["aux_verdicts"]:
            for s in ent["hit"]:
                if s != "斗君":
                    self.assertIn(s, present, ent)
            self.assertTrue(ent["classic"], ent)

    def test_palace_jue_matches_soul_branch(self):
        """十二宫得地/失陷诀：命宫地支须落在命中条的 palace_branch 内。"""
        ch = _chart("f1983")
        d = build_classical_detail(ch)
        self.assertTrue(d["palace_jue"])
        for ent in d["palace_jue"]:
            self.assertIn(ch.soul_earthly_branch, ent["palace_branch"])

    def test_classical_patterns_stars_within_scope(self):
        """格局候选：supporting_stars 须全部在本盘命三方（不得硬编造）。"""
        ch = _chart("m1990")
        d = build_classical_detail(ch)
        present = set()
        for p in ch.palaces.values():
            present |= set(p.get("major", []) or [])
            present |= set(p.get("minor", []) or [])
        for ent in d["classical_patterns"]:
            for s in ent["supporting_stars"]:
                self.assertIn(s, present, ent["pattern_name"])
            self.assertEqual(ent["match_level"], "candidate")

    def test_nvming_only_female(self):
        self.assertTrue(build_classical_detail(_chart("f1983"))["nvming"])
        self.assertEqual(build_classical_detail(_chart("m1990"))["nvming"], [])

    def test_nvming_hit_stars_real(self):
        ch = _chart("f1983")
        d = build_classical_detail(ch)
        ming = set(ch.palaces["命宫"].get("major", []) or []) | set(
            ch.palaces["命宫"].get("minor", []) or [])
        for ent in d["nvming"]:
            for s in ent["hit_stars"]:
                self.assertIn(s, ming)

    def test_child_limit_always_has_strength_rule(self):
        d = build_classical_detail(_chart("f1983"))
        self.assertIn("CL-05", [x["rule_id"] for x in d["child_limit"]])

    def test_temporal_facts_block(self):
        d = build_classical_detail(_chart("f1983"))
        tf = d["temporal_facts"]
        self.assertIn("doujun_palace", tf)
        self.assertEqual(tf["doujun_palace"], _chart("f1983").doujun_palace)
        self.assertIn("flow_stars", tf)
        self.assertEqual(set(tf["flow_stars"]), {"禄", "羊", "陀"})


@unittest.skipUnless(_HAVE_IZTRO, "iztro 不可用")
class TestBuildAnswerIntegration(unittest.TestCase):

    def test_classical_detail_key_added(self):
        ans = build_answer(_chart("f1983"))
        self.assertIn("classical_detail", ans)
        self.assertIn("summary", ans["classical_detail"])

    def test_existing_channels_unchanged(self):
        """接线不得改变既有 12 宫位维 / 体用层结构。"""
        from tongshu.engines.ziwei.rules.answer_layer import (
            PALACE_DIMENSIONS, BODY_USE_KEYS,
        )
        ans = build_answer(_chart("f1983"))
        self.assertEqual(ans["dimensions"], PALACE_DIMENSIONS)
        self.assertEqual(set(ans["answer"].keys()), set(PALACE_DIMENSIONS))
        self.assertEqual(set(ans["body_use"].keys()), set(BODY_USE_KEYS))


class TestDoujunConvergence(unittest.TestCase):
    """斗君安法收敛：引擎与 temporal_facts 公式一致（单一事实源）。"""

    def test_formula_equivalent(self):
        # 1984 甲子年，农历三月，辰时(idx=2) → 两实现应一致
        got = temporal_facts.doujun_branch("子", 3, 2)
        # 手算：i=0 → month=(0-2)%12=10(戌) → j=10 → (10+2)%12=0(子)
        self.assertEqual(got, "子")

    def test_small_limit_start(self):
        self.assertEqual(temporal_facts.small_limit_start_branch("寅"), "辰")
        self.assertEqual(temporal_facts.small_limit_start_branch("子"), "戌")


class TestAssetIndexWired(unittest.TestCase):

    def test_six_assets_wired(self):
        wired = [a for a in ZIWEI_UNWIRED_ASSETS
                 if a.disposition == AssetDisposition.WIRED]
        self.assertEqual(len(wired), 6)
        for a in wired:
            self.assertTrue(a.wired_to, a.module)

    def test_report_reflects_wired(self):
        from tongshu.engines.ziwei.rules.asset_index import asset_report
        rep = asset_report()["by_disposition"]
        self.assertEqual(len(rep.get(AssetDisposition.WIRED, [])), 6)
        self.assertEqual(rep.get(AssetDisposition.CONVERGE), ["palace_relationship"])

    def test_inventory_exposes_wired_to(self):
        for row in asset_inventory():
            if row["disposition"] == AssetDisposition.WIRED:
                self.assertTrue(row["wired_to"])


if __name__ == "__main__":
    unittest.main()
