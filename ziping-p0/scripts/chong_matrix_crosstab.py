# -*- coding: utf-8 -*-
"""读 chong_matrix_detail.json, 按盘去重, 出 根位档×距离×kind 交叉矩阵。"""
import sys, os, json
from collections import defaultdict
ROOT = r"D:/shuntian-ziping-p0"
recs = json.load(open(os.path.join(ROOT, "scripts", "chong_matrix_detail.json"),
                      encoding="utf-8"))

ROOT_RANK = {"本气/禄": 3, "长生/刃": 2, "墓库/余气": 1, "无": 0}
DIST_RANK = {"紧贴": 3, "隔一": 2, "遥隔": 1}

# 每盘聚合: 取"最强身根被冲"的那处(根位档最高, 其次距离最近)
by_cid = defaultdict(list)
for x in recs:
    if x["hits_dm"]:
        by_cid[x["cid"]].append(x)

cell = defaultdict(lambda: [0, 0, 0])  # key -> [漏(bad,good), 误(good,bad), 一致分歧?]
meta = {}
for cid, xs in by_cid.items():
    def keyf(x):
        r = max(ROOT_RANK[x["rootA"]], ROOT_RANK[x["rootB"]])
        return (r, DIST_RANK[x["dist"]])
    x = max(xs, key=keyf)
    r = max(ROOT_RANK[x["rootA"]], ROOT_RANK[x["rootB"]])
    root_lbl = {3: "本气/禄", 2: "长生/刃", 1: "墓库/余气"}[r]
    k = (root_lbl, x["dist"], x["kind"])
    meta[cid] = (k, x["label"], x["eng"], x["book"])
    if x["label"] == "bad" and x["eng"] == "good":
        cell[k][0] += 1   # 漏: 根被冲引擎没拔
    elif x["label"] == "good" and x["eng"] == "bad":
        cell[k][1] += 1   # 误: 根被冲引擎拔了/报病
    else:
        cell[k][2] += 1   # 该格一致(含非goodbad)

print("涉身根被冲的盘数(去重)=%d" % len(by_cid))
print("\n根位档 | 距离 | kind | 漏(bad引擎good) | 误(good引擎bad) | 一致")
print("-" * 78)
for k in sorted(cell, key=lambda z: (ROOT_RANK[z[0]], -DIST_RANK[z[1]], z[2])):
    l, w, ok = cell[k]
    print(" %-8s %-4s %-4s | 漏=%-3d 误=%-3d 一致=%-3d" % (k[0], k[1], k[2], l, w, ok))
