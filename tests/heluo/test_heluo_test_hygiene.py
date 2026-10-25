# -*- coding: utf-8 -*-
r"""守卫：测试函数**不得重名**（2026-10-25 新增）。

为什么要有这条
--------------
**同名测试方法会互相覆盖** —— Python 里后定义的 `def test_x` 会把先前的
**整个替换掉**，pytest 按名字收集 ⇒ **先前的守卫从未被执行**，却**看不出任何异常**
（测试数少一个、其余全绿）。

本项目实测踩过（2026-10-25，Ruff F811 抓到）：
    tests/heluo/test_no_fabricated_verdict.py
      L85  def test_shu_xiong_cites_real_original_lines(self)   ← 被覆盖，从未跑
      L111 def test_shu_xiong_cites_real_original_lines(self)   ← 实际执行的那个
    两条断言几乎相同 ⇒ 表面看不出差别，但**L85 那条从此是死代码**。

这类缺陷是典型的「恒绿陷阱」：测试全绿、CI 全绿、覆盖率不降，
但**一条守卫已经死了**。故必须**静态**钉住。

⚠ 静态检查必须用 **AST**（不能用文本搜索）：
    文本搜索会把「类内同名」与「不同类里的同名」混为一谈。
"""
from __future__ import annotations

import ast
import sys
import unittest
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

#: ⚠ 只扫**河洛域**的测试（``tests/heluo/``），不扫全仓 ``tests/``。
#:
#: 理由（职责边界）：本包在主仓里是 **vendor 副本**，主仓 ``tests/`` 下还有
#: ziwei / bazi / blind / platform 等**他域**的测试文件。实测主仓有 21 个
#: 带 BOM（U+FEFF）的测试文件 —— 那是**主仓的既有问题**，属他域责任。
#: 本守卫若扫全仓，就会把**他域**的问题拉进河洛的 CI ⇒ 越界且不可修
#: （改了也超出河洛域）。
#: ⇒ 河洛域只守自己的测试；主仓侧由主仓自己的治理负责。
_TESTS = _REPO / "tests" / "heluo"


def _collect_duplicates():
    """返回 [(文件相对路径, 类名, 函数名, 行号列表)] —— 同类内重名的测试。"""
    dups = []
    for path in sorted(_TESTS.rglob("test_*.py")):
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        try:
            tree = ast.parse(raw.decode("utf-8", errors="replace"))
        except SyntaxError as e:
            raise AssertionError(
                "%s 语法错误：%s" % (path.name, e)) from e
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            seen = defaultdict(list)
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and item.name.startswith("test"):
                    seen[item.name].append(item.lineno)
            for name, lines in seen.items():
                if len(lines) > 1:
                    rel = path.relative_to(_REPO).as_posix()
                    dups.append((rel, node.name, name, lines))
    return dups


class TestNoDuplicateTestNames(unittest.TestCase):
    """同类内不得有同名测试方法。"""

    def test_no_duplicate_test_methods(self):
        dups = _collect_duplicates()
        detail = "\n".join(
            "  %s :: %s :: %s  (行 %s)"
            % (rel, cls, name, lines)
            for rel, cls, name, lines in dups)
        self.assertEqual(dups, [],
                         "同类内存在**同名**测试方法（后者会覆盖前者 ⇒ "
                         "先前的守卫从未执行）：\n%s" % detail)

    def test_no_duplicate_module_level_test_functions(self):
        """模块级测试函数也不得重名（同名会互相覆盖）。"""
        dups = []
        for path in sorted(_TESTS.rglob("test_*.py")):
            raw = path.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            try:
                tree = ast.parse(raw.decode("utf-8", errors="replace"))
            except SyntaxError:
                continue
            seen = defaultdict(list)
            for item in tree.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and item.name.startswith("test"):
                    seen[item.name].append(item.lineno)
            for name, lines in seen.items():
                if len(lines) > 1:
                    rel = path.relative_to(_REPO).as_posix()
                    dups.append((rel, name, lines))
        detail = "\n".join("  %s :: %s  (行 %s)" % (r, n, l) for r, n, l in dups)
        self.assertEqual(dups, [],
                         "模块级存在同名测试函数：\n%s" % detail)

    def test_all_test_files_parse(self):
        """所有测试文件必须能被 AST 解析（BOM 已剥离）。"""
        broken = []
        for path in sorted(_TESTS.rglob("test_*.py")):
            raw = path.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            try:
                ast.parse(raw.decode("utf-8", errors="replace"))
            except SyntaxError as e:
                broken.append("%s: %s" % (path.name, e))
        self.assertEqual(broken, [], "测试文件无法解析：%s" % broken)


if __name__ == "__main__":
    unittest.main()
