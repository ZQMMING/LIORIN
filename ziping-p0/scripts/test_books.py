# -*- coding: utf-8 -*-
"""test_books.py —— 六部经典案例跑盘

案例源: p0_v2/case_audit/<BOOK>_clean.jsonl  (每行含 bazi/raw/analysis/book/case_id/label)
         六本合集 _all_clean.jsonl (2106) 已归档, 本脚本只按书跑。

用法:
    python scripts/test_books.py --list                 # 列出六本及条数
    python scripts/test_books.py --book PZZQ            # 只跑子平真诠
    python scripts/test_books.py --book all            # 跑六本全部
    python scripts/test_books.py --book PZZQ --limit 20 --dump-fail
    python scripts/test_books.py --book PZZQ --label good

口径: 跑盘只为暴露引擎问题, 不是维护绿指标。
      输出按「引擎无输出 / 有输出 / 崩溃」分桶 + 逐条可选 dump。
"""
import sys, os, json, argparse, collections

ROOT = r"D:/shuntian-ziping-p0"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

CA = os.path.join(ROOT, "p0_v2", "case_audit")
BOOKS = [("DTS", "滴天髓"), ("PZZQ", "子平真诠"), ("QTBJ", "穷通宝鉴"),
         ("YHZP", "渊海子平"), ("SMTH", "三命通会"), ("SFTK", "神峰通考")]


def load_cases(book):
    fp = os.path.join(CA, "%s_clean.jsonl" % book)
    if not os.path.exists(fp):
        raise SystemExit("找不到 %s" % fp)
    rows = []
    for line in open(fp, encoding="utf-8-sig"):
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def run_one(bazi):
    """返回 (状态, 结果或 None, 错误信息)"""
    from p0_v2.bazi_gate import paipan
    try:
        r = paipan(bazi)
        return "OK", r, ""
    except Exception as e:
        return "CRASH", None, "%s: %s" % (type(e).__name__, str(e)[:120])


def summarize(r):
    """从引擎输出里抓四范式关键事实(只取实际输出, 不推断)"""
    gc = r.get("ge_cheng") or {}
    sp = r.get("special") or {}
    bl = r.get("bing_list") or []
    db = r.get("bing_debate") or {}
    l3 = r.get("l3_contract") or {}
    return {
        "ge": gc.get("ge"),
        "ti_wx": gc.get("ti_wx") or [],
        "xi_wx": gc.get("xi_wx") or [],
        "po_ge_n": len(gc.get("po_ge") or []),
        "cong": sp.get("cong_type"),
        "cong_state": sp.get("cong_state"),
        "bing_n": len(bl),
        "bing_ids": sorted(b.get("bing_id") for b in bl),
        "no_slice": [b.get("bing_id") for b in bl if not b.get("slice_id")],
        "primary": db.get("primary"),
        "compare_key": db.get("compare_key"),
        "yongyao": (r.get("yongyao") or {}).get("primary"),
        "l3": {k: l3.get(k) for k in
               ("dm_ben_eff", "ling_state", "root_grade",
                "support_state", "strength_verdict")},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", help="PZZQ/DTS/QTBJ/YHZP/SMTH/SFTK 或 all")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--label", help="good/neutral/bad/mixed")
    ap.add_argument("--dump-fail", action="store_true",
                    help="逐条打印引擎输出摘要")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list or not a.book:
        print("=" * 70)
        print("六部经典案例源  %s" % CA)
        print("=" * 70)
        tot = 0
        for bk, nm in BOOKS:
            fp = os.path.join(CA, "%s_clean.jsonl" % bk)
            n = len([l for l in open(fp, encoding="utf-8-sig") if l.strip()]) \
                if os.path.exists(fp) else 0
            tot += n
            print("  %-6s %-10s %5d 条" % (bk, nm, n))
        print("  %-17s %5d 条" % ("【合计】", tot))
        return 0

    from p0_v2.bazi_gate import paipan
    import p0_v2.bazi_gate as _bg

    targets = [b for b, _ in BOOKS] if a.book == "all" else [a.book.upper()]
    grand = collections.Counter()

    for bk in targets:
        name = dict(BOOKS).get(bk, bk)
        cases = load_cases(bk)
        if a.label:
            cases = [c for c in cases if c.get("label") == a.label]
        if a.limit:
            cases = cases[:a.limit]
        print()
        print("=" * 96)
        print("《%s》 %s   案例 %d 条" % (name, bk, len(cases)))
        print("=" * 96)

        bucket = collections.Counter()
        ge_cnt = collections.Counter()
        cong_cnt = collections.Counter()
        noslice = collections.Counter()
        rows = []
        for c in cases:
            bazi = (c.get("bazi") or "").replace(" ", "")
            if not bazi:
                bucket["无四柱"] += 1
                continue
            st, r, err = run_one(bazi)
            if st == "CRASH":
                bucket["崩溃"] += 1
                rows.append((c.get("case_id"), bazi, "CRASH", err))
                continue
            s = summarize(r)
            if not s["ge"] and not s["cong"]:
                bucket["引擎无输出"] += 1
            else:
                bucket["有输出"] += 1
            ge_cnt[s["ge"] or "(无格)"] += 1
            if s["cong"]:
                cong_cnt["%s/%s" % (s["cong"], s["cong_state"])] += 1
            for b in s["no_slice"]:
                noslice[b] += 1
            rows.append((c.get("case_id"), bazi, s, None))

        print("  桶: %s" % " | ".join("%s=%d" % (k, v) for k, v in bucket.items()))
        print("  格局分布 前10: %s" % ", ".join(
            "%s=%d" % (k, v) for k, v in ge_cnt.most_common(10)))
        if cong_cnt:
            print("  从格/专旺: %s" % ", ".join(
                "%s=%d" % (k, v) for k, v in cong_cnt.most_common(8)))
        if noslice:
            print("  ★ 无切片ID 的病机: %s" % ", ".join(
                "%s=%d" % (k, v) for k, v in noslice.most_common(8)))
        print("  崩溃详情: %s" % ([r for r in rows if r[2] == "CRASH"][:3] or "无"))
        grand.update(bucket)

        if a.dump_fail:
            for cid, bazi, s, err in rows:
                print("    %-9s %-17s %s" % (cid, bazi,
                                            err or json.dumps(s, ensure_ascii=False)[:150]))

    print()
    print("=" * 96)
    print("总计: %s" % " | ".join("%s=%d" % (k, v) for k, v in grand.items()))
    print("=" * 96)
    return 0


if __name__ == "__main__":
    sys.exit(main())