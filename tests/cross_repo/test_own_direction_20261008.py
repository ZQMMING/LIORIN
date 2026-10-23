"""批次 K 守卫：河洛诊断方向必须来自河洛自有判据（2026-10-08）

背景：诊断 8 条断言里 6 条方向是 neutral —— 信号引擎只产出 1 条**八字**
信号（rule_refs 全为 ZPZ-*），河洛信号为 0。若只依赖信号层，河洛方向
会永远停在默认值，而「默认值 neutral」与「判过了是中性」在输出上
完全一样，没人能分辨。

用户选 B：河洛方向来自**河洛自己的判据**，信号层只作补充。

三条纪律：
  1. 河洛判据优先，且必须留下**依据文本**（heluo_own_basis）
  2. 数格**只判凶不判吉** —— 「不凶」不得当成「吉」
  3. 判不了要明说（不判），不得静默落成中性
"""
from __future__ import annotations

import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_E = _ROOT / "src" / "heluo_engine" / "engines" / "heluo"


class TestHeluoOwnDirection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo import diagnosis_rule_graph as dg
        cls.dg = dg

    def _fs(self, **kw):
        from tongshu.engines.heluo.frozen_state import build_frozen_state
        import os
        from datetime import date
        from tongshu.pipeline import TONGSHUPipeline
        os.environ.setdefault("TONGSHU_ALLOW_ZIWEI_STUB", "1")
        os.environ.setdefault(
            "TONGSHU_AUTHORITY_CREDENTIALS",
            "architecture-governance:schema-v1-arch-gov-2026;"
            "admission_registry:test-cred-hash")
        # 默认用一个**数格判凶**的案子（1990-05-20 → 阴阳相战）：
        # 下面多条守卫要断言「数格被走到、方向被登记」，
        # 用不凶的案子会永远落在「只判凶不判吉」那条分支上。
        bd = kw.pop("birth_date", (1990, 5, 20, 8))
        gender = kw.pop("gender", "male")
        r = TONGSHUPipeline.for_demo(_ROOT).run(
            analysis_date=date(2026, 10, 8), birth_date=bd, gender=gender,
            theme="WORK", compute_only=True,
            heluo_target_date=date(2026, 8, 17))
        return r

    def test_tian_di_shu_uses_shu_ge(self):
        """天数地数 → 数格判据，不是信号层。"""
        r = self._fs()
        d, note = self.dg.heluo_own_direction("HL_TIAN_DI_SHU", _fs_of(r))
        self.assertIsNotNone(d, "天数地数未走数格判据")
        self.assertIn("数格", note)

    def test_yuan_tang_uses_liu_ju(self):
        r = self._fs()
        d, note = self.dg.heluo_own_direction("HL_YUANTANG", _fs_of(r))
        self.assertIsNotNone(d, "元堂未走六项·爻位判据")
        self.assertIn("爻位", note)

    def test_hua_gong_consistent_in_both_paths(self):
        """同一条 HL_HUA_GONG 在证据环与冻结态两条路径上方向必须一致。"""
        r = self._fs()
        dirs = {a.direction.value for a in r.heluo_diagnosis.assertions
                if a.source_rule == "HL_HUA_GONG"}
        self.assertEqual(len(dirs), 1,
                         "HL_HUA_GONG 两条断言方向不一致：%s" % dirs)

    def test_shu_ge_never_reports_auspicious(self):
        """⚠ 数格只判凶、不判吉 —— 「不凶」不是「吉」。

        把没有判据说成有判据，是本项目最常见的一类有害伪造。
        """
        # 用**数格不凶**的案子：变异点就在「不凶」这条分支上，
        # 拿判凶的案子去测永远走不到，等于没测。
        r = self._fs(birth_date=(1985, 3, 2, 12))
        d, note = self.dg.heluo_own_direction("HL_TIAN_DI_SHU", _fs_of(r))
        if d is not None:
            self.assertEqual(d.value, "caution",
                             "数格只可能判出 caution（凶）；得到 %s 说明把"
                             "「不凶」当成了「吉」" % d.value)
            self.assertIn("凶", note)

    def test_undecidable_is_none_not_neutral(self):
        """判不了 → 返回 None（回落信号档），不是直接给个中性。"""
        d, note = self.dg.heluo_own_direction("HL_JIEHOU_GUA", None)
        self.assertIsNone(d)
        self.assertTrue(note)

    def test_own_basis_registered_in_real_run(self):
        r = self._fs()
        own = self.dg.heluo_own_basis()
        self.assertIn("HL_TIAN_DI_SHU", own)
        self.assertIn("HL_YUANTANG", own)
        self.assertIn("HL_HUA_GONG", own)
        for k, v in own.items():
            self.assertTrue(v, "%s 登记了空的依据文本" % k)

    def test_at_least_half_assertions_get_real_direction(self):
        """河洛自己的断言不该大面积停在默认值。

        ⚠ 只统计 ``HL_*`` 断言 —— 诊断图里还有由**八字信号**生成的 ZPZ-* 断言，
          那些的方向本就该由信号层给，拿它们一起算分母会把这个断言拖成永假。
        """
        r = self._fs()
        hl = [a for a in r.heluo_diagnosis.assertions
              if str(a.source_rule).startswith("HL_")]
        self.assertTrue(hl, "没有河洛断言")
        real = [a for a in hl if a.direction.value != "neutral"]
        self.assertGreaterEqual(
            len(real) * 2, len(hl),
            "仅 %d/%d 条河洛断言拿到非默认方向" % (len(real), len(hl)))


def _fs_of(r):
    from tongshu.engines.heluo.frozen_state import build_frozen_state
    return build_frozen_state(r.heluo_result)


if __name__ == "__main__":
    unittest.main()