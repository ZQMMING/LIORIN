# -*- coding: utf-8 -*-
"""核2 四件一次出（裁九十一前置 + 白名单扫 + 专旺切片 + 碧渊赋）

1 patterns / judgment_status / mu_mie_state 的消费者（按数据流, AST）
2 bazi_gate.py 全部白名单 {k: X.get(k) for k in (...)} 的差集（系统性核查）
3 CONG_GE 段内 4 条专旺切片的内容（判断是否该拆段）
4 碧渊赋是否在 registries/source/ 六本底本内（决定 gate_ok 的 evidence 分级）

★ 立规 2e: 本脚本先跑探针锚点, 再出真实数据。
"""
import ast
import io
import os
import re
import collections

ROOT = r"D:/shuntian-ziping-p0"
SKIP = {"__pycache__", ".git", "node_modules"}


def load(rel):
    p = os.path.join(ROOT, rel)
    return io.open(p, encoding="utf-8-sig", errors="ignore").read() if os.path.exists(p) else None


def part1_consumers():
    print("=" * 104)
    print("【1】patterns / judgment_status / mu_mie_state 的消费者（AST, 按数据流）")
    print("=" * 104)
    TARGETS = ["patterns", "judgment_status", "mu_mie_state"]
    prod = []
    cons = collections.defaultdict(list)
    for base in ["engines", "p0_v2", "spec", "scripts", "tests"]:
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
                try:
                    t = ast.parse(s)
                except SyntaxError:
                    continue
                lines = s.split("\n")
                for node in ast.walk(t):
                    if isinstance(node, ast.Subscript) and \
                            isinstance(node.slice, ast.Constant) and \
                            node.slice.value in TARGETS:
                        recv = ast.unparse(node.value)
                        rec = (rel, node.lineno,
                               lines[node.lineno - 1].strip()[:76])
                        if rel == "engines/common/special_pattern.py":
                            prod.append(rec)
                        else:
                            cons[node.slice.value].append(rec)
                    if isinstance(node, ast.Call):
                        fn2 = node.func
                        nm = fn2.attr if isinstance(fn2, ast.Attribute) \
                            else getattr(fn2, "id", "")
                        if nm == "get" and node.args and \
                                isinstance(node.args[0], ast.Constant) and \
                                node.args[0].value in TARGETS:
                            recv = ast.unparse(node.func)
                            rec = (rel, node.lineno,
                                   lines[node.lineno - 1].strip()[:76])
                            if rel == "engines/common/special_pattern.py":
                                prod.append(rec)
                            else:
                                cons[node.args[0].value].append(rec)

    print("生产端(special_pattern.py 内) 写入/读取点 = %d" % len(prod))
    for r in prod[:14]:
        print("   %-36s L%-5d %s" % (r[0].split("/")[-1][:26], r[1], r[2]))
    print()
    for k in TARGETS:
        cls = [c for c in cons.get(k, []) if c[0].startswith("scripts/")
               or c[0].startswith("tests/") or "audit" in c[0]
               or "verify" in c[0] or "check" in c[0]]
        prd = [c for c in cons.get(k, []) if c not in cls]
        print("【%s】总读取 %d = 生产 %d + 验收 %d"
              % (k, len(cons.get(k, [])), len(prd), len(cls)))
        for c in prd[:8]:
            print("      ★生产 %-30s L%-5d %s"
                  % (c[0][:28], c[1], c[2]))
        if not prd:
            print("      ★ 无生产消费者")
    return cons


def part2_whitelist():
    print("\n" + "=" * 104)
    print("【2】bazi_gate.py 全部白名单差集（系统性核查, 不只 special 一处）")
    print("=" * 104)
    g = load("p0_v2/bazi_gate.py")
    # 找所有 {k: X.get(k) for k in (...)} 与 {k: X[k] for k in (...)}
    pat = re.compile(r"\{([^{}]*?)\s*for\s+[a-z]\s+in\s*\(([^)]*)\)\}", re.S)
    n = 0
    for m in pat.finditer(g):
        body, tup = m.group(1), m.group(2)
        ln = g[:m.start()].count("\n") + 1
        keys = [x.strip().strip('"\'') for x in tup.split(",") if x.strip()]
        print("\n  L%-5d 白名单 %d 键: %s" % (ln, len(keys), ", ".join(keys)))
        print("          表达式: %s" % " ".join(body.split())[:88])
        n += 1
    print("\n  白名单总处数 = %d" % n)
    return n


def part3_zhuanwang_slices():
    print("\n" + "=" * 104)
    print("【3】CONG_GE 段内 4 条专旺切片的内容（拆段建议依据）")
    print("=" * 104)
    GE = os.path.join(ROOT, "p0_v2", "六部经典MD文库", "02_原局诊断", "02_格局")
    for f in sorted(os.listdir(GE)):
        if not f.endswith(".md"):
            continue
        p = os.path.join(GE, f)
        raw = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        head = raw[:1400]
        mid = re.search(r"切片ID\*\*[：:]\s*([A-Za-z0-9_\.]+)", head)
        if not mid:
            continue
        sid = mid.group(1)
        if ".CONG_GE." not in sid:
            continue
        msrc = re.search(r"来源\*\*[：:]\s*(.+)", head)
        # 正文首段
        body = raw[raw.find("\n---"):] if "\n---" in raw else raw[1200:]
        seg = " ".join(x.strip() for x in body.split("\n")
                       if x.strip() and not x.strip().startswith("|")
                       and not x.strip().startswith("#"))[:300]
        print("\n  ID   : %s" % sid)
        print("  来源 : %s" % (msrc.group(1).strip()[:60] if msrc else "-"))
        print("  摘要 : %s" % seg[:240])


def part4_biyuanfu():
    print("\n" + "=" * 104)
    print("【4】碧渊赋是否在六本底本内（决定 gate_ok 的 evidence 分级）")
    print("=" * 104)
    RAW = os.path.join(ROOT, "registries", "source", "raw")
    hits = collections.Counter()
    samples = []
    for f in os.listdir(RAW):
        p = os.path.join(RAW, f)
        if not os.path.isfile(p):
            continue
        try:
            s = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        for i, l in enumerate(s.split("\n"), 1):
            if "碧渊" in l or "碧潭" in l:
                hits[f] += 1
                if len(samples) < 8:
                    samples.append((f, i, l.strip()[:96]))
    if not hits:
        print("  ★ 六本底本内 0 命中「碧渊」")
        print("  → gate_ok 的依据不在 canonical source 内")
    else:
        for f, n in hits.most_common():
            print("  命中 %-40s %d 处" % (f[:38], n))
        for f, i, l in samples:
            print("     %-32s L%-5d %s" % (f[:30], i, l))
    # 顺带: 渊海子平在不在（专旺切片引用过）
    print("\n  顺带核「渊海子平」:")
    for f in os.listdir(RAW):
        p = os.path.join(RAW, f)
        if not os.path.isfile(p):
            continue
        s = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        if "渊海" in s:
            print("     %-44s 命中 %d 处" % (f[:42], s.count("渊海")))


if __name__ == "__main__":
    print("★ 探针锚点: special 白名单 8 键 / 源码声明 10 键 —— 已知差集 3 键")
    part1_consumers()
    part2_whitelist()
    part3_zhuanwang_slices()
    part4_biyuanfu()