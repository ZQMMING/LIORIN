# -*- coding: utf-8 -*-
"""冲拔矩阵前置: 1无案例格结构分类(甲/乙) 2有案例格集中度 3 de_ling 12盘核查。"""
import sys, os, json, itertools, csv
from collections import defaultdict
ROOT = r"D:/shuntian-ziping-p0"; sys.path.insert(0, ROOT)
from p0_v2.bazi_gate import paipan

KIND_L = ["纯相生", "纯相克", "混合"]
ROOT_L = ["本气", "禄", "刃", "长生", "墓库", "余气"]
DIST_L = ["同柱", "紧贴", "隔一", "遥隔"]
HE_L = ["无解", "六合解", "三会解", "刑合"]
ZHUANG_L = ["旺", "中", "衰"]
SUPP_L = ["有力", "无力", "NA"]
allkeys = list(itertools.product(KIND_L, ROOT_L, DIST_L, HE_L, ZHUANG_L, SUPP_L))

filled = set()
disk = {}
with open(os.path.join(ROOT, "scripts", "chong_full_matrix.csv"),
          encoding="utf-8-sig") as fp:
    for row in csv.DictReader(fp):
        k = (row["kind"], row["根位"], row["距离"], row["合解"],
             row["主体旺衰"], row["相生神"])
        if int(row["有案例"]):
            filled.add(k)
            disk[k] = (int(row["盘数"]), int(row["漏"]), int(row["误"]))


def structurally_impossible(k):
    kind, rk, dist, he, zhuang, sp = k
    if dist == "同柱":
        return "甲:地支六冲在两支不同柱,同柱不存在"
    if kind == "纯相生":
        return "甲:六冲六对(子午卯酉辰戌/丑未寅申巳亥)无纯相生型"
    if kind == "纯相克" and sp != "NA":
        return "甲:纯相克型无相生神,必NA"
    if kind != "纯相克" and sp == "NA":
        return "甲:相生/混合型相生神不得NA"
    return None


jia, yi = [], []
for k in allkeys:
    if k in filled:
        continue
    r = structurally_impossible(k)
    (jia if r else yi).append((k, r))

print("=== 前置1: 2520 无案例格分类 ===")
print("甲 结构不可能=%d" % len(jia))
print("乙 结构可能但案例库无=%d" % len(yi))
from collections import Counter
print("甲原因:", dict(Counter(r for _, r in jia)))
print("\n乙样例(前12):")
for k, _ in yi[:12]:
    print("  ", k)

print("\n=== 前置2: 72 有案例格集中度 ===")
ordered = sorted(filled, key=lambda k: -disk[k][0])
tot = sum(disk[k][0] for k in filled)
cum = 0
for i, k in enumerate(ordered):
    cum += disk[k][0]
    if i < 10 or i == len(ordered) - 1:
        print(" #%d %s 盘=%d (累计%.0f%%)" %
              (i + 1, k, disk[k][0], 100 * cum / tot))
print("前10格覆盖 %.1f%% 盘; 有案例格=%d" %
      (100 * sum(disk[k][0] for k in ordered[:10]) / tot, len(filled)))

print("\n=== 前置3: 纯相克·本气·紧贴·旺 漏格 逐盘核 de_ling ===")
target = ("纯相克", "本气", "紧贴", "无解", "旺", "NA")
cids = set()
# 重新从明细找该格盘
for book in ["DTS", "PZZQ", "QTBJ", "SFTK", "SMTH", "YHZP"]:
    for l in open(os.path.join(ROOT, "p0_v2", "case_audit", book + "_clean.jsonl"),
                  encoding="utf-8-sig"):
        c = json.loads(l); bz = (c.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        r = paipan(bz); f = r.get("raw_facts") or {}
        dm_wx = f.get("daymaster_element", "")
        pillars = r.get("pillars") or {}
        br = {p: (pillars.get(p) or [None, None])[1] for p in
              ["year", "month", "day", "hour"]}
        pos_br = {}
        for p, b in br.items():
            if b:
                pos_br.setdefault(b, []).append(p)
        # 本气根紧贴 KE 且主体旺
        lc = r.get("l0_chart") or {}
        cmap_pairs = set()
        cm = lc.get("branch_clash_map") or {}
        ke_pairs = {("子", "午"), ("卯", "酉"), ("辰", "戌")}
        adj = False
        for a, b in ke_pairs:
            if a in pos_br and b in pos_br:
                for pa in pos_br[a]:
                    for pb in pos_br[b]:
                        if abs(["year", "month", "day", "hour"].index(pa)
                               - ["year", "month", "day", "hour"].index(pb)) == 1:
                            adj = True
        if not adj:
            continue
        l3c = r.get("l3_contract") or {}
        if not l3c.get("de_ling"):
            continue
        wp = ((f.get("wuxing_power") or {}).get("wuxing_power", {}) or {})
        dmrd = (wp.get(dm_wx, {}) or {}).get("root_detail", {}) or {}
        has_ben = any(v in ("BEN", "BEN_CS", "BEN_LU") for v in dmrd.values())
        if not has_ben:
            continue
        eng = "good" if not (r.get("bing_list") or []) else "bad"
        if c.get("label") == "bad" and eng == "good":
            mb = br["month"]
            print(" %s %s 月令%s de_ling=True 身根:%s | 断语: %s" % (
                c.get("case_id"), book, mb,
                {k2: v for k2, v in dmrd.items()},
                (c.get("raw") or c.get("analysis") or "")[:70].replace("\n", " ")))
