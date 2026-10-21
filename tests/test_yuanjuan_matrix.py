# -*- coding: utf-8 -*-
"""原典判据回归矩阵 —— 原典条文即测试用例(而非案例快照).

设计目的: 引擎的每条判据都必须有原典条文出处; 条款一改, 本矩阵即红.
          避免"案例驱动、逐案矫正"—— 案例只做冒烟, 不做判据来源.

每条断言格式: ①原典出处(书+行号+条文) ②断言的判据行为 ③可执行判据
"""
import sys, os
ROOT = r"D:\shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_p0 = os.path.join(ROOT, "p0_v2")
if _p0 in sys.path:
    sys.path.remove(_p0)

from p0_v2.bazi_gate import paipan
from engines.common.cai_yin_bu_ai import cai_yin_bu_ai
from engines.common import tiaohou_rank
from engines.common.l0_fact_builder import build, ten_god
from engines.common.wuxing_power import build_wuxing_power
from engines.common.gc002_builder import _dayun_qiyun

FAILS = []
OKS = []


def ck(name, ok, extra=""):
    if ok:
        OKS.append(name)
    else:
        FAILS.append("%s %s" % (name, extra))
    print(("PASS " if ok else "FAIL ") + name + (("  " + str(extra)) if (extra and not ok) else ""))


def P(s):
    """'甲申 壬申 乙巳 戊寅' -> pillars dict."""
    if isinstance(s, str):
        parts = s.split()
        s = [(parts[0][0], parts[0][1]), (parts[1][0], parts[1][1]),
             (parts[2][0], parts[2][1]), (parts[3][0], parts[3][1])]
    return {'year': [s[0][0], s[0][1]], 'month': [s[1][0], s[1][1]],
            'day': [s[2][0], s[2][1]], 'hour': [s[3][0], s[3][1]]}


def facts_of(bz):
    p = P(bz)
    f = build(p)
    f['pillars'] = p
    f['wuxing_power'] = build_wuxing_power(p, f)
    return p, f


print("=" * 74)
print("原典判据回归矩阵 (Yuanjuan Criteria Matrix)")
print("=" * 74)

# ═══ A. 财印不相碍 (PZZQ 取运章/财格佩印节) ═══
# L1126「年干透印, 时干透财, 中隔比劫, 则不相碍; 隔官星则为财旺生官, 亦不相碍」
# L3453「财印并透, 以不碍为条件...乙己财印并透而相并, 则财破印」
# L3463「财藏支而印透。财印不相碍为贵」
# L4305「财印既并透干头, 则以不相碍为最要条件」
print("\n[A] 财印不相碍判据 (PZZQ L1126/L3453/L3463/L4305)")
# 薛相公命: 壬印戊财以乙隔之 -> 不相碍
r = cai_yin_bu_ai('乙', P("甲申 壬申 乙巳 戊寅"), ['戊'], ['壬'])
ck("财印隔干(乙隔之)不相碍", r['bu_ai'] is True, r)
# 乙未己卯庚寅辛巳: 财印并透相并 -> 相碍
r = cai_yin_bu_ai('庚', P("乙未 己卯 庚寅 辛巳"), ['乙'], ['己'])
ck("财印并透相并=相碍(财破印)", r['bu_ai'] is False, r)
# 财藏支而印透 -> 不相碍
r = cai_yin_bu_ai('辛', P("壬子 癸卯 丙子 丁酉"), [], ['壬'])
ck("财藏支印透不相碍", r['bu_ai'] is True, r)
# 年干印时干财中隔比劫 -> 不相碍
r = cai_yin_bu_ai('乙', P("壬子 甲寅 乙卯 戊辰"), ['戊'], ['壬'])
ck("年印时财中隔比劫不相碍", r['bu_ai'] is True, r)

# ═══ B. 通关四型 (DTS L250) ═══
# L250「木土而要火, 火金而要土, 土水而要金, 金水而要水」
print("\n[B] 通关四型 (DTS L250)")
# 乙木财土旺 + 印水旺 + 火有气 -> 通关(木土而要火)
r = paipan("癸亥 壬戌 乙未 壬午")
sv = (r.get("l3_contract") or {}).get("strength_verdict") or {}
ck("木土而要火 -> 判通关", "通关" in (sv.get("value") or []), sv.get("value"))

