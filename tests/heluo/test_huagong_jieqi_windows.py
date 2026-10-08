"""批次 F-3 守卫：四正卦化工节气窗口（原典 L558–L567）

原典四条，起止全是节气：

    L558「坎卦自冬至十一月中以后至惊蛰终止。」
    L561「震卦自春分二月中以后至芒种终止。」
    L564「离卦自夏至五月中以后至白露终止。」
    L567「兑卦自秋分八月中以后至大雪终止。」

**本文件最硬的一条守卫是「互证」而不是「照抄」**：L585–L594 的四条
「化工相反」窗口（夏至后秋分前等）是原典**另一张独立的表**，它必须
与本表逐条对上。若两表对不上，说明至少一张抄错了——比任何一条
自我一致的断言都灵。

另有一条**反向守卫**钉住「生产链尚未切换」这个已知差异：F-3 的窗口
算对了但 canonical 没接线，若无人看守，这事会被当成已完成。
"""
from __future__ import annotations

import ast
import io
import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_E = _ROOT / "src" / "tongshu" / "engines" / "heluo"
HG = _E / "hua_gong.py"
CN = _E / "canonical.py"


def _code_only(path: Path) -> str:
    src = io.open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            b = node.body
            if (b and isinstance(b[0], ast.Expr)
                    and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)):
                node.body = b[1:] or [ast.Pass()]
    code = ast.unparse(tree)
    return "\n".join(re.sub(r"\s+#.*$", "", ln) for ln in code.split("\n"))


