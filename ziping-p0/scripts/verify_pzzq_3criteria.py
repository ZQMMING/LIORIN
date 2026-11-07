# -*- coding: utf-8 -*-
"""PZZQ 三条强弱判据 —— 独立手算 vs 引擎 l3_contract 值

判据全部取 PZZQ 沈孝瞻正文, 不看引擎实现:
  判据1 L765-L769「党众为强, 助寡为弱」:
      比劫印绶为党众。春木夏火秋金冬水为得时。
      「干庚辛而支酉丑, 则金之党众, 而木之助寡」 -> 党众=同党五行计数, 助寡=异党
  判据2 L770-L774「四柱有根便能受财官食神」+ 根之轻重:
      重根 = 长生/禄/帝旺; 轻根 = 墓库/余气
      「天干得一比肩, 不如得支中一墓库(甲逢未、丙逢戌)」
      「得三比肩, 不如得一长生禄刃(甲逢亥子寅卯)」
      「阴长生不作此论(乙逢午、丁逢酉), 然亦为明根, 可比得一余气」
      「乙逢戌、丁逢丑, 不作此论, 以戌中无藏木, 丑中无藏火也」
  判据3 L2018 徐注「日临四库, 如壬辰丙戌均作通根身库。若丙辰壬戌, 即非为身库也」:
      阳干 + 自己本命库 = 身库通根 (壬辰水库/丙戌火库/甲未木库/庚丑金库)
      阴干或非本命库 -> 不作身库

本脚本不 import引擎任何判定逻辑, 只读 l3_contract 的值做比对。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
YANG = set("甲丙戊庚壬")
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
# 藏干成分(成分表, 不含次序)
CANG = {"子": ["癸"], "丑": ["己", "辛", "癸"], "寅": ["甲", "丙", "戊"],
        "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "戊", "庚"],
        "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
        "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"]}
CHANG_SHENG = {"亥": "木", "子": "水", "寅": "木", "卯": "木", "巳": "火",
               "午": "火", "申": "金", "酉": "金", "亥水": "水"}
# PZZQ 本气(孟)定位
BEN = {"子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
       "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬"}
# 各干的 本气/长生/禄/墓库
LU = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
      "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
MU_KU = {"甲": "未", "丙": "戌", "戊": "丑", "庚": "丑", "壬": "辰"}   # 阳干本命库
CHANG_SHENG_ZHI = {   # 十二长生 阳干
    "甲": {"长生": "亥", "沐浴": "子", "冠带": "丑", "临官": "寅", "帝旺": "卯"},
    "丙": {"长生": "寅", "帝旺": "午"}, "戊": {"长生": "寅", "帝旺": "午"},
    "庚": {"长生": "巳", "帝旺": "酉"}, "壬": {"长生": "申", "帝旺": "子"},
}
BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]


def judge1(dm, zhis, stems):
    """判据1 党众为强, 助寡为弱。返回 (同党数, 异党数, 方向)
    同党 = 比劫(日主五行) + 印(生日主)
    异党 = 食伤(生我) + 财(我生) + 官杀(克我)"""
    dwx = GAN_WX[dm]
    yin = SHENG_WO = [k for k, v in SHENG.items() if v == dwx][0]
    tong, yi = 0, 0
    for z in zhis:
        for g in CANG[z]:
            wx = GAN_WX[g]
            if wx == dwx or wx == yin:
                tong += 1
            else:
                yi += 1
    for g in stems:
        wx = GAN_WX[g]
        if g == dm:
            continue
        if wx == dwx or wx == yin:
            tong += 1
        else:
            yi += 1
    return tong, yi, ("党众" if tong > yi else ("助寡" if yi > tong else "均衡"))


def judge2(dm, zhis):
    """判据2 根之轻重。重根=长生/禄/帝旺; 轻根=墓库/余气。
    阴干长生不作此论(但仍为明根, 可比一余气); 阴干逢非本命库不作通根论。
    返回 (重根数, 轻根数, 说明)"""
    dwx = GAN_WX[dm]
    yang = dm in YANG
    zhong, qing = 0, 0
    notes = []
    for z in zhis:
        gs = [g for g in CANG[z] if GAN_WX[g] == dwx]
        if not gs:
            continue
        is_lu = (z == LU.get(dm))
        is_changsheng = yang and (CHANG_SHENG_ZHI.get(dm, {}).get("长生") == z)
        is_diwang = yang and (CHANG_SHENG_ZHI.get(dm, {}).get("帝旺") == z)
        is_ku = (z == MU_KU.get(dm))
        if is_lu or is_changsheng or is_diwang:
            zhong += 1; notes.append((z, gs[0], "重根"))
        elif is_ku:
            qing += 1; notes.append((z, gs[0], "轻根-身库" if yang else "轻根"))
        elif z == BEN[z]:
            zhong += 1; notes.append((z, gs[0], "重根-本气"))
        else:
            qing += 1; notes.append((z, gs[0], "轻根-余气"))
    return zhong, qing, notes


def judge3(dm, zhis):
    """判据3 阳干逢本命库=通根身库; 阴干/非本命库 不作身库。
    返回 (是否身库, 库支或None)"""
    k = MU_KU.get(dm)
    if not k:
        return False, None
    return (k in zhis), k


def main():
    from p0_v2.bazi_gate import paipan
    stat = collections.Counter()
    bad1, bad2, bad3 = [], [], []
    n = 0
    rg_vals = collections.Counter()
    ss_vals = collections.Counter()
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
            dm = bz[4]
            zhis = [bz[1], bz[3], bz[5], bz[7]]
            stems = [bz[0], bz[2], bz[4], bz[6]]
            try:
                r = paipan(bz)
            except Exception:
                stat["崩溃"] += 1
                continue
            lc = (r.get("l3_contract") or (r.get("raw_facts") or {}).get("l3_contract")) or {}
            rg = lc.get("root_grade")
            ss = lc.get("support_state")
            rg_vals[str(rg)] += 1
            ss_vals[str(ss)] += 1
            if not lc:
                stat["★无 l3_contract"] += 1
                if len(bad1) < 5:
                    bad1.append((d["case_id"], bz, "无 l3_contract"))
                continue
            stat["已核"] += 1
            # 判据1
            t, y, d1 = judge1(dm, zhis, stems)
            eng_ss = {"SHENG_FU_CHENG_SHI": "党众", "KE_XIE_CHENG_SHI": "助寡",
                      "PINGHENG": "均衡"}.get(ss, ss)
            if eng_ss != d1:
                stat["判据1★不符"] += 1
                if len(bad1) < 8:
                    bad1.append((d["case_id"], bz, "同党%d异党%d 手算=%s 引擎=%s" % (t, y, d1, eng_ss)))
            else:
                stat["判据1一致"] += 1
            # 判据2
            z_, q_, notes = judge2(dm, zhis)
            mine2 = "无根" if (z_ == 0 and q_ == 0) else ("重根" if z_ > 0 else "轻根")
            eng2 = {"本": "重根", "余": "轻根", "无": "无根"}.get(rg, str(rg))
            if eng2 != mine2:
                stat["判据2★不符"] += 1
                if len(bad2) < 8:
                    bad2.append((d["case_id"], bz, "重%d轻%d 手算=%s 引擎=%s 明细=%s"
                                 % (z_, q_, mine2, eng2, notes)))
            else:
                stat["判据2一致"] += 1
            # 判据3
            sk, kz = judge3(dm, zhis)
            if sk:
                stat["判据3-有身库"] += 1
            else:
                stat["判据3-无身库"] += 1

    print("=" * 92)
    print("PZZQ 三条判据独立核   盘 %d" % n)
    print("=" * 92)
    print("  " + " | ".join("%s=%d" % (k, v) for k, v in sorted(stat.items())))
    print("\n  引擎 root_grade 取值: %s" % dict(rg_vals))
    print("  引擎 support_state  : %s" % dict(ss_vals))
    for tag, lst in (("判据1 党众为强助寡为弱", bad1), ("判据2 根之轻重", bad2)):
        print("\n  %s 不符(最多8): %d" % (tag, len(lst)))
        for c, b, m in lst:
            print("    %-9s %-17s %s" % (c, b, m))


if __name__ == "__main__":
    main()