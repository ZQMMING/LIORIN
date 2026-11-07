# -*- coding: utf-8 -*-
"""得地层·冲拔完整六维规则矩阵。笛卡尔积全枚举, 逐盘归类, 全格落CSV(含无案例)。
维: kind(3) x 根位(6) x 距离(4) x 合解(4) x 主体旺衰(3) x 相生神(3) = 2592。"""
import sys, os, json, itertools, csv
from collections import defaultdict
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
KU = {"辰", "戌", "丑", "未"}
POS = {"year": 0, "month": 1, "day": 2, "hour": 3}
POSN = {0: "年", 1: "月", 2: "日", 3: "时"}
CHONG_PAIR = [("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"),
              ("辰", "戌"), ("巳", "亥")]
CHONG_OF = {}
for a, b in CHONG_PAIR:
    CHONG_OF[a] = b; CHONG_OF[b] = a

KIND_L = ["纯相生", "纯相克", "混合"]
ROOT_L = ["本气", "禄", "刃", "长生", "墓库", "余气"]
DIST_L = ["同柱", "紧贴", "隔一", "遥隔"]
HE_L = ["无解", "六合解", "三会解", "刑合"]
ZHUANG_L = ["旺", "中", "衰"]
SUPP_L = ["有力", "无力", "NA"]


def clash_kind(a, b):
    if BRANCH_WX[a] == BRANCH_WX[b]:
        return "纯相克"
    A = {GAN_WX[g] for g in CANG[a]}; B = {GAN_WX[g] for g in CANG[b]}
    s = any(SHENG.get(x) == y or SHENG.get(y) == x for x in A for y in B)
    k = any(KE.get(x) == y or KE.get(y) == x for x in A for y in B)
    if s and k:
        return "混合"
    return "纯相生" if s else "纯相克"


def root_kind(br, dm_rd, tg_state):
    tag = dm_rd.get(br)
    if tag in ("BEN", "BEN_CS"):
        return "本气"
    if tag == "BEN_LU":
        return "禄"
    if tag in ("ZHONG", "YU"):
        if tg_state == "帝旺":
            return "刃"
        if tg_state == "长生":
            return "长生"
        if br in KU:
            return "墓库"
        return "余气"
    return None


cells = defaultdict(lambda: {"cids": set(), "lou": 0, "wu": 0, "ok": 0})
for book in ["DTS", "PZZQ", "QTBJ", "SFTK", "SMTH", "YHZP"]:
    for l in open(os.path.join(ROOT, "p0_v2", "case_audit", book + "_clean.jsonl"),
                  encoding="utf-8-sig"):
        c = json.loads(l); bz = (c.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        r = paipan(bz); f = r.get("raw_facts") or {}
        dm_wx = f.get("daymaster_element", "")
        pillars = r.get("pillars") or {}
        br_pos = {p: (pillars.get(p) or [None, None])[1] for p in POS}
        pos_br = {}
        for p, b in br_pos.items():
            if b:
                pos_br.setdefault(b, []).append(p)
        lc = r.get("l0_chart") or {}
        tg = lc.get("twelve_growth") or {}
        tg_by_pos = {p: tg.get(p) for p in POS}
        wp = ((f.get("wuxing_power") or {}).get("wuxing_power", {}) or {})
        dm_rd = (wp.get(dm_wx, {}) or {}).get("root_detail", {}) or {}
        yin_wx = SHENG_ME.get(dm_wx, "")
        yin = wp.get(yin_wx, {}) or {}
        yben = int(yin.get("ben_n", 0))
        yz = int(yin.get("zhong_n", 0)) + int(yin.get("yu_n", 0))
        ystem = int(yin.get("stem_n", 0)); yling = yin.get("ling_state", "")
        supp = "有力" if (yben >= 1 or (yling in ("相", "旺") and yz >= 1)
                         or (ystem >= 1 and yz >= 1)) else "无力"
        # 主体旺衰
        l3c = r.get("l3_contract") or {}
        if l3c.get("de_ling"):
            zhuang = "旺"
        elif (l3c.get("support_state") or "") == "SHENG_FU_CHENG_SHI":
            zhuang = "中"
        else:
            zhuang = "衰"
        resolved = r.get("resolved") or {}
        canceled = {tuple(x.get("pair", [])) for x in
                    resolved.get("chong_canceled", []) if isinstance(x, dict)}
        xinghe = {tuple(x) for x in resolved.get("xinghe", [])}
        eng = "good" if not (r.get("bing_list") or []) else "bad"
        for a, b in CHONG_PAIR:
            if a in pos_br and b in pos_br:
                for pa in pos_br[a]:
                    for pb in pos_br[b]:
                        d = abs(POS[pa] - POS[pb])
                        dist = "紧贴" if d == 1 else ("隔一" if d == 2 else "遥隔")
                        kind = clash_kind(a, b)
                        rka = root_kind(a, dm_rd, tg_by_pos.get(pa))
                        rkb = root_kind(b, dm_rd, tg_by_pos.get(pb))
                        rk = rka or rkb
                        if not rk:
                            continue  # 非身根支
                        # 合解状态
                        pair_t = (a, b)
                        he = "刑合" if pair_t in xinghe or (b, a) in xinghe else "无解"
                        if pair_t in canceled or (b, a) in canceled:
                            he = "六合解"  # 简化, 三会/六合细分待 resolved 标注
                        sp = "NA" if kind == "纯相克" else supp
                        key = (kind, rk, dist, he, zhuang, sp)
                        g = cells[key]
                        g["cids"].add(c.get("case_id"))
                        if c.get("label") == "bad" and eng == "good":
                            g["lou"] += 1
                        elif c.get("label") == "good" and eng == "bad":
                            g["wu"] += 1
                        else:
                            g["ok"] += 1

# 完整笛卡尔积落 CSV
allkeys = list(itertools.product(KIND_L, ROOT_L, DIST_L, HE_L, ZHUANG_L, SUPP_L))
with open(os.path.join(ROOT, "scripts", "chong_full_matrix.csv"), "w",
          newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["kind", "根位", "距离", "合解", "主体旺衰", "相生神",
                "盘数", "漏", "误", "一致", "有案例"])
    for k in allkeys:
        g = cells.get(k)
        if g:
            w.writerow(list(k) + [len(g["cids"]), g["lou"], g["wu"], g["ok"], 1])
        else:
            w.writerow(list(k) + [0, 0, 0, 0, 0])

filled = [k for k in cells]
print("完整矩阵格数=%d, 有案例格=%d, 无案例格=%d" %
      (len(allkeys), len(filled), len(allkeys) - len(filled)))
print("\n=== 有案例且漏/误>0 的格 (按 漏+误 排序) ===")
for k in sorted(filled, key=lambda z: -(cells[z]["lou"] + cells[z]["wu"])):
    g = cells[k]
    if g["lou"] + g["wu"] > 0:
        print(" %s %s %s %s %s %s | 盘=%d 漏=%d 误=%d 一致=%d" %
              (k[0], k[1], k[2], k[3], k[4], k[5],
               len(g["cids"]), g["lou"], g["wu"], g["ok"]))
