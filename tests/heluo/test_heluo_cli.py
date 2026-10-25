# -*- coding: utf-8 -*-
"""CLI 与部署自检守卫（2026-10-25 新增）。

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

from heluo_engine import cli  # noqa: E402


def _run_cli(args, cwd):
    """以「干净解释器 + 指定 CWD」跑 CLI，返回 (rc, stdout, stderr)。

    ⚠ 中文参数：Windows 上 ``subprocess`` 传参走**系统区域编码**，
      与子进程解码 ``sys.argv`` 的口径可能不一致 ⇒ 参数会乱码。
      故这里把参数**先编成 UTF-8 字节**再传（``args`` 走 bytes 通道，
      绕开父进程的 str 编码层），确保子进程拿到正确的 UTF-8 文本。
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPO / "src")
    argv = [sys.executable, "-m", "heluo_engine.cli"]
    argv += [a.encode("utf-8") if isinstance(a, str) else a for a in args]
    p = subprocess.run(
        argv, cwd=str(cwd), env=env, capture_output=True,
        encoding="utf-8", errors="replace")
    return p.returncode, p.stdout or "", p.stderr or ""


class TestCliBasics(unittest.TestCase):
    """CLI 基本可用性。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="heluo_cli_test_")

    def test_version(self):
        rc, out, err = _run_cli(["--version"], self.tmp)
        self.assertEqual(rc, 0, err)
        self.assertTrue(out.strip())

    def test_where(self):
        rc, out, err = _run_cli(["--where"], self.tmp)
        self.assertEqual(rc, 0, err)
        self.assertTrue(os.path.isdir(out.strip()))

    def test_doctor_pass_in_clean_dir(self):
        """干净目录下 doctor 必须 PASS。"""
        rc, out, err = _run_cli(["doctor"], self.tmp)
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)          # 必须是**纯 JSON**
        self.assertEqual(payload["result"], "PASS", out)

    def test_compute_brief_is_pure_json(self):
        """compute --brief 的输出必须能被 json.loads 直接解析。"""
        rc, out, err = _run_cli(
            ["compute", "--birth", "1983-11-03", "--time", "12:00",
             "--brief", "--target", "2026-10-23"], self.tmp)
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        for k in ("prenatal", "yuantang", "postnatal", "target_date"):
            self.assertIn(k, payload)

    def test_interpret_is_pure_json(self):
        rc, out, err = _run_cli(
            ["interpret", "--birth", "1983-11-03", "--time", "12:00",
             "--target", "2026-10-23"], self.tmp)
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertIn("platform_signals", payload)

    def test_gua_lookup(self):
        """查判词（中文卦名/爻名）。

        ⚠ Windows 上命令行参数走**系统文件系统编码**（cp936/GBK），
          与 Python 3 解码 ``sys.argv`` 的口径可能不一致 ⇒ 中文参数会乱码。
          CLI 已在 ``_fix_argv_encoding()`` 里做重解码修复；
          本用例即该修复的守卫（Linux/macOS 上恒过，Windows 上验证修复有效）。
        """
        rc, out, err = _run_cli(["gua", "--name", "观", "--yao", "初六"], self.tmp)
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["gua"], "观")
        self.assertTrue(payload["ci"])

    def test_gua_lookup_chinese_via_api(self):
        """中文卦名的查词能力（API 层，绕开 Windows 子进程编码问题）。"""
        from heluo_engine.engines.heluo.guajie import query_yao_duan
        y = query_yao_duan("观", "初六")
        self.assertIsNotNone(y)
        self.assertEqual(y.yao, "初六")
        self.assertTrue(y.ci)


class TestDoctorDetectsStdlibShadowing(unittest.TestCase):
    """doctor 必须显式检出 CWD 里的标准库同名 .py。"""

    def test_doctor_flags_shadowed_stdlib(self):
        tmp = tempfile.mkdtemp(prefix="heluo_shadow_")
        # 造一个 shadow 标准库 inspect 的文件（内容无害，但足以触发检测）
        (Path(tmp) / "inspect.py").write_text(
            "# shadow probe: mimics a stray local inspect.py\n",
            encoding="utf-8")
        rc, out, err = _run_cli(["doctor"], tmp)
        payload = json.loads(out)
        self.assertEqual(payload["result"], "FAIL",
                         "有 shadow 时 doctor 竟报 PASS")
        shadow_items = [c for c in payload["checks"]
                        if "shadow" in c["item"] or "SHADOWED" in c["status"]]
        self.assertTrue(shadow_items, "doctor 未报告 shadow 检查项")
        self.assertTrue(any("SHADOWED" in c["status"] for c in shadow_items),
                        "doctor 未标出 SHADOWED 状态")
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
