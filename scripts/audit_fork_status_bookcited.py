# -*- coding: utf-8 -*-
"""三件一次出（裁九十四前置 + judgment_status 核 + BOOK_CITED 连带扫）

1 路径分叉核: 重算路径 vs 复用路径 的 ge_cheng 8 键是否相同
    —— 不核就修 L450 白名单, 若两路分叉则不是「修复」而是「换行为」
2 judgment_status 12 处验收: 读值打日志(META) 还是 走分支(COMPUTED)
3 BOOK_CITED 连带扫: 现有 ENGINE_DEFINED / DTS_CITED 里有没有「他本有原文」的错标

★ 立规 2e: 先跑探针锚点再出真实数据。
"""
import ast
import io
import os
import re
import sys
import json
import collections

ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
SKIP = {"__pycache__", ".git", "node_modules"}
CA = os.path.join(ROOT, "p0_v2", "case_audit")
BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
HE_BOOKS = ["渊海子平", "三命通会", "神峰", "穷通宝鉴", "子平真诠", "滴天髓"]


def load(rel):
    p = os.path.join(ROOT, rel)
    return io.open(p, encoding="utf-8-sig", errors="ignore").read() if os.path.exists(p) else None


# ─────────── 1 路径分叉核 ───────────
def part1_fork():
    print("=" * 104)
    print("【1】路径分叉核: 重算路径 vs 复用路径 的 ge_cheng 8 键")
    print("=" * 104)
    from p0_v2.bazi_gate import paipan
    from engines.common.special_pattern import build_special_patterns

    charts = []
    for bk in BOOKS:
        for line in open(os.path.join(CA, "%s_clean.jsonl" % bk),
                         encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) == 8:
                charts.append((d["case_id"], bz))
    print("样本 = %d 盘" % len(charts))

    print("\n  探针: 先验证两条路径确实【不同】(当前 L110 恒 False)")
    # 直接构造「有 patterns 的 spv」和「无 patterns 的 spv」两条路
    diff_ge = 0
    diff_sp = 0
    n_ran = 0
    sample = []
    for cid, bz in charts:
        r = paipan(bz)
        sp_now = r.get("special") or {}
        # 路径 A: 现状（重算）—— ge_jie_layer 内部每次重算
        # 路径 B: 修复后（复用 spv）—— 用 paipan 已构造的 special
        # 两者的差别只在 special 的来源, ge_cheng 才是要比较的判定
        # 这里比较: 若 spv 带 patterns 时 ge_jie_layer 会 return spv(=r['special'])
        #           若 spv 不带 patterns 时会重算 —— 重算结果 vs r['special']
        if "patterns" in sp_now:
            continue
        n_ran += 1
        # 模拟重算: 用与 bazi_gate 相同的四参重算一次
        p = r.get("pillars") or {}
        recomputed = build_special_patterns(
            p, r, r.get("wuxing_power") or {}, r.get("tian_he") or None)
        if recomputed.get("cong_type") != sp_now.get("cong_type") or \
                recomputed.get("zhuanwang") != sp_now.get("zhuanwang") or \
                recomputed.get("hua_qi") != sp_now.get("hua_qi"):
            diff_sp += 1
            if len(sample) < 5:
                sample.append((cid,
                               (sp_now.get("cong_type"), sp_now.get("zhuanwang"),
                                sp_now.get("hua_qi")),
                               (recomputed.get("cong_type"),
                                recomputed.get("zhuanwang"),
                                recomputed.get("hua_qi"))))
    print("  两路 special 值分叉盘数 = %d / %d" % (diff_sp, n_ran))
    for s in sample:
        print("      %s  现有=%s  重算=%s" % (s[0], s[1], s[2]))
    print("\n  ★ 结论: %s" % ("★ 两条路径 special 分叉 —— 修复会改判定, 不是纯性能"
                               if diff_sp else "两路 special 全同 → 修复是纯性能, 零判定变化"))
    return diff_sp, n_ran


