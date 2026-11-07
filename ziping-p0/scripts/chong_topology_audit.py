# -*- coding: utf-8 -*-
"""得地层·冲拔拓扑全量普查。六冲对全枚举 × 六维分类 × 断语对照。
只产出事实矩阵/明细, 不改判定。"""
import sys, os, json
ROOT = r"D:/shuntian-ziping-p0"; sys.path.insert(0, ROOT)
from p0_v2.bazi_gate import paipan

CANG = {"子": ["癸"], "丑": ["己", "辛", "癸"], "寅": ["甲", "丙", "戊"],
        "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "戊", "庚"],
        "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
        "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"]}
GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
SHENG_ME = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
BRANCH_WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火',
             '午': '火', '申': '金', '酉': '金', '辰': '土', '戌': '土',
             '丑': '土', '未': '土'}
POS = {"year": 0, "month": 1, "day": 2, "hour": 3}
POSN = {0: "年", 1: "月", 2: "日", 3: "时"}
CHONG_PAIR = [("子", "午"), ("丑", "未"), ("寅", "申"),
              ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]
CHONG_OF = {}
for a, b in CHONG_PAIR:
    CHONG_OF[a] = b; CHONG_OF[b] = a


def clash_kind(a, b):
    if BRANCH_WX[a] == BRANCH_WX[b]:
        return "KE"
    A = {GAN_WX[g] for g in CANG[a]}; B = {GAN_WX[g] for g in CANG[b]}
    sheng = any(SHENG.get(x) == y or SHENG.get(y) == x for x in A for y in B)
    ke = any(KE.get(x) == y or KE.get(y) == x for x in A for y in B)
    if sheng and ke:
        return "MIX"
    return "SHENG" if sheng else "KE"


def root_pos_of(br, dm_wx, rwc_branch_class, dm_root_detail):
    """日主在该支的根位类型。"""
    tag = dm_root_detail.get(br)
    cls = rwc_branch_class.get(br)
    if not tag:
        return "无"
    if tag in ("BEN", "BEN_LU", "BEN_CS"):
        return "本气/禄"
    if cls == "HEAVY":
        return "长生/刃"
    if cls == "LIGHT":
        return "墓库/余气"
    return tag


records = []
for book in ["DTS", "PZZQ", "QTBJ", "SFTK", "SMTH", "YHZP"]:
    for l in open(os.path.join(ROOT, "p0_v2", "case_audit", book + "_clean.jsonl"),
                  encoding="utf-8-sig"):
        c = json.loads(l); bz = (c.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        r = paipan(bz); f = r.get("raw_facts") or {}
        dm_wx = f.get("daymaster_element", "")
        pillars = r.get("pillars") or {}
        br_by_pos = {p: (pillars.get(p) or [None, None])[1] for p in POS}
        pos_by_br = {}
        for p, b in br_by_pos.items():
            if b:
                pos_by_br.setdefault(b, []).append(p)
        # 六冲列表
        lc = r.get("l0_chart") or {}
        cmap = lc.get("branch_clash_map") or {}
        rwc = {(_v or {}).get("branch"): (_v or {}).get("class")
               for _v in (r.get("root_weight_class") or {}).values()}
        wp = ((f.get("wuxing_power") or {}).get("wuxing_power", {}) or {})
        dm_rd = ((wp.get(dm_wx, {}) or {}).get("root_detail", {}) or {})
        yin_wx = SHENG_ME.get(dm_wx, "")
        yin = wp.get(yin_wx, {}) or {}
        resolved = r.get("resolved") or {}
        removed = set((f.get("special_pattern") or {}).get("root_removed_branches") or [])
        eng = "good" if not (r.get("bing_list") or []) else "bad"
        # 逐冲对
        seen = set()
        for a, b in CHONG_PAIR:
            if a in pos_by_br and b in pos_by_br:
                for pa in pos_by_br[a]:
                    for pb in pos_by_br[b]:
                        key = tuple(sorted([pa, pb]))
                        if key in seen:
                            continue
                        seen.add(key)
                        dist = abs(POS[pa] - POS[pb])
                        dl = "紧贴" if dist == 1 else ("隔一" if dist == 2 else "遥隔")
                        kind = clash_kind(a, b)
                        ra = root_pos_of(a, dm_wx, rwc, dm_rd)
                        rb = root_pos_of(b, dm_wx, rwc, dm_rd)
                        hits_dm = (ra != "无") or (rb != "无")
                        # 相生神力量(混合)
                        yben = int(yin.get("ben_n", 0))
                        yz = int(yin.get("zhong_n", 0)) + int(yin.get("yu_n", 0))
                        ystem = int(yin.get("stem_n", 0)); yling = yin.get("ling_state", "")
                        supp = yben >= 1 or (yling in ("相", "旺") and yz >= 1) \
                            or (ystem >= 1 and yz >= 1)
                        records.append({
                            "cid": c.get("case_id"), "book": book,
                            "label": c.get("label"), "eng": eng,
                            "pair": a + b, "pos": POSN[POS[pa]] + POSN[POS[pb]],
                            "dist": dl, "kind": kind,
                            "rootA": ra, "rootB": rb, "hits_dm": hits_dm,
                            "removed": sorted(removed), "supp": supp,
                            "resolved": json.dumps(resolved, ensure_ascii=False)[:120],
                        })

# 明细落盘
with open(os.path.join(ROOT, "scripts", "chong_matrix_detail.json"), "w",
          encoding="utf-8") as fp:
    json.dump(records, fp, ensure_ascii=False, indent=1)

# 汇总
from collections import Counter
print("涉六冲记录数=%d (盘可能多处)" % len(records))
print("\n冲对类型:", dict(Counter(x["kind"] for x in records)))
print("距离:", dict(Counter(x["dist"] for x in records)))
print("冲对:", dict(Counter(x["pair"] for x in records)))
print("涉日主根的冲=%d" % sum(1 for x in records if x["hits_dm"]))
print("\n=== 身根支参与冲 且 label!=eng (冲拔疑似分歧) ===")
bad = [x for x in records if x["hits_dm"] and x["label"] in ("good", "bad")
       and x["label"] != x["eng"]]
print("数量=%d" % len(bad))
for x in bad:
    print(" %s %s %s %s 根:%s/%s kind=%s supp=%s removed=%s label=%s eng=%s" % (
        x["cid"], x["book"], x["pair"], x["pos"], x["rootA"], x["rootB"],
        x["kind"], x["supp"], x["removed"], x["label"], x["eng"]))
