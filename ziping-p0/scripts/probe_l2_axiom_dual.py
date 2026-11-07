# -*- coding: utf-8 -*-
"""探针 10 双版（裁一百零三丙）: 紧邻版=判据候选池 / 跨字版=线索池

★ 两版都不是「冲突数」, 是【候选清单】—— 真实冲突数必须人工核上下文。
★ 理由（第九次同类错）: 语义区分（次序 vs 卦象/脏腑）机器做不了。

版本口径:
  紧邻版  X(生|克|制|耗)Y  四字紧邻, 零跨字
          → 无跨字假象, 是判据的候选池（仍需人工核语境）
  跨字版  X…(生|克|制|耗)…Y  允许中间 ≤6 字
          → 会造假冲突（DTS「火者木之子也…欺金」）, 只作线索池

输出: 两版候选数 + 每条上下文（人工筛）。本脚本【不出】真实冲突数。
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
RX_TIGHT = re.compile(r"([木火土金水])\s?(生|克|制|耗)\s?([木火土金水])")
RX_LOOSE = re.compile(r"([木火土金水])[^\n]{0,6}?(生|克|制|耗)[^\n]{0,6}?([木火土金水])")


def scan(rx, label):
    hits = collections.defaultdict(lambda: {"agree": [], "cand": []})
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
            if len(l) < 5:
                continue
            for m in rx.finditer(l):
                a, op, b = m.group(1), m.group(2), m.group(3)
                if a == b:
                    continue
                exp = (CODE_SHENG if op == "生" else CODE_KE).get(a)
                if exp is None:
                    continue
                rec = (i, l.strip()[:70], lines)
                if b == exp:
                    hits[f]["agree"].append((a, op, b, rec))
                else:
                    hits[f]["cand"].append((a, op, b, exp, rec))
    ta = sum(len(d["agree"]) for d in hits.values())
    tc = sum(len(d["cand"]) for d in hits.values())
    cov_s = {a for f in hits for (a, op, b, r) in hits[f]["agree"] if op == "生"}
    cov_k = {a for f in hits for (a, op, b, r) in hits[f]["agree"] if op == "克"}
    print("\n" + "=" * 100)
    print("【%s】" % label)
    print("=" * 100)
    print("%-46s %8s %8s" % ("底本", "一致", "候选"))
    for f, d in hits.items():
        print("%-46s %8d %8d" % (f[:44], len(d["agree"]), len(d["cand"])))
    print("%-46s %8d %8d" % ("合计", ta, tc))
    print("\n[覆盖参考] 相生源 %d/5   相克源 %d/5   缺: 生%s 克%s"
          % (len(cov_s), len(cov_k),
             sorted(set(WX) - cov_s) or "无", sorted(set(WX) - cov_k) or "无"))
    print("\n★ 候选 %d 处 —— 【不是冲突数】, 须人工核上下文" % tc)
    return hits, tc


def main():
    print("=" * 100)
    print("探针 10 双版  紧邻版（判据候选池） + 跨字版（线索池）")
    print("=" * 100)
    hits_t, n_t = scan(RX_TIGHT, "紧邻版（四字紧邻, 零跨字）—— 判据候选池")
    hits_l, n_l = scan(RX_LOOSE, "跨字版（允许 ≤6 字）—— 线索池, 会造假冲突")

    print("\n" + "=" * 100)
    print("紧邻版候选逐处 + 上下文（供人工判「次序 vs 语境」）")
    print("=" * 100)
    n = 0
    for f, d in hits_t.items():
        for (a, op, b, exp, rec) in d["cand"]:
            n += 1
            i, txt, lines = rec
            print("\n【候选 %d】%s L%d   原文「%s%s%s」 引擎表「%s%s%s」"
                  % (n, f[:26], i, a, op, b, a, op, exp))
            for j in range(max(0, i - 2), min(len(lines), i + 1)):
                print("   %s L%-6d %s" % (">>" if j == i - 1 else "  ",
                                          j + 1, lines[j].strip()[:88]))
    print("\n" + "=" * 100)
    print("汇总: 紧邻版候选 %d 处 / 跨字版候选 %d 处" % (n_t, n_l))
    print("★ 两版都是候选池 —— 真实冲突数 = 人工核完的数, 本脚本【不出】该数。")
    print("=" * 100)


if __name__ == "__main__":
    main()