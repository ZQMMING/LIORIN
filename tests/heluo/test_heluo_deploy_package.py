# -*- coding: utf-8 -*-
"""河洛引擎**独立部署守卫**（2026-10-24 结构性重构）。

**这个守卫盯住什么**

用户交付要求：河洛引擎要能**单独装到服务器上**跑 ——
不依赖主仓仓库、不依赖运行目录、不依赖 CWD、不依赖任何绝对路径。

这类要求最容易**悄悄退化**：哪天有人为了「快速修个 bug」
在某个模块里写回 `Path(__file__).resolve().parents[4] / "data" / ...`，
测试照样全绿（只要那个仓库结构还在），但**服务器上直接炸**。
本守卫把这类退化变成 CI 红灯。

**守卫清单**

1. **零路径绑定（源码扫描）**
   - 不得用 `parents[N]`（N≥2）反推仓库根 —— 换目录层级即失效；
   - 不得出现机器绝对路径字面量（`D:\\` / `C:\\` / `D:/`）；
   - 不得出现旧布局字面量 `data/heluo`；
   - 不得用 `os.path.join(..., "..", "..", ...)` 拼路径。
2. **数据定位唯一入口**：判词库 / 参评诗断语料 / 出生地点表三处
   必须走包内定位（`_paths`），不得各自造轮子。
3. **随包三件套**：`data/` / `orig/` / `docs/` 必须在包内且非空，
   且被 `pyproject.toml` 的 package-data 覆盖（否则 pip 装完是空壳）。
4. **独立可运行**：在**仓库外**的临时目录、**干净子进程**里
   `import heluo_engine` 并跑通一例完整算例 ——
   这是「服务器上能不能用」的直接证据。
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

PKG_DIR = ROOT / "src" / "heluo_engine"
PKG_NAME = "heluo_engine"

#: 必须随包分发的资源三件套（目录名 → 至少要有的文件数）
REQUIRED_RESOURCE_DIRS = {
    "data": 4,       # 判词库/精义/扩展断语/locations + canping/
    "orig": 4,      # 原典切片
    "docs": 4,      # 依据文档
}


def _src_files():
    return sorted((ROOT / "src").rglob("*.py"))


def _code_only(src: str) -> str:
    """返回**只含可执行代码**的源码：剥掉三引号文档字符串与 ``#`` 注释。

    ⚠ 为什么必须剥：本包大量注释在**说明旧实现**
    （如「旧实现 `_REPO_ROOT = Path(__file__).resolve().parents[4]`」），
    若不剥，全文扫描会把**历史说明**误判成**现存缺陷** ——
    那是假红；反过来，若只查注释，又会漏掉真正的代码。
    注释是否提及与缺陷是否存在是两件事，故断言必须落在可执行代码上。
    """
    tree = ast.parse(src.lstrip("﻿"))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list):
            node.body = [n for n in body
                         if not (isinstance(n, ast.Expr)
                                 and isinstance(n.value, ast.Constant)
                                 and isinstance(n.value.value, str))]
    out = []
    for line in ast.unparse(tree).split("\n"):
        out.append(re.sub(r"\s+#.*$", "", line))
    return "\n".join(out)


class TestZeroPathBinding(unittest.TestCase):
    """源码层：不得有任何「靠目录层级/绝对路径」定位资源。"""

    def test_no_repo_root_inference_by_parents_depth(self):
        """不得用 `parents[N]`（N≥2）反推仓库根。

        旧实现：`Path(__file__).resolve().parents[4] / "data" / "heluo"`。
        任何 `parents[2]` 及以上都意味着「包内层级深度被写死」——
        包一换位置就失效。包内定位必须走 `heluo_engine._paths`。
        """
        bad = []
        for p in _src_files():
            rel = p.relative_to(ROOT).as_posix()
            for i, ln in enumerate(_code_only(p.read_text(encoding="utf-8")).splitlines(), 1):
                if re.search(r"parents\[\s*([2-9])\s*\]", ln):
                    bad.append(f"{rel}:{i}: {ln.strip()[:90]}")
        self.assertEqual(bad, [],
                         "src/ 内用 parents[N≥2] 反推仓库根（换层级即失效）：\n"
                         + "\n".join(bad))

    def test_no_machine_absolute_path_literals(self):
        """不得出现机器绝对路径字面量。"""
        bad = []
        pat = re.compile(r"[\"']([A-Za-z]:[\\/])")
        for p in _src_files():
            rel = p.relative_to(ROOT).as_posix()
            for i, ln in enumerate(_code_only(p.read_text(encoding="utf-8")).splitlines(), 1):
                if pat.search(ln):
                    bad.append(f"{rel}:{i}: {ln.strip()[:90]}")
        self.assertEqual(bad, [],
                         "src/ 内出现机器绝对路径字面量（换机器即失效）：\n"
                         + "\n".join(bad))

    def test_no_legacy_layout_literal(self):
        """不得出现旧布局字面量 `data/heluo`。"""
        bad = []
        for p in _src_files():
            rel = p.relative_to(ROOT).as_posix()
            for i, ln in enumerate(_code_only(p.read_text(encoding="utf-8")).splitlines(), 1):
                if "data/heluo" in ln:
                    bad.append(f"{rel}:{i}: {ln.strip()[:90]}")
        self.assertEqual(bad, [],
                         "src/ 内仍引用旧布局 data/heluo（资源已随包）：\n"
                         + "\n".join(bad))

    def test_no_dotdot_path_join(self):
        """不得用 `..` 逐级上跳拼路径。"""
        bad = []
        pat = re.compile(r"[\"']\.\.[\"']")
        for p in _src_files():
            rel = p.relative_to(ROOT).as_posix()
            for i, ln in enumerate(_code_only(p.read_text(encoding="utf-8")).splitlines(), 1):
                if pat.search(ln):
                    bad.append(f"{rel}:{i}: {ln.strip()[:90]}")
        self.assertEqual(bad, [],
                         "src/ 内用 '..' 逐级上跳拼路径（层级一换即失效）：\n"
                         + "\n".join(bad))


class TestDataLocationSingleEntrance(unittest.TestCase):
    """数据定位必须走包内定位模块，不得各自造轮子。"""

    def test_guajie_uses_pkg_data(self):
        """判词库必须经 `_paths.pkg_data` 取得，且不得自己拼路径。

        ⚠ 不能只断言「代码里出现过 `pkg_data`」—— 那太弱：
        有人照样可以写 `pkg_data("x")` 之后再用 `Path(__file__).resolve().parents[N]`
        去覆盖它。故此处断三件事：
          (a) 代码里**没有任何** `Path(__file__)` 相对定位；
          (b) 判词库 / 精义 / 扩展断语三个数据入口**都**由 `_pkg_data(...)` 赋值；
          (c) 断的是**赋值语句的形态**，不是「出现过某关键词」。
        """
        txt = (PKG_DIR / "engines" / "heluo" / "guajie.py").read_text(encoding="utf-8")
        code = _code_only(txt)
        self.assertIn("pkg_data", txt,
                      "guajie.py 未走包内数据定位")
        self.assertNotIn("Path(__file__", code,
                         "guajie.py 的可执行代码里出现 Path(__file__) 相对定位"
                         "（数据必须由 _paths.pkg_data 取得）")
        for var, f in (("_GUAJIE_DATA", "guajie_data.json"),
                       ("_JINGYI_DATA", "guajie_jingyi.json")):
            with self.subTest(var=var):
                self.assertRegex(
                    code, rf"{var}\s*=\s*_pkg_data\(\s*[\"']{re.escape(f)}[\"']\s*\)",
                    f"{var} 不是由 _pkg_data(\"{f}\") 取得 —— 数据定位被绕过了")

    def test_canping_uses_pkg_data(self):
        """参评诗断语料走 `_paths.pkg_data`。"""
        txt = (PKG_DIR / "engines" / "heluo" / "canping.py").read_text(encoding="utf-8")
        self.assertIn("pkg_data", txt,
                      "canping.py 未走包内数据定位")

    def test_location_registry_uses_package_resources(self):
        """出生地点表走包内资源定位。"""
        txt = (PKG_DIR / "engines" / "time" / "location_registry.py").read_text(encoding="utf-8")
        self.assertIn("heluo_engine", txt,
                      "location_registry.py 未按包名定位 locations.json")
        self.assertIn("locations.json", txt)


class TestResourcesShipWithPackage(unittest.TestCase):
    """随包资源三件套：齐备 + 被 package-data 覆盖。"""

    def test_resource_dirs_exist_and_nonempty(self):
        for name, min_files in REQUIRED_RESOURCE_DIRS.items():
            with self.subTest(dir=name):
                d = PKG_DIR / name
                self.assertTrue(d.is_dir(), f"包内缺 {name}/ 目录")
                n = sum(1 for _ in d.rglob("*") if _.is_file())
                self.assertGreaterEqual(
                    n, min_files,
                    f"包内 {name}/ 只有 {n} 个文件（至少 {min_files}）")

    def test_runtime_json_present(self):
        """运行时必需的 4 个 JSON + 参评语料目录。"""
        for n in ("guajie_data.json", "guajie_jingyi.json",
                  "kuozhan_duanyu.json", "locations.json"):
            with self.subTest(f=n):
                self.assertTrue((PKG_DIR / "data" / n).is_file(),
                                f"包内缺 {n}")
        self.assertTrue((PKG_DIR / "data" / "canping").is_dir(),
                        "包内缺 data/canping/")

    def test_pyproject_packages_them(self):
        """`pyproject.toml` 的 package-data 必须覆盖三件套。"""
        txt = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r"\[tool\.setuptools\.package-data\](.*?)(\n\[|\Z)",
                      txt, re.S)
        self.assertIsNotNone(m, "pyproject.toml 缺 package-data 段")
        block = m.group(1)
        for frag in ("data/*.json", "data/canping/*.json",
                     "orig/*.txt", "docs/*.md"):
            with self.subTest(frag=frag):
                self.assertIn(frag, block,
                              f"package-data 未覆盖 {frag} —— pip 装完是空壳")


class TestStandaloneRunnable(unittest.TestCase):
    """★ 独立部署的直接证据：仓库外、干净子进程、跑通一例完整算例。"""

    def test_import_and_compute_outside_repo(self):
        """在仓库外的临时目录里，用干净子进程 import + 算一例。"""
        with tempfile.TemporaryDirectory(prefix="heluo_deploy_") as td:
            script = Path(td) / "run.py"
            script.write_text(
                "import json\n"
                "from heluo_engine import HeluoAdapter\n"
                "from heluo_engine._paths import pkg_data, pkg_orig, pkg_doc\n"
                "# ★ 资源必须**按包**解析得到（不是仓库路径拼出来的）\n"
                "for p in (pkg_data('guajie_data.json'),\n"
                "          pkg_data('guajie_jingyi.json'),\n"
                "          pkg_data('kuozhan_duanyu.json'),\n"
                "          pkg_data('locations.json'),\n"
                "          pkg_data('canping', '448_duizhao.json'),\n"
                "          pkg_orig('河洛真数_起例卷之上.txt'),\n"
                "          pkg_doc('死断四条件核定_20261024.md')):\n"
                "    assert p.is_file(), '包内资源缺失: %s' % p\n"
                "ad = HeluoAdapter()\n"
                "r = ad.compute((1983, 11, 3, 12), gender='male',\n"
                "               target_date='2026-10-23')\n"
                "print(json.dumps({\n"
                "    'prenatal': r.prenatal.hexagram_name,\n"
                "    'yuantang': r.yuantang.yuantang,\n"
                "    'postnatal': r.postnatal.hexagram_name,\n"
                "}, ensure_ascii=False))\n",
                encoding="utf-8")
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            # ★ 不把仓库根放进 PYTHONPATH —— 只放 src（模拟已安装形态的源码可见性）
            env["PYTHONPATH"] = str(ROOT / "src")
            env.pop("PYTHONHOME", None)
            p = subprocess.run(
                [sys.executable, str(script)],
                cwd=td, env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=300)
            self.assertEqual(
                p.returncode, 0,
                "仓库外独立运行失败：\nSTDOUT:\n"
                + (p.stdout or "")[-2000:] + "\nSTDERR:\n" + (p.stderr or "")[-3000:])
            out = json.loads((p.stdout or "").strip().splitlines()[-1])
            # 基准案例：1983-11-03 午时男
            self.assertEqual(out["prenatal"], "风山渐")
            self.assertEqual(out["postnatal"], "火风鼎")
            self.assertEqual(out["yuantang"], "初六")

    def test_package_resources_resolvable(self):
        """包内资源定位在**已安装形态**下也可用（importlib.resources）。"""
        code = (
            "from importlib.resources import files\n"
            "p = files('heluo_engine') / 'data' / 'guajie_data.json'\n"
            "assert p.is_file(), p\n"
            "print('OK')\n"
        )
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONPATH"] = str(ROOT / "src")
        p = subprocess.run([sys.executable, "-c", code],
                           cwd=tempfile.gettempdir(), env=env,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        self.assertEqual(p.returncode, 0,
                         "包内资源定位失败：\n" + (p.stderr or "")[-2000:])
        self.assertIn("OK", p.stdout or "")


if __name__ == "__main__":
    unittest.main()
