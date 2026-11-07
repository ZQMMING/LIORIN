# -*- coding: utf-8 -*-
"""6 盘六维逐盘核 —— DTS 原文断语 vs 引擎实跑"""
import sys, os, json
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

CASES = [
    ("DT-0029", "甲申甲戌甲寅甲戌",
     "年支申金冲去日主寅木; 戌土乘权重见生金助杀; 四甲一寅似乎强旺, "
     "第秋木休囚, 冲去禄神其根已拔, 不作旺论"),
    ("DT-0001", "辛卯丁酉庚午丙子",
     "支全四正气贯八方, 然五行无土, 虽诞秋令, 不作旺论"),
    ("DT-0021", "戊辰辛酉丙午癸巳",
     "此造旺财当令, 加以年上食神生助, 日逢时禄, 不为无根"),
    ("DT-0035", "癸巳丙辰丙午庚寅",
     "天干金水似乎无根, 喜月支辰土泄火蓄水而生金, 庚金挂角逢生, 则庚金可用"),
    ("DT-0044", "壬午己酉甲申甲子",
     "壬水坐午之绝地, 敌杀无力 (旺衰≠强弱)"),
    ("DT-0006", "丁亥庚戌甲辰壬申",
     "丁火虽弱, 通根身库, 戌乃燥土火之本根, 辰乃湿土"),
]
GAN_WX = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
          "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}


def main():
    for cid, bz, duan in CASES:
        r = paipan(bz)
        wp = (r.get("wuxing_power") or {}).get("wuxing_power") or {}
        lc = r.get("l3_contract") or (r.get("raw_facts") or {}).get("l3_contract") or {}
        dm = bz[4]
        dwx = GAN_WX[dm]
        d = wp.get(dwx) or {}
        print("=" * 96)
        print("★ %s  %s   日主=%s(%s)" % (cid, bz, dm, dwx))
        print("  原文断语: %s" % duan)
        print("  ── 六维 ──")
        print("  ① 月令 ling_state      = %r" % d.get("ling_state"))
        print("  ② 得地 root_grade       = %r" % lc.get("root_grade"))
        print("  ② 得地 ben_n/zhong/yu   = %s / %s / %s"
              % (d.get("ben_n"), d.get("zhong_n"), d.get("yu_n")))
        print("  ② 得地 root_detail      = %r" % d.get("root_detail"))
        print("  ② 得地 dm_ben_eff      = %r" % lc.get("dm_ben_eff"))
        print("  ③ 得势 support_state    = %r" % lc.get("support_state"))
        print("  ④ 通根 wpd[dm] ben_n    = %r" % d.get("ben_n"))
        print("  ⑥ 透干 stem_n           = %r" % d.get("stem_n"))
        cf = r.get("combination_facts") or (r.get("raw_facts") or {}).get("combination_facts") or {}
        print("  ⑤ 合冲 combination      = %r" % (cf if not isinstance(cf, dict)
                                            else {k: cf[k] for k in list(cf)[:8]}))
        print("  格局 ge_cheng           = %r" % (r.get("ge_cheng") or {}).get("ge"))
        print("  strength_verdict        = %r" % lc.get("strength_verdict"))


if __name__ == "__main__":
    main()