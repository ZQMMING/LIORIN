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
import time
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
    # ⚠ 声明「本次运行处在**扫描**中」⇒ 工具自检守卫会**跳过**
    #   （否则：扫描 → 慢速确认跑全量 tests/heluo → 自检守卫 →
    #     又一个扫描 ⇒ 无限套娃 + 并发改同一份 src/ ⇒ 结果全错）。
    #   实测踩过：自检守卫没跳 ⇒ 基线从 26 秒涨到 150 秒，
    #   且扫描期间真实 src/ 被污染（残留 frozen_state / hua_gong 变异）。
    env["HELUO_SWEEP_SELFTEST"] = "1"
    # ⚠⚠ **必须固定 PYTHONHASHSEED**（2026-10-26 加固）。
    #   原因：set / dict 的字符串表示顺序依赖 PYTHONHASHSEED（默认**每进程随机**）
    #   ⇒ 若基线快照与变异快照拿到**不同 seed**，两者在**任何** set/dict 插值处
    #   都必然不同 ⇒ **所有存活变异都会被误判成「真盲区」** ⇒ 盲区清单全是噪音。
    #   ⇒ 固定同一个 seed ⇒ 顺序稳定 ⇒ 只有**真正的行为差异**才会被看到。
    #   （配套守卫：tests/heluo/test_heluo_snapshot_determinism.py
    #     用**两个不同 seed** 验证快照本身确实确定。）
    env["PYTHONHASHSEED"] = "0"
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
#:
#: ⚠ 2026-10-25 删除：原 ``LITERAL_SWAPS`` 表**从未被使用**（死代码），
#:   且表本身是错的 —— Python 里 ``True == 1``、``False == 0``，
#:   所以 ``{True: False, False: True, 0: 1, 1: 0}`` 的键**塌成两个**
#:   （``0`` 覆盖 ``False``、``1`` 覆盖 ``True``）⇒ ruff F601 报重复键。
#:   实际字面量替换逻辑在 ``_swap_literal`` 里（按类型分别处理），
#:   不需要这张表。保留它只会让后来者以为「表驱动」是实际机制。


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
        if isinstance(node, ast.Constant):
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

