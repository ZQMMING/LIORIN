# -*- coding: utf-8 -*-
"""裁「落前核」: L3 strength_verdict 与 strength_producer.strength_state 的管线关系

★ 核三件（不预判, 按数据流走, 不按字符串出现）:
  核A strength_producer.produce_strength() 的入参从哪来? 有没有读 L3?
  核B 20+ 读 strength_state 的文件, 读的是 produce_strength 的返回值,
      还是别处独立的同名字段?
  核C 两条管线是否共用同一个值域? 有无交集?

判据: 数据流（谁填/谁读/流向哪），不是键名 grep。
"""
import ast
import io
import os
import collections

ROOT = r"D:/shuntian-ziping-p0"
SKIP = {"__pycache__", ".git", "node_modules"}
PROD = "engines/common/strength_producer.py"


def load(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    return io.open(p, encoding="utf-8-sig", errors="ignore").read()


def main():
    print("=" * 100)
    print("裁「落前核」  L3 strength_verdict  vs  strength_producer.strength_state")
    print("=" * 100)

    # ── 核A: produce_strength 的定义与调用点 ──
    print("\n【核A】produce_strength 定义 + 全仓调用点")
    src = load(PROD)
    print("  %s 存在: %s" % (PROD, src is not None))
    if src:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "produce_strength":
                args = [a.arg for a in node.args.args]
                print("  定义 L%d  produce_strength(%s)"
                      % (node.lineno, ", ".join(args)))
                lines = src.split("\n")
                for i in range(node.lineno - 1,
                               min(node.lineno + 22, len(lines))):
                    print("      L%-5d %s" % (i + 1, lines[i].rstrip()[:92]))
    calls = []
    for base in ["engines", "p0_v2", "spec", "scripts", "tests"]:
        bp = os.path.join(ROOT, base)
        for dp, dn, fn in os.walk(bp):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                if rel == PROD:
                    continue
                s = load(rel)
                if s and "produce_strength" in s:
                    for i, l in enumerate(s.split("\n"), 1):
                        if "produce_strength" in l and not l.strip().startswith("#"):
                            calls.append((rel, i, l.strip()[:80]))
    print("\n  全仓 produce_strength 调用点 = %d" % len(calls))
    for rel, i, l in calls[:20]:
        print("      %-44s L%-5d %s" % (rel[:42], i, l))

    # ── 核B: strength_state 的生产者 vs 消费者 ──
    print("\n" + "=" * 100)
    print("【核B】strength_state 的【赋值点】(生产者) —— 值从哪来")
    print("=" * 100)
    producers = []
    for base in ["engines", "p0_v2", "spec"]:
        bp = os.path.join(ROOT, base)
        for dp, dn, fn in os.walk(bp):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if not f.endswith(".py"):
                    continue
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                s = load(rel)
                if not s:
                    continue
                for i, l in enumerate(s.split("\n"), 1):
                    st = l.strip()
                    if st.startswith("#"):
                        continue
                    if ("['strength_state']" in st or
                            '"strength_state"' in st and "=" in st) and "==" not in st:
                        producers.append((rel, i, st[:88]))
                    elif re.search(r"'strength_state'\s*:", st) if False else False:
                        pass
    print("  strength_state 赋值/写入点 = %d" % len(producers))
    seen = collections.Counter(r for r, _, _ in producers)
    for r, n in seen.most_common(14):
        print("      %-52s %d 处" % (r, n))
    print("\n  写入点明细(前 16):")
    for rel, i, l in producers[:16]:
        print("      %-40s L%-5d %s" % (rel.split("/")[-1][:28], i, l))

    # ── 核C: 值域交集 ──
    print("\n" + "=" * 100)
    print("【核C】两条管线的值域是否交集")
    print("=" * 100)
    l3 = load("p0_v2/bazi_gate.py")
    if l3:
        for i, l in enumerate(l3.split("\n"), 1):
            if "strength_verdict" in l:
                print("  bazi_gate.py L%-5d %s" % (i, l.strip()[:88]))
    print()
    if src:
        for i, l in enumerate(src.split("\n"), 1):
            if "UNDETERMINED" in l or "strength_state" in l:
                print("  strength_producer.py L%-5d %s" % (i, l.strip()[:88]))


import re  # noqa: E402

if __name__ == "__main__":
    main()