class TestJieqiWindows(unittest.TestCase):
    """L558–L567 四窗口。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo.hua_gong import (
            HUAGONG_FAN_JIEQI, HUAGONG_JIEQI_WINDOWS, _JQ_ORDER,
            huagong_by_jieqi)
        cls.W = HUAGONG_JIEQI_WINDOWS
        cls.FAN = HUAGONG_FAN_JIEQI
        cls.JQ = _JQ_ORDER
        cls._by = staticmethod(huagong_by_jieqi)

    def test_four_windows_match_original(self):
        self.assertEqual(self.W, (("坎", 0, 5), ("震", 6, 11),
                                  ("离", 12, 17), ("兑", 18, 23)))

    def test_jq_order_matches_repo_canonical(self):
        """节气序必须与全库唯一的节气序一致，不得另立一套。"""
        from tongshu.engines.heluo.yue_ling_shu_ge import JIE_QI_ORDER
        self.assertEqual(list(self.JQ), list(JIE_QI_ORDER))

    def test_windows_partition_the_year_with_no_gap(self):
        """jq 0–23 必须被四段**无缝切满**。
        这条是防「压成月支表」的根：压回去就会出现三段凭空多出来的空档，
        而原典里根本没有洞。
        """
        cov = []
        for _g, lo, hi in self.W:
            cov.extend(range(lo, hi + 1))
        self.assertEqual(sorted(cov), list(range(24)),
                         "四窗口未把 jq 0–23 切满——不是无缝就是有重叠")

    def test_every_jq_resolves(self):
        for jq in range(24):
            self.assertIn(self._by(jq), ("坎", "震", "离", "兑"), f"jq={jq}")

    def test_out_of_range_returns_empty_not_guess(self):
        for jq in (-1, 24, 99, None):
            self.assertEqual(self._by(jq), "", f"jq={jq} 越界却给了卦")

    def test_window_endpoints_land_on_named_terms(self):
        """起止名对不上就是抄错了行。"""
        pairs = [("坎", "冬至", "惊蛰"), ("震", "春分", "芒种"),
                 ("离", "夏至", "白露"), ("兑", "秋分", "大雪")]
        for (gua, lo, hi), (_g, a, b) in zip(self.W, pairs):
            self.assertEqual(self.JQ[lo], a, f"{gua} 起点")
            self.assertEqual(self.JQ[hi], b, f"{gua} 终点")

    # ── 互证：L585–L594 必须与本表逐条对上 ──────────────────
    def test_cross_check_with_fan_table_L585_L594(self):
        """原典另一张表说的话，必须和本表一致。"""
        for gua, fan, lo, hi in self.FAN:
            inside = {g for g, a, b in self.W if a >= lo and b < hi}
            self.assertEqual(inside, {fan},
                             f"L585–L594「{gua}反{fan}」jq[{lo},{hi}) "
                             f"实际覆盖 {inside or '空'}")

    def test_fan_table_covers_exactly_the_four(self):
        self.assertEqual({g for g, _f, _lo, _hi in self.FAN},
                         {g for g, _lo, _hi in self.W})

    def test_fan_table_still_agrees_with_opposite_trigram(self):
        from tongshu.engines.heluo.hua_gong import HUAGONG_FAN_GUA
        for gua, fan, _lo, _hi in self.FAN:
            self.assertEqual(HUAGONG_FAN_GUA[gua], fan)

    # ── 静态：自校验必须在导入期跑 ───────────────────────────
    def test_self_check_runs_at_import(self):
        code = re.sub(r"\s+", "", _code_only(HG))
        self.assertIn("_huagong_self_check()", code.replace("def_huagong_self_check", ""))
        body = _code_only(HG)
        i = body.find("def _huagong_self_check")
        j = body.find("def ", i + 10)
        blk = re.sub(r"\s+", "", body[i:j])
        # 三件都要在：切满、互证、与 HUAGONG_FAN_GUA 一致
        self.assertIn("==list(range(len(_JQ_ORDER)))", blk)
        self.assertIn("inside=={fan}", blk)
        self.assertIn("HUAGONG_FAN_GUA.get(gua)==fan", blk)

    def test_tampering_with_window_is_caught_by_self_check(self):
        """把窗口改坏，导入期自校验必须直接炸——不能带着错表跑。"""
        import os
        import subprocess
        import sys
        orig = io.open(HG, encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in orig else "\n"
        body = orig.replace("\r\n", "\n")
        head = "HUAGONG_JIEQI_WINDOWS: tuple[tuple[str, int, int], ...] = ("
        i = body.index(head)
        j = body.index("\n)\n", i) + len("\n)\n")
        # 把坎的终止从惊蛰(5) 挪到雨水(4)：切不满 24 个 jq
        tampered = body[:i] + head + "\n    (\"坎\", 0, 4), (\"震\", 5, 11),\n" \
                              "    (\"离\", 12, 17), (\"兑\", 18, 23),\n)\n" + body[j:]
        self.assertNotEqual(tampered, body, "篡改没生效，本用例等于没测")
        env = dict(os.environ)
        env["PYTHONPATH"] = "src"
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            io.open(HG, "w", encoding="utf-8", newline="").write(
                tampered.replace("\n", nl))
            pr = subprocess.run(
                [sys.executable, "-c",
                 "import tongshu.engines.heluo.hua_gong"],
                cwd=_ROOT, env=env, capture_output=True,
                text=True, encoding="utf-8", errors="replace")
        finally:
            io.open(HG, "w", encoding="utf-8", newline="").write(orig)
        self.assertNotEqual(pr.returncode, 0,
                            "窗口改坏了却能正常导入——自校验是摆设")
        self.assertIn("AssertionError", pr.stderr)


class TestKunGenEighteenDaysRefused(unittest.TestCase):
    """L570「坤艮十八日」判据不全 → 必须仍拒算，且理由要写清。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo.hua_gong import HUAGONG_REFUSED
        cls.R = HUAGONG_REFUSED

    def test_registered_with_line_number(self):
        joined = " ".join(c for c, _w, _n in self.R)
        self.assertIn("L570", joined)
        self.assertIn("坤艮", joined)

    def test_reason_names_the_gap(self):
        joined = " ".join(w for _c, w, _n in self.R)
        self.assertIn("正节气十二日", joined)
        self.assertIn("未给", joined, "须写明缺的是「正节气十二日」的起讫")

    def test_not_implemented_anywhere(self):
        """不得一边登记拒算、一边偷偷实现一个十八日窗口。

        判据不能是「全文没有『十八日』」——拒算登记**本身**就得引用原典原话，
        那也是可执行代码里的字符串字面量。故改为：**『十八日』只允许出现在
        HUAGONG_REFUSED 那一段**，出了这一段就是偷偷实现了。
        """
        src = io.open(HG, encoding="utf-8").read()
        i = src.index("HUAGONG_REFUSED: tuple")
        j = src.index("\nSEASON_BRANCH_TO_HUAGONG", i)
        self.assertIn("十八日", src[i:j], "拒算登记连原话都不引了，等于没登记")
        # 「之外」要按**可执行代码**判：注释里那句「坤艮十八日不落码」是说明，
        # 不是实现。剥掉三引号文档字符串与 # 注释后再查。
        code = _code_only(HG)
        c0 = code.index("HUAGONG_REFUSED")
        c1 = code.index("SEASON_BRANCH_TO_HUAGONG", c0)
        outside = code[:c0] + code[c1:]
        for token in ("十八日", "12日", "18日"):
            self.assertNotIn(token, outside,
                             f"「{token}」出现在可执行代码里（拒算登记之外）——坤艮窗口被偷偷实现了")
        for fake in ("KUN_GEN", "KUNGEN", "shishiba"):
            self.assertNotIn(fake, code,
                             f"可执行代码里冒出了未经原典定义的「{fake}」坤艮常量")