def _module_guard_map(targets: List[Path], tests_dir: str) -> dict:
    """被测模块 → 提到它的守卫文件（用于快速筛）。

    只用**文本引用**做粗筛（快）；粗筛放过的不代表真盲区，
    后面还会跑全量确认。

    ⚠ 2026-10-25 修正：**必须跟随 ``--tests`` 指定的范围**。
      原实现硬编码 ``tests/heluo`` ⇒ 当 ``--tests`` 指向别处时，
      快筛仍会跑**范围外**的守卫 ⇒ 那些守卫把变异杀掉 ⇒
      「这个范围内有没有守卫」的问题被**范围外的守卫**回答了
      ⇒ 结论与「守卫生效范围」这个前提**不一致**。
      ⇒ 现在快筛与慢筛用**同一个** tests_dir。
    """
    import re as _re
    root = Path(tests_dir)
    if not root.exists():
        return {p: [] for p in targets}
    if root.is_file():
        tfiles = [str(root)]
    else:
        tfiles = []
        for dp, dns, fns in os.walk(root):
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

    def run_tests(self, cache_dir: str, timeout: int = 45):
        """跑守卫。

        Returns:
            (rc, 输出尾部, 是否**子进程**超时, 耗时秒)
            ⚠ **超时必须单独返回**：把超时当成「失败」会把
              「守卫自身太慢 / 挂起」误判成「变异被抓住」⇒ **掩盖真盲区**。
              故超时一律由调用方单独处理。
        """
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        env["PYTHONPYCACHEPREFIX"] = cache_dir
        # ⚠ 声明「本次 pytest 处在**扫描**中」⇒ 工具自检守卫会跳过。
        #   （自检守卫在 tests/heluo/ 里 ⇒ 扫描的「慢速确认」跑全量时
        #     会把它也跑起来 ⇒ 它又启动一个扫描 ⇒ 无限套娃 + 并发污染。
        #     实测踩过：基线从 26 秒涨到 150 秒，且真实 src/ 被污染。）
        env["HELUO_SWEEP_SELFTEST"] = "1"
        t0 = time.time()
        try:
            p = subprocess.run(
                [sys.executable, "-m", "pytest", *self.test_paths,
                 "-q", "--no-header", "-p", "no:cacheprovider", "-x"],
                cwd=str(ROOT), env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired:
            # ⚠ 超时 = 挂起（**不是**普通失败）⇒ 交由调用方区分
            return 1, "TIMEOUT", True, time.time() - t0
        return p.returncode, (p.stdout or "")[-1500:], False, time.time() - t0


#: pytest-timeout 失败在输出里的痕迹（用于区分「真的断言失败」
#: 与「用例被 pytest-timeout 判超时」——后者不能直接当「变异被抓住」，
#: 因为守卫文件**本身**慢也会这样 ⇒ 须升级到慢筛复核）。
_TIMEOUT_MARKERS = ("Timeout", "timeout >", "Timeout >", "timed out")


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
    ap.add_argument("--json-out", default="",
                    help="把结果写成**机器可读 JSON**（CI 用）")
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

    # ⚠⚠ **中断必还原**（2026-10-25 加）：扫描是**原地改 src/** 的。
    #   一旦进程被 Ctrl-C / 被杀 / 抛异常 ⇒ 源码会**残留变异**，
    #   而残留的变异可能恰好让测试绿 ⇒ **下一个使用者拿到的是被污染的源码**。
    #   实测踩过：手动取消扫描后 ``time_layer_judgment._yao_ci_from_guajie``
    #   残留了 ``return None``（原为 ``return ("", "")``）⇒ 靠 ``git diff``
    #   才抓到。⇒ 必须注册 finally + 信号处理器，无条件还原。
    _restored = {"done": False}

    def _force_restore(interrupted: bool = False):
        """还原源码。

        ⚠ ``interrupted=True`` 才打「扫描被中断」——
          正常跑完时也会走 finally ⇒ 若无条件打这句，
          **每次正常扫描的日志末尾都会出现「中断」字样** ⇒
          看日志的人会以为扫描是被打断的（假警报），
          而且真出事时反而被淹没。
        """
        if _restored["done"]:
            return
        _restored["done"] = True
        try:
            runner.restore()
            bad = runner.verify_restored()
            if bad:
                _log("⚠⚠ 强制还原后哈希仍不符：%s" % bad)
            elif interrupted:
                _log("⚠ 已强制还原源码（扫描被中断）")
        except Exception as exc:
            _log("⚠⚠ 强制还原失败：%s" % exc)

    def _sig_handler(signum, frame):
        _force_restore(interrupted=True)
        raise KeyboardInterrupt("扫描被信号 %d 中断" % signum)

    import signal
    for _sig in (getattr(signal, "SIGINT", None),
                 getattr(signal, "SIGTERM", None),
                 getattr(signal, "SIGBREAK", None)):
        if _sig is None:
            continue
        try:
            signal.signal(_sig, _sig_handler)
        except (ValueError, OSError, RuntimeError):
            pass          # 非主线程 / 平台不支持 ⇒ 忽略

    _interrupted = {"flag": False}
    try:
        return _run_sweep(args, targets, muts, runner, base_snap=None)
    except KeyboardInterrupt:
        _interrupted["flag"] = True
        _log("⚠ 扫描被中断")
        return 130
    except BaseException:
        # ⚠ 任何异常都必须还原源码（否则留下污染的 src/）
        _interrupted["flag"] = True
        raise
    finally:
        _force_restore(interrupted=_interrupted["flag"])
        for _sig in (getattr(signal, "SIGINT", None),
                     getattr(signal, "SIGTERM", None),
                     getattr(signal, "SIGBREAK", None)):
            if _sig is None:
                continue
            try:
                signal.signal(_sig, signal.SIG_DFL)
            except (ValueError, OSError, RuntimeError):
                pass


def _run_sweep(args, targets, muts, runner, base_snap=None) -> int:
    """真正的扫描流程。**中断还原由调用方 main() 的 finally 负责**。"""
    baseline_rc, _, _base_to, baseline_to = runner.run_tests(
        tempfile.mkdtemp(prefix="mutbase_"), timeout=180)
    _log("基线（未变异）rc=%d %s"
          % (baseline_rc, "OK" if baseline_rc == 0 else "❌ 基线就红，先修基线"))
    if baseline_rc != 0:
        return 1

    # ⚠ 超时预算必须**按基线实际耗时**定，不能拍脑袋。
    #   拍脑袋 ⇒ 两种错法：
    #     · 预算过小 ⇒ 基线自己就超时 ⇒ 全部变异被误判成「挂起」；
    #     · 预算过大 ⇒ 真挂起的变异要等很久才判死，扫描慢到跑不完。
    #   ⇒ 慢筛预算 = max(120, 基线耗时 × 4)。
    #
    # ⚠ 为何要 **120s** 下限（本仓 pytest addopts 里有 ``--timeout=60``）：
    #   真挂起的变异 ⇒ pytest-timeout 会在 **60s** 处把该用例判失败 ⇒
    #   pytest 返回 rc≠0（**不是** subprocess 超时）⇒ 我们能干净地
    #   把它归为「被抓住（挂起）」。
    #   若 subprocess 预算比 60s 还小 ⇒ subprocess 先超时 ⇒ 拿不到
    #   pytest 的失败结论 ⇒ 只能笼统说「挂起」，反而丢失了
    #   「pytest-timeout 确实抓得住」这个**有价值**的信息。
    slow_timeout = max(120, int(baseline_to * 4))
    # 快筛也要够大：快筛超时**不代表**变异被抓住（可能是守卫文件本身慢）
    # ⇒ 快筛超时的变异一律**升级到慢筛**重新判，不在快筛阶段下结论。
    fast_timeout = max(60, int(baseline_to * 3))
    _log("快筛超时预算: %ds ／ 慢筛超时预算: %ds（基线耗时 %.1fs）"
         % (fast_timeout, slow_timeout, baseline_to))

    # ── 基线行为快照（用于区分「等价变异」与「真盲区」）──
    base_snap = _behaviour_snapshot(tempfile.mkdtemp(prefix="snapbase_"))
    _log("基线行为快照: %s" % ("已取得" if base_snap is not None else "取不到"))

    # ── 两级筛：先跑「与被测模块相关的单个守卫文件」（快），
    #    疑似存活的再跑全量（准）──
    #    否则每条变异都跑全量（~5s），几百条要跑几十分钟。
    fast_map = _module_guard_map(targets, args.tests)

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
            rc, out, timed_out, _ = runner.run_tests(cache, timeout=fast_timeout)
            fast_checked += 1
            if rc != 0 and not timed_out:
                # ⚠ 只有「**确实失败**」才能在快筛阶段定罪。
                #   快筛超时 ⇒ 可能是守卫文件本身慢 ⇒ 升级到慢筛复核。
                #   快筛失败但输出带 pytest-timeout 痕迹 ⇒ 同理，升级复核。
                if not any(mk in out for mk in _TIMEOUT_MARKERS):
                    killed += 1
                    runner.test_paths = [args.tests]
                    runner.restore()
                    if i % 10 == 0:
                        _log("    ... %d/%d（已杀 %d，存活 %d）"
                             % (i, len(muts), killed, len(survived)))
                    continue
        # ② 慢速确认：跑全量
        runner.test_paths = [args.tests]
        rc, out, timed_out, _ = runner.run_tests(cache, timeout=slow_timeout)
        # ⚠⚠⚠ **必须先取快照，再还原源码**（2026-10-26 修正，**致命顺序错误**）。
        #   原顺序是「先 restore() 再取快照」⇒ 快照子进程读到的是**已还原**的源码
        #   ⇒ 快照**必然**等于基线 ⇒ **每一个存活变异都被判成「等价变异」**
        #   ⇒ **真盲区被系统性掩盖**（扫描报告「盲区 0」但其实根本没测）。
        #   ⇒ 正确顺序：先在**变异态**下取快照，再还原。
        mut_snap = None
        if not timed_out and rc == 0:
            # 存活 ⇒ 再看**行为**是否真的变了
            mut_snap = _behaviour_snapshot(cache)
        runner.restore()
        if timed_out:
            # ⚠ 子进程层面的超时（连 pytest-timeout 都没能收住）⇒
            #   归为「挂起型」：引擎被变异逼进死循环 ⇒ 不是盲区。
            hung.append(m)
            _log("  [挂起] %-52s %s" % (m.label, m))
        elif rc == 0:
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

    # ── 机器可读结果（CI 用）──
    # ⚠ 为什么要有它：CI 判定「有没有真盲区」不能靠 grep 日志文本
    #   （文案一改 grep 就失效 ⇒ 又变成恒绿陷阱）。
    #   ⇒ 输出**稳定的字段名 + 稳定的结构**，CI 只认这些字段。
    if args.json_out:
        import json as _json
        payload = {
            "schema": 1,
            "targets": [p.name for p in targets],
            "mutations_total": len(muts),
            "killed": killed,
            "blind_spots": [
                {
                    "module": m.path.name,
                    "label": m.label,
                    "line": m.lineno,
                    "old": m.old[:200],
                    "new": m.new[:200],
                }
                for m in survived
            ],
            "equivalent": len(equivalent),
            "hung": len(hung),
            "unknown": len(unknown),
            "skipped": skipped,
            "restore_ok": not bad,
            "restore_failures": list(bad),
            "baseline_ok": baseline_rc == 0,
        }
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            _json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        _log("机器可读结果已写入: %s" % out_path)

        # ⚠ **有真盲区 ⇒ 退出码非 0** ⇒ CI 直接红。
        #   不靠 CI 再去解析文本（避免"解析失败=通过"的静默通过）。
        if survived or bad or baseline_rc != 0:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
