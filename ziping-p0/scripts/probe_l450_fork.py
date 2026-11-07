# -*- coding: utf-8 -*-
"""探针脚本（只跑探针, 不出业务结论）—— 报告用

探针目标:
  P1/P2  facts 内部键名 vs paipan 顶层投影键名是否同名
        —— 决定「同构重算」能否用顶层投影替代内部 facts
  P3     judgment_status 的 AST 读取点数（应为 12）
  P4     已知锚点: facts['special'] 读 2 处 / facts['ge_cheng'] 读 31 处
  P5     bazi_gate L166 的实参 p 是什么形态（能否从顶层重建）
"""
import ast
import io
import os
import sys

ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
SKIP = {"__pycache__", ".git", "node_modules"}


def load(rel):
    p = os.path.join(ROOT, rel)
    return io.open(p, encoding="utf-8-sig", errors="ignore").read() if os.path.exists(p) else None


def main():
    print("=" * 96)
    print("探针（只验证工具本身, 不出业务结论）")
    print("=" * 96)

    from p0_v2.bazi_gate import paipan
    r = paipan("癸酉丁巳己卯甲戌")

    # ── P1/P2: 键名对照 ──
    top = set(r.keys())
    print("\nP1/P2  顶层投影键名")
    for k in ("hidden", "hidden_stems", "pillars", "day_stem", "special",
              "combination_facts", "tian_he", "wuxing_power"):
        print("   %-20s in 顶层 = %s" % (k, k in top))
    print("   → 顶层有 'hidden' 但【无】'hidden_stems': %s"
          % ("hidden" in top and "hidden_stems" not in top))

    # 内部 facts 到底有哪些键 —— 探 bazi_gate 里 f 的构造
    g = load("p0_v2/bazi_gate.py")
    L = g.split("\n")
    print("\nP5  bazi_gate 里 f[...] 赋值点（内部 facts 的键全集来源）")
    keys = []
    for i, l in enumerate(L, 1):
        if "hidden_stems" in l or 'f["hidden"]' in l or "f['hidden']" in l:
            print("   L%-5d %s" % (i, l.strip()[:92]))
    # paipan 顶层 hidden 是怎么来的
    for i, l in enumerate(L, 1):
        if '"hidden"' in l and ":" in l:
            print("   L%-5d %s" % (i, l.strip()[:92]))

    # ── P3: judgment_status AST 读取数（不加任何字符串窄过滤）──
    print("\nP3  judgment_status 的 AST 读取点（无过滤）")
    TARGET = "judgment_status"
    n_all = 0
    n_out = 0
    detail = []
    for base in ["engines", "p0_v2", "spec", "scripts", "tests"]:
        bp = os.path.join(ROOT, base)
        for dp, dn, fn in os.walk(bp):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if not f.endswith(".py"):
                    continue
                rel = os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/")
                if rel.endswith("probe_l450_fork.py"):
                    continue
                s = load(rel)
                if not s:
                    continue
                try:
                    t = ast.parse(s)
                except SyntaxError:
                    continue
                lines = s.split("\n")
                for node in ast.walk(t):
                    hit = None
                    if isinstance(node, ast.Subscript) and \
                            isinstance(node.slice, ast.Constant) and \
                            node.slice.value == TARGET:
                        hit = "Subscript"
                    if isinstance(node, ast.Call):
                        fn2 = node.func
                        nm = fn2.attr if isinstance(fn2, ast.Attribute) \
                            else getattr(fn2, "id", "")
                        if nm == "get" and node.args and \
                                isinstance(node.args[0], ast.Constant) and \
                                node.args[0].value == TARGET:
                            hit = ".get"
                    if hit:
                        n_all += 1
                        if rel != "engines/common/special_pattern.py":
                            n_out += 1
                            detail.append((rel, node.lineno, hit,
                                           lines[node.lineno - 1].strip()[:74]))
    print("   总 AST 读取 = %d  (生产端 special_pattern.py 之外 = %d)"
          % (n_all, n_out))
    for d in detail:
        print("      %-38s L%-5d %-9s %s" % (d[0][:36], d[1], d[2], d[3]))

    # ── P4: 已知锚点 ──
    print("\nP4  已知锚点")
    for key, exp in (("special", 2), ("ge_cheng", 31)):
        n = 0
        s = load("engines/common/ge_jie_layer.py")
        for m in __import__("re").finditer(
                r"facts\[[\"']%s[\"']\]|facts\.get\([\"']%s[\"']" % (key, key), s):
            n += 1
        print("   facts['%s']  预期 %d  实测 %d  %s"
              % (key, exp, n, "PASS" if n == exp else "★FAIL"))
    return r


if __name__ == "__main__":
    main()