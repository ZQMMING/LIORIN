# -*- coding: utf-8 -*-
r"""守卫：行为快照必须**跨进程确定**（2026-10-26 新增）。

为什么要有这条
--------------
变异扫描的核心判定是「**基线快照 vs 变异快照**」：
  · 相同 ⇒ 等价变异（行为没变）；
  · 不同 ⇒ **真盲区**（行为变了却没人发现）。

⇒ 这个判定成立的前提是「快照是**确定**的」。
若快照非确定，则基线与变异快照**永远不同**
⇒ **所有存活变异都会被误判成真盲区** ⇒ 盲区清单全是噪音。

⚠ 实测踩过（2026-10-26）：
  ``yuan_qi.py`` 的证据文本里插值了一个 Python **set**：
      f"先天/后天卦含元气卦: {has_qi}（{all_trigrams}）"
  而 set 的字符串表示顺序依赖 **PYTHONHASHSEED**（每进程随机）
  ⇒ 同一盘排两次，证据文本的卦名顺序不同
  ⇒ 快照非确定 ⇒ 扫描结论不可信。

  这不只是工具问题 —— 它同时是**生产缺陷**：
  证据文本是**审计留痕**，不可复现的留痕无法用于回归比对。

怎么检
------
**跨进程**跑两次快照并逐字段比对：
  · 必须**跨进程**（不是同进程跑两次）—— 哈希种子按进程分配，
    同进程内两次结果必然相同 ⇒ 检不出来；
  · 逐字段比对（不只比哈希）⇒ 失败时能**指出具体是哪个字段**在飘。

⚠ 边界：只扫河洛域（``src/heluo_engine/``）。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

_SNAPSHOT = _REPO / "tools" / "heluo" / "behaviour_snapshot.py"


def _run_snapshot() -> dict:
    """跑一次快照（**独立子进程**）。

    ⚠ 必须显式传 ``env``（含 ``PYTHONPATH=src``）：
      否则子进程走父进程环境 ⇒ 本机未 pip install 时**导入失败**、
      CI 里 ``pip install -e .`` 时却能跑 ⇒ 同一份代码两种结论
      （这正是 ``test_heluo_subprocess_env.py`` 守卫的那类缺陷）。
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPO / "src")
    env["PYTHONUTF8"] = "1"
    p = subprocess.run(
        [sys.executable, "-X", "utf8", str(_SNAPSHOT)],
        cwd=str(_REPO), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=600)
    if p.returncode != 0:
        raise AssertionError(
            "行为快照运行失败（rc=%d）：%s" % (p.returncode, (p.stderr or "")[-1500:]))
    return json.loads(p.stdout)


def _diff(a, b, path="") -> list:
    """逐字段找差异（不只比哈希 ⇒ 失败时能指出**哪个字段**在飘）。"""
    out = []
    if type(a) is not type(b):
        return ["%s: 类型不同 %s vs %s" % (path, type(a).__name__,
                                          type(b).__name__)]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append("%s.%s: 一边缺失" % (path, k))
            else:
                out += _diff(a[k], b[k], "%s.%s" % (path, k))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append("%s: 长度不同 %d vs %d" % (path, len(a), len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += _diff(x, y, "%s[%d]" % (path, i))
    elif a != b:
        out.append("%s: %r vs %r" % (path, str(a)[:150], str(b)[:150]))
    return out


class TestBehaviourSnapshotDeterministic(unittest.TestCase):
    """行为快照必须跨进程确定。"""

    def test_snapshot_is_stable_across_processes(self):
        a = _run_snapshot()
        b = _run_snapshot()
        diffs = _diff(a, b)
        self.assertEqual(
            diffs, [],
            "行为快照**跨进程不确定** ⇒ 变异扫描的「等价 vs 真盲区」判定"
            "完全失效（基线与变异快照永远不同 ⇒ 全部存活变异被误判成盲区）；"
            "且证据文本不可复现（审计留痕失效）。\n"
            "  常见成因：把 **set / dict / frozenset** 直接插值进字符串"
            "（其表示顺序依赖 PYTHONHASHSEED）⇒ 必须 sorted() 后再拼。\n"
            "  差异处:\n    " + "\n    ".join(diffs[:30]))

    def test_snapshot_covers_main_output_surfaces(self):
        """快照必须覆盖 HeluoResult 的主要输出面。

        ⚠ 覆盖面不足 ⇒ 该模块的变异会让快照输出**不变**
        ⇒ 被误判成「等价变异」⇒ **真盲区被静默掩盖**。
        实测踩过：``frozen_state`` 的产出原先完全没进快照，
        它的 3 条变异全被误判成等价。
        """
        snap = _run_snapshot()
        self.assertTrue(snap, "快照为空")
        first = snap[0]
        required = [
            "prenatal", "postnatal", "yuantang", "hua_gong",
            "numbers", "yuan_qi", "era", "seasonal_hexagram", "structure",
            "timeline", "guajie", "interpretation", "frozen_state",
            "time_layers",
        ]
        missing = [k for k in required if k not in first]
        self.assertEqual(
            missing, [],
            "快照缺少输出面 %s ⇒ 这些模块的变异会让快照不变 ⇒ "
            "真盲区被误判成「等价变异」而静默掩盖" % missing)


if __name__ == "__main__":
    unittest.main()
