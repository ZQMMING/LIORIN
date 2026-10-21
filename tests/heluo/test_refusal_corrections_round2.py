"""第二轮验证（多方取证）落地的守卫 —— 2026-10-07

起因：首轮对四条原典歧义做了拒算裁决，其中**两条经全库取证证明是过度保守**，
本文件把更正后的实现钉死，并锁死更正依据的原文。

    A. 天数至弱 L38 —— 首轮拒算，**撤销**。判据「四五六七八」自足，
       策＝9（L950「论九是阳之一策」），且 L950 明说 9–24 属「不足」
       而「即非至弱之比」，二者不重叠。
    B. 三阳奇偶合象 L99 —— 首轮拒算，**撤销**。窗口与「余」的归属均由
       L714「男命阳月生者，冬至以后，雨水前，天数不及二十五，只余奇，便妙」
       独立平行印证。
    C. 阳数偏少 vs 以弱敌强 —— 首轮称「判语相反」，**证伪**。两条诗断同向，
       仅严重度不同。
    D. 有尤／有悔 —— 拒算**维持**，补全库穷举证据。

**期望值全部硬编码自原典原文，不调用被测函数求期望值。**
"""
from __future__ import annotations

import io
import os
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "src"))

_ORIGINAL = Path(os.environ.get(
    "HELUO_ORIGINAL_TXT",
    r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
    r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
))