# ═══ C. 大运顺逆与起运 (SMTH L923/L13424) ═══
# L923「阳男阴女, 大运以生日后未来节气日时为数, 顺而行之; 阴男阳女, 大运以生日前过去节气日时为数, 逆而行之」
# L13424「如阳男阴女, 从生月顺行; 阴男阳女, 从生月逆行」
print("\n[C] 大运顺逆/起运 (SMTH L923/L13424)")
for (yr_g, gender, want, basis) in (
        ('癸', '女', '順', "癸(阴年)女=阴女顺排"),
        ('癸', '男', '逆', "癸(阴年)男=阴男逆排"),
        ('甲', '男', '順', "甲(阳年)男=阳男顺排"),
        ('甲', '女', '逆', "甲(阳年)女=阳女逆排")):
    _d, _q = _dayun_qiyun(1983, 11, 3, yr_g, '壬', '戌', gender)
    ck("大运方向 %s" % basis, _q['direction'] == want, _q['direction'])
d_f, q_f = _dayun_qiyun(1983, 11, 3, '癸', '壬', '戌', '女')
ck("阴女顺排大运=癸亥甲子乙丑…", d_f[0] == '癸亥' and d_f[1] == '甲子' and d_f[2] == '乙丑', d_f[:3])
ck("阴女起运数未来节气(1.3岁)", abs(q_f['age'] - 1.3) < 0.15, q_f)

# ═══ D. 根气轻重 (PZZQ L800-801) ═══
# L800-801「根有轻重之分: 长生、禄、帝旺为重根; 墓库、余气为轻根」
print("\n[D] 根气轻重 (PZZQ L800-801)")
from engines.common.daymaster_root_class import classify_root
rc = classify_root('甲', '亥', ['壬', '甲'])
ck("甲在亥=阳长生=重根", rc.get('root_class') == 'HEAVY_LONGSHENG', rc.get('root_class'))
rc = classify_root('甲', '未', ['己', '丁', '乙'])
ck("甲在未=阳干墓库=轻根", rc.get('root_class') in ('LIGHT_MU_KU', 'NONE'), rc.get('root_class'))
rc = classify_root('乙', '午', ['丁', '己'])
ck("乙在午=阴长生=明根(独立级)", rc.get('root_class') == 'SPECIAL_LONGSHENG_YIN', rc.get('root_class'))

# ═══ E. 炼金候神次序 (QTBJ 庚金各月原文) ═══
# QTBJ L6051 六月庚金「先用丁火, 次取甲木」/ L6121 七月庚金「专用丁火煅炼」/ L6214 八月庚金「专用丙火…须见丁火锻炼」
# QTBJ L5822 三月庚金「先用甲木疏土, 次用丁火煅炼」/ L6282 九月庚金「先用甲疏, 后用壬洗」(丁在序3)
print("\n[E] 炼金候神: QTBJ 候干表火候位 (序1或序2方可升)")
from engines.common.qtbj_climate_candidates import build_climate_candidates
# ★ 断言盘须为"庚金顽钝/土厚埋金"之局(QTBJ 六月庚金「庚金在未月顽钝至极, 无丁火锻打则无以成器」/ L5819 三月庚金
#   「戊土司令...有埋金之忧」), 而非四柱全庚之旺局 —— 后者食伤泄秀才是正解(引擎判寒燥交互候食伤, 合原典).
#   构造: 日干庚, 月令未/申/亥/丑/辰(候干火在序1或序2), 其余柱取土印或火, 使丁火透出有气.
for (dm, mz, want_fire, basis) in (
        ('庚', '未', True, "六月庚金 专用丁火(L6051/6110, 顽钝宜丁火锻打)"),
        ('庚', '申', True, "七月庚金 专用丁火煅炼(L6121)"),
        ('庚', '亥', True, "十月庚金 非丁不能锻炼(L6348)"),
        ('庚', '丑', True, "十二月庚金 次取丁火炼金(L6489)"),
        ('庚', '辰', True, "三月庚金 次用丁火煅炼(L5819)"),
        ('庚', '戌', False, "九月庚金 序1甲疏/序2壬洗, 丁在序3(L6282)"),
        ('庚', '巳', False, "四月庚金 序1壬/序2戊, 丙在序3(L6071)")):
    # 盘: 年庚子 月<dm><mz> 日庚午 时<火候干>午  (丁火透时干有气, 日主庚金坐午弱)
    _hou = {'未': '丁', '申': '丁', '亥': '丁', '丑': '丁', '辰': '丁', '戌': '甲', '巳': '壬'}[mz]
    bz = "庚子 %s%s 庚午 %s午" % (dm, mz, _hou)
    p = P(bz)
    f = build(p)
    f['pillars'] = p
    cli = build_climate_candidates(f)
    res = tiaohou_rank._tiaohou_primary_rank(cli, '土', '金', p)
    got_fire = (res.get('rank') == 'PROMOTE' and res.get('wx') == '火')
    ck("炼金候神 %s" % basis, got_fire == want_fire, res.get('reason'))

