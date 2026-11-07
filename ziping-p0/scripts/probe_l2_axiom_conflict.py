# -*- coding: utf-8 -*-
"""探针 10 修正版: 判据从「覆盖率」换成「有无冲突」（裁一百丙）

★ 否掉「放宽正则补覆盖率」—— 那是治症状; 判据本身选错了。
★ AXIOM 的定义是「六本共享, 无单一出处」→ 判据是【有无冲突】, 不是覆盖率。

新判据:
  扫六本全部「X…生/克/制/耗…Y」显式配对, 列出【与引擎 sheng/ke 表字面冲突】者。
  冲突 = 0 → AXIOM 成立
  冲突 > 0 → 逐条读上下文, 判「真冲突 / 语境不同」

★ 这是第八次同类错的变体: 用【能计数的指标】代替【该判的东西】。
"""
import io
import os
import re
import collections

ROOT = r"D:/shuntian-ziping-p0"
RAW = os.path.join(ROOT, "registries", "source", "raw")
CODE_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CODE_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
WX = "木火土金水"
RX = re.compile(r"([木火土金水])[^\n]{0,6}?(生|克|制|耗)[^\n]{0,6}?([木火土金水])")


def main():
    print("=" * 100)
    print("探针 10 修正版  判据 = 有无冲突（不是覆盖率）")
    print("=" * 100)

    hits = collections.defaultdict(lambda: {"agree": [], "conflict": []})
    for f in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, f)
        if not os.path.isfile(p):
            continue
        try:
            s = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        lines = s.split("\n")
        for i, l in enumerate(lines, 1):
            if len(l) < 6:
                continue
            for m in RX.finditer(l):
                a, op, b = m.group(1), m.group(2), m.group(3)
                if a == b:
                    continue
                tbl = CODE_SHENG if op == "生" else CODE_KE
                exp = tbl.get(a)
                if exp is None:
                    continue
                rec = (i, l.strip()[:72], lines)
                if b == exp:
                    hits[f]["agree"].append((a, op, b, rec))
                else:
                    hits[f]["conflict"].append((a, op, b, exp, rec))

    tot_a = sum(len(d["agree"]) for d in hits.values())
    tot_c = sum(len(d["conflict"]) for d in hits.values())
    print("\n六本显式配对: 一致 %d 处 / 冲突 %d 处" % (tot_a, tot_c))
    print("-" * 100)
    print("%-46s %8s %8s" % ("底本", "一致", "冲突"))
    for f, d in hits.items():
        print("%-46s %8d %8d" % (f[:44], len(d["agree"]), len(d["conflict"])))

    cov_s = {a for f in hits for (a, op, b, r) in hits[f]["agree"] if op == "生"}
    cov_k = {a for f in hits for (a, op, b, r) in hits[f]["agree"] if op == "克"}
    print("\n[参考, 非判据] 相生源覆盖 %d/5  相克源覆盖 %d/5"
          % (len(cov_s), len(cov_k)))
    print("        相生缺: %s   相克缺: %s"
          % (sorted(set(WX) - cov_s) or "无", sorted(set(WX) - cov_k) or "无"))

    print("\n" + "=" * 100)
    print("冲突逐条 + 上下文（人工判「真冲突 / 语境不同」）")
    print("=" * 100)
    n = 0
    for f, d in hits.items():
        for (a, op, b, exp, rec) in d["conflict"]:
            n += 1
            i, txt, lines = rec
            print("\n【冲突 %d】%s L%d" % (n, f[:30], i))
            print("   原文: 「%s%s%s」   引擎表: 「%s%s%s」"
                  % (a, op, b, a, op, exp))
            lo, hi = max(0, i - 3), min(len(lines), i + 2)
            for j in range(lo, hi):
                mark = ">>" if j == i - 1 else "  "
                print("   %s L%-6d %s" % (mark, j + 1, lines[j].strip()[:80]))

    print("\n" + "=" * 100)
    print("探针 10 判定（判据=有无冲突）: %s"
          % ("★ PASS —— 冲突 0 处, AXIOM 成立"
             if n == 0 else
             "★ %d 处冲突 —— 须逐条人工判「真冲突 / 语境不同」后才定 AXIOM" % n))
    print("=" * 100)


if __name__ == "__main__":
    main()