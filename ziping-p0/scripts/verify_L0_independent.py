# -*- coding: utf-8 -*-
"""L0 底层独立核验 —— 不读引擎表, 全部手算/古书原文常量

方法(按裁决要求, 不复用旧 check_L*.py):
  1) 藏干:权威值取自YHZP 原文十二月候诗诀眉批(用事日数) + 白话译文, 逐支手写常量
  2) 十神: 按五行生克 + 阴阳同性独立推导 10x10 全组合, 再与引擎跑值对
  3) 月令本气: 独立常量
  4) 旺相休囚死: 四时x五行 全 20 组独立推导
本脚本只 import 引擎做「被测对象」, 自己不复制引擎任何逻辑。
"""
import sys, os, json, itertools
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

# ============ 权威常量(来源: YHZP 渊海子平 原文 候诗诀眉批 / 白话译文) ============
# 格式: 支: [(干, 用事日数, 出处行)]
AUTH_CANG = {
    "子": [("癸", 23, "L10475 十一月壬吉, 壬水七日, 癸水二十三日")],
    "丑": [("己", 18, "L10512 己土十八日"), ("辛", 7, "辛金库七日"), ("癸", 5, "癸水五日")],
    "寅": [("甲", 22, "L10089 甲木二十二日"), ("丙", 5, "丁丙火生主五日"), ("戊", 3, "艮土生三日")],
    "卯": [("乙", None, "二月建卯候诗诀, 乙木专主卯位, 气性纯一(L4475)")],
    "辰": [("戊", 18, "L10179 戊土十八日"), ("乙", 7, "乙木七日"), ("癸", 5, "癸水五日")],
    "巳": [("丙", 22, "L10208 巳宫火旺二十二日"), ("庚", 5, "庚金生五日"), ("戊", 3, "戊土三日")],
    "午": [("丁", 22, "L10244 午月中丁火旺盛二十二日"), ("己", None, "诗诀: 财官印绶如藏午; 丑土虽可藏蓄")],
    "未": [("己", 18, "L10277 己土十八日"), ("丁", 7, "丁火七日"), ("乙", 5, "乙木五日")],
    "申": [("庚", 22, "L10309 庚金旺二十二日"), ("壬", 5, "壬水生五日"), ("戊", 2, "戊土二日")],
    "酉": [("辛", 23, "L10346 辛金二十三日"), ("庚", None, "白话: 辛金当令")],
    "戌": [("戊", 18, "L10388/L10395 戊土十八日"), ("辛", 7, "辛金七日"), ("丙", 5, "丙火库五日")],
    "亥": [("壬", 21, "L10432 壬水旺二十一日"), ("甲", 6, "甲木六日"), ("戊", 3, "乾金三日(戊)")],
}
AUTH_BEN_QI = {   # 月令本气 = 用事日数最长者
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
    "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬",
}
# 十神独立推导用(不读引擎)
GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
YANG = set("甲丙戊庚壬")
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}   # X生SHENG[X]
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}       # X克KE[X]


def ten_god(dm, other):
    """独立推导十神: 同我比劫/我生食伤/我克财/克我官杀/生我印。阴阳同性为偏/同。"""
    d, o = GAN_WX[dm], GAN_WX[other]
    same = (dm in YANG) == (other in YANG)
    if o == d:
        return "比肩" if same else "劫财"
    if SHENG[d] == o:
        return "食神" if same else "伤官"
    if KE[d] == o:
        return "偏财" if same else "正财"
    if KE[o] == d:
        return "七杀" if same else "正官"
    if SHENG[o] == d:
        return "偏印" if same else "正印"
    return "?"


def ling_state(month_wx, wx):
    """独立推导旺相休囚死 (《五行精纪》: 当令者旺, 我生者相, 生我者休, 克我者囚, 我克者死)。"""
    if wx == month_wx: return "旺"
    if SHENG[month_wx] == wx: return "相"
    if SHENG[wx] == month_wx: return "休"
    if KE[wx] == month_wx: return "囚"
    return "死"