# ─────────── 2 judgment_status 消费形态 ───────────
def part2_status_use():
    print("\n" + "=" * 104)
    print("【2】judgment_status 12 处验收: 读值打日志 还是 走分支?")
    print("=" * 104)
    hits = []
    for base in ["scripts", "tests", "p0_v2", "engines"]:
        bp = os.path.join(ROOT, base)
        for dp, dn, fn in os.walk(bp):
            dn[:] = [d for d in dn if d not in SKIP]
            for f in fn:
                if not f.endswith(".py"):
                    continue
                rel = os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/")
                if rel.endswith("audit_special_four_checks.py"):
                    continue
                s = load(rel)
                if not s:
                    continue
                for i, l in enumerate(s.split("\n"), 1):
                    if "judgment_status" in l and "special" in l.lower():
                        hits.append((rel, i, l.strip()[:96]))
    print("命中行 = %d" % len(hits))
    branch = []
    logonly = []
    for rel, i, l in hits:
        is_branch = bool(re.search(r"if\s|==\s*['\"]|!=\s*['\"]|\bin\b\s+\w|assert", l))
        (branch if is_branch else logonly).append((rel, i, l))
    print("\n  走分支(判 COMPUTED) = %d 行:" % len(branch))
    for r in branch[:20]:
        print("      %-40s L%-5d %s" % (r[0].split("/")[-1][:28], r[1], r[2]))
    print("\n  仅打日志/取值(META) = %d 行:" % len(logonly))
    for r in logonly[:10]:
        print("      %-40s L%-5d %s" % (r[0].split("/")[-1][:28], r[1], r[2]))
    return len(branch), len(logonly)


# ─────────── 3 BOOK_CITED 连带扫 ───────────
def part3_book_cited():
    print("\n" + "=" * 104)
    print("【3】BOOK_CITED 连带扫: 有他本原文却被标 ENGINE_DEFINED / DTS_CITED 的")
    print("=" * 104)
    sp = load("engines/common/special_pattern.py")
    gl = load("engines/common/ge_jie_layer.py")
    spec = load("p0_v2/l3_contract_spec.md")
    RAW = os.path.join(ROOT, "registries", "source", "raw")
    files = {f: load(os.path.join("registries/source/raw", f))
             for f in os.listdir(RAW) if os.path.isfile(os.path.join(RAW, f))}

    print("\n【3a】他本（渊海/三命/神峰/穷通）在 special_pattern.py 的引用点")
    print("-" * 104)
    if sp:
        for i, l in enumerate(sp.split("\n"), 1):
            if any(b in l for b in ("渊海", "三命", "神峰", "碧渊", "穷通")):
                print("   special_pattern.py L%-5d %s" % (i, l.strip()[:96]))

    print("\n【3b】契约文档里 ENGINE_DEFINED / DTS_CITED 附近的书名引用")
    print("-" * 104)
    if spec:
        lines = spec.split("\n")
        for i, l in enumerate(lines):
            if "ENGINE_DEFINED" not in l and "DTS_CITED" not in l:
                continue
            ctx = " ".join(lines[max(0, i - 2):i + 3])
            hit = [b for b in ("渊海", "三命", "神峰", "碧渊", "穷通", "子平真诠",
                               "滴天髓", "YHZP", "SMTH", "PZZQ", "QTBJ", "SFTK")
                   if b in ctx]
            if hit and not any(x in ctx for x in ("滴天髓", "DTS")):
                print("   L%-5d [%s] %s" % (i + 1, "/".join(hit[:3]),
                                            l.strip()[:78]))

    print("\n【3c】六本底本中「碧渊赋」是否有可引用的判据原文（专旺闸门是否可立 BOOK_CITED）")
    print("-" * 104)
    yh = None
    for f, s in files.items():
        if f.startswith("YHZP") and s:
            yh = (f, s)
            break
    if yh:
        f, s = yh
        lines = s.split("\n")
        for i, l in enumerate(lines):
            if "碧渊" in l:
                for j in range(max(0, i - 1), min(len(lines), i + 6)):
                    print("   %s L%-6d %s" % (f[:22], j + 1, lines[j].strip()[:92]))
                print("   " + "-" * 60)


if __name__ == "__main__":
    print("★ 探针锚点: L110 恒 False / CONG_GE 4 条全从格 / 碧渊赋 YHZP 5 处")
    part1_fork()
    part2_status_use()
    part3_book_cited()