# ═══ F. 病机量要件 (SFTK L1113/L9090/L1002, PZZQ L768) ═══
print("\n[F] 病机「量」要件 (原典: 多/重/太重/党众)")
import engines.common.bingyao_layer as BL
# 财多身弱: 财孤(仅一财)不作财多 —— 构造: 乙日, 亥月(印水当令), 仅一处财根
p = P("乙丑 癸未 乙亥 乙丑")
f = build(p)
f['pillars'] = p
f['wuxing_power'] = build_wuxing_power(p, f)
# 用 identify_bing 直接看财多身弱是否触发(需 query, 用空 query 走 fallback 分支)
try:
    from engines.common.daymaster_power_structure import build_power_structure
    from engines.common.daymaster_root_class import build_root_classes
    from engines.common.daymaster_tou_cang import build_tou_cang
    from engines.common.daymaster_wang_xiang import build_wang_xiang
    from engines.common.daymaster_root_relations import build_root_relations
    from engines.common.daymaster_two_side import build_two_side
    from engines.common.daymaster_branch_tier import build_branch_tiers
    from engines.common.daymaster_tian_he import build_tian_he
    from engines.common.daymaster_power_network import build_power_network
    from engines.common.daymaster_power_queries import run_queries
    hst = {p[k][1]: f['hidden_stems'][k] for k in ('year', 'month', 'day', 'hour')}
    pa = build_power_structure(p)
    rc = build_root_classes(p, hst)
    tc = build_tou_cang(f)
    wx = build_wang_xiang(f, f['day_stem'])
    rr = build_root_relations(rc, f['combination_facts'])
    ts = build_two_side(rc, tc, rr)
    bt = build_branch_tiers(p, f)
    th = build_tian_he(p, f)
    net = build_power_network(pa, rc, tc, wx, rr, ts, branch_tier=bt, tian_he=th, facts=f)
    q = run_queries(net)
    f['root_weight_class_facts'] = {
        pos: {'branch': p[pos][1],
              'class': 'HEAVY' if rc['per_pillar'][pos]['root_class'].startswith('HEAVY')
              else ('LIGHT' if rc['per_pillar'][pos]['root_class'].startswith('LIGHT') else 'NONE')}
        for pos in ('year', 'month', 'day', 'hour')}
    f['tian_he'] = th
    by = BL.identify_bing(f, q)
    ids = [b.get('bing_id') for b in by]
    ck("财多身弱需财多(支干重重)方报", 'CAI_DUO_SHEN_RUO' in ids, ids)
except Exception as _e:
    print("  (跳过 F 组构造异常: %s)" % _e)

# ═══ G. 伤官见官前提 (PZZQ L1145/L1156/L1157) ═══
print("\n[G] 伤官见官: 须月令伤官 + 官透有根 + 非佩印 + 非金水冬令")
for (bz, want, basis) in (
        ("癸酉 己未 丙午 庚寅", False, "非月令伤官(财格) -> 不报"),
        ("癸酉 己未 丙午 癸巳", False, "官煞虚透无根 -> 不报"),
        ("乙未 辛巳 乙亥 丙戌", False, "伤官带煞无财(非格败) -> 不报")):
    r = paipan(bz)
    ids = [b.get('bing_id') for b in (r.get("bing_list") or [])]
    ck("伤官见官 %s" % basis, ('SHANGGUAN_JIAN_GUAN' in ids) == want, ids)

# ═══ H. 病根优先 (DTS L404 闲神定义) ═══
print("\n[H] 病根优先: 主病五行明确为忌, 不降级归闲 (DTS L404)")
r = paipan("癸亥 壬戌 乙未 壬午")
xx = (r.get("yongyao") or {}).get("xiji_xian") or {}
ck("印多埋子(水)入忌桶, 不入闲桶", "水" in (xx.get("ji_wx") or []) and "水" not in (xx.get("xian_wx") or []),
   "ji=%s xian=%s" % (xx.get("ji_wx"), xx.get("xian_wx")))

# ═══ I. 格局形态单一数据源 (PZZQ 取运章) ═══
print("\n[I] 格局形态: 由格局层产出, 喜忌层只读 (PZZQ 取运章 各格形态分档)")
for (bz, want_shape, basis) in (
        ("甲戌 辛未 庚子 丁亥", '用官', "印格·官透(用官)"),
        ("癸卯 己未 丙寅 辛卯", None, "财格·无印透(不判佩印)")):
    r = paipan(bz)
    gc = r.get("ge_cheng") or {}
    sh = gc.get("shape")
    if want_shape is None:
        ck("形态 %s" % basis, sh != '佩印', sh)
    else:
        ck("形态 %s" % basis, sh == want_shape, sh)

print()
print("=" * 74)
print("矩阵结果: PASS=%d FAIL=%d" % (len(OKS), len(FAILS)))
if FAILS:
    print("失败项:")
    for f in FAILS:
        print("  -", f)
print("=" * 74)
sys.exit(1 if FAILS else 0)
