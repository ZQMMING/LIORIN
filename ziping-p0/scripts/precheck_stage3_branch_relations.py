# -*- coding: utf-8 -*-
"""阶段3 前置核: branch_relations vs relations

核点1  branch_relations.liuhe 的支对集合 == relations 里 type=HE 的支对集合 ?
核点2  branch_relations 全部 type 与 relations 9 类对照
核点3  distance / blocking 的挂载粒度 (支对 还是 盘)
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
if os.path.join(ROOT, "p0_v2") in sys.path:
    sys.path.remove(os.path.join(ROOT, "p0_v2"))
POSK = ("year", "month", "day", "hour")


def main():
    from engines.common.l0_fact_builder import build as l0build
    st = collections.Counter()
    diffs = []
    field_keys = collections.Counter()
    type_cnt = collections.Counter()
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
            pil = {k: [bz[2 * i], bz[2 * i + 1]] for i, k in enumerate(POSK)}
            facts = l0build(pil)
            br = facts.get("branch_relations") or []
            R = facts.get("relations") or []
            for r in br:
                type_cnt[r.get("type")] += 1
                for k in r:
                    field_keys["br.%s" % k] += 1
            for r in R:
                rel_cnt[r["type"]] += 1
            # 核点1: liuhe 支对集合 vs HE 支对集合
            br_he = set()
            for r in br:
                if r.get("type") == "liuhe":
                    br_he.add((frozenset(r["branches"]), tuple(sorted(r.get("positions") or []))))
            rel_he = set()
            for r in R:
                if r["type"] == "HE":
                    for pair in r["positions"]:
                        rel_he.add((frozenset(r["branches"]), tuple(sorted(x[0] for x in pair))))
            if br_he == rel_he:
                st["liuhe==HE (支对+柱位)" ] += 1
            else:
                only_br = br_he - rel_he
                only_rel = rel_he - br_he
                st["★liuhe != HE"] += 1
                if len(diffs) < 5:
                    diffs.append((d["case_id"], bz, sorted(map(str, only_br)),
                                  sorted(map(str, only_rel))))
    print("=" * 96)
    print("阶段3 前置核   六本 %d 盘" % n)
    print("=" * 96)
    print("\n【核点1】branch_relations.liuhe  vs  relations.type=HE   (支对 + 柱位)")
    for k in sorted(st):
        print("    %-28s %5d" % (k[2:], st[k]))
    if diffs:
        print("\n  差异样本:")
        for cid, bz, ob, orl in diffs:
            print("    %-9s %-17s  仅branch_relations=%s  仅relations=%s" % (cid, bz, ob, orl))
    print("\n【核点2】type 清单对照")
    print("    branch_relations 的 type:")
    for k, v in sorted(type_cnt.items(), key=lambda x: -x[1]):
        print("        %-12s %6d" % (k, v))
    print("    relations 的 type (9类):")
    for k, v in sorted(rel_cnt.items(), key=lambda x: -x[1]):
        print("        %-12s %6d" % (k, v))
    print("\n【核点3】字段清单 (挂载粒度: 看字段是每条关系一份, 还是全盘一份)")
    print("    branch_relations 每条关系的字段:")
    for k, v in sorted(field_keys.items()):
        print("        %-32s 出现 %6d 次" % (k[3:], v))
    print("    relations 每条关系的字段: type / branches / positions / wx / meta / instance_count")


if __name__ == "__main__":
    main()