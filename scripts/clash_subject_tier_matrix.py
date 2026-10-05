# -*- coding: utf-8 -*-
"""clash_subject_tier (冲拔主体档) 六维矩阵。冲拔算子局部量, 不进顶层。
维: 月令位5 x 有效根7 x 扣冲拔4 x 党势3 x 财压2 x 天干帮身4 = 3360。"""
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


GEN_RANK = {g: 6 - i for i, g in enumerate(GEN_L)}


def compose(ling, gen, cb, dang, caiya, bang):
    """工程合成(ENGINE_DEFINED): 旺/中/衰。"""
    weak_ling = ling in ("囚", "死")
    strong_ling = ling in ("旺", "相")
    heavy_gen = gen in ("本气", "禄", "刃", "长生")
    gen_gone = (gen == "无") or (cb == "被冲拔")
    opp = (dang == "异党成势") or (caiya == "财重压身")
    tong = dang == "同党成势"
    if weak_ling and (gen_gone or not heavy_gen) and opp:
        return "衰"
    if strong_ling and heavy_gen and not gen_gone and not opp:
        return "旺"
    if weak_ling and gen_gone:
        return "衰"
    if strong_ling and heavy_gen and not gen_gone:
        return "旺"
    return "中"


cells = defaultdict(set)
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
        # 最强有效根 + 扣冲拔/合
        best = "无"; best_br = None; cb = "无"
        for p, b in br.items():
            g = gen_kind(b, dm_rd, tg.get(p))
            if GEN_RANK[g] > GEN_RANK[best]:
                best, best_br = g, b
        resolved = r.get("resolved") or {}
        if best_br:
            other = {"子": "午", "午": "子", "卯": "酉", "酉": "卯", "辰": "戌",
                     "戌": "辰", "寅": "申", "申": "寅", "巳": "亥", "亥": "巳",
                     "丑": "未", "未": "丑"}.get(best_br)
            if other and other in br.values():
                pa = [p for p, b in br.items() if b == best_br][0]
                pb = [p for p, b in br.items() if b == other][0]
                if abs(POS_L.index(pa) - POS_L.index(pb)) == 1:
                    cb = "被冲拔"
            # 被合
            hemap = lc.get("branch_he_map") or {}
            if cb == "无" and best_br in json.dumps(hemap, ensure_ascii=False):
                cb = "被合"
        # 党势: 比劫+印 combo vs 财+官杀+食伤
        def mass(wxs):
            return sum(int((wp.get(x, {}) or {}).get("ben_n", 0))
                       + int((wp.get(x, {}) or {}).get("stem_n", 0)) for x in wxs)
        sheng_me = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
        y = sheng_me[dm_wx]
        tong_m = mass([dm_wx, y])
        allw = ["木", "火", "土", "金", "水"]
        opp_m = sum(int((wp.get(x, {}) or {}).get("ben_n", 0))
                    + int((wp.get(x, {}) or {}).get("stem_n", 0)) for x in allw) - tong_m
        dang = "同党成势" if tong_m > opp_m + 1 else ("异党成势" if opp_m > tong_m + 1 else "平衡")
        # 财压: 我克者 combo 重
        cai = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}[dm_wx]
        caiw = wp.get(cai, {}) or {}
        cai_mass = int(caiw.get("ben_n", 0)) + int(caiw.get("stem_n", 0))
        shen_mass = int(dm.get("ben_n", 0)) + int(dm.get("stem_n", 0))
        caiya = "财重压身" if cai_mass > shen_mass + 1 else "无压"
        bang_n = int(dm.get("stem_n", 0))
        bang = "0" if bang_n == 0 else ("1" if bang_n == 1 else ("2" if bang_n == 2 else "3+"))
        tier = compose(ling, best, cb, dang, caiya, bang)
        key = (ling, best, cb, dang, caiya, bang)
        cells[key].add(c.get("case_id"))
        tier_dist[tier] += 1
        if c.get("case_id") in focus8:
            focus_dump.append((c.get("case_id"), key, tier))

# 完整笛卡尔积落 CSV
allkeys = list(itertools.product(LING_L, GEN_L, CHONGBA_L, DANG_L, CAIYA_L, BANG_L))
with open(os.path.join(ROOT, "scripts", "clash_subject_tier_matrix.csv"), "w",
          newline="", encoding="utf-8-sig") as fp:
    w = csv.writer(fp)
    w.writerow(["月令位", "有效根", "扣冲拔", "党势", "财压", "天干帮身", "盘数"])
    for k in allkeys:
        w.writerow(list(k) + [len(cells.get(k, []))])

filled = [k for k in cells]
print("clash_subject_tier 矩阵: 总=%d 有案例=%d 无=%d" %
      (len(allkeys), len(filled), len(allkeys) - len(filled)))
print("全量主体档分布:", dict(tier_dist))
print("\n=== 8 盘归位 ===")
for cid, key, tier in focus_dump:
    print(" %s | 月令%s 根%s %s %s %s 帮%s => %s" %
          (cid, key[0], key[1], key[2], key[3], key[4], key[5], tier))
