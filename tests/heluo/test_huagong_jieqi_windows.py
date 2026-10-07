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
        from tongshu.engines.heluo.hua_gong import OPPOSITE_TRIGRAM
        for gua, fan, _lo, _hi in self.FAN:
            self.assertEqual(OPPOSITE_TRIGRAM[gua], fan)

    # ── 静态：自校验必须在导入期跑 ───────────────────────────
    def test_self_check_runs_at_import(self):
        code = re.sub(r"\s+", "", _code_only(HG))
        self.assertIn("_huagong_self_check()", code.replace("def_huagong_self_check", ""))
        body = _code_only(HG)
        i = body.find("def _huagong_self_check")
        j = body.find("def ", i + 10)
        blk = re.sub(r"\s+", "", body[i:j])
        # 三件都要在：切满、互证、与 OPPOSITE_TRIGRAM 一致
        self.assertIn("==list(range(len(_JQ_ORDER)))", blk)
        self.assertIn("inside=={fan}", blk)
        self.assertIn("OPPOSITE_TRIGRAM.get(gua)==fan", blk)

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


class TestBranchSwitchPendingIsDeclared(unittest.TestCase):
    """反向守卫：窗口算对了不等于接上了。没接线这件事必须写在明处。"""

    @classmethod
    def setUpClass(cls):
        from tongshu.engines.heluo.hua_gong import HUAGONG_PENDING_BRANCH_SWITCH
        cls.P = HUAGONG_PENDING_BRANCH_SWITCH

    def test_pending_registered(self):
        self.assertIn("未接线", self.P)
        self.assertTrue(self.P["未接线"])

    def test_lists_both_affected_golden_tests(self):
        self.assertEqual(len(self.P["受影响 Golden"]), 2)
        joined = " ".join(self.P["受影响 Golden"])
        self.assertIn("test_h2_frozen_state.py", joined)
        self.assertIn("test_audit_batch_20261007.py", joined)

    def test_canonical_really_does_not_pass_birth_date_yet(self):
        """登记表说没接线，代码就真得没接——否则登记表在骗人。"""
        code = re.sub(r"\s+", "", _code_only(CN))
        i = code.find("returncompute_huagong(")
        self.assertGreater(i, 0)
        seg = code[i:i + 300]
        self.assertNotIn("birth_date=birth_date", seg,
                         "canonical 已下传 birth_date——待批准登记该撤销并改 Golden")

    def test_compute_huagong_does_accept_birth_date(self):
        """接口侧必须已就位，解除条件才只剩「改两条 Golden」。"""
        from tongshu.engines.heluo.hua_gong import compute_huagong
        import inspect
        self.assertIn("birth_date", inspect.signature(compute_huagong).parameters)

    def test_disclosed_in_evidence_when_falling_back(self):
        """没给出生日时，evidence 必须自曝走了兜底近似，不能装作用了原典。"""
        from tongshu.engines.heluo.hua_gong import compute_huagong
        r = compute_huagong("乾", "乾", "乾", "乾", "午")
        ev = " ".join(r.evidence)
        self.assertIn("兜底", ev)
        self.assertIn("寅/巳/申/亥", ev,
                      "兜底时须写明近似表与原典窗口差在哪些月支")

    def test_date_path_discloses_which_basis_used(self):
        from tongshu.engines.heluo.hua_gong import compute_huagong
        r = compute_huagong("乾", "乾", "乾", "乾", "午",
                            birth_date="1724-05-22")
        ev = " ".join(r.evidence)
        self.assertIn("L558–L567", ev)
        self.assertIn("震", ev)


if __name__ == "__main__":
    unittest.main()