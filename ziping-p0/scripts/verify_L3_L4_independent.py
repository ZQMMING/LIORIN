# -*- coding: utf-8 -*-
"""L3/L4 底层独立核验 —— 不用旧 check_L*.py, 规则独立手写

核项(裁决 §五):
  ⑤ 有根/无根dm_ben_eff   独立手算: 日主本气在四支本气/中气/余气是否出现
  ⑥ 通根/根气分级root_grade 独立手算
  ⑦ 得势/失势 support_state
  ⑧ 旺/衰/中和strength_verdict (引擎现 NOT_AUTHORIZED —— 核是否仍空)
  ⑨ 反局 FAN_JU
  ⑩ 从格边界 cong_type
  ⑪ 月令权重字段是否存在
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

# 独立常量(不用引擎表)
GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
# 独立藏干: 本气(权重最高)/中气/余气。来源 BEN_QI_TOU.002 用事日数降序 + 歌诀成分
# 格式 支: [(干, 级别)] 级别 2=本气 1=中气 0=余气
CANG_LV = {
    "子": [("癸", 2)],
    "丑": [("己", 2), ("辛", 1), ("癸", 0)],
    "寅": [("甲", 2), ("丙", 1), ("戊", 0)],
    "卯": [("乙", 2)],
    "辰": [("戊", 2), ("乙", 1), ("癸", 0)],
    "巳": [("丙", 2), ("戊", 1), ("庚", 0)],
    "午": [("丁", 2), ("己", 1)],
    "未": [("己", 2), ("丁", 1), ("乙", 0)],
    "申": [("庚", 2), ("壬", 1), ("戊", 0)],
    "酉": [("辛", 2)],
    "戌": [("戊", 2), ("辛", 1), ("丁", 0)],
    "亥": [("壬", 2), ("甲", 1)],
}
LIU_CHONG = {("子", "午"), ("午", "子"), ("丑", "未"), ("未", "丑"),
             ("寅", "申"), ("申", "寅"), ("卯", "酉"), ("酉", "卯"),
             ("辰", "戌"), ("戌", "辰"), ("巳", "亥"), ("亥", "巳")}
BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]


def mine_ben_eff(dm, zhis):
    """独立手算 dm_ben_eff: 日主本气根的有效力(被冲/合局扣减)。
    返回 (ben_eff, ben_cnt, detail)
    规则(独立自写, 不读引擎):
      - 本气根(level2) 每处计 1
      - 中气根(level1) 每处计 1 但标 WEAK
      - 余气根(level0) 记为「有余气根」, 计 0(不入本气根力)
      - 冲: 若某支被对冲, 该支本气根被冲去(拉平)"""
    dwx = GAN_WX[dm]
    eff = 0
    cnt = 0
    detail = []
    for pos, z in enumerate(zhis):
        for g, lv in CANG_LV[z]:
            if GAN_WX[g] != dwx:
                continue
            # 裁决(2026-10-03): 本气根被冲【不拉平】—— 命理主流「冲不拔根, 只减力」,
            #   子午冲后子中癸水仍在, 只是受伤。故chong 不参与本气根计数。
            chong = any((z, zz) in LIU_CHONG for zz in zhis if zz != z)
            if lv == 2:
                eff += 1; cnt += 1
                detail.append((pos, z, g, "本气根" + ("(被冲, 不拔根)" if chong else "")))
            elif lv == 1:
                detail.append((pos, z, g, "中气根(弱)"))
            else:
                detail.append((pos, z, g, "余气根(不计)"))
    return eff, cnt, detail


def main():
    from p0_v2.bazi_gate import _pillars
    from engines.common.l0_fact_builder import build as l0build
    from engines.common.wuxing_power import build_wuxing_power
    from engines.common.daymaster_root_class import build_root_classes

    stat = collections.Counter()
    bad = []
    n = 0
    crash = 0
    samples = []
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
            dm = bz[4]   # 日柱天干在第5字符(bz[4]), 非bz[6](时干)
            zhis = [bz[1], bz[3], bz[5], bz[7]]
            mine, mcnt, mdet = mine_ben_eff(dm, zhis)
            try:
                p = _pillars(bz); f = l0build(p)
                wp = build_wuxing_power(p, f)
                wpd = wp.get("wuxing_power", wp)
                dwx = GAN_WX[dm]
                me = (wpd.get(dwx) or {}).get("ben_n")
            except Exception as e:
                crash += 1
                stat["崩溃"] += 1
                if len(bad) < 3:
                    bad.append((d["case_id"], bz, "崩溃 %s" % str(e)[:50]))
                continue
            if me is None:
                stat["引擎ben_n缺失"] += 1
                continue
            stat["已核"] += 1
            if int(me) == mine:
                stat["ben_n一致"] += 1
            else:
                stat["ben_n★不一致"] += 1
                if len(bad) < 8:
                    bad.append((d["case_id"], bz,
                                "引擎ben_n=%s 独立=%d 明细=%s" % (me, mine, mdet)))
            # 其他字段存在性
            for fld, cnt_key in (("root_grade", "root_grade"),
                                 ("strength_verdict", "strength_verdict"),
                                 ("support_state", "support_state")):
                if wpd.get(dwx, {}).get(fld) is not None:
                    stat["有" + cnt_key] += 1

    print("=" * 88)
    print("⑤ L3 有根/无根 dm_ben_eff 独立核   盘 %d  崩溃 %d" % (n, crash))
    print("=" * 88)
    print("  " + " | ".join("%s=%d" % (k, v) for k, v in sorted(stat.items())))
    print("\n  不符样本(最多8):")
    if not bad:
        print("    无")
    for c, b, m in bad:
        print("    %-9s %-17s %s" % (c, b, m))

    print("\n" + "=" * 88)
    print("⑥⑦⑧⑨⑩⑪ 字段存在性全量普查(不分盘)")
    print("=" * 88)
    from p0_v2.bazi_gate import paipan
    allp = []
    for bk in BOOKS:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if line.strip():
                dd = json.loads(line)
                bzz = (dd.get("bazi") or "").replace(" ", "")
                if len(bzz) == 8:
                    allp.append((bk, dd["case_id"], bzz))
    FIELDS = {
        "wp[dm].ben_n": lambda r: ((r.get("wuxing_power", {}).get("wuxing_power", {}) or {}).get(
            (r.get("wuxing_power", {}).get("daymaster_element") or "")) or {}).get("ben_n"),
        "wp[dm].root_grade": lambda r: ((r.get("wuxing_power", {}).get("wuxing_power", {}) or {}).get(
            (r.get("wuxing_power", {}).get("daymaster_element") or "")) or {}).get("root_grade"),
        "wp[dm].ling_state": lambda r: ((r.get("wuxing_power", {}).get("wuxing_power", {}) or {}).get(
            (r.get("wuxing_power", {}).get("daymaster_element") or "")) or {}).get("ling_state"),
        "strength_verdict": lambda r: r.get("strength_verdict") or (r.get("structure") or {}).get("comprehensive_verdict"),
        "support_state": lambda r: ((r.get("wuxing_power", {}).get("wuxing_power", {}) or {}).get(
            (r.get("wuxing_power", {}).get("daymaster_element") or "")) or {}).get("support_state"),
        "fan_ju": lambda r: r.get("fan_ju") or r.get("反局"),
        "cong_type": lambda r: (r.get("special") or {}).get("cong_type"),
        "ge_cheng": lambda r: r.get("ge_cheng"),
    }
    pres = collections.Counter()
    vals = collections.defaultdict(collections.Counter)
    for bk, cid, bzz in allp[:2106]:
        try:
            r = paipan(bzz)
        except Exception:
            continue
        for name, fn in FIELDS.items():
            try:
                v = fn(r)
            except Exception:
                v = None
            if v is None or (isinstance(v, (dict, list, str)) and len(v) == 0):
                pres[name + "=空"] += 1
            else:
                pres[name + "=有"] += 1
                if isinstance(v, str):
                    vals[name][v[:20]] += 1
                elif isinstance(v, dict) and "comprehensive_verdict" in v:
                    vals[name][str(v.get("comprehensive_verdict"))[:24]] += 1
    for name in FIELDS:
        print("  %-18s 有值 %5d   空/缺 %5d" % (
            name, pres[name + "=有"], pres[name + "=空"]))
        if vals[name]:
            print("      取值: %s" % ", ".join("%s=%d" % (k, v)
                                             for k, v in vals[name].most_common(6)))


if __name__ == "__main__":
    main()