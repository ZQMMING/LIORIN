# -*- coding: utf-8 -*-
r"""守卫：变异扫描**工具本身**必须自检通过（2026-10-26 新增）。

为什么要有这条
--------------
变异扫描是「**用工具验守卫**」的工具。⇒ 若**工具坏了**，它会给出
「一切正常」的假象 —— 这是**最坏**的失效模式：
守卫有洞却报告「盲区 0」。

工具可能坏在哪儿：
  · **扫描器自己跑不起来**（import 错、参数解析错）；
  · **变异没真注入进去**（如源码上下文变了 ⇒ 全部「跳过」）；
  · **永远判不出真盲区**（如快照不覆盖被测模块 ⇒ 全判成「等价」）；
  · **有盲区却仍返回 0**（退出码逻辑写错 ⇒ CI 恒绿）。

⇒ 本守卫**故意制造一个真盲区**，验证工具能抓到它：

    把守卫生效范围（--tests）指向一个只含**恒真用例**的临时目录
    ⇒ 没有任何守卫能抓住任何变异
    ⇒ 存活且行为改变的变异 ⇒ **必须**被判为真盲区
    ⇒ 扫描器**必须**返回退出码 **2**

⚠ 若这条守卫变红 ⇒ **扫描结论一律不可信**（别急着修产品代码，
  先修扫描器或快照）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

_SWEEP = _REPO / "tools" / "heluo" / "mutation_sweep.py"


class TestMutationSweepSelfCheck(unittest.TestCase):
    """扫描器必须能「发现真盲区」，且必须以非 0 退出码报告。"""

    def test_sweep_detects_a_planted_blind_spot(self):
        tmp = Path(tempfile.mkdtemp(prefix="mutsweep_selfcheck_"))
        # 只含恒真用例 ⇒ 任何变异都抓不住
        (tmp / "test_always_passes.py").write_text(
            "# -*- coding: utf-8 -*-\n"
            "def test_always_passes():\n"
            "    assert True\n",
            encoding="utf-8")
        out_json = tmp / "result.json"

        env = dict(os.environ)
        env["PYTHONPATH"] = str(_REPO / "src")
        env["PYTHONUTF8"] = "1"
        # ⚠ 固定 seed：保证「基线 vs 变异」可比（扫描器自己也固定了）
        env["PYTHONHASHSEED"] = "0"
        p = subprocess.run(
            [sys.executable, "-X", "utf8", str(_SWEEP),
             "--module", "frozen_state.py",
             "--tests", str(tmp),
             "--json-out", str(out_json),
             "--limit", "6"],
            cwd=str(_REPO), env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=1800)

        self.assertTrue(out_json.exists(),
                        "扫描器未产出结果 JSON（工具坏了？）：%s"
                        % ((p.stdout or "") + (p.stderr or ""))[-1500:])
        data = json.loads(out_json.read_text(encoding="utf-8"))

        self.assertTrue(
            data["baseline_ok"],
            "基线（未变异）就没通过 ⇒ 工具状态不对")
        self.assertTrue(
            data["restore_ok"],
            "扫描后源码未还原（工具坏了）⇒ 绝不能信任其结论")

        blind = data["blind_spots"]
        self.assertTrue(
            blind,
            "把守卫生效范围指向「只有恒真用例」的目录后，"
            "**所有**变异都该存活且行为改变 ⇒ 扫描器必须判为真盲区，"
            "但它报告了 0 条盲区 ⇒ **扫描器的盲区判定失效**"
            "（结论一律不可信）。当前统计：killed=%s equivalent=%s"
            % (data["killed"], data["equivalent"]))

        # ⚠ 退出码必须非 0（CI 靠它判红）
        self.assertNotEqual(
            p.returncode, 0,
            "发现了 %d 条真盲区，但扫描器退出码是 0 ⇒ "
            "CI 会判绿 ⇒ 守卫的洞被静默放过" % len(blind))
        self.assertEqual(
            p.returncode, 2,
            "真盲区场景下退出码应为 2，实际 %d" % p.returncode)

    def test_sweep_result_schema_is_stable(self):
        """扫描结果 JSON 的**字段名**必须稳定（CI 只认这些字段）。"""
        tmp = Path(tempfile.mkdtemp(prefix="mutsweep_schema_"))
        out_json = tmp / "r.json"
        # ⚠⚠ 基线范围**必须用隔离的临时目录**，**不能**用全量 tests/heluo。
        #   原因：全量里**包含本守卫自己** ⇒ 扫描器的基线跑全量时
        #   会再次调用本守卫 ⇒ **无限套娃** ⇒ 基线超时/红 ⇒ 假失败。
        #   （实测踩过：基线 rc=1，错误信息是「基线就红，先修基线」，
        #     极具误导性 —— 真实原因是套娃，不是产品代码坏了。）
        (tmp / "test_always_passes.py").write_text(
            "# -*- coding: utf-8 -*-\n"
            "def test_always_passes():\n"
            "    assert True\n",
            encoding="utf-8")
        env = dict(os.environ)
        env["PYTHONPATH"] = str(_REPO / "src")
        env["PYTHONUTF8"] = "1"
        env["PYTHONHASHSEED"] = "0"
        p = subprocess.run(
            [sys.executable, "-X", "utf8", str(_SWEEP),
             "--module", "frozen_state.py",
             "--tests", str(tmp),
             "--json-out", str(out_json),
             "--limit", "1"],
            cwd=str(_REPO), env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=1800)
        self.assertTrue(out_json.exists(),
                        "未产出 JSON：%s" % ((p.stdout or "") + (p.stderr or ""))[-1200:])
        data = json.loads(out_json.read_text(encoding="utf-8"))
        for key in ("schema", "killed", "blind_spots", "equivalent",
                    "hung", "unknown", "skipped", "restore_ok",
                    "restore_failures", "baseline_ok", "mutations_total"):
            self.assertIn(key, data, "结果 JSON 缺少字段 %r（CI 依赖它）" % key)
        self.assertEqual(data["schema"], 1, "结果 JSON 的 schema 版本变了")


if __name__ == "__main__":
    unittest.main()
