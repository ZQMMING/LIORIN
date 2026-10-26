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

⚠⚠⚠ **本守卫绝不能碰真实的 ``src/``**（2026-10-26 实测踩过）
----------------------------------------------------------------
扫描是**原地改源码**的。本守卫若直接对真实仓库跑扫描：

  · 会**污染真实源码**（实测：残留了 frozen_state / hua_gong 的变异）；
  · 而本守卫文件**本身在 ``tests/heluo/`` 里** ⇒ 扫描器的「慢速确认」
    会跑全量 ``tests/heluo`` ⇒ **把本守卫也跑起来** ⇒
    本守卫又启动一个扫描 ⇒ **两个扫描进程同时改同一份 src/**
    ⇒ 结果全错（这正是仓里「一次只跑一个扫描进程」纪律要防的事）。

⇒ 修法（本文件采用）：
  1. **把源码与工具拷到临时目录**再跑扫描 ⇒ 真实 ``src/`` 绝不被碰；
  2. 设环境变量 ``HELUO_SWEEP_SELFTEST=1`` ⇒ 副本里的本守卫**立即跳过**
     ⇒ **递归熔断**（否则无限套娃：扫描 → 全量测试 → 本守卫 → 扫描 → …）。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

#: ★ 递归熔断标记：副本里的本守卫看到它就跳过。
#:   （否则 扫描 → 慢速确认跑全量 tests/heluo → 本守卫 → 又一个扫描 → 无限套娃）
_SELFTEST_ENV = "HELUO_SWEEP_SELFTEST"

_SWEEP_REL = Path("tools") / "heluo" / "mutation_sweep.py"


def _make_sandbox() -> Path:
    """把**源码与工具**拷到临时目录（真实 src/ 绝不被碰）。"""
    sandbox = Path(tempfile.mkdtemp(prefix="mutsweep_sandbox_"))
    (sandbox / "src").mkdir(parents=True, exist_ok=True)
    shutil.copytree(_REPO / "src" / "heluo_engine",
                    sandbox / "src" / "heluo_engine",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # ⚠ 目标目录**不要**预先 mkdir（copytree 要求目标不存在）
    (sandbox / "tools").mkdir(parents=True, exist_ok=True)
    shutil.copytree(_REPO / "tools" / "heluo", sandbox / "tools" / "heluo",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return sandbox


def _run_sweep_in_sandbox(sandbox: Path, tests_dir: Path, out_json: Path):
    """在**副本**里跑一次扫描（绝不触碰真实源码）。"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(sandbox / "src")
    env["PYTHONUTF8"] = "1"
    env["PYTHONHASHSEED"] = "0"
    # ★ 递归熔断：副本里的本守卫看到这个标记就跳过
    env[_SELFTEST_ENV] = "1"
    p = subprocess.run(
        [sys.executable, "-X", "utf8", str(sandbox / _SWEEP_REL),
         "--module", "frozen_state.py",
         "--tests", str(tests_dir),
         "--json-out", str(out_json),
         "--limit", "6"],
        cwd=str(sandbox), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=1800)
    return p


class TestMutationSweepSelfCheck(unittest.TestCase):
    """扫描器必须能「发现真盲区」，且必须以非 0 退出码报告。"""

    def setUp(self):
        # ⚠ 递归熔断：若本测试是被**另一个扫描**触发的（慢速确认跑全量
        #   tests/heluo 时会包含本文件）⇒ 立即跳过，避免无限套娃。
        if os.environ.get(_SELFTEST_ENV):
            self.skipTest("自检熔断：本次运行处在扫描器的慢速确认里")

    def test_sweep_detects_a_planted_blind_spot(self):
        sandbox = _make_sandbox()
        try:
            # 只含恒真用例 ⇒ 任何变异都抓不住
            tests_dir = sandbox / "trivial_tests"
            tests_dir.mkdir()
            (tests_dir / "test_always_passes.py").write_text(
                "# -*- coding: utf-8 -*-\n"
                "def test_always_passes():\n"
                "    assert True\n",
                encoding="utf-8")
            out_json = sandbox / "result.json"

            p = _run_sweep_in_sandbox(sandbox, tests_dir, out_json)

            self.assertTrue(out_json.exists(),
                            "扫描器未产出结果 JSON（工具坏了？）：%s"
                            % ((p.stdout or "") + (p.stderr or ""))[-1500:])
            data = json.loads(out_json.read_text(encoding="utf-8"))

            self.assertTrue(data["baseline_ok"],
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
            self.assertEqual(p.returncode, 2,
                             "真盲区场景下退出码应为 2，实际 %d" % p.returncode)
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)

    def test_sweep_result_schema_is_stable(self):
        """扫描结果 JSON 的**字段名**必须稳定（CI 只认这些字段）。"""
        sandbox = _make_sandbox()
        try:
            tests_dir = sandbox / "trivial_tests"
            tests_dir.mkdir()
            (tests_dir / "test_always_passes.py").write_text(
                "# -*- coding: utf-8 -*-\n"
                "def test_always_passes():\n"
                "    assert True\n",
                encoding="utf-8")
            out_json = sandbox / "r.json"
            p = _run_sweep_in_sandbox(sandbox, tests_dir, out_json)
            self.assertTrue(out_json.exists(),
                            "未产出 JSON：%s"
                            % ((p.stdout or "") + (p.stderr or ""))[-1200:])
            data = json.loads(out_json.read_text(encoding="utf-8"))
            for key in ("schema", "killed", "blind_spots", "equivalent",
                        "hung", "unknown", "skipped", "restore_ok",
                        "restore_failures", "baseline_ok", "mutations_total"):
                self.assertIn(key, data, "结果 JSON 缺少字段 %r（CI 依赖它）" % key)
            self.assertEqual(data["schema"], 1, "结果 JSON 的 schema 版本变了")
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)

    def test_real_repo_source_is_untouched(self):
        """自检**绝不能**碰真实 src/（否则会污染仓库、且与扫描并发 ⇒ 结果全错）。"""
        before = {p: p.read_bytes() for p in
                  sorted((_REPO / "src" / "heluo_engine").rglob("*.py"))
                  if "__pycache__" not in p.parts}
        sandbox = _make_sandbox()
        try:
            tests_dir = sandbox / "trivial_tests"
            tests_dir.mkdir()
            (tests_dir / "test_always_passes.py").write_text(
                "def test_always_passes():\n    assert True\n", encoding="utf-8")
            _run_sweep_in_sandbox(sandbox, tests_dir, sandbox / "r.json")
        finally:
            shutil.rmtree(sandbox, ignore_errors=True)
        after = {p: p.read_bytes() for p in before}
        changed = [p.name for p in before if before[p] != after.get(p)]
        self.assertEqual(
            changed, [],
            "自检改动了真实源码 %s ⇒ 扫描与自检并发时会互相污染" % changed)


if __name__ == "__main__":
    unittest.main()
