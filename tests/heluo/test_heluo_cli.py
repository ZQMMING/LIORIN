# -*- coding: utf-8 -*-
"""CLI 守卫（2026-10-25 新增）。

守护三件事：
1. ``heluo-engine`` 命令行可用（``compute`` / ``doctor`` / ``gua`` / ``--version``）；
2. ``doctor`` 必须**显式检出**「CWD 里与标准库同名的 .py」——
   2026-10-25 实测踩坑：系统 TEMP 里的 ``inspect.py`` shadow 了标准库
   ``inspect`` ⇒ ``dataclasses`` import 期抛
   ``module 'inspect' has no attribute 'get_annotations'``，
   且该 shadow 文件被执行、向 stdout 打印 800 多条无关内容，
   把真正的错误彻底淹没。部署方必须能一眼看出这件事。
3. CLI 的输出必须是**干净 JSON**（不夹带任何旁路输出）——
   业务侧会直接 ``json.loads`` 引擎输出，夹带内容即解析失败。

⚠ 测试策略：**in-process 为主**（``cli.main(argv)`` 直接调用），
   子进程只保留「真实安装形态」的那几条。
   原因：子进程**不被 coverage 跟踪** ⇒ 若只用子进程测，
   cli.py 的覆盖率会显示 ~11%（实测），形成**假盲区**
   —— 「有测试」但覆盖率工具看不见，反过来让人误以为测过了。
   故两条路都要有：in-process 测逻辑分支，子进程测真实安装形态。
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from heluo_engine import cli  # noqa: E402


def _run_cli_inproc(argv):
    """in-process 调用 CLI：返回 (rc, stdout, stderr)。"""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:            # argparse 的 --help / 错误退出
            rc = int(exc.code or 0)
    return rc, out.getvalue(), err.getvalue()


def _run_cli_subproc(args, cwd):
    """子进程调用（验真实安装形态）。参数走 **bytes** 通道，
    绕开 Windows 父进程的 str 编码层（cp936 vs utf-8 不一致会毁掉中文参数）。"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPO / "src")
    argv = [sys.executable, "-m", "heluo_engine.cli"]
    argv += [a.encode("utf-8") if isinstance(a, str) else a for a in args]
    p = subprocess.run(
        argv, cwd=str(cwd), env=env, capture_output=True,
        encoding="utf-8", errors="replace")
    return p.returncode, p.stdout or "", p.stderr or ""


class TestCliInProcess(unittest.TestCase):
    """in-process：CLI 逻辑分支全覆盖（coverage 可跟踪）。"""

    def setUp(self):
        # ⚠ 必须在**干净目录**里跑：doctor 会检查「CWD 有无标准库同名 .py」，
        #   而仓库根下可能存在同名文件（历史上就踩过 inspect.py）。
        self.tmp = tempfile.mkdtemp(prefix="heluo_cli_inproc_")
        self._prev_cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_version(self):
        rc, out, err = _run_cli_inproc(["--version"])
        self.assertEqual(rc, 0, err)
        self.assertTrue(out.strip())

    def test_where(self):
        rc, out, err = _run_cli_inproc(["--where"])
        self.assertEqual(rc, 0, err)
        self.assertTrue(os.path.isdir(out.strip()))

    def test_no_command_prints_help(self):
        """不给子命令 ⇒ 打印帮助并返回 1（便于 shell 判成败）。"""
        rc, out, err = _run_cli_inproc([])
        self.assertEqual(rc, 1)
        self.assertIn("usage:", out)

    def test_doctor_pass_in_clean_dir(self):
        rc, out, err = _run_cli_inproc(["doctor"])
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["result"], "PASS", out)

    def test_doctor_reports_every_check(self):
        rc, out, err = _run_cli_inproc(["doctor"])
        payload = json.loads(out)
        items = [c["item"] for c in payload["checks"]]
        for must in ("包位置", "data/canping", "data/guajie_data.json",
                     "orig/河洛真数_起例卷之上.txt"):
            self.assertIn(must, items)
        # 必须含「CWD 无标准库同名 .py」这一项（部署风险显式化）
        self.assertTrue(any("shadow" in i or "CWD" in i for i in items),
                        "doctor 缺 CWD 检查项：%r" % items)

    def test_compute_brief_is_pure_json(self):
        rc, out, err = _run_cli_inproc(
            ["compute", "--birth", "1983-11-03", "--time", "12:00",
             "--brief", "--target", "2026-10-23"])
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        for k in ("prenatal", "yuantang", "postnatal", "target_date"):
            self.assertIn(k, payload)

    def test_compute_full_is_pure_json(self):
        rc, out, err = _run_cli_inproc(
            ["compute", "--birth", "1983-11-03", "--time", "12:00",
             "--target", "2026-10-23"])
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertIn("numbers", payload)
        self.assertIn("era", payload)
        self.assertIn("target_date_caliber", payload)

    def test_interpret_is_pure_json(self):
        rc, out, err = _run_cli_inproc(
            ["interpret", "--birth", "1983-11-03", "--time", "12:00",
             "--target", "2026-10-23"])
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertIn("platform_signals", payload)

    def test_gua_lookup(self):
        """中文卦名/爻名。

        ⚠ Windows 上命令行参数走**系统区域编码**（cp936/GBK），
          与 Python 3 解码 ``sys.argv`` 的口径可能不一致 ⇒ 中文参数会乱码。
          CLI 已在 ``_fix_argv_encoding()`` 里做重解码修复；
          本用例即该修复的守卫（Linux/macOS 上恒过，Windows 上验证修复有效）。
        """
        rc, out, err = _run_cli_inproc(["gua", "--name", "观", "--yao", "初六"])
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["gua"], "观")
        self.assertTrue(payload["ci"])

    def test_gua_not_found_returns_1(self):
        """查无此卦 ⇒ 退出码 1，错误走 stderr，**stdout 须为空**。"""
        rc, out, err = _run_cli_inproc(["gua", "--name", "不存在", "--yao", "初六"])
        self.assertEqual(rc, 1)
        self.assertEqual(out.strip(), "", "失败时 stdout 必须为空（否则污染 JSON 通道）")
        self.assertIn("查无此爻", err)

    def test_invalid_birth_returns_1(self):
        """非法出生日期 ⇒ 失败走 stderr、退出码 1（不抛栈给用户看）。"""
        rc, out, err = _run_cli_inproc(
            ["compute", "--birth", "not-a-date", "--time", "12:00"])
        self.assertEqual(rc, 1)
        self.assertIn("执行失败", err)


