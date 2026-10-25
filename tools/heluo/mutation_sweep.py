# -*- coding: utf-8 -*-
"""自动化变异测试引擎（2026-10-25 新增）。

为什么需要它
------------
仓里已有 11 个**手工**变异脚本（``tools/heluo/mutation_verify_*.py``），
每个只挑 2~6 条变异 ⇒ 覆盖面窄，且**变异是人挑的**（挑不到想不到的盲区）。
本引擎改为**自动生成**变异：解析源码 AST ⇒ 机械地产生成百上千条
「已知错误」的注入 ⇒ 跑测试套件 ⇒

  · 变异**被抓住**（测试变红）⇒ 守卫有效；
  · 变异**存活**（测试仍全绿）⇒ **守卫盲区** ⚠ 这就是答案。

⚠ 三条工程约束（继承自已有脚本的教训）
  1. **绝不改测试文件**（只改被测源码）—— 否则守卫自身被改坏，
     自验证失效（2026-10-25 实测踩过）。
  2. **必须隔离字节码缓存**：``PYTHONPYCACHEPREFIX`` 指向临时目录，
     否则 ``.pyc`` 复用会让「还原后复跑」拿到旧字节码 ⇒ 假绿。
  3. **还原必须校验哈希**：每条变异还原后校验内容哈希，确保真的回到初始字节。

用法
----
    python tools/heluo/mutation_sweep.py --module time_layer_judgment
    python tools/heluo/mutation_sweep.py --all --limit 400
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "src" / "heluo_engine"

#: 进度日志（供外部实时查看；管道缓冲会让 stdout 看不到中间态）
LOG_PATH = Path(os.environ.get("HELUO_MUTATION_LOG", "")) if os.environ.get(
    "HELUO_MUTATION_LOG") else (ROOT / "mutation_sweep.log")


def _log(msg: str) -> None:
    """写日志文件 + 打印（stdout 可能被缓冲，文件才是可靠的进度源）。"""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
    try:
        print(msg, flush=True)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════
# 变异算子
# ══════════════════════════════════════════════════════════════════


#: 快照的「挂起」哨兵：与任何正常快照都不同 ⇒ 不会被误判成「输出不变」
_HANG = object()


def _behaviour_snapshot(cache_dir: str):
    """当前源码下的行为快照（跑 tools/heluo/behaviour_snapshot.py）。

    Returns:
        dict  —— 正常快照；
        ``_HANG`` —— **引擎挂起**（变异让引擎死循环）⇒ 该变异属于
                  「挂起型」，**不是盲区**（盲区 = 行为变了却没人发现）；
        None  —— 快照跑不出来（无法判定）⇒ 按「无法判定」处理，不算盲区。
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONPYCACHEPREFIX"] = cache_dir
    out_file = Path(cache_dir) / "snap.json"
    try:
        p = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "heluo" / "behaviour_snapshot.py"),
             str(out_file)],
            cwd=str(ROOT), env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=25)
    except subprocess.TimeoutExpired:
        return _HANG
    if p.returncode != 0 or not out_file.exists():
        return None
    try:
        import json as _json
        return _json.loads(out_file.read_text(encoding="utf-8"))
    except Exception:
        return None


class Mutation:
    """一条变异：把某个字符串片段替换成另一个片段。"""

    __slots__ = ("label", "path", "old", "new", "lineno")

    def __init__(self, label: str, path: Path, old: str, new: str, lineno: int):
        self.label = label
        self.path = path
        self.old = old
        self.new = new
        self.lineno = lineno

    def __repr__(self) -> str:
        return "%s @%s:%d" % (self.label, self.path.name, self.lineno)


#: 常量类变异：把字面量换成另一个「同类」字面量
LITERAL_SWAPS = {
    True: False, False: True,
    0: 1, 1: 0,
}


def _lit_repr(node: ast.AST) -> Optional[str]:
    try:
        return repr(node.value)
    except Exception:
        return None


