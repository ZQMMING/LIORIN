# -*- coding: utf-8 -*-
"""河洛包打包身份守卫：**顶层包名隔离 + 命名空间干净**（2026-10-24 结构性重构）。

**为什么要有这个守卫**

重构前，河洛包 `pyproject.toml` 写 `name = "heluo-engine"`，
但 `[tool.setuptools.packages.find] where = ["src"]` 会把 `src/tongshu`
装成顶层包 `tongshu`。

后果（实测两种安装顺序）：
* 主仓 src 在前 ⇒ 河洛的 `heluo_engine.engines.heluo.canonical_signals` 消失
* 河洛包 site-packages 在前 ⇒ **主仓 32 个顶层子包全消失**
  （`tongshu.signal` / `tongshu.pipeline_stages` / `tongshu.api` …），
  且报错只说「找不到 tongshu.signal」，**不提示你装了本包** —— 静默破坏。

且本包与主仓**顶层包名都是 `tongshu`**，`engines/facts/reasoning/spec`
四个子包**同名重叠** ⇒ 两个 `tongshu` 不能同时 import。

**重构后的状态（2026-10-24）**

顶层包名已由 `tongshu` 改为 **`heluo_engine`**：
* 与主仓命名空间**完全隔离** ⇒ 同环境共存、互不干扰；
* `src/tongshu/` **必须不存在**（哪怕只剩空目录也会被 Python 当成
  **命名空间包**，导致 `import tongshu` 成功却无任何子模块 ——
  实测踩过，是「守卫恒不生效」的隐形坑）。

**本守卫的职责（河洛域内、不越权）**：
1. 断言顶层包目录为 `heluo_engine`，且 `src/tongshu/` 不存在（含空目录）；
2. 断言 `pyproject.toml` 的包发现**只**认 `heluo_engine*`；
3. 断言 `src/` 内**没有**任何 `tongshu` 绝对导入
   （误留会在主仓环境里静默取到主仓的同名模块）；
4. 断言历史冲突已被**显式登记**在决策单里（含实测证据），
   防止后人以为「从来没出过这个问题」而把顶层包名改回去。
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

PKG_NAME = "heluo-engine"
#: 本包实际使用的顶层包名（= src/ 下的目录名）
TOP_PACKAGE = "heluo_engine"
#: 主仓顶层包名 —— 本包**不得**再占用
MAIN_TOP_PACKAGE = "tongshu"

#: 主仓**专有**的顶层子包 —— 本包 src/ 内若出现这些绝对导入，
#: 说明某处误从主仓取模块（在本包独立环境里会 ModuleNotFoundError，
#: 在主仓环境里则会静默用主仓的版本 —— 正是「同名不同源」陷阱）。
MAIN_ONLY_TOP = (
    "pipeline", "pipeline_stages", "signal", "api", "render", "services",
    "db", "golden", "governance", "models", "types", "main",
    "assertion", "assertion_v2", "cross_domain", "feature_registry",
    "canonical", "corpus", "evaluation", "k2g", "luming", "chain",
    "bian", "temporal", "validation", "audit", "classic_evidence",
)


class TestPackageIdentity(unittest.TestCase):
    """包名与顶层包的一致性。"""

    def test_pyproject_name_matches_distribution(self):
        """`pyproject.toml` 的 name 存在且非空。"""
        p = ROOT / "pyproject.toml"
        self.assertTrue(p.exists(), "缺 pyproject.toml")
        txt = p.read_text(encoding="utf-8")
        m = re.search(r'^name\s*=\s*"([^"]+)"', txt, re.M)
        self.assertIsNotNone(m, "pyproject.toml 读不到 [project].name")
        self.assertEqual(m.group(1), PKG_NAME)

    def test_top_level_package_dir_exists(self):
        """src/ 下的顶层包目录存在。"""
        self.assertTrue((ROOT / "src" / TOP_PACKAGE).is_dir(),
                        f"src/{TOP_PACKAGE}/ 不存在")

    def test_main_repo_namespace_not_occupied(self):
        """★ `src/tongshu/` **必须不存在**。

        ⚠ 不只是「没有源码」—— **空目录也不行**：
        Python 会把无 `__init__.py` 的目录当成**命名空间包**，
        于是 `import tongshu` **成功**、但 `tongshu.pipeline` 等子模块全缺
        （实测踩过：残留 `src/tongshu/__pycache__` 导致跨仓守卫
        「主仓可用」的判定恒真，跨仓测试照样在独立包内炸红）。
        """
        legacy = ROOT / "src" / MAIN_TOP_PACKAGE
        self.assertFalse(legacy.exists(),
                         f"src/{MAIN_TOP_PACKAGE}/ 仍存在 —— 本包已改用顶层包 "
                         f"`{TOP_PACKAGE}`，留着它会与主仓抢命名空间"
                         "（空目录亦会被 Python 当成命名空间包）")

    def test_packages_find_targets_only_own_package(self):
        """★ 包发现只认 `heluo_engine*`，不得装出 `tongshu`。"""
        txt = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r"\[tool\.setuptools\.packages\.find\](.*?)(\n\[|\Z)",
                      txt, re.S)
        self.assertIsNotNone(m, "pyproject.toml 读不到 packages.find 段")
        block = m.group(1)
        inc = re.search(r'include\s*=\s*\[([^\]]*)\]', block)
        self.assertIsNotNone(inc, "packages.find 缺 include")
        items = [s.strip().strip('"\'') for s in inc.group(1).split(",") if s.strip()]
        self.assertIn(f"{TOP_PACKAGE}*", items,
                      f"packages.find 未包含 {TOP_PACKAGE}* —— 会装不出本包")
        for bad in items:
            self.assertFalse(bad.startswith(MAIN_TOP_PACKAGE),
                             f"packages.find 含 {bad} —— 会装出与主仓同名的顶层包")
        # 断言 include 是**穷举**的：不能有别的顶层包混进来
        self.assertEqual(sorted(items), sorted([f"{TOP_PACKAGE}*"]),
                         f"packages.find 的 include 混入了其它包：{items}")

    def test_name_conflict_is_registered_not_silent(self):
        """★ 顶层包名 `tongshu` 与主仓**同名** —— 这是已发生过的破坏性冲突。

        本包 `name = "heluo-engine"` 却曾装出顶层包 `tongshu`：
        两个 `tongshu` 不能同时 import（实测会互相吃掉对方，
        见决策单 §2.1）。

        故此处**不是**断言「无冲突」，而是断言：
        **这个冲突已被显式登记在决策单里** —— 防止它被当成「已解决」
        而静默留存。若将来顶层包名改了，本守卫会失败，
        提醒同步更新决策单。
        """
        doc = ROOT / "src" / TOP_PACKAGE / "docs" / "河洛回灌接线决策单_20261024.md"
        self.assertTrue(doc.exists(),
                        "缺河洛回灌接线决策单 —— 顶层包名冲突必须显式登记")
        txt = doc.read_text(encoding="utf-8")
        # ⚠ 不能只断言「出现过某关键词」—— 删掉其中一处仍会绿。
        #   故按**必须共现的证据组合**断言（每组都是该决策不可缺的要素）。
        combos = [
            # 冲突事实 + 实测证据（两种安装顺序互相吃掉）
            ("tongshu", "互", "site-packages"),
            # 冲突 + 处置方案（顶层改名）
            ("tongshu", "heluo_engine", "顶层"),
            # 冲突 + 影响面（主仓子包消失）
            ("tongshu", "signal", "UNKNOWN"),
        ]
        for combo in combos:
            with self.subTest(combo=combo):
                missing = [k for k in combo if k not in txt]
                self.assertEqual(missing, [],
                                 f"决策单缺要素 {missing} —— "
                                 "顶层包名冲突的登记不完整")
        # ⚠ 关键词「出现过」不够：删掉其中一处仍会绿。
        #   故对**决定性证据**断言**出现次数下界**：
        #   「两个同名 tongshu 会互相吃掉对方」这一实测结论，
        #   是路径 A/C 的**否决依据**，其证据（报错形态 + 主仓子包消失）
        #   不得被删减。
        for frag, need in (("ModuleNotFoundError", 2),
                           ("tongshu.signal", 2),
                           ("顶层包名", 4),
                           ("静默", 2)):
            with self.subTest(frag=frag):
                self.assertGreaterEqual(
                    txt.count(frag), need,
                    f"决策单中「{frag}」出现次数不足 {need} —— "
                    "顶层包名冲突的实测证据被削弱，"
                    "该结论是路径 A/C 的否决依据，不得删减")

    def test_src_has_no_absolute_import_of_main_only_modules(self):
        """src/ 内不得有指向**主仓专有**模块的绝对导入。

        这类导入在本包独立环境里 ModuleNotFoundError；
        在主仓环境里则**静默**取到主仓的同名模块 —— 「同名不同源」陷阱。
        """
        bad = []
        for p in sorted((ROOT / "src").rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                m = re.search(r"from\s+tongshu\.([a-z_]+)", ln)
                if m and m.group(1) in MAIN_ONLY_TOP:
                    bad.append(f"{rel}:{i}: {ln.strip()[:80]}")
        self.assertEqual(bad, [],
                         "src/ 内有指向主仓专有模块的绝对导入（会静默取主仓版本）：\n"
                         + "\n".join(bad))


class TestNoCrossRepoImportInSrc(unittest.TestCase):
    """src/ 内的绝对导入只能是**本包自有**模块。"""

    def test_absolute_imports_target_only_own_package(self):
        """src/ 内**不得**有任何 `from tongshu.X` 绝对导入。

        重构后本包顶层包名是 `heluo_engine`，与主仓命名空间**完全隔离**：
        src/ 内残留任何 `tongshu` 绝对导入都意味着
        「本包运行时偷偷依赖主仓」—— 在独立部署（服务器）上必炸。
        """
        bad = []
        for p in sorted((ROOT / "src").rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"^\s*from\s+tongshu[\s.]", ln) or \
                        re.search(r"^\s*import\s+tongshu[\s.]", ln):
                    bad.append(f"{rel}:{i}: {ln.strip()[:80]}")
        self.assertEqual(bad, [],
                         "src/ 内有指向主仓顶层包的绝对导入（本包须能独立部署）：\n"
                         + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