class TestCliSubprocess(unittest.TestCase):
    """子进程：验**真实安装形态**（与 in-process 互补）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="heluo_cli_sub_")

    def test_doctor_pass_in_clean_dir(self):
        rc, out, err = _run_cli_subproc(["doctor"], self.tmp)
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["result"], "PASS", out)

    def test_compute_brief_is_pure_json(self):
        rc, out, err = _run_cli_subproc(
            ["compute", "--birth", "1983-11-03", "--time", "12:00",
             "--brief", "--target", "2026-10-23"], self.tmp)
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertIn("prenatal", payload)


class TestDoctorDetectsStdlibShadowing(unittest.TestCase):
    """doctor 必须显式检出 CWD 里的标准库同名 .py。"""

    def test_doctor_flags_shadowed_stdlib(self):
        tmp = tempfile.mkdtemp(prefix="heluo_shadow_")
        # 造一个 shadow 标准库 inspect 的文件（内容无害，但足以触发检测）
        (Path(tmp) / "inspect.py").write_text(
            "# shadow probe: mimics a stray local inspect.py\n", encoding="utf-8")
        prev = os.getcwd()
        os.chdir(tmp)
        try:
            rc, out, err = _run_cli_inproc(["doctor"])
        finally:
            os.chdir(prev)
        payload = json.loads(out)
        self.assertEqual(payload["result"], "FAIL",
                         "有 shadow 时 doctor 竟报 PASS")
        shadow_items = [c for c in payload["checks"]
                        if "SHADOWED" in c["status"]]
        self.assertTrue(shadow_items, "doctor 未标出 SHADOWED 状态")
        self.assertNotEqual(rc, 0, "有 shadow 时 doctor 仍返回 0")


class TestNoStrayOutput(unittest.TestCase):
    """导入引擎本身不得产生任何 stdout 噪声。"""

    def test_import_is_silent(self):
        code = (
            "import io, contextlib, sys\n"
            "buf = io.StringIO()\n"
            "with contextlib.redirect_stdout(buf):\n"
            "    import heluo_engine\n"
            "    from heluo_engine import HeluoAdapter\n"
            "out = buf.getvalue()\n"
            "if out.strip():\n"
            "    print('STRAY:', repr(out[:200]))\n"
            "    raise SystemExit(1)\n"
            "print('SILENT')\n"
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = str(_REPO / "src")
        p = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        self.assertEqual(p.returncode, 0,
                         "import 期间有 stdout 噪声：%s" % p.stdout)


if __name__ == "__main__":
    unittest.main()
