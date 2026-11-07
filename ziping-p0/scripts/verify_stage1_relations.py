# -*- coding: utf-8 -*-
"""阶段1 三项验收 (契约 v1.1 §四)

验收①  旧键读路径值不变         → relations 挂载前后 diff=0
验收②  relations 派生旧键 == L0 数据层旧键   ← 命门
验收③  93 处消费者零回归         → 见 §五 八层检查器
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
if os.path.join(ROOT, "p0_v2") in sys.path:
    sys.path.remove(os.path.join(ROOT, "p0_v2"))
from p0_v2.bazi_gate import _pillars

KEYS = ['liuhe', 'liuchong', 'sanhe', 'sanhui', 'banhe',
        'liuhai', 'liupo', 'sanxing', 'self_punishment']


def main():
    from engines.common.l0_fact_builder import build as l0build
    from engines.common.relations_builder import build_relations, derive_all
    st = collections.Counter()
    diffs = collections.defaultdict(list)
    crash = 0
    rel_cnt = collections.Counter()
    n = 0
    for bk in ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            pil = _pillars(bz)
            try:
                facts = l0build(pil)
            except Exception as e:
                crash += 1
                if crash <= 3:
                    print("  崩溃 %s %s: %s" % (d["case_id"], bz, e))
                continue
            cf = facts.get("combination_facts", {}) or {}
            # 验收②: L0 relations 字段 vs 独立重算 → 派生旧键 → 与数据层旧键逐条比
            R = facts.get("relations")
            if R is None:
                st["★relations 缺失"] += 1
                continue
            # 与独立重算比 (确保挂载点正确)
            zlis = [pil[k][1] for k in ("year", "month", "day", "hour")]
            if R != build_relations(zlis):
                st["★挂载值≠独立重算"] += 1
                if len(diffs['_mount']) < 3:
                    diffs['_mount'].append((d["case_id"], bz, None, None))
                continue
            der = derive_all(R)
            for r in R:
                rel_cnt[r['type']] += 1
            for k in KEYS:
                o = cf.get(k) or []
                nv = der[k]
                if k == 'self_punishment':
                    eq = (sorted((x['branch'], tuple(x['positions'])) for x in o)
                          == sorted((x['branch'], tuple(x['positions'])) for x in nv))
                else:
                    eq = (o == nv)
                if eq:
                    st["%s ✓" % k] += 1
                else:
                    st["%s ✗" % k] += 1
                    if len(diffs[k]) < 3:
                        diffs[k].append((d["case_id"], bz, o, nv))
    print("=" * 96)
    print("阶段1 验收②  relations 派生旧键 == L0 数据层旧键   六本 %d 盘  崩溃 %d" % (n, crash))
    print("=" * 96)
    tot = 0
    for k in KEYS:
        a, b = st["%s ✓" % k], st["%s ✗" % k]
        tot += b
        print("  %s %-18s 一致 %5d   不一致 %4d" % ("OK  " if b == 0 else "DIFF", k, a, b))
    if st["★relations 缺失"]:
        print("  ★ relations 缺失 %d" % st["★relations 缺失"])
    if st["★挂载值≠独立重算"]:
        print("  ★ 挂载值≠独立重算 %d" % st["★挂载值≠独立重算"])
    print("\n  差异总数 = %d" % tot)
    print("\n  relations 的 type 分布 (relations 已生效证据):")
    for t in sorted(rel_cnt):
        print("    %-8s %6d 条" % (t, rel_cnt[t]))
    print("    %-8s %6d 条 (合计)" % ('TOTAL', sum(rel_cnt.values())))
    for k, v in diffs.items():
        if k == '_mount':
            print("\n  【挂载值≠独立重算 样本】")
            for cid, bz, o, nw in v:
                print("    %-9s %-17s" % (cid, bz))
            continue
        print("\n  【%s 差异样本】" % k)
        for cid, bz, o, nw in v:
            print("    %-9s %-17s" % (cid, bz))
            print("      L0旧键=%s" % json.dumps(o, ensure_ascii=False)[:130])
            print("      派生值=%s" % json.dumps(nw, ensure_ascii=False)[:130])


if __name__ == "__main__":
    main()