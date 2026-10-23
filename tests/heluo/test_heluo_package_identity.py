# -*- coding: utf-8 -*-
"""河洛包打包守卫：防止「顶层包名 ≠ pyproject name」这类静默破坏复发。

**为什么要有这个守卫**

实测（2026-10-24）：河洛包 `pyproject.toml` 写 `name = "heluo-engine"`，
但 `[tool.setuptools.packages.find] where = ["src"]` 会把 `src/tongshu`
装成顶层包 `tongshu`。

后果（实测两种安装顺序）：
* 主仓 src 在前 ⇒ 河洛的 `tongshu.engines.heluo.canonical_signals` 消失
* 河洛包 site-packages 在前 ⇒ **主仓 32 个顶层子包全消失**
  （`tongshu.signal` / `tongshu.pipeline_stages` / `tongshu.api` …），
  且报错只说「找不到 tongshu.signal」，**不提示你装了河洛包** —— 静默破坏。

且本包与主仓**顶层包名都是 `tongshu`**，`engines/facts/reasoning/spec`
四个子包**同名重叠** ⇒ 两个 `tongshu` 不能同时 import。

**本守卫的职责（河洛域内、不越权）**：
1. 断言本包顶层包名与 `pyproject.toml` 的 `name` **一致**
   （或显式登记为「已知冲突 + 处置方案」）；
2. 断言本包**不**声明会覆盖主仓同名顶层包的安装布局；
3. 断言 `src/` 内**没有**指向主仓专有模块的绝对导入
   （`tongshu.pipeline` 等在主仓才有，误留在本包会静默指向主仓）。

**不改行为、不改包名** —— 包名处置属架构决策，见
`data/heluo/河洛回灌接线决策单_20261024.md` §5。
本守卫只负责：**让这个隐患显形、可被 CI 抓住**。
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
TOP_PACKAGE = "tongshu"

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

    def test_name_conflict_is_registered_not_silent(self):
        """★ 顶层包名 `tongshu` 与主仓**同名** —— 这是已知的破坏性冲突。

        本包 `name = "heluo-engine"` 却装出顶层包 `tongshu`：
        两个 `tongshu` 不能同时 import（实测会互相吃掉对方，
        见决策单 §2.1）。

        故此处**不是**断言「无冲突」，而是断言：
        **这个冲突已被显式登记在决策单里** —— 防止它被当成「已解决」
        而静默留存。若将来顶层包名改了，本守卫会失败，
        提醒同步更新决策单。
        """
        doc = ROOT / "data" / "heluo" / "河洛回灌接线决策单_20261024.md"
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
        """src/ 内的 `from tongshu.X` 只允许本包自有的子包。"""
        own = {"engines", "facts", "reasoning", "spec"}
        bad = []
        for p in sorted((ROOT / "src").rglob("*.py")):
            rel = p.relative_to(ROOT).as_posix()
            for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                m = re.search(r"from\s+tongshu\.([a-z_]+)", ln)
                if m and m.group(1) not in own:
                    bad.append(f"{rel}:{i}: {ln.strip()[:80]}")
        self.assertEqual(bad, [],
                         "src/ 内有指向本包不存在子包的绝对导入：\n"
                         + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
