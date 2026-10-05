# -*- coding: utf-8 -*-
"""clash_subject_tier v2: 多根分别判冲拔(校准点1,结构性); 得令反弱只落原则,
阈值(有效重根<=1且财压/异党)全355格核断语支持度(校准点2)。"""
import sys, os, json, itertools, csv
from collections import defaultdict
ROOT = r"D:/shuntian-ziping-p0"; sys.path.insert(0, ROOT)
from p0_v2.bazi_gate import paipan

KU = {"辰", "戌", "丑", "未"}
POS_L = ["year", "month", "day", "hour"]
LING_L = ["旺", "相", "休", "囚", "死"]
GEN_L = ["本气", "禄", "刃", "长生", "墓库", "余气", "无"]
CHONGBA_L = ["被冲拔", "被合", "被克", "无"]
DANG_L = ["同党成势", "异党成势", "平衡"]
CAIYA_L = ["财重压身", "无压"]
BANG_L = ["0", "1", "2", "3+"]
HEAVY = {"本气", "禄", "刃", "长生"}
GEN_RANK = {g: 6 - i for i, g in enumerate(GEN_L)}
CLASH_OTHER = {"子": "午", "午": "子", "卯": "酉", "酉": "卯", "辰": "戌",
               "戌": "辰", "寅": "申", "申": "寅", "巳": "亥", "亥": "巳",
               "丑": "未", "未": "丑"}
WEAK_KW = ["弱", "衰", "孤", "贫", "夭", "不能托", "无根", "身轻", "绝", "枯"]


def gen_kind(br, dm_rd, tg):
    t = dm_rd.get(br)
    if t in ("BEN", "BEN_CS"):
        return "本气"
    if t == "BEN_LU":
        return "禄"
    if t in ("ZHONG", "YU"):
        if tg == "帝旺":
            return "刃"
        if tg == "长生":
            return "长生"
        return "墓库" if br in KU else "余气"
    return "无"


def compose(ling, eff_heavy, dang, caiya):
    opp = dang == "异党成势" or caiya == "财重压身"
    if eff_heavy == 0:
        return "衰"                      # 重根全被冲拔 L139
    if ling in ("囚", "死") and eff_heavy <= 1 and opp:
        return "衰"
    if ling in ("旺", "相"):
        if eff_heavy <= 1 and opp:
            return "衰"                  # 校准点2 阈值(全格核)
        if eff_heavy >= 2 and caiya == "无压":
            return "旺"
        if eff_heavy >= 1:
            return "旺"
    return "中"


cells = defaultdict(list)
tier_dist = defaultdict(int)
focus8 = ["DT-0256", "DT-0280", "DT-0407", "PZ-0114", "QT-0121",
          "QT-0348", "SM-0050", "YH-0180"]
focus_dump = []
for book in ["DTS", "PZZQ", "QTBJ", "SFTK", "SMTH", "YHZP"]:
    for l in open(os.path.join(ROOT, "p0_v2", "case_audit", book + "_clean.jsonl"),
                  encoding="utf-8-sig"):
        c = json.loads(l); bz = (c.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        r = paipan(bz); f = r.get("raw_facts") or {}
        dm_wx = f.get("daymaster_element", "")
        pillars = r.get("pillars") or {}
        br = {p: (pillars.get(p) or [None, None])[1] for p in POS_L}
        lc = r.get("l0_chart") or {}
        tg = lc.get("twelve_growth") or {}
        wp = ((f.get("wuxing_power") or {}).get("wuxing_power", {}) or {})
        dm = wp.get(dm_wx, {}) or {}
        ling = dm.get("ling_state", "休")
        dm_rd = dm.get("root_detail", {}) or {}
        # === 校准点1: 逐根分别判冲拔/合, 聚合有效重根数 ===
        eff_heavy = 0; cb_state = "无"; best_survive = "无"
        for p, b in br.items():
            g = gen_kind(b, dm_rd, tg.get(p))
            if g == "无":
                continue
            struck = False
            o = CLASH_OTHER.get(b)
            if o and o in br.values():
                po = [q for q, x in br.items() if x == o][0]
                if abs(POS_L.index(p) - POS_L.index(po)) == 1:
                    struck = True
            if struck:
                cb_state = "被冲拔"
                continue
            if g in HEAVY:
                eff_heavy += 1
                if GEN_RANK[g] > GEN_RANK[best_survive]:
                    best_survive = g
        if cb_state != "被冲拔":
            hej = json.dumps(lc.get("branch_he_map") or {}, ensure_ascii=False)
            if any(b and b in hej for b in br.values()):
                cb_state = "被合"
        # 党势
        sm = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[dm_wx]
        def mass(x):
            v = wp.get(x, {}) or {}
            return int(v.get("ben_n", 0)) + int(v.get("stem_n", 0))
        tong_m = mass(dm_wx) + mass(sm)
        totm = sum(mass(x) for x in ["木", "火", "土", "金", "水"])
        opp_m = totm - tong_m
        dang = "同党成势" if tong_m > opp_m + 1 else (
            "异党成势" if opp_m > tong_m + 1 else "平衡")
        cai = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}[dm_wx]
        cm = mass(cai); shen = mass(dm_wx)
        caiya = "财重压身" if cm > shen + 1 else "无压"
        bang_n = int(dm.get("stem_n", 0))
        bang = "0" if bang_n == 0 else ("1" if bang_n == 1 else
                                        ("2" if bang_n == 2 else "3+"))
        tier = compose(ling, eff_heavy, dang, caiya)
        key = (ling, best_survive, cb_state, dang, caiya, bang)
        text = (c.get("raw") or c.get("analysis") or "")
        cells[key].append((c.get("case_id"), tier, text, c.get("label")))
        tier_dist[tier] += 1
        if c.get("case_id") in focus8:
            focus_dump.append((c.get("case_id"), ling, eff_heavy, cb_state,
                               dang, caiya, tier))

# 矩阵落 CSV + 阈值全格核
allkeys = list(itertools.product(LING_L, GEN_L, CHONGBA_L, DANG_L, CAIYA_L, BANG_L))
thresh_rows = []
with open(os.path.join(ROOT, "scripts", "clash_subject_tier_matrix_v2.csv"), "w",
          newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["月令位", "有效根", "扣冲拔", "党势", "财压", "天干帮身",
                "盘数", "降衰数", "断语支持", "断语反对"])
    for k in allkeys:
        items = cells.get(k, [])
        if not items:
            w.writerow(list(k) + [0, 0, 0, 0]); continue
        jiang = [x for x in items if x[1] == "衰"]
        sup = sum(1 for x in jiang if any(w0 in x[2] for w0 in WEAK_KW))
        w.writerow(list(k) + [len(items), len(jiang), sup, len(jiang) - sup])
        # 阈值核: 月令旺相格 且 有降衰
        if k[0] in ("旺", "相") and jiang:
            thresh_rows.append((k, len(items), len(jiang), sup, len(jiang) - sup))

print("v2 主体档分布:", dict(tier_dist))
print("\n=== 8 盘归位 v2 ===")
for cid, ling, eh, cb, dang, caiya, tier in focus_dump:
    print(" %s 月令%s 有效重根%d %s %s %s => %s" %
          (cid, ling, eh, cb, dang, caiya, tier))
print("\n=== 校准点2 阈值全格核 (月令旺相且降衰的格) ===")
for k, n, j, sup, opp in sorted(thresh_rows, key=lambda x: -x[2]):
    print(" %s 盘%d 降衰%d 断语支持%d 反对%d %s" %
          (k, n, j, sup, opp, "✓" if opp == 0 else "✗反例"))
