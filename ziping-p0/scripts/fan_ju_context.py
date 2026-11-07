# -*- coding: utf-8 -*-
"""31 盘原文断语全文 + 语境正负判定 —— 反标定前必须清污染"""
import sys, os, json, re
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
KW = ['君赖臣生', '儿能救母', '儿能生母', '母慈灭子', '慈母', '灭子', '灭母',
      '夫健', '怕妻', '水泛木浮', '土重金埋', '木旺火炽', '火旺土焦', '金旺则水浊']
# 否定语境标志
NEG = ['非反局', '不作反局', '不是反局', '非君赖', '不作君赖', '非儿能',
       '不作成反局', '难以', '不得谓', '非也。', '未必', '不可以', '非母慈']


def main():
    rows = []
    for bk in BOOKS:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            raw = (d.get("raw") or "") + (d.get("liu_annotation") or "")
            hits = [k for k in KW if k in raw]
            if hits:
                rows.append((bk, d["case_id"], bz, hits, raw))

    print("=" * 100)
    print("31 盘原文断语全文 + 语境判定   共 %d 盘" % len(rows))
    print("=" * 100)
    pos, neg, unclear = [], [], []
    for bk, cid, bz, hits, raw in rows:
        # 取每处关键词前后 60 字
        ctxs = []
        for k in hits:
            for m in re.finditer(re.escape(k), raw):
                s = max(0, m.start() - 55)
                e = min(len(raw), m.end() + 55)
                ctxs.append(raw[s:e].replace("\n", " "))
        joined = "  ||  ".join(ctxs)
        is_neg = any(nk in raw for nk in NEG)
        # 更严: 看关键词紧邻前 25 字有无否定词
        tight_neg = False
        for k in hits:
            for m in re.finditer(re.escape(k), raw):
                pre = raw[max(0, m.start() - 25):m.start()]
                if re.search(r"非|不|未|莫|勿|难", pre):
                    tight_neg = True
        verdict = "否定" if (is_neg or tight_neg) else "肯定"
        (neg if verdict == "否定" else pos).append((bk, cid, bz, hits, joined))
        print("\n【%s】%s %s   [%s]  语境=%s" % (cid, bz, ",".join(hits), verdict, "" ))
        for c in ctxs[:3]:
            print("    ...%s..." % c)

    print("\n" + "=" * 100)
    print("正样本 %d 盘 / 否定样本 %d 盘" % (len(pos), len(neg)))
    print("=" * 100)
    print("\n【否定语境 —— 应从反标定剔除】")
    for bk, cid, bz, h, c in neg:
        print("  %-9s %-17s %-24s %s" % (cid, bz, ",".join(h), c[:150]))
    print("\n【肯定语境 —— 正样本】")
    for bk, cid, bz, h, c in pos:
        print("  %-9s %-17s %-24s %s" % (cid, bz, ",".join(h), c[:130]))


if __name__ == "__main__":
    main()