class TestBranchSwitchedAndMustNotRegress(unittest.TestCase):
    """接线已获批准并完成。此处钉的是**不得回退**，外加「吃引擎」三条纪律。

    这一类曾两次翻车：
      * 早先接线被 AGENTS.md 拦下（改 Golden 须显式批准）——那次拦对了；
      * 后来接线获批时，我又顺手造了第三份节气计算、自造了一张节气名表——
        那是「能跑就行」的惯性，与本项目「单一来源」的纪律相悖。
    故这三条纪律各有守卫，防止下一个人再犯。
    """

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo.hua_gong import HUAGONG_BRANCH_SWITCH
        cls.S = HUAGONG_BRANCH_SWITCH

    def test_switch_recorded_as_done(self):
        self.assertIn("已接线", self.S["状态"])
        self.assertTrue(self.S["不得回退"])

    def test_lists_the_two_flipped_goldens(self):
        self.assertEqual(len(self.S["已翻转的 Golden"]), 2)
        joined = " ".join(self.S["已翻转的 Golden"])
        self.assertIn("test_h2_frozen_state.py", joined)
        self.assertIn("test_audit_batch_20261007.py", joined)

    def test_canonical_really_passes_jieqi_index(self):
        """登记说已接线，代码就真得在传——否则登记在骗人。"""
        code = re.sub(r"\s+", "", _code_only(CN))
        i = code.find("returncompute_huagong(")
        self.assertGreater(i, 0)
        self.assertIn("jieqi_index=jieqi_index", code[i:i + 300],
                      "canonical 未把 jieqi_index 传给化工——生产链退回兜底近似表了")

    def test_seasonal_hexagram_computed_before_huagong(self):
        """jq 必须**先**算出来，否则化工拿不到、只能自己再算一遍。"""
        src = io.open(CN, encoding="utf-8").read()
        a = src.index("self._compute_seasonal_hexagram(")
        b = src.index("self._compute_huagong(")
        self.assertLess(a, b,
                        "节候卦又排到化工之后了——顺序倒回去，jq 就得算两遍")

    # ── 缺失输入不得被当成真实输入 ──────────────────────────
    def test_synthetic_birth_date_never_drives_the_judgment(self):
        """⚠ 本轮真实踩过的坑。

        calculate() 会把缺失的 birth_date 补成 f"{yr}-01-01" 喂 HeluoInput。
        节候卦提到化工之前后，这个**合成日期**也跟着进了节气链路 ——
        1724 年补成 01-01 → 算出「冬至 jq=0」→ 化工凭空得到一个当令卦，
        且 evidence 不再标兜底。**缺失输入被当成真实输入，比答错更坏。**
        """
        from tongshu.engines.heluo.canonical import HeluoCanonical
        r = HeluoCanonical().calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male", birth_hour="午", era="zhong", birth_year=1724)
        self.assertIsNone(r.seasonal_hexagram,
                          "没给出生日却算出了节候卦——用的是合成日期")
        self.assertIn("兜底", " ".join(r.hua_gong.evidence),
                      "拿不到 jq 时必须自曝走的是兜底近似表")

    def test_real_birth_date_is_kept_separate_from_the_placeholder(self):
        """占位日期只许喂 HeluoInput，须留住真值供节气层使用。"""
        src = io.open(CN, encoding="utf-8").read()
        code = re.sub(r"\s+", "", _code_only(CN))
        self.assertIn("_real_birth_date", code)
        self.assertIn("self._compute_seasonal_hexagram(_real_birth_date)", code,
                      "节候卦仍在吃可能被替换过的 birth_date")
        # 顺序：先留真值，后补占位
        self.assertLess(src.index("_real_birth_date = birth_date"),
                        src.index('birth_date = f"{yr}-01-01"'))

    def test_same_case_gives_same_answer_either_way(self):
        """同一具案例：有出生日走原典窗口、无出生日走兜底，**两个都要能说清**。

        这里钉的不是「两者答案相同」——它们本就该不同（有输入优于无输入），
        而是：给定完整输入时，答案必须与另一组测试一致（KEZHI/震）。
        """
        from tongshu.engines.heluo.canonical import HeluoCanonical
        a = HeluoCanonical().calculate(
            bazi=[("甲", "辰"), ("辛", "未"), ("丙", "戌"), ("甲", "午")],
            gender="male", birth_hour="午", era="zhong", birth_year=1724,
            birth_date="1724-05-22")
        self.assertEqual(a.hua_gong.huagong_trigram, "震")
        self.assertEqual(a.hua_gong.state.value, "KEZHI")
        self.assertEqual(a.hua_gong.level, "正体")

    # ── 纪律一：不重复计算 ──────────────────────────────────
    def test_no_second_sxtwl_call_inside_huagong(self):
        """化工**不得**在有 jieqi_index 时还去调 sxtwl。"""
        code = re.sub(r"\s+", "", _code_only(HG))
        # huagong_by_jieqi_index 纯查表，不许碰节气换算
        i = code.find("defhuagong_by_jieqi_index")
        j = code.find("defhuagong_by_birth_date", i)
        self.assertGreater(i, 0)
        body = code[i:j]
        for forbidden in ("get_current_jieqi_info", "solar_jq_index", "fromsolar",
                          "sxtwl"):
            self.assertNotIn(forbidden, body,
                             f"huagong_by_jieqi_index 里又调了 {forbidden}——重复计算")

    def test_huagong_stops_using_the_second_jq_implementation(self):
        """全库已有 jiehhou 一份带缓存的实现；化工不得再吃 yue_ling 那份。"""
        code = re.sub(r"\s+", "", _code_only(HG))
        self.assertNotIn("solar_jq_index", code,
                         "化工又改回 solar_jq_index——全库会出现第三份节气计算")

    def test_evidence_says_it_reused_upstream_jq(self):
        """复用必须**可审计**：evidence 要写明未重复计算。"""
        from tongshu.engines.heluo.hua_gong import compute_huagong
        r = compute_huagong("乾", "乾", "乾", "乾", "午", jieqi_index=10)
        ev = " ".join(r.evidence)
        self.assertIn("复用", ev)
        self.assertIn("未重复计算", ev)

    # ── 纪律二：不自造表 ────────────────────────────────────
    def test_no_self_made_solar_term_table(self):
        """节气名必须引 jiehhou.SOLAR_TERMS，不得在化工里另抄一份 24 字元组。"""
        src = io.open(HG, encoding="utf-8").read()
        self.assertIn("from .jiehhou import SOLAR_TERMS as _JQ_ORDER", src,
                      "节气名未引 jiehhou.SOLAR_TERMS")
        code = re.sub(r"\s+", "", _code_only(HG))
        # 自造表长这样：_JQ_ORDER=(...24个字...) 或 _JQ_ORDER=[...]
        self.assertNotIn("_JQ_ORDER=('冬至'", code)
        self.assertNotIn('_JQ_ORDER=("冬至"', code)
        self.assertNotIn("_JQ_ORDER=['冬至'", code)

    def test_solar_term_list_is_the_engine_one(self):
        from tongshu.engines.heluo.hua_gong import _JQ_ORDER
        from tongshu.engines.heluo.jiehhou import SOLAR_TERMS
        self.assertIs(_JQ_ORDER, SOLAR_TERMS, "引的不是引擎那份对象")

    def test_window_table_is_still_original_text_not_a_duplicate(self):
        """窗口表**不是**重复实现——它是原典 L558–L567 的规则本身，必须保留。

        这条防的是把「不重复计算」执行过头：把原典规则也当成"自造表"删掉。
        """
        code = re.sub(r"\s+", "", _code_only(HG))
        self.assertIn("HUAGONG_JIEQI_WINDOWS", code)
        self.assertIn("HUAGONG_FAN_JIEQI", code, "L585–L594 互证表被删了")

    # ── 纪律三：兜底必须自曝 ────────────────────────────────
    def test_fallback_disclosed_when_no_jq(self):
        from tongshu.engines.heluo.hua_gong import compute_huagong
        r = compute_huagong("乾", "乾", "乾", "乾", "午")
        ev = " ".join(r.evidence)
        self.assertIn("兜底", ev)
        self.assertIn("寅/巳/申/亥", ev,
                      "兜底时须写明近似表与原典窗口差在哪些月支")

    def test_date_path_still_works_when_no_upstream_jq(self):
        """无上游 jq 时仍可由出生日换算（委托 jiehhou，零自造）。"""
        from tongshu.engines.heluo.hua_gong import compute_huagong
        r = compute_huagong("乾", "乾", "乾", "乾", "午", birth_date="1724-05-22")
        ev = " ".join(r.evidence)
        self.assertIn("L558–L567", ev)
        self.assertIn("小满", ev)

    def test_bad_date_is_refused_not_guessed(self):
        from tongshu.engines.heluo.hua_gong import huagong_by_birth_date
        gua, note = huagong_by_birth_date("not-a-date")
        self.assertEqual(gua, "")
        self.assertIn("不是合法 ISO 日期", note)


if __name__ == "__main__":
    unittest.main()