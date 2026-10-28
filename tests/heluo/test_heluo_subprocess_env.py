# -*- coding: utf-8 -*-
r"""守卫：子进程调用**不得漏传 env**（2026-10-25 新增）。

为什么要有这条
--------------
本项目实测踩过（2026-10-25，全量回归中出现的**假红**）：

    tests/heluo/test_heluo_cli.py :: TestNoStrayOutput::test_import_is_silent
      env = dict(os.environ)
      env["PYTHONPATH"] = str(_REPO / "src")      ← 构造了
      p = subprocess.run([sys.executable, "-c", code], capture_output=True, ...)
                                                  ↑ **没把 env 传进去**

⇒ 子进程走的是**父进程的环境**。后果是**同一份代码在不同环境下结论相反**：

    · 本机（未 pip install）⇒ heluo_engine 不可导入 ⇒ rc=1 ⇒ **假红**；
    · CI（pip install -e .）⇒ 包全局可导入 ⇒ rc=0 ⇒ **假绿**。

而这条测试真正要验的是「**导入引擎本身**不产生 stdout 噪声」，
不是「环境里装没装包」⇒ **env 必须传下去**，否则测的根本不是那件事。

这类缺陷是典型的「恒绿陷阱」：
  · 全量回归在本机是红的（被当成"环境问题"忽略），
  · CI 是绿的（因为 pip install -e . 恰好掩盖了它），
  · 而**被测的断言从未真正生效**。

怎么静态检出
------------
用 **AST**（不能用文本搜索）：
  · 文本搜索会把「env 变量名恰好叫别的」漏掉，也会把
    「函数参数里传了 env 但另有一处没传」混为一谈；
  · AST 能精确定位「subprocess.run / Popen / check_output
    等调用点的**关键字实参**里有没有 env=」。

⚠ 只扫**河洛域**的测试（tests/heluo/）—— 职责边界同
   test_heluo_test_hygiene.py（主仓他域测试不归河洛管）。
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TESTS = _REPO / "tests" / "heluo"

#: 会启动子进程的调用名（``subprocess.run`` / ``Popen`` / …）
_SUBPROCESS_CALLS = {
    "run", "Popen", "check_output", "check_call", "call",
}


def _subprocess_calls(tree: ast.AST):
    """遍历 AST，产出 ``(文件相对路径, 行号, 是否传了 env)``。"""
    out = []
    for path in sorted(_TESTS.rglob("test_*.py")):
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        try:
            tree = ast.parse(raw.decode("utf-8", errors="replace"))
        except SyntaxError:
            continue
        rel = path.relative_to(_REPO).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            # 只认 ``subprocess.<x>`` 与 ``from subprocess import <x>``
            if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                pass
            elif isinstance(func.value, ast.Name) and func.value.id == "sp":
                pass
            else:
                # ``from subprocess import run`` ⇒ func.value 是 Name('run')
                if not (isinstance(func.value, ast.Name)
                        and func.value.id in _SUBPROCESS_CALLS):
                    continue
            if func.attr not in _SUBPROCESS_CALLS:
                continue
            has_env = any(kw.arg == "env" for kw in node.keywords)
            out.append((rel, node.lineno, func.attr, has_env))
    return out


class TestSubprocessEnvNotDropped(unittest.TestCase):
    """子进程调用必须显式传 env。"""

    def test_subprocess_calls_must_pass_env(self):
        missing = [
            "%s:%d  subprocess.%s(...) 未传 env=" % (rel, ln, fn)
            for rel, ln, fn, has_env in _subprocess_calls(None)
            if not has_env
        ]
        self.assertEqual(
            missing, [],
            "子进程调用未传 env=（⇒ 子进程走父进程环境 ⇒ 同一份代码在不同环境"
            "下结论相反：未安装时假红、CI 里 pip install -e . 假绿；"
            "被测断言从未真正生效）：\n  " + "\n  ".join(missing))