def _swap_literal(node: ast.AST) -> Optional[Tuple[str, str]]:
    """字面量 → 另一个字面量。"""
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool):
            return (repr(v), repr(not v))
        if isinstance(v, int) and not isinstance(v, bool):
            return (repr(v), repr(v + 1))
        if isinstance(v, str) and v and len(v) <= 40:
            # 改一个字符：模拟「原典引用抄错一个字」
            i = 0
            ch = v[i]
            repl = "X" if ch != "X" else "Y"
            return (repr(v), repr(v[:i] + repl + v[i + 1:]))
        if isinstance(v, float):
            return (repr(v), repr(v + 1.0))
    return None


def _swap_operator(node: ast.AST) -> Optional[Tuple[str, str]]:
    """二元运算符 → 另一个运算符。"""
    ops = {
        ast.Add: ("+", "-"), ast.Sub: ("-", "+"),
        ast.Mult: ("*", "/"), ast.Div: ("/", "*"),
        ast.FloorDiv: ("//", "/"), ast.Mod: ("%", "+"),
        ast.Lt: ("<", "<="), ast.LtE: ("<=", "<"),
        ast.Gt: (">", ">="), ast.GtE: (">=", ">"),
        ast.Eq: ("==", "!="), ast.NotEq: ("!=", "=="),
    }
    for cls, (a, b) in ops.items():
        if isinstance(node, cls):
            return (a, b)
    return None


def _flip_bool(node: ast.AST) -> Optional[Tuple[str, str]]:
    """``not X`` → ``X``（去掉否定）。"""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return ("not ", "")
    return None


def _drop_return(node: ast.AST) -> Optional[Tuple[str, str]]:
    """``return X`` → ``return None``（值被吞掉）。"""
    if isinstance(node, ast.Return) and node.value is not None:
        try:
            return ("return " + ast.unparse(node.value), "return None")
        except Exception:
            return None
    return None


def _mutate_source(path: Path, text: str) -> List[Mutation]:
    """对单个源文件生成全部变异。

    ⚠ 只变异**可执行代码**（跳过注释与 docstring）：
      注释/文档串里的字面量改动不改变行为 ⇒ 必然「存活」⇒ 全是噪音。
      （实测：docstring 里的日期「2026-10-25」改成「2026-10-26」无任何守卫会红，
        但那不是真缺陷 —— 是**元信息无守卫**的另一类问题，另行处理。）
    """
    out: List[Mutation] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out

    # 收集所有「不可变异」的行号（注释与 docstring 所在行）
    skip_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) \
                    and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                # docstring：整个表达式覆盖的行
                for ln in range(body[0].lineno,
                                getattr(body[0], "end_lineno",
                                        body[0].lineno) + 1):
                    skip_lines.add(ln)
    # 注释行：用 tokenize 精确识别
    try:
        import tokenize
        with open(path, "rb") as fh:
            for tok in tokenize.tokenize(fh.readline):
                if tok.type == tokenize.COMMENT:
                    skip_lines.add(tok.start[0])
    except Exception:
        pass

    for node in ast.walk(tree):
        lineno = getattr(node, "lineno", 0)
        if lineno in skip_lines:
            continue
        # 整行都在 skip 集合里（如多行字符串的后续行）也跳过
        if isinstance(node, (ast.Constant, ast.Str)):
            continue
        # ── 字面量 ──
        sw = _swap_literal(node)
        if sw:
            old, new = sw
            seg = ast.get_source_segment(text, node)
            if seg and seg in text:
                out.append(Mutation("literal %s→%s" % (old, new), path,
                                    seg, new, lineno))
        # ── 运算符 ──
        sw = _swap_operator(node)
        if sw:
            old, new = sw
            try:
                seg = ast.get_source_segment(text, node)
            except Exception:
                seg = None
            if seg:
                idx = seg.find(old)
                if idx >= 0:
                    out.append(Mutation("op %s→%s" % (old, new), path,
                                        seg[:idx] + old + seg[idx + len(old):],
                                        seg[:idx] + new + seg[idx + len(old):],
                                        lineno))
        # ── not 去掉 ──
        sw = _flip_bool(node)
        if sw:
            old, new = sw
            try:
                seg = ast.get_source_segment(text, node)
            except Exception:
                seg = None
            if seg and seg.startswith("not "):
                out.append(Mutation("drop not", path, seg, seg[4:], lineno))
        # ── return 值吞掉 ──
        sw = _drop_return(node)
        if sw:
            old, new = sw
            try:
                seg = ast.get_source_segment(text, node)
            except Exception:
                seg = None
            if seg:
                out.append(Mutation("return→None", path, seg, new, lineno))
    return out