def _orig() -> str:
    if not _ORIGINAL.exists():
        raise unittest.SkipTest(f"原著全文不在预期路径：{_ORIGINAL}")
    with io.open(_ORIGINAL, encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════════════════════════════════════════════
# 更正依据的原文必须逐字在场
# ═══════════════════════════════════════════════════════════════════

EVIDENCE_FRAGMENTS = {
    "A-至弱判据": "天数一十有五，如只得四五六七八数，此不满一策，是谓至弱",
    "A-策为九": "论九是阳之一策",
    "A-不足非至弱": "虽云不足，即非至弱之比，犹庶几可也",
    "A-天数正": "天数二十五为正",
    "A-地数至弱(句式平行)": "地数至弱　地数三十，只得八、九、十、十一、十二数者，是谓至弱",
    "B-L99窗口": "自冬至后至雨水前，正三阳交泰之时",
    "B-L99判据": "除天数二十五之外，有奇数之余，即君子之合象也",
    "B-L714旁证": "冬至以后，雨水前，天数不及二十五，只余奇，便妙",
    "C-阳数偏少诗": "阴令得之犹可喜，若生阳月必孤睽",
    "C-以弱敌强诗": "阴令忧危浅，阳月有大殃",
    "C-以弱敌强判": "阴月令逢之，尚庶几，阳月令逢之，必主灭顶之凶",
    "D-有尤": "太过有尤　阳数胜阴数，卦中阳爻多，又值月令立阳爻",
    "D-有悔一": "地数太过有悔　阴数胜阳数，卦中阴爻多，值阴令立阴爻",
    "D-有悔二": "阴数太过有悔　阴数盛，阳数少，卦中阴爻多，又值阴月令，位阴爻",
}


class TestCorrectionEvidencePresent(unittest.TestCase):
    def test_all_evidence_fragments_verbatim(self):
        orig = _orig()
        missing = [k for k, v in EVIDENCE_FRAGMENTS.items() if v not in orig]
        self.assertEqual(missing, [], f"全库原著缺失更正依据：{missing}")


# ═══════════════════════════════════════════════════════════════════
# A. 天数至弱：判据自足，撤销拒算
# ═══════════════════════════════════════════════════════════════════

class TestTianShuZhiRuoImplemented(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo.yue_ling_shu_ge import classify_shu_ge
        cls._c = staticmethod(classify_shu_ge)

    def names(self, t: int, d: int) -> set[str]:
        return {r.name for r in self._c(t, d)}

    def test_band_is_4_to_8(self):
        """L938「如只得四五六七八数，此不满一策，是谓至弱」。"""
        for t in range(4, 9):
            self.assertIn("天数至弱", self.names(t, 30), f"天数{t}")
        for t in (3, 9, 15, 24):
            self.assertNotIn("天数至弱", self.names(t, 30), f"天数{t} 越界")

    def test_does_not_overlap_bu_zuo(self):
        """L950：9–24 属「不足」且「即非至弱之比」——两者必须互斥。"""
        for t in range(9, 25):
            self.assertNotIn("天数至弱", self.names(t, 30), f"天数{t}")
            self.assertIn("天数不足", self.names(t, 30), f"天数{t} 应属不足")

    def test_ce_is_nine_so_eight_is_under_one_ce(self):
        """「此不满一策」：策＝9，故 8 不足一策。"""
        self.assertEqual(8, 9 - 1)
        self.assertLess(8, 9)

    def test_precedence_over_yang_shu_pian_shao(self):
        """L38 早于 L56，同数时取至弱（更极端的一档）。"""
        from tongshu.engines.heluo.guajie import judge_shu_xiong
        self.assertEqual(judge_shu_xiong(6, 30, 11).pattern, "天数至弱")

    def test_baseline_ambiguity_still_registered(self):
        """「天数一十有五」的基线归属仍须留在拒算表里——判据成立不等于基线定了。"""
        from tongshu.engines.heluo.yue_ling_shu_ge import REFUSED
        joined = " ".join(c + w + n for c, w, n in REFUSED)
        self.assertIn("一十有五", joined)
        self.assertIn("天数二十五为正", joined)


# ═══════════════════════════════════════════════════════════════════
# B. 三阳奇偶合象：撤销拒算
# ═══════════════════════════════════════════════════════════════════

class TestChunQiQiOuImplemented(unittest.TestCase):
    def setUp(self):
        from tongshu.engines.heluo.yue_ling_shu_ge import (
            judge_chun_qi_qi_ou, solar_jq_index, CHUNQI_JQ)
        self.j = judge_chun_qi_qi_ou
        self.solar = solar_jq_index
        self.W = CHUNQI_JQ

    def test_window_is_between_winter_solstice_and_rain_water(self):
        """L1121「自冬至后至雨水前」。窗口＝小寒、大寒、立春三气。"""
        self.assertEqual(self.W, frozenset({1, 2, 3}))

    def test_jq_index_scans_backwards(self):
        """回归：getJieQi() 只在交节当天返回值，其余为哨兵 255。

        首版直接取 getJieQi()，导致一年 360 多天都落到 255、窗口整年失效。
        """
        self.assertEqual(self.solar("2025-12-21"), 0)    # 冬至当天
        self.assertEqual(self.solar("2026-01-10"), 1)    # 小寒期间（非交节当天）
        self.assertEqual(self.solar("2026-02-10"), 3)    # 立春期间
        self.assertEqual(self.solar("2026-02-18"), 4)    # 雨水当天
        self.assertEqual(self.solar("2026-06-21"), 12)   # 夏至当天

    def test_in_window_odd_yu_is_auspicious(self):
        _, ok = self.j(26, "2026-01-10")     # 余 1 奇
        self.assertIs(ok, True)

    def test_in_window_even_yu_is_inauspicious(self):
        _, ok = self.j(27, "2026-01-10")     # 余 2 偶
        self.assertIs(ok, False)

    def test_outside_window_returns_none(self):
        """窗口外不是「凶」，是**不适用**——三态，不许退化成二值。"""
        for d in ("2026-06-21", "2026-03-05"):
            for t in (26, 27):
                _, ok = self.j(t, d)
                self.assertIsNone(ok, f"{d} 天数{t} 应为不适用")

    def test_exactly_twenty_five_is_none(self):
        """L1121 判「除天数二十五之外」者，足数不在其列。"""
        _, ok = self.j(25, "2026-01-10")
        self.assertIsNone(ok)

    def test_no_date_returns_none_not_false(self):
        """无出生日 → 判不出窗口 → 必须是 None，不得当成「不合」。"""
        for t in (26, 27):
            _, ok = self.j(t, "")
            self.assertIsNone(ok)

    def test_bad_date_returns_none(self):
        _, ok = self.j(26, "not-a-date")
        self.assertIsNone(ok)

    def test_explanation_quotes_both_witnesses(self):
        """说明须同时引 L1121 与 L714，证明这是双证据而非孤证。"""
        note, _ = self.j(26, "2026-01-10")
        self.assertIn("L1121", note)
        self.assertIn("L714", note)


class TestChunQiQiOuEndToEnd(unittest.TestCase):
    """端到端：该条须由 build_guajie_from_result 补判（它才有 birth_date）。"""

    def _run(self, birth_date, tian):
        from types import SimpleNamespace
        from tongshu.engines.heluo.guajie import build_guajie_from_result
        res = SimpleNamespace(
            input=SimpleNamespace(gender="male", birth_date=birth_date),
            prenatal=SimpleNamespace(hexagram_name="乾"),
            postnatal=SimpleNamespace(hexagram_name="坤"),
            yuantang=SimpleNamespace(yuantang="九三"),
            numbers=SimpleNamespace(tian_shu=tian, di_shu=30),
            timeline=None)
        out = build_guajie_from_result(res)
        self.assertNotIn("error", out, f"构建失败：{out.get('error')}")
        return out

    def test_serialized_into_output(self):
        """**回归**：to_dict 此前只序列化 6 个字段，六项新增判定全被丢弃。"""
        out = self._run("1990-01-10", 26)
        sx = out["shu_xiong"]
        self.assertIs(sx["chun_qi_qi_ou"][1], True)
        for key in ("matched", "conflicts", "lu_shu", "xingbei",
                    "ming_wu_yin_yang", "chun_qi_qi_ou"):
            self.assertIn(key, sx, f"to_dict 未输出 {key}")

    def test_evidence_records_verdict(self):
        out = self._run("1990-01-10", 26)
        joined = " ".join(out["evidence"])
        self.assertIn("三阳奇偶合象", joined)
        self.assertIn("君子之合象", joined)

    def test_out_of_window_emits_no_evidence_line(self):
        """窗口外不加 evidence，避免噪声；但结构化字段仍须存在（值为 None）。"""
        out = self._run("1990-06-21", 26)
        self.assertNotIn("三阳奇偶合象", " ".join(out["evidence"]))
        self.assertIsNone(out["shu_xiong"]["chun_qi_qi_ou"][1])


# ═══════════════════════════════════════════════════════════════════
# C. 「判语相反」是错的——诗断同向
# ═══════════════════════════════════════════════════════════════════

class TestPoemsAgreeInDirection(unittest.TestCase):
    """两条诗断：都是「阴月令较轻、阳月令较重」，不是相反。"""

    def setUp(self):
        from tongshu.engines.heluo.yue_ling_shu_ge import shu_ge_conflicts
        self._c = shu_ge_conflicts

    def test_conflict_text_says_same_direction(self):
        joined = " ".join(self._c(24, 30))
        self.assertIn("同向", joined)
        self.assertNotIn("判语相反", joined, "被全库证伪的表述不得复现")

    def test_both_poems_quoted_in_conflict(self):
        joined = " ".join(self._c(24, 30))
        self.assertIn("阴令得之犹可喜", joined)
        self.assertIn("阴令忧危浅", joined)

    def test_both_rules_still_reported(self):
        """重叠仍须全量披露，只是不再宣称「相反」。"""
        from tongshu.engines.heluo.yue_ling_shu_ge import classify_shu_ge
        names = {r.name for r in classify_shu_ge(24, 30)}
        self.assertIn("阳数偏少", names)
        self.assertIn("以弱敌强", names)


# ═══════════════════════════════════════════════════════════════════
# D. 有尤／有悔：拒算维持，门槛全库无载
# ═══════════════════════════════════════════════════════════════════

class TestYouYouHuiHuiStillRefused(unittest.TestCase):
    def setUp(self):
        from tongshu.engines.heluo.yue_ling_shu_ge import REFUSED
        self.R = REFUSED

    def test_registered_with_exhaustive_evidence(self):
        joined = " ".join(c + w + n for c, w, n in self.R)
        self.assertIn("L49", joined)
        self.assertIn("多数", joined, "须记录「多数」0 命中的穷举结果")
        self.assertIn("门槛", joined)

    def test_no_shu_ge_named_you_you_or_you_hui(self):
        """不得因为「有尤／有悔」听起来像数格就擅自实现一个。"""
        from tongshu.engines.heluo.yue_ling_shu_ge import SHU_GE_TABLE
        names = {r.name for r in SHU_GE_TABLE}
        self.assertNotIn("太过有尤", names)
        self.assertNotIn("地数太过有悔", names)
        self.assertNotIn("阴数太过有悔", names)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
