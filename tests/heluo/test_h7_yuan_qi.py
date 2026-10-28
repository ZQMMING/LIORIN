# -*- coding: utf-8 -*-
"""H7: 元气层接入回归测试

覆盖：
  1. compute_yuan_qi 单元映射（与模块 docstring 三案例互证）
  2. canonical 主链接入：HeluoResult.yuan_qi 有值、状态正确
  3. frozen_state 序列化暴露元气流
"""
import unittest

from heluo_engine.engines.heluo.yuan_qi import (
    compute_yuan_qi, YuanQiState, STEM_TO_TRIGRAM, BRANCH_TO_TRIGRAM,
)
from heluo_engine.engines.heluo.canonical import HeluoResult
from heluo_engine.engines.heluo.frozen_state import build_frozen_state
from heluo_engine.adapter import HeluoAdapter


class TestYuanQiMapping(unittest.TestCase):
    """天干纳甲 / 地支后天宫映射（原典 + 案例互证）。"""

    def test_stem_nayin(self):
        # 原典明文 + 案例互证：癸巳→坤、戊申→坎、甲辰→乾
        self.assertEqual(STEM_TO_TRIGRAM["甲"], "乾")
        self.assertEqual(STEM_TO_TRIGRAM["壬"], "乾")
        self.assertEqual(STEM_TO_TRIGRAM["癸"], "坤")
        self.assertEqual(STEM_TO_TRIGRAM["戊"], "坎")
        self.assertEqual(STEM_TO_TRIGRAM["庚"], "震")

    def test_branch_houtian(self):
        # 癸巳→地元气巽（巳→巽）；甲辰→地元气巽（辰→巽，反=震）
        self.assertEqual(BRANCH_TO_TRIGRAM["巳"], "巽")
        self.assertEqual(BRANCH_TO_TRIGRAM["辰"], "巽")
        self.assertEqual(BRANCH_TO_TRIGRAM["亥"], "乾")

    def test_jixiaolan_aochen(self):
        # 纪晓岚日（甲辰年）：天元气乾（甲→乾）、地元气巽（辰→巽）、反=震
        yq = compute_yuan_qi("甲", "辰", "乾", "坎", "乾", "巽")
        self.assertEqual(yq.tian_yuan_qi, "乾")
        self.assertEqual(yq.di_yuan_qi, "巽")
        self.assertEqual(yq.tian_yuan_fan, "坤")
        self.assertEqual(yq.di_yuan_fan, "震")
        self.assertEqual(yq.state, YuanQiState.NORMAL)


class TestYuanQiCanonicalWiring(unittest.TestCase):
    """canonical 主链接入：HeluoResult 携带元气流。"""

    def _compute(self, solar, gender="male"):
        return HeluoAdapter().compute(solar, gender=gender)

    def test_result_has_yuan_qi_field(self):
        r = self._compute((1980, 6, 22, 10))
        self.assertIsInstance(r, HeluoResult)
        self.assertIsNotNone(r.yuan_qi, "canonical 主链应产出元气流（Step 8.5）")
        self.assertTrue(hasattr(r.yuan_qi, "tian_yuan_qi"))
        self.assertTrue(hasattr(r.yuan_qi, "di_yuan_qi"))

    def test_gengshen_male(self):
        # 1980-06-22 庚申男：天元气震（庚→震）、地元气坤（申→坤）
        r = self._compute((1980, 6, 22, 10))
        self.assertEqual(r.yuan_qi.tian_yuan_qi, "震")
        self.assertEqual(r.yuan_qi.di_yuan_qi, "坤")
        self.assertIn(r.yuan_qi.state, (YuanQiState.NORMAL, YuanQiState.REVERSE))

    def test_jixiaolan_wiring(self):
        # 纪晓岚日（甲辰年）主链：天元气乾、地元气巽、NORMAL（与模块互证）
        r = self._compute((1724, 6, 5, 12))
        self.assertEqual(r.yuan_qi.tian_yuan_qi, "乾")
        self.assertEqual(r.yuan_qi.di_yuan_qi, "巽")
        self.assertEqual(r.yuan_qi.state, YuanQiState.NORMAL)


class TestYuanQiFrozenState(unittest.TestCase):
    """frozen_state 序列化暴露元气流。"""

    def test_frozen_exposes_yuan_qi(self):
        r = HeluoAdapter().compute((1980, 6, 22, 10), gender="male")
        fs = build_frozen_state(r)
        d = fs.to_dict()
        self.assertIn("yuan_qi", d)
        self.assertIsNotNone(d["yuan_qi"]["state"])
        self.assertIsNotNone(d["yuan_qi"]["tian"])
        self.assertIsNotNone(d["yuan_qi"]["di"])
        self.assertEqual(d["yuan_qi"]["tian"], r.yuan_qi.tian_yuan_qi)


if __name__ == "__main__":
    unittest.main()
