# -*- coding: utf-8 -*-
"""方局混纯 甲/乙 双版判据对比 (裁三十丙)

★ 独立进程跑(禁 execute_code 持久 kernel)—— 双路径 import 陷阱。

乙版(当前 check_fang_ju_ming)        : 额外支 ∈ 12支并集(任一另一类型组)
甲版(新增 check_fang_ju_ming_same_wx): 额外支 ∈ 【同五行】的另一类型组

判据口径未定 —— DTS L183 总纲无五行限制语, 两例(均木)同五行可能只是举木为例。
本脚本量两版命中数 + 列差异盘, 由案例断语定口径。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan
from engines.common.topology_paths import (
    check_fang_ju_ming_same_wx, check_fang_ju_ming_loose,
)

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]


def main():
    st = collections.Counter()
    samples = []
    diffs = []
    n = 0
    for bk in BOOKS:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            try:
                r = paipan(bz)
            except Exception as e:
                st["崩溃"] += 1
                if st["崩溃"] <= 3:
                    print("  崩溃 %s %s: %s" % (d["case_id"], bz, e))
                continue
            R = (r.get("raw_facts") or {}).get("relations") or []
            zlis = [bz[1], bz[3], bz[5], bz[7]]
            mB = check_fang_ju_ming_loose(R, zlis)
            mA = check_fang_ju_ming_same_wx(R, zlis)

            st["A=%s" % mA["jun_za_ming"]] += 1
            st["B=%s" % mB["jun_za_ming"]] += 1
            # 前提分布: 直接由 relations 判「完整组是否存在」(relations 只在三支齐时生成)
            _sanhe = [r for r in R if r.get("type") == "SANHE"]
            _hui = [r for r in R if r.get("type") == "HUI"]
            both = bool(_sanhe) and bool(_hui)
            st["both_complete=%s" % both] += 1
            if _sanhe and not _hui:
                st["前提_仅完整SANHE"] += 1
            if _hui and not _sanhe:
                st["前提_仅完整HUI"] += 1

            if mA["jun_za_ming"]:
                st["甲_方向_%s" % mA["group_type"]] += 1
                for f in mA["findings"]:
                    st["甲_evidence_%s" % f["evidence"]] += 1
            if mB["jun_za_ming"] and not mA["jun_za_ming"]:
                st["★乙命中甲不命中"] += 1
                ana = str(d.get("analysis") or "") + " " + str(d.get("raw") or "")
                diffs.append((d["case_id"], bk, bz, mB, ana))
            if mA["jun_za_ming"] and not mB["jun_za_ming"]:
                st["★甲命中乙不命中_逻辑矛盾"] += 1
            if mA["jun_za_ming"] and len(samples) < 6:
                samples.append((d["case_id"], bz, mA))

    print("=" * 96)
    print("方局混纯 甲/乙 双版对比   六本 %d 盘   崩溃 %d" % (n, st["崩溃"]))
    print("=" * 96)

    print("\n【命中数】")
    print("    %-14s %6d  (%.2f%%)" % ("甲版 同五行", st["A=True"], st["A=True"] * 100.0 / n))
    print("    %-14s %6d  (%.2f%%)" % ("乙版 任意", st["B=True"], st["B=True"] * 100.0 / n))
    print("    %-14s %6d" % ("差(乙-甲)", st["B=True"] - st["A=True"]))

    print("\n【前提分布】")
    for k in sorted(st):
        if k.startswith("前提_") or k.startswith("both_"):
            print("    %-24s %6d  (%.2f%%)" % (k, st[k], st[k] * 100.0 / n))

    print("\n【甲版方向分布】")
    for k in sorted(k for k in st if k.startswith("甲_方向")):
        print("    %-24s %6d" % (k[4:], st[k]))

    print("\n【甲版 evidence 分级(裁三十一)】")
    for k in sorted(k for k in st if k.startswith("甲_evidence")):
        print("    %-24s %6d" % (k[7:], st[k]))

    print("\n【两版差异】")
    star = [k for k in sorted(st) if k.startswith("★")]
    if star:
        for k in star:
            print("    %-30s %6d" % (k, st[k]))
    else:
        print("    (无)")

    print("\n【甲版命中样本】")
    for cid, bz, m in samples:
        print("  %-9s %-17s" % (cid, bz))
        for f in m["findings"]:
            print("      [%s] 完整组 %s + 额外一支 %s  同五行组 %s  [%s]"
                  % (f["group_type"], f["complete_group_display"],
                     f["extra_branch"], f["peer_group_display"], f["evidence"]))

    print("\n【差异盘(乙命中/甲不命中) 明细 — 需核案例断语】")
    print("  ★ 断语说「混局/纯疵/太过」→ 甲漏判; 断语无相关词 → 乙过宽")
    KW = ["混局", "纯疵", "太过", "纯一"]
    with_kw = 0
    for cid, bk, bz, mB, ana in diffs:
        if any(k in ana for k in KW):
            with_kw += 1
    print("    差异盘总数        = %d" % len(diffs))
    print("    断语含相关词      = %d   ← 若案例说混局, 说明甲漏判" % with_kw)
    print("    断语无相关词      = %d   ← 乙过宽的候选" % (len(diffs) - with_kw))
    print()
    for cid, bk, bz, mB, ana in diffs[:14]:
        hit = [k for k in KW if k in ana]
        print("  %-9s %-4s %-17s 乙=%d  断语%s"
              % (cid, bk, bz, mB["findings_count"],
                 ("含 " + ",".join(hit)) if hit else "【无相关词】"))
        if hit:
            i = ana.find(hit[0])
            print("        …%s…" % ana[max(0, i - 45):i + 55].replace("\n", " "))


if __name__ == "__main__":
    main()