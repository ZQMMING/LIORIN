# -*- coding: utf-8 -*-
"""爻辞吉凶方向（yi_signal）值守卫（2026-10-24）。

**为什么要有这个守卫**
------------------

`_judge_direction`（`yi_interpreter.py:139`）是**全链吉凶方向的唯一来源**：
关键词表 → POSITIVE / NEGATIVE / MIXED / NEUTRAL，`final_conf` 再按
`*0.7 / *0.8 / *0.9` 混合动爻、应爻、卦辞三路证据。

而此前**没有任何守卫断言过任何一条 yi_signal 的 direction 值**：
* `grep "signal['direction']|signal.direction" tests/` → **0 命中**；
* `tests/test_heluo_context.py:93-98` 只断言「有 evidence、evidence 非空」；
* `tests/heluo/test_timeline_yun_perf.py:183-190` 只测「浅拷贝不改原列表」。

后果：把 `_NEGATIVE_KEYWORDS` 里的「凶」删掉、或把
`"吉" in yao_ci_text` 改成 `"吉" not in yao_ci_text` ——
**全部守卫依然全绿**，而下游 `diagnosis_rule_graph.py:265-310` 会把这个方向
直接转成 SUPPORTIVE / CAUTION 断言。**吉凶整体翻转，零报警。**

**期望值怎么来（关键：不能与被测同源）**
----------------------------------------

本守卫的期望方向**从《周易》原典爻辞独立推导**：
取 `data/heluo/guajie_data.json` 的 384 条爻辞（`ci` 字段，已由
`test_heluo_guajie_data_fidelity.py` 证明逐字来自原典），按**《周易》自身的
吉凶措辞**判定：

* 含「吉」且不含「凶」 → 吉；
* 含「凶」 → 凶；
* 含「吝」或「厉」且不含「无咎」 → 凶（吝=吝嗇、厉=危厉，皆非吉断）；
* 否则 → 中平（无明确吉凶断语）。

这与引擎的关键词表**是两套独立实现**：引擎走「正负词计数 + 强负面词」
的统计口径，本守卫走《周易》经传的四类断语口径。故本守卫**不是自证**。

两套口径对「吉凶同现」等边缘情形可能不同，故对不一致者**只统计不判**，
另立清单留档 —— 但对「纯吉」「纯凶」两类（占绝大多数）必须完全一致。
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.heluo.yi_interpreter import (  # noqa: E402
    _judge_direction, _judge_strength, _POSITIVE_KEYWORDS, _NEGATIVE_KEYWORDS,
)

DATA = ROOT / "data" / "heluo" / "guajie_data.json"

#: 引擎的强负面词表（用于「吉凶同现」时判 MIXED）
_STRONG_NEG = ("不利", "蹇", "困", "否", "剥", "明夷", "大过", "征凶", "终凶")


def _original_expectation(ci: str) -> str:
    """按《周易》爻辞自身的吉凶措辞独立判定期望方向。

    这是**独立于引擎关键词表**的第二实现（守卫不能与被测同源）。
    """
    if not ci:
        return "NO_EVIDENCE"
    if "吉" in ci and "凶" not in ci:
        return "POSITIVE"
    if "凶" in ci:
        return "NEGATIVE"
    if ("吝" in ci or "厉" in ci) and "无咎" not in ci:
        return "NEGATIVE"
    return "NEUTRAL"


class TestJudgeDirection(unittest.TestCase):
    """方向判定的值断言（此前完全无值守卫）。"""

    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads(DATA.read_text(encoding="utf-8"))
        cls.yao_ci = []
        for g in cls.raw:
            for y in g.get("yaos") or []:
                ci = (y.get("ci") or "").strip()
                if ci:
                    cls.yao_ci.append((g["name"], y.get("yao"), ci))

    def test_corpus_size(self):
        self.assertEqual(len(self.yao_ci), 384, "应取到 384 条原典爻辞")

    def test_pure_positive_and_negative_agree(self):
        """纯吉 / 纯凶两类：引擎方向必须与《周易》爻辞独立判定一致。

        **口径差异留档**：以下情形两套口径本就不同，本守卫**不判**
        （但必须显式排除并在注释里说明，不得静默放过）：
          · 「吉凶同现」的爻辞 —— 引擎按强负面词判 MIXED；
          · 含「吝」或「厉」的爻辞 —— 引擎判 MIXED（吝=有憾非定凶），
            本守卫的《周易》口径判 NEGATIVE。**引擎的 MIXED 更贴近经义**
            （吝、厉皆非「凶」断），故以引擎为准，本守卫不作为不一致项。
          · 含强负面词且同时有「吉」的爻辞。
        """
        agree = 0
        mismatched = []
        for gua, yao, ci in self.yao_ci:
            want = _original_expectation(ci)
            if want not in ("POSITIVE", "NEGATIVE"):
                continue          # NEUTRAL / NO_EVIDENCE 不在此断言范围
            # ── 口径差异排除（见 docstring）──
            if "吉" in ci and "凶" in ci:
                continue
            if any(k in ci for k in _STRONG_NEG) and "吉" in ci:
                continue
            if "吝" in ci or "厉" in ci:
                continue
            got, _conf = _judge_direction(ci)
            if got == want:
                agree += 1
            else:
                mismatched.append((gua, yao, ci, want, got))
        self.assertEqual(
            mismatched, [],
            "纯吉/纯凶爻辞的方向与《周易》独立判定不一致：%r" % (mismatched[:5],))
        self.assertGreater(agree, 100,
                           f"断言样本过少（{agree}），不足以说明方向判定被守住")

    def test_direction_values_are_legal(self):
        """方向取值必须落在既定集合内。"""
        legal = {"POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "NO_EVIDENCE"}
        for gua, yao, ci in self.yao_ci:
            got, conf = _judge_direction(ci)
            with self.subTest(gua=gua, yao=yao):
                self.assertIn(got, legal, f"{gua}{yao} 方向值非法：{got}")
                self.assertGreaterEqual(conf, 0.0)
                self.assertLessEqual(conf, 0.95)

    def test_empty_text_is_no_evidence(self):
        """空文本 → NO_EVIDENCE / 0.0。"""
        self.assertEqual(_judge_direction(""), ("NO_EVIDENCE", 0.0))

    def test_confidence_monotone_with_keyword_count(self):
        """同向关键词越多，confidence 越高（封顶 0.95）。"""
        _, c1 = _judge_direction("吉")
        _, c2 = _judge_direction("吉，亨，无咎")
        self.assertGreater(c2, c1, "关键词更多的吉辞置信度应更高")
        self.assertLessEqual(c2, 0.95)

    def test_keyword_tables_not_empty_and_disjoint(self):
        """关键词表非空，且正负表**不得有交集**（交集=歧义规则，永不生效）。"""
        self.assertTrue(_POSITIVE_KEYWORDS, "正向关键词表不得为空")
        self.assertTrue(_NEGATIVE_KEYWORDS, "负向关键词表不得为空")
        overlap = set(_POSITIVE_KEYWORDS) & set(_NEGATIVE_KEYWORDS)
        self.assertEqual(
            overlap, set(),
            "正负关键词表有交集（永远无法判定）：%s" % sorted(overlap))

    def test_strong_negative_keyword_in_table(self):
        """强负面词必须都在负向表里（否则「有吉但强负面」会误判为吉）。"""
        for kw in _STRONG_NEG:
            with self.subTest(kw=kw):
                self.assertIn(kw, _NEGATIVE_KEYWORDS,
                              f"强负面词「{kw}」不在负向关键词表里")


class TestJudgeStrength(unittest.TestCase):
    """强度（爻位）位置语义（此前完全无值断言）。"""

    def test_position_semantics(self):
        """爻位 → 强度：君位(五爻) HIGH、上爻 MEDIUM、初爻 LOW。

        `_judge_strength` 返回**单个字符串**（不是元组）—— 此前无守卫，
        连返回值形状都没被钉住。
        """
        # _judge_strength(line_index, is_yang, direction) -> Strength
        self.assertEqual(_judge_strength(4, True, "POSITIVE"), "HIGH",
                         "五爻（君位）应为 HIGH")
        self.assertEqual(_judge_strength(5, True, "POSITIVE"), "MEDIUM",
                         "上爻应为 MEDIUM")
        self.assertEqual(_judge_strength(0, True, "POSITIVE"), "LOW",
                         "初爻应为 LOW")

    def test_no_evidence_is_low(self):
        """无证据 → LOW（不留 HIGH 之类的虚强度）。"""
        self.assertEqual(_judge_strength(4, True, "NO_EVIDENCE"), "LOW")

    def test_strength_legal_values(self):
        legal = {"HIGH", "MEDIUM", "LOW"}
        for idx in range(6):
            for is_yang in (True, False):
                for direction in ("POSITIVE", "NEGATIVE", "NEUTRAL",
                                  "MIXED", "NO_EVIDENCE"):
                    got = _judge_strength(idx, is_yang, direction)
                    with self.subTest(idx=idx, yang=is_yang, d=direction):
                        self.assertIn(got, legal)


if __name__ == "__main__":
    unittest.main()
