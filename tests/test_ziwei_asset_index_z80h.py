# -*- coding: utf-8 -*-
"""Z80-H：11 未接线资产索引 + palace_relationship 收敛 单元测试。"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei.rules.asset_index import (
    AssetDisposition,
    ZIWEI_UNWIRED_ASSETS,
    asset_inventory,
    asset_report,
    load_asset,
    self_check,
)
from tongshu.engines.ziwei.rules import palace_relationship as pr
from tongshu.engines.ziwei_palace_resolution import EARTHLY_BRANCHES


class TestAssetIndex(unittest.TestCase):
    """未接线资产索引。"""

    def test_self_check_ok(self):
        rep = self_check()
        self.assertTrue(rep["ok"], f"problems: {rep['problems']}")

    def test_eleven_modules_registered(self):
        self.assertEqual(len(ZIWEI_UNWIRED_ASSETS), 11)

    def test_dispositions_cover_four_classes(self):
        report = asset_report()
        by = report["by_disposition"]
        # Z80-H 接线后：6 个 WIRE 资产已接入 classical_detail 通道
        self.assertEqual(len(by.get(AssetDisposition.WIRED, [])), 6)
        self.assertEqual(len(by.get(AssetDisposition.WIRE, [])), 0)
        self.assertEqual(by.get(AssetDisposition.CONVERGE), ["palace_relationship"])
        self.assertEqual(len(by.get(AssetDisposition.EVIDENCE_INDEX, [])), 4)

    def test_inventory_counts_nonzero(self):
        """除收敛项外，各资产内容规模 > 0。"""
        for row in asset_inventory():
            if row["disposition"] == AssetDisposition.CONVERGE:
                continue
            self.assertGreater(row["total_items"], 0, row["module"])

    def test_load_asset_ok_and_fail_closed(self):
        mod = load_asset("pattern_rules")
        self.assertTrue(hasattr(mod, "ALL_PATTERNS"))
        with self.assertRaises(ValueError):
            load_asset("no_such_module")


class TestPalaceRelationshipConvergence(unittest.TestCase):
    """palace_relationship 收敛：地支序复用 canonical，行为不变。"""

    def test_branch_order_is_canonical(self):
        self.assertIs(pr.BRANCH_ORDER, EARTHLY_BRANCHES)

    def test_relation_semantics(self):
        self.assertEqual(pr.relation("子", "子"), pr.SAME_PALACE)
        self.assertEqual(pr.relation("子", "午"), pr.OPPOSITE)   # +6
        self.assertEqual(pr.relation("子", "辰"), pr.TRINE_1)    # +4
        self.assertEqual(pr.relation("子", "申"), pr.TRINE_2)    # +8

    def test_three_square_four(self):
        tsf = pr.three_square_four("子")
        self.assertEqual(tsf["self"], "子")
        self.assertEqual(tsf["opposite"], "午")
        self.assertEqual(tsf["trine_1"], "辰")
        self.assertEqual(tsf["trine_2"], "申")

    def test_in_three_square_four(self):
        self.assertTrue(pr.in_three_square_four("子", "午"))
        self.assertTrue(pr.in_three_square_four("子", "辰"))
        self.assertFalse(pr.in_three_square_four("子", "丑"))


if __name__ == "__main__":
    unittest.main()