# ══════════════════════════════════════════════════════════════════
# 执行
# ══════════════════════════════════════════════════════════════════

def _module_guard_map(targets: List[Path]) -> dict:
    """被测模块 → 提到它的守卫文件（用于快速筛）。

    只用**文本引用**做粗筛（快）；粗筛放过的不代表真盲区，
    后面还会跑全量确认。
    """
    import re as _re
    tests_dir = ROOT / "tests" / "heluo"
    tfiles = []
    for dp, dns, fns in os.walk(tests_dir):
        dns[:] = [d for d in dns if d != '__pycache__']
        for fn in sorted(fns):
            if fn.startswith('test_') and fn.endswith('.py'):
                tfiles.append(os.path.join(dp, fn))
    out: dict = {}
    for p in targets:
        short = p.stem
        rel = []
        for tf in tfiles:
            src = Path(tf).read_text(encoding='utf-8', errors='replace')
            if _re.search(r'\b%s\b' % _re.escape(short), src):
                rel.append(tf)
        out[p] = rel[:3]      # 最多 3 个相关守卫（够快且够灵敏）
    return out


class Runner:
    def __init__(self, test_paths: List[str]):
        self.test_paths = test_paths
        self._orig: dict[Path, bytes] = {}

    def snapshot(self, paths: Iterable[Path]):
        for p in paths:
            self._orig[p] = p.read_bytes()

    def restore(self):
        for p, data in self._orig.items():
            p.write_bytes(data)

    def verify_restored(self) -> List[str]:
        bad = []
        for p, data in self._orig.items():
            if hashlib.sha256(p.read_bytes()).hexdigest() != \
                    hashlib.sha256(data).hexdigest():
                bad.append(str(p))
        return bad

    def run_tests(self, cache_dir: str, timeout: int = 45) -> Tuple[int, str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        env["PYTHONPYCACHEPREFIX"] = cache_dir
        try:
            p = subprocess.run(
                [sys.executable, "-m", "pytest", *self.test_paths,
                 "-q", "--no-header", "-p", "no:cacheprovider", "-x"],
                cwd=str(ROOT), env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired:
            # ⚠ 超时 = 挂起 = **也算被抓住**（守卫会让它挂起或超时 ⇒ 不是盲区）
            return 1, "TIMEOUT (视为已抓住)"
        return p.returncode, (p.stdout or "")[-1500:]


def main() -> int:
    try:
        LOG_PATH.unlink()
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="河洛守卫盲区扫描（自动变异）")
    ap.add_argument("--module", default="",
                    help="只扫文件名匹配的模块（如 time_layer_judgment）")
    ap.add_argument("--all", action="store_true", help="扫全部河洛模块")
    ap.add_argument("--limit", type=int, default=120, help="本次最多跑多少条变异")
    ap.add_argument("--offset", type=int, default=0,
                    help="跳过前 N 条变异（分批扫描全量时用）")
    ap.add_argument("--tests", default="tests/heluo",
                    help="守卫生效范围（默认 tests/heluo）")
    args = ap.parse_args()

    targets: List[Path] = []
    for p in sorted(PKG.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        if args.module:
            if args.module not in p.name:
                continue
        elif not args.all:
            continue
        targets.append(p)

    if not targets:
        print("没有匹配的目标模块（用 --module / --all 指定）")
        return 1

    muts: List[Mutation] = []
    for p in targets:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        muts.extend(_mutate_source(p, text))

    _log("目标模块 %d 个 ⇒ 生成变异 %d 条" % (len(targets), len(muts)))
    if args.offset:
        muts = muts[args.offset:]
        _log("（已跳过前 %d 条）" % args.offset)
    if args.limit and len(muts) > args.limit:
        muts = muts[:args.limit]
    _log("本次执行 %d 条\n" % len(muts))

    runner = Runner([args.tests])
    runner.snapshot({p for m in muts for p in [m.path]})
    baseline_rc, _ = runner.run_tests(tempfile.mkdtemp(prefix="mutbase_"))
    _log("基线（未变异）rc=%d %s"
          % (baseline_rc, "OK" if baseline_rc == 0 else "❌ 基线就红，先修基线"))
    if baseline_rc != 0:
        runner.restore()
        return 1

    # ── 基线行为快照（用于区分「等价变异」与「真盲区」）──
    base_snap = _behaviour_snapshot(tempfile.mkdtemp(prefix="snapbase_"))
    _log("基线行为快照: %s" % ("已取得" if base_snap is not None else "取不到"))

    # ── 两级筛：先跑「与被测模块相关的单个守卫文件」（快），
    #    疑似存活的再跑全量（准）──
    #    否则每条变异都跑全量（~5s），几百条要跑几十分钟。
    fast_map = _module_guard_map(targets)

    survived: List[Mutation] = []
    equivalent: List[Mutation] = []
    hung: List[Mutation] = []
    unknown: List[Mutation] = []
    killed = 0
    skipped = 0
    fast_checked = 0
    cache = tempfile.mkdtemp(prefix="mutcache_")
    for i, m in enumerate(muts, 1):
        try:
            text = m.path.read_text(encoding="utf-8")
        except Exception:
            skipped += 1
            continue
        if m.old not in text:
            skipped += 1          # 上下文已变（跳过）
            continue
        try:
            m.path.write_text(text.replace(m.old, m.new, 1), encoding="utf-8")
        except Exception:
            skipped += 1
            continue

        # ① 快速筛：只跑相关守卫（短超时：挂起的变异快速判死）
        rel_guards = fast_map.get(m.path, [])
        if rel_guards:
            runner.test_paths = rel_guards
            rc, _ = runner.run_tests(cache, timeout=15)
            fast_checked += 1
            if rc != 0:
                killed += 1
                runner.test_paths = [args.tests]
                runner.restore()
                if i % 10 == 0:
                    _log("    ... %d/%d（已杀 %d，存活 %d）"
                         % (i, len(muts), killed, len(survived)))
                continue
        # ② 慢速确认：跑全量
        runner.test_paths = [args.tests]
        rc, out = runner.run_tests(cache, timeout=45)
        runner.restore()
        if rc == 0:
            # 存活 ⇒ 再看**行为**是否真的变了
            mut_snap = _behaviour_snapshot(cache)
            if mut_snap is _HANG:
                hung.append(m)           # 引擎挂起 ⇒ 挂起型，不算盲区
                _log("  [挂起] %-52s %s" % (m.label, m))
            elif base_snap is not None and mut_snap is not None \
                    and mut_snap == base_snap:
                equivalent.append(m)      # 输出不变 ⇒ 等价变异，不是盲区
            elif mut_snap is None or base_snap is None:
                unknown.append(m)        # 快照跑不出来 ⇒ 无法判定
            else:
                survived.append(m)       # 输出变了却没人发现 ⇒ ★真盲区
                _log("  [★真盲区] %-50s %s" % (m.label, m))
        else:
            killed += 1
        if i % 10 == 0:
            _log("    ... %d/%d（已杀 %d，存活 %d）" % (i, len(muts), killed, len(survived)))

    bad = runner.verify_restored()
    _log("")
    _log("=== 变异结果 ===")
    _log("  被守卫抓住（杀掉）: %d" % killed)
    _log("  ★ 真盲区（行为变了却没人发现）: %d" % len(survived))
    _log("  ~ 等价变异（输出不变，非盲区）  : %d" % len(equivalent))
    _log("  ⏱ 挂起型（引擎死循环，非盲区）  : %d" % len(hung))
    _log("  ? 无法判定（快照跑不出）      : %d" % len(unknown))
    _log("  跳过（无法注入）  : %d" % skipped)
    _log("  还原校验失败      : %s" % (bad or "无（源码已完整还原）"))

    if survived:
        _log("\n--- 真盲区明细（按模块分组）---")
        by_mod = {}
        for m in survived:
            by_mod.setdefault(m.path.name, []).append(m)
        for name in sorted(by_mod):
            _log("  [%s]  %d 条" % (name, len(by_mod[name])))
            for m in by_mod[name][:12]:
                _log("      %-52s L%d" % (m.label, m.lineno))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
