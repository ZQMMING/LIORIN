# -*- coding: utf-8 -*-
"""守卫：包内不得有**零引用**的死函数 / 死类（2026-10-25 新增）。

为什么要有这条
--------------
2026-10-25 变异扫描实测发现：``time_layer_judgment._polarity_of``
在我重构（把判据改成内联）之后**变成了死代码** —— 定义了、零调用。
⇒ 它的所有变异都「存活」⇒ 变异扫描把盲区指到了它身上，
   但它**不是**行为盲区，而是**死代码**。
⇒ 说明缺一条「死代码」守卫：死代码会让 (a) 变异扫描的盲区清单被噪音污染，
   (b) 读者误以为该函数在起作用。

怎么判「零引用」
--------------
* 收集包内所有 ``def`` / ``class`` 的名字；
* 收集全仓（包 + 测试 + 工具）对这些名字的**文本引用**；
* 只被「定义处」自己引用 ⇒ 零引用 ⇒ 判为死代码。

⚠ 边界：只查**模块级**的函数/类（嵌套在函数内的不查）。
⚠ 白名单：``__init__.py`` 的 re-export 门面（有 ``__all__``）不算死代码。
"""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

_PKG = _REPO / "src" / "heluo_engine"
_TESTS = _REPO / "tests"
_TOOLS = _REPO / "tools"

#: ★ 主仓 vendor 镜像目录（本包在主仓里是 ``src/heluo_engine/``）。
#:
#: 为什么必须把它算进引用范围：本包的许多函数是**跨仓公开 API** ——
#: 主仓 ``tongshu`` 会调用它们（如 ``transparent_ten_gods`` 主仓引用 14 次、
#: ``hidden_stems_all`` 1 次）。若只看包内，这些会被误判成死代码。
#: ⚠ 该目录**可能不存在**（独立包单独用时）⇒ 不存在就跳过。
_VENDOR_ROOTS = [
    Path(r"D:\shuntian\.wt-jd\src"),
    Path(r"D:\shuntian\src"),
]


def _vendor_sources():
    """主仓里的**河洛相关**引用（避免全仓扫描导致守卫跑几分钟）。

    ⚠ 只扫主仓的 ``src/tongshu`` 下**引用了河洛包**的文件 —— 因为
      跨仓公开 API 的调用方必然 import 了 heluo_engine，
      先用「文件里是否出现 heluo_engine」粗筛，再做名字匹配。
    """
    for root in _VENDOR_ROOTS:
        if not root.exists():
            continue
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns
                      if d not in ("__pycache__", ".git", "node_modules",
                                  "build", "dist")]
            for fn in sorted(fns):
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    text = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                if "heluo_engine" not in text:
                    continue          # 不碰河洛的文件 ⇒ 不可能有引用
                yield p, text


def _module_level_defs(path: Path):
    """模块级函数/类名 → 行号。"""
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        tree = ast.parse(raw.decode("utf-8", errors="replace"))
    except SyntaxError:
        return []
    out = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append((node.name, node.lineno))
        elif isinstance(node, ast.ClassDef):
            out.append((node.name, node.lineno))
    return out


def _all_sources():
    """包 + 测试 + 工具 + 主仓 vendor 的全部源码文本（用于统计引用）。"""
    for root in (_PKG, _TESTS, _TOOLS):
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns
                      if d not in ("__pycache__", ".git", "build", "dist")]
            for fn in sorted(fns):
                if fn.endswith(".py"):
                    p = os.path.join(dp, fn)
                    try:
                        yield p, open(p, encoding="utf-8", errors="replace").read()
                    except OSError:
                        continue
    # 主仓（跨仓公开 API 的调用方）
    yield from _vendor_sources()


#: 守卫**自身**的文件：它的注释里会提到被检查的函数名
#: （如「本守卫曾发现 `_polarity_of` 是死代码」）⇒ 若把它算进引用统计，
#: 死代码就会被自己的注释「洗白」⇒ 必须排除。
_SELF = Path(__file__).resolve()


import os  # noqa: E402  (放在函数定义之后，避免上方顺序困扰)


class TestNoDeadCode(unittest.TestCase):
    """包内模块级函数/类不得零引用。"""

    @classmethod
    def setUpClass(cls):
        # ⚠ 一次性建索引：每个源文件只扫一次，抽出全部**标识符**集合。
        #   （原先是 O(定义数 × 源文件数) 次正则 ⇒ 守卫要跑几分钟）
        cls._sources = list(_all_sources())
        cls._id_index = {}          # name -> set(source_path)
        for path, text in cls._sources:
            # ⚠ 守卫**自身**的文件：它的注释里会提到被检查的函数名
            #   （如「本守卫曾发现 `_polarity_of` 是死代码」）⇒ 若把它算进引用，
            #   死代码就会被自己的注释「洗白」⇒ 必须排除。
            if Path(path).resolve() == _SELF:
                continue
            names = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
            for n in names:
                cls._id_index.setdefault(n, set()).add(path)

    def test_no_zero_reference_definitions(self):
        dead = []
        for p in sorted(_PKG.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            if p.name == "__init__.py":
                continue          # re-export 门面（有 __all__）不算死代码
            for name, lineno in _module_level_defs(p):
                if name.startswith("__") and name.endswith("__"):
                    continue      # dunder 不算
                refs = self._id_index.get(name, set())
                # 定义处本身算 1 次 ⇒ 去掉后仍 >0 才算被引用
                n = len(refs) - (1 if p in refs else 0)
                if n <= 0:
                    rel = p.relative_to(_REPO).as_posix()
                    dead.append("%s:%d  %s" % (rel, lineno, name))
        self.assertEqual(dead, [],
                         "包内存在**零引用**的死函数/死类（会让变异扫描的盲区清单"
                         "被噪音污染，且误导读者）：\n  " + "\n  ".join(dead))


if __name__ == "__main__":
    unittest.main()