def main():
    from engines.common.l0_fact_builder import build as l0build
    from p0_v2.bazi_gate import _pillars
    from spec.root_qi import BRANCH_CANGGAN        # 被测对象

    print("=" * 92)
    print("① L0 藏干表 独立核(权威: YHZP 候诗诀眉批, 不读引擎表)")
    print("=" * 92)
    bad = 0
    for z, auth in AUTH_CANG.items():
        eng = list(BRANCH_CANGGAN.get(z, ()))
        a_set = [g for g, _d, _s in auth]
        ok = (eng == a_set)
        if not ok: bad += 1
        print("  %s %-4s 权威=%-12s 引擎=%-12s  %s" % (
            z, "✓" if ok else "✗", ",".join(a_set), ",".join(eng),
            "" if ok else "★次序或成分不同"))
        if not ok:
            for g, d, src in auth:
                print("        权威依据: %s %s %s日" % (g, src[:40], d if d else "(无日)"))
    print("  -> 不符 %d/12" % bad)

    print("\n" + "=" * 92)
    print("② L0 月令本气 独立核")
    print("=" * 92)
    bad = 0
    for z, g in AUTH_BEN_QI.items():
        eng = BRANCH_CANGGAN.get(z, ("",))[0]
        ok = (eng == g)
        if not ok: bad += 1
        print("  %s %s 权威=%s 引擎=%s" % (z, "✓" if ok else "✗", g, eng))
    print("  -> 不符 %d/12" % bad)

    print("\n" + "=" * 92)
    print("③ L2 十神 10x10 全枚举 x 全仓全部 ten_god 实现(唯一性+正确性)")
    print("=" * 92)
    IMPLS = [
        ("l0_fact_builder", "engines.common.l0_fact_builder", "ten_god"),
        ("l0_paipan", "engines.l0_paipan", "ten_god"),
        ("ge_jie_layer", "engines.common.ge_jie_layer", "ten_god"),
        ("vendor_tongshu", "vendor.tongshu.reasoning.bazi_ten_gods", "ten_god"),
        ("legacy_pattern_routes", "archive.ziping_v3_legacy.pattern_routes", "ten_god_of"),
    ]
    import importlib
    for label, mod, fn in IMPLS:
        try:
            m = importlib.import_module(mod)
            f = getattr(m, fn)
        except Exception as e:
            print("  %-22s 导入失败: %s" % (label, str(e)[:60]))
            continue
        bad = []
        for dm, ot in itertools.product(GAN_WX, repeat=2):
            mine = ten_god(dm, ot)
            try:
                eng = f(dm, ot)
            except Exception as e:
                eng = "ERR:%s" % str(e)[:30]
            if mine != eng:
                bad.append((dm, ot, mine, eng))
        print("  %-22s 不符 %2d/100 %s" % (label, len(bad),
              ("" if not bad else "例:" + str(bad[:3]))))

    print("\n" + "=" * 92)
    print("④ L1 旺相休囚死 四时 x 五行 全 20 组(独立推导 vs 引擎实跑)")
    print("=" * 92)
    # 用真实四柱造出各月令各五行日主, 读引擎 ling_state
    from engines.common.wuxing_power import build_wuxing_power
    SEASON = {"木": "寅", "火": "午", "土": "辰", "金": "申", "水": "子"}
    bad = 0
    checked = 0
    for mw in ("木", "火", "土", "金", "水"):
        z = SEASON[mw]
        for wx, dmk in (("木", "甲"), ("火", "丙"), ("土", "戊"), ("金", "庚"), ("水", "壬")):
            p = _pillars("%s%s%s%s%s%s%s%s" % (dmk, dmk, dmk, dmk, dmk, z, dmk, dmk))
            f = l0build(p)
            wp = build_wuxing_power(p, f)
            wpd = wp.get("wuxing_power", wp)
            eng = (wpd.get(wx) or {}).get("ling_state")
            mine = ling_state(mw, wx)
            checked += 1
            if eng != mine:
                bad += 1
                print("  ✗ %s月令/%s: 独立=%s 引擎=%s" % (z, wx, mine, eng))
    print("  -> %d 组中不符 %d" % (checked, bad))


if __name__ == "__main__":
    main()