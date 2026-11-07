# -*- coding: utf-8 -*-
"""核3: 格局切片覆盖度 —— 格 × 经典 × 条数矩阵

★ 先看料, 再看用料的代码（核1/核2）。切片是 canonical source, 是 L4 的判据上游。
数据源: p0_v2/六部经典MD文库/02_原局诊断/02_格局/ 全部 .md
读 frontmatter 的「切片ID」+ 正文标题 + 来源, 不靠文件名猜。
"""
import io
import os
import re
import collections

ROOT = r"D:/shuntian-ziping-p0"
LIB = os.path.join(ROOT, "p0_v2", "六部经典MD文库")
GE = os.path.join(LIB, "02_原局诊断", "02_格局")

# 格类关键词（用于把切片归到具体格）
GE_KINDS = [
    ("正官", "正官"), ("偏官_七杀", "七杀"), ("偏官", "七杀"), ("杀", "七杀"),
    ("正财", "正财"), ("偏财", "偏财"), ("财", "财"),
    ("正印", "正印"), ("偏印", "偏印"), ("印", "印"),
    ("食神", "食神"), ("伤官", "伤官"),
    ("建禄", "建禄"), ("月刃", "月刃"), ("阳刃", "月刃"),
    ("从格", "从格"), ("从财", "从财"), ("从杀", "从杀"), ("从儿", "从儿"),
    ("从旺", "从旺"), ("专旺", "专旺"), ("专生", "专生"), ("专月", "专月"),
    ("化气", "化气"), ("化格", "化格"), ("化象", "化气"),
    ("外格", "外格"), ("八格", "八格"), ("正格", "八格"),
    ("禄命", "八格"),
]
CONG = ["从格", "从财", "从杀", "从儿", "从旺", "专旺", "专生", "专月"]
HUA = ["化气", "化格", "化象"]


def kind_of(text):
    t = text
    if any(k in t for k in CONG):
        for k in CONG:
            if k in t:
                return k
    if any(k in t for k in HUA):
        for k in HUA:
            if k in t:
                return k
    return None


def main():
    print("=" * 100)
    print("核3格局切片覆盖度   格 × 经典 × 条数")
    print("=" * 100)
    if not os.path.isdir(GE):
        print("★ 目录不存在: %s" % GE)
        for dp, dn, fn in os.walk(LIB):
            depth = dp[len(LIB):].count(os.sep)
            if depth <= 2 and any(f.endswith(".md") for f in fn):
                print("   %-44s %d 个 md" % (dp[len(LIB):] or "/", len(fn)))
        return

    recs = []
    for f in sorted(os.listdir(GE)):
        if not f.endswith(".md"):
            continue
        p = os.path.join(GE, f)
        raw = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        head = raw[:1400]
        mid = re.search(r"切片ID\*\*[：:]\s*([A-Za-z0-9_\.]+)", head)
        msrc = re.search(r"来源\*\*[：:]\s*(.+)", head)
        # 标题 = 切片ID 后第一个非空非 frontmatter 行
        title = ""
        for l in raw.split("\n"):
            s = l.strip().lstrip("#").strip()
            if s and "：" not in s and ":" not in s[:6]:
                title = s[:60]
                break
        recs.append({
            "file": f,
            "id": mid.group(1) if mid else None,
            "src": (msrc.group(1).strip()[:28] if msrc else None),
            "title": title,
            "text": raw,
            "kind": kind_of(raw),
        })

    print("格局目录 = %s" % GE[len(ROOT) + 1:])
    print("切片总数 = %d  (有 frontmatter 切片ID 的 = %d)"
          % (len(recs), sum(1 for r in recs if r["id"])))

    # ── 切片ID 前缀聚类（这是权威的格归类依据）──
    print("\n" + "=" * 100)
    print("【A】按切片ID 前缀聚类（权威口径）")
    print("=" * 100)
    pref = collections.Counter()
    for r in recs:
        if r["id"]:
            pref[".".join(r["id"].split(".")[:2])] += 1
    for k, v in pref.most_common():
        print("    %-46s %d 条" % (k, v))

    # ── 逐条列清单 ──
    print("\n" + "=" * 100)
    print("【B】逐条清单: 切片ID | 来源 | 标题 | 格归类")
    print("=" * 100)
    kindcnt = collections.Counter()
    srccnt = collections.Counter()
    for r in recs:
        k = r["kind"] or "(未归类)"
        kindcnt[k] += 1
        if r["src"]:
            srccnt[r["src"][:16]] += 1
        print("  %-42s %-16s %-40s %s"
              % ((r["id"] or "(无ID)")[:40], (r["src"] or "-")[:15],
                 r["title"][:38], k))

    print("\n" + "=" * 100)
    print("【C】格类 × 条数")
    print("=" * 100)
    for k, v in kindcnt.most_common():
        print("    %-14s %d 条" % (k, v))

    print("\n" + "=" * 100)
    print("【D】来源分布（六部经典）")
    print("=" * 100)
    for k, v in srccnt.most_common():
        print("    %-20s %d 条" % (k, v))

    # ── 判据链完整度：八格逐格核 ──
    print("\n" + "=" * 100)
    print("【E】八格 / 从化专旺 逐格判据链完整度")
    print("=" * 100)
    alltext = " ".join(r["text"] for r in recs)
    BAGE = [("正官", ["正官"]), ("七杀", ["七杀", "偏官"]),
            ("正财", ["正财"]), ("偏财", ["偏财"]),
            ("正印", ["正印"]), ("偏印", ["偏印"]),
            ("食神", ["食神"]), ("伤官", ["伤官"]),
            ("建禄", ["建禄", "禄命"]), ("月刃", ["月刃", "羊刃", "阳刃"]),
            ("从格", ["从格", "从财", "从杀", "从儿"]),
            ("专旺", ["专旺", "从旺", "专生", "专月"]),
            ("化气", ["化气", "化格", "化象"]),
            ("外格", ["外格"])]
    print("  %-10s %6s %s" % ("格", "切片条数", "命例数(原文「造」/命造标记)"))
    print("  " + "-" * 72)
    for name, kws in BAGE:
        n = sum(1 for r in recs if r["kind"] == name or
                any(k == r["kind"] for k in kws))
        ncase = alltext.count(name + "造")
        print("  %-10s %6d %d" % (name, n, ncase))

    print("\n  ★ 判据链完整度口径: 1 条 = 有切片; ≥2 条 = 有判据+约束可拼判据树")
    print("    0 条 = 该格无 canonical 依据 → 核1/核2 的「有无 DTS 明文」无参照")


if __name__ == "__main__":
    main()