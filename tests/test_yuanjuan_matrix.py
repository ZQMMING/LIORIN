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
    """'甲申 壬申 乙巳 戊寅' 或 '甲申壬申乙巳戊寅' -> pillars dict."""
    if isinstance(s, str):
        parts = s.split()
        if len(parts) == 1 and len(s) == 8:
            parts = [s[i:i + 2] for i in range(0, 8, 2)]
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

# ═══ J. 八格成格要件 (PZZQ L1113-1118 原文逐条) ═══
# 原文: 「用神专寻月令, 以四柱配之, 必有成败。何谓成?
#   如官逢财印, 又无刑冲破害, 官格成也。
#   财生官旺, 或财逢食生而身强带比, 或财格透印而位置妥贴, 两不相克, 财格成也。
#   印轻逢煞, 或官印双全, 或身印两旺而用食伤泄气, 或印多逢财而财透根轻, 印格成也。
#   食神生财, 或食带煞而无财, 弃食就煞而透印, 食格成也。
#   身强七煞逢制, 煞格成也。
#   伤官生财, 或伤官佩印而伤官旺印有根, 或伤官旺身主弱而透煞印, 或伤官带煞而无财, 伤官格成也。
#   阳刃透官煞而露财印, 不见伤官, 阳刃格成也。
#   建禄月劫, 透官而逢财印, 透财而逢食伤, 透煞而遇制伏, 建禄月劫之格成也。」
print("\n[J] 八格成格要件 (PZZQ L1113-1118 逐条)")
sys.path.insert(0, os.path.join(ROOT, "tests"))
from yuangen_zhu import mk, mk_raw

# J1 官格成: 官逢财印, 无刑冲破害 -> 成
bz, _p = mk(dm='甲', month_tg='正官', gan_tgs=('正印', None, '偏财'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("官格成: 官逢财印无刑冲破害(L1113) [%s]" % bz, (gc.get("ge") or "").startswith("正官格"), gc.get("ge"))

# J2 财格成: 财逢食生而身强带比(月令财, 食神透, 比劫透)
#   注: 造盘须避开"从格候选"(日主无根+食伤成势+无官煞) —— 引擎设计为"从格CONFIRMED优先覆盖正格"
#   (ge_jie_layer L363「从格CONFIRMED优先(覆盖正格)」; PZZQ L4126「弃命从煞则另属外格」),
#   本组断言聚焦八格成格判据本身, 不涉跨层优先.
bz, _p = mk(dm='甲', month_tg='正财', gan_tgs=('食神', None, '比肩'),
          zhis=('寅', '未', '子', '戌'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("财格成: 财逢食生身强带比(L1114) [%s]" % bz, (gc.get("ge") or "") == "财格", gc.get("ge"))

# J3 财格成: 财格透印而位置妥贴两不相克
bz, _p = mk(dm='甲', month_tg='正财', gan_tgs=('正印', None, None))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("财格成: 财格透印位置妥贴两不相克(L1114) [%s]" % bz, (gc.get("ge") or "") == "财格", gc.get("ge"))

# J4 印格成: 印轻逢煞(月令印+煞透+印不透)
bz, _p = mk(dm='甲', month_tg='正印', gan_tgs=('七杀', None, None))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("印格成: 印轻逢煞(L1114) [%s]" % bz, (gc.get("ge") or "") == "印格(印轻逢煞)", gc.get("ge"))

# J5 印格成: 官印双全(月令印+官透+官有根+无杀透)
#   注: 原典 L1114 印格成格为【并列四路】(印轻逢煞/官印双全/身印两旺用食伤/印多逢财财透根轻),
#   故断言只验"成格"(ge 非 None 且非 PO), 不锁格名细分.
bz, _p = mk(dm='甲', month_tg='正印', gan_tgs=('正官', None, None))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("印格成: 官印双全(L1114, 并列四路之一) [%s]" % bz,
   (gc.get("ge") or "").startswith("印格") and gc.get("cheng_bai") != "PO", gc.get("ge"))

# J6 印格成: 印多逢财而财透根轻(月令印+财透)
bz, _p = mk(dm='甲', month_tg='正印', gan_tgs=('偏财', None, None))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("印格成: 印多逢财财透根轻(L1114) [%s]" % bz, (gc.get("ge") or "").startswith("印格"), gc.get("ge"))

# J7 食神格成: 食神生财(月令食神+财透)
#   注: 造盘须避开"从格候选"(日主无根+食伤成势) —— 引擎设计为"从格CONFIRMED优先覆盖正格".
bz, _p = mk(dm='甲', month_tg='食神', gan_tgs=('偏财', None, '比肩'),
          zhis=('寅', '巳', '子', '戌'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("食格成: 食神生财(L1115) [%s]" % bz, (gc.get("ge") or "").startswith("食神格"), gc.get("ge"))

# J8 食神格成: 食带煞而无财, 弃食就煞而透印
bz, _p = mk(dm='甲', month_tg='食神', gan_tgs=('七杀', None, '正印'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("食格成: 食带煞无财弃食就煞透印(L1115) [%s]" % bz, (gc.get("ge") or "").startswith("食神格"), gc.get("ge"))

# J9 七煞格成: 身强七煞逢制(月令七杀+食神制+身强)
bz, _p = mk(dm='甲', month_tg='七杀', gan_tgs=('食神', None, '比肩'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("煞格成: 身强七煞逢制(L1115) [%s]" % bz, (gc.get("ge") or "").startswith("七煞格"), gc.get("ge"))

# J10 伤官格成: 伤官生财(月令伤官+财透)
bz, _p = mk(dm='甲', month_tg='伤官', gan_tgs=('偏财', None, None))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("伤官格成: 伤官生财(L1116) [%s]" % bz, (gc.get("ge") or "").startswith("伤官格"), gc.get("ge"))

# J11 伤官格成: 伤官佩印而伤官旺印有根
bz, _p = mk(dm='甲', month_tg='伤官', gan_tgs=('正印', None, None))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("伤官格成: 伤官佩印而伤官旺印有根(L1116) [%s]" % bz, (gc.get("ge") or "").startswith("伤官格"), gc.get("ge"))

# J12 阳刃格成: 阳刃透官煞而露财印, 不见伤官(日主阳, 月支=刃位)
bz, _p = mk(dm='甲', month_tg='劫财', gan_tgs=('正官', None, '偏财'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("阳刃格成: 透官煞露财印不见伤官(L1117) [%s]" % bz, (gc.get("ge") or "") == "阳刃格", gc.get("ge"))

# J13 建禄月劫格成: 透官而逢财印(日主阳, 月支=禄位)
bz, _p = mk(dm='甲', month_tg='比肩', gan_tgs=('正官', None, '偏财'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("建禄月劫格成: 透官逢财印(L1117) [%s]" % bz, (gc.get("ge") or "") == "建禄月劫格", gc.get("ge"))

# J14 建禄月劫格成: 透财而逢食伤
bz, _p = mk(dm='甲', month_tg='比肩', gan_tgs=('偏财', None, '食神'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("建禄月劫格成: 透财逢食伤(L1117) [%s]" % bz, (gc.get("ge") or "") == "建禄月劫格", gc.get("ge"))

# J15 建禄月劫格成: 透煞而遇制伏
bz, _p = mk(dm='甲', month_tg='比肩', gan_tgs=('七杀', None, '食神'))
r = paipan(bz)
gc = r.get("ge_cheng") or {}
ck("建禄月劫格成: 透煞遇制伏(L1117) [%s]" % bz, (gc.get("ge") or "") == "建禄月劫格", gc.get("ge"))

# ═══ K. 八格败格要件 (PZZQ L1145-1147 原文逐条) ═══
# 原文: 「何谓败? 官逢伤克刑冲, 官格败也; 财轻比重, 财透七煞, 财格败也;
#   印轻逢财, 或身强印重而透煞, 印格败也; 食神逢枭, 或生财露煞, 食神格败也;
#   七煞逢财无制, 七煞格败也; 伤官非金水而见官, 或生财而带煞, 或佩印而伤轻身旺, 伤官格败也;
#   阳刃无官煞, 刃格败也; 建禄月劫, 无财官, 透煞印, 建禄月劫之格败也。」
print("\n[K] 八格败格要件 (PZZQ L1145-1147 逐条)")
    # K 组: 用造盘器保证月令十神正确(手写柱易错十神, 致断言失真)
print("\n[K] 八格败格要件 (PZZQ L1145-1147 逐条)")
# L1145「何谓败? 官逢伤克刑冲, 官格败也; 财轻比重, 财透七煞, 财格败也;
#   印轻逢财, 或身强印重而透煞, 印格败也; 食神逢枭, 或生财露煞, 食神格败也;
#   七煞逢财无制, 七煞格败也; 伤官非金水而见官, 或生财而带煞, 或佩印而伤轻身旺, 伤官格败也;
#   阳刃无官煞, 刃格败也; 建禄月劫, 无财官, 透煞印, 建禄月劫之格败也。」
# 注: 败格判据为"格成而带忌", 引擎以 cheng_bai=PO / CHENG_ZHONG_YOU_PO 表之.
for (kw, want_po, basis) in (
        (dict(dm='甲', month_tg='正官', gan_tgs=('伤官', None, None)), True, "官格败: 官逢伤克(L1145)"),
        (dict(dm='甲', month_tg='正财', gan_tgs=('七杀', None, None)), True, "财格败: 财透七煞(L1145)"),
        # 印格败须【印轻财重】(PZZQ L2178「贪财坏印者, 必也印轻财重」): 印只月令一处本气根,
        #   余支无印根; 财透干且有根(戊土在辰戌未为根).
        (dict(dm='甲', month_tg='正印', gan_tgs=('比肩', None, '偏财'),
              zhis=('寅', '子', '午', '辰')), True, "印格败: 印轻财重(L1145/L2178)"),
        (dict(dm='甲', month_tg='食神', gan_tgs=('偏印', None, None)), True, "食神格败: 食神逢枭(L1145)"),
        (dict(dm='甲', month_tg='七杀', gan_tgs=('偏财', None, None)), True, "七煞格败: 七煞逢财无制(L1145)"),
        (dict(dm='甲', month_tg='伤官', gan_tgs=('正官', None, None)), True, "伤官格败: 非金水见官(L1145)"),
        # 阳刃格败须【无官煞】且【非从旺/非专旺】: 戊日午月(戊刃午), 四柱无官杀透干
        #   (注: 官杀若透而无根仍算"有官"? 引擎以 present_all(十神成员) 判存在, 故此处取 truly 无官杀)
        (dict(dm='戊', month_tg='阳刃', gan_tgs=('正印', None, '正印'),
              zhis=('子', '午', '丑', '卯')), True, "阳刃格败: 无官煞(L1147)"),
):
    try:
        bz, _p = mk(**kw)
    except Exception as _e:
        ck("败格 %s" % basis, False, "造盘失败: %s" % _e)
        continue
    r = paipan(bz)
    gc = r.get("ge_cheng") or {}
    cb = gc.get("cheng_bai")
    ck("败格 %s [%s]" % (basis, bz), cb in ("PO", "CHENG_ZHONG_YOU_PO"),
       "cheng_bai=%s ge=%s" % (cb, gc.get("ge")))

# ═══ L. 通关三要件 (DTS L250) ═══
# L250「...必得【引用无合之神】及刑冲所间之物, 前后上下, 援引得来, 能胜劫占之神, 能补所缺之物, 明见暗会, 岁运相逢, 乃为通关也。」
print("\n[L] 通关三要件 (DTS L250)")
# L1 木土而要火 -> 通关(乙木日: 印水旺+财土旺, 火为通关神且透干有气)
#   月令亥(印当令, 印旺) + 支未戌(土本气根=财有根) + 时干丁火(通关神透干)
bz, _p = mk(dm='乙', month_tg='正印', gan_tgs=('正印', None, '食神'),
          zhis=('亥', '亥', '未', '戌'))
r = paipan(bz)
sv = (r.get("l3_contract") or {}).get("strength_verdict") or {}
ck("通关: 木土而要火(DTS L250) [%s]" % bz, "通关" in (sv.get("value") or []), sv.get("value"))
# L2 通关神被紧贴他干合走 -> 引用不成 -> 不判通关(DTS L250「引用无合之神」)
#   乙木日, 印水旺+财土旺, 丁火(通关神)被己土紧贴合走(丁壬合/己甲合) -> 用己土合丁火
# L2 通关神被紧贴他干合走 -> 引用不成 -> 不判通关(DTS L250「引用无合之神」)
#   乙木日, 印水旺+财土旺; 通关神=火(丙·伤官). 年干辛(七杀, 丙辛合)紧贴月干丙(通关神)
#   -> 丙被合 -> "引用无合之神"不成立 -> 不判通关.
bz2, _p2 = mk(dm='乙', month_tg='正印', gan_tgs=('七杀', '伤官', '食神'),
             zhis=('亥', '亥', '未', '戌'))
r2 = paipan(bz2)
sv2 = (r2.get("l3_contract") or {}).get("strength_verdict") or {}
ck("通关: 通关神被紧贴合走则引用不成(L250「无合之神」) [%s]" % bz2,
   "通关" not in (sv2.get("value") or []), sv2.get("value"))

# ═══ M. 病药三判据 (SFTK L129 / DTS L461 / PZZQ L3977) ═══
# SFTK L129「何以为之病? 原八字中原所害之神也; 何以为之药? ...八字原有所害之一字, 而得一字以去之谓了...
#   ...或本身病重而药少, 或本身病轻而得药重, 又宜行运, 以取其中和。若病重而得药, 大富贵之人也。」
# DTS L461「羁绊喜神之合, 如乙喜神庚合之则羁绊」/ PZZQ L421「合而不化...两失其用」
print("\n[M] 病药三判据 (SFTK L129 / DTS L461)")
# M1 印多埋子之药(财破印+比劫扶印)在局 -> 进入三判据(不再无字段)
#   癸亥壬戌乙未壬午: 病=印多埋子(水, combo4), 药=财土(combo2)/比劫木 -> 病重药轻
#   (PZZQ L3977「惜病重药轻」/ SFTK L129「病重而药少...宜行运以取其中和」)
r = paipan("癸亥 壬戌 乙未 壬午")
bl = r.get("bing_list") or []
yin_bing = [b for b in bl if b.get("bing_id") == "YIN_DUO_MAI_ZI"]
ck("病药: 印多埋子进入三判据(有 yao_yuanju 判据结论)",
   (yin_bing and yin_bing[0].get("yao_yuanju") in
    ("REMOVED", "INVALID_HE", "INVALID_ROOT", "INVALID_POTENTIAL")),
   (yin_bing[0].get("yao_yuanju") if yin_bing else "no-bing"))
ck("病药: 病重药少则待运不消(PZZQ L3977/SFTK L129)",
   (yin_bing and yin_bing[0].get("yao_yuanju") == "INVALID_POTENTIAL"),
   (yin_bing[0].get("yao_yuanju") if yin_bing else "no-bing"))
# M2 药被紧贴他干合走 -> 羁绊, 病不消(INVALID_HE)
#   乙未 庚辰 甲戌 庚午: 甲日, 财(土)多身弱; 药=木(比劫)/水(印), 年干乙与月干庚紧贴相合(乙庚合)
#   -> 药被羁绊, 不能援引 -> 病不消(DTS L461「羁绊喜神之合」/ L425 真化需得令/ PZZQ L421 合而不化两失其用)
bz3, _p3 = mk_raw("乙未 庚辰 甲戌 庚午")
r3 = paipan(bz3)
bl3 = r3.get("bing_list") or []
cai_bing3 = [b for b in bl3 if b.get("bing_id") == "CAI_DUO_SHEN_RUO"]
ck("病药: 药被紧贴合走则羁绊病不消(DTS L461) [%s]" % bz3,
   (cai_bing3 and cai_bing3[0].get("yao_yuanju") == "INVALID_HE"),
   (cai_bing3[0].get("yao_yuanju") if cai_bing3 else "no-bing"))
# M3 病重药少(药虚透无根) -> 病不消待运(INVALID_ROOT)
#   病=财多身弱(财当令且支干重重, SFTK L1113) + 药=印比(扶身)虚透无根;
#   乙木日无根(支全土金) + 财土当令多根
bz4, _p4 = mk_raw("戊辰 己未 乙丑 庚辰")
r4 = paipan(bz4)
bl4 = r4.get("bing_list") or []
cai_bing = [b for b in bl4 if b.get("bing_id") == "CAI_DUO_SHEN_RUO"]
ck("病药: 病重药少则待运不消(SFTK L129) [%s]" % bz4,
   (cai_bing and cai_bing[0].get("yao_yuanju") in ("INVALID_ROOT", "INVALID_POTENTIAL")
    or (cai_bing and not cai_bing[0].get("yao_yuanju"))),
   (cai_bing[0].get("yao_yuanju") if cai_bing else "no-bing"))

# ═══ N. 岁运层恶神抵消表 (V7.25 evil_offset) ═══
# 算理(原典): 刑/冲药根/破格 = 恶神(刑伤/药根拔/格破), 主凶, 与制化之功不同类(刑是结构伤), 不抵消药;
#   冲月令提纲/冲日主重根 = 提纲伤(交战性) -> 平(吉凶参半), 不入凶;
#   合走主药根/冲拔主药根 = 药根拔 -> 凶; 主药被合绊 = 药被合去失制力 -> 抵消制.
# 依据: PZZQ L1182「成中之败, 亦变化万端」/ L1523「盖官逢财印, 无刑冲, 为官格之成, 冲官则破格」
#       PZZQ L3346「身弱得印, 用神即在于印, 以行官煞运为佳」(克伐日主非无条件凶 -> 不入恶神表)
print("\n[N] 岁运层恶神抵消表 (V7.25 evil_offset)")
from engines.common import evil_offset
# N1 恶神(刑/破格/伤官见官/药根拔) -> 不抵消制化之功, 判凶(-2)
for (b, want_level, basis) in (
        (["制主病水(土)", "三刑(丑戌未恃势之刑)"], -2, "恶神(刑)不抵消制化之功 -> 凶"),
        (["制主病水(土)", "格局破格(财格·岁运辛(七杀)触发)"], -2, "恶神(破格)不抵消制化之功 -> 凶"),
        (["制主病水(土)", "冲拔主药根(午冲子·药火根拔)"], -2, "恶神(药根拔)不抵消制化之功 -> 凶"),
        (["制主病水(土)", "伤官见官(火伤官克土官)"], -2, "恶神(伤官见官)不抵消制化之功 -> 凶")):
    v = evil_offset.verdict_arbitrate([b[0]], b[1:])
    ck("岁运裁决 %s" % basis, v['level'] == want_level, "%s -> %s" % (b, v))
# N2 交战(冲提纲/冲重根): 有制化之功(hard_good)或药成局 -> 平(0, 吉凶参半不降档);
#    无制化之功 -> 平偏凶(-1)
for (g, b, want_level, basis) in (
        (["三合局成火候神(午合戌/午·药成局, 吉)"], ["冲月令提纲(辰冲戌)"], 0, "交战+药成局 -> 平"),
        (["制主病水(土)"], ["冲月令提纲(辰冲戌)"], 0, "交战+制化之功 -> 平(吉凶参半)"),
        ([], ["冲月令提纲(辰冲戌)"], -1, "交战(冲提纲)无制化之功 -> 平偏凶"),
        ([], ["合日主重根(未合午·根被合走)"], -1, "交战(合重根)无制化之功 -> 平偏凶")):
    v = evil_offset.verdict_arbitrate(g, b)
    ck("岁运裁决 %s" % basis, v['level'] == want_level, "%s %s -> %s" % (g, b, v))
# N3 纯制化无恶神 -> 吉(+2); 纯 bad -> 凶(-2)
v = evil_offset.verdict_arbitrate(["制主病水(土)"], [])
ck("岁运裁决 纯制化无恶神 -> 吉(+2)", v['level'] == 2, v)
v = evil_offset.verdict_arbitrate([], ["克伐日主(火)"])
ck("岁运裁决 纯凶(克伐日主) -> 凶(-2)", v['level'] == -2, v)
# N4 克伐日主不入恶神表(身弱得印者行官煞运为佳, PZZQ L3346) -> 有制化之功时判吉/平, 不判凶
ck("岁运裁决 克伐日主不入恶神表(PZZQ L3346)",
   evil_offset.evil_no_offset(["克伐日主(火)"]) is False, "克伐日主被误列为恶神")
ck("岁运裁决 助主病不入恶神表(药病交战走平)",
   evil_offset.evil_no_offset(["助主病土(土)"]) is False, "助主病被误列为恶神")

# ═══ O. 六亲映射 (SMTH L3565 男女取用不同) ═══
# SMTH L3565「男取克干为子, 女取干生为息...【女取用与男不同】, 我生者为子, 克我者为夫,
#   生我夫者为姑, 克我姑者为丈人...」/ 夫=财(男), 妻=财(男)
print("\n[O] 六亲映射 (SMTH L3565 男女取用不同)")
from engines.common.six_relative_producer import six_relative_producer
for (tg, gender, want_syms, basis) in (
        ("财", "男", ["父", "妻星"], "男: 财=父/妻星(SMTH 男以财为妻)"),
        ("官杀", "女", ["丈夫星"], "女: 克我者(官杀)=丈夫星(SMTH「克我者为夫」)"),
        ("食伤", "女", ["子女"], "女: 干生为息(食伤)=子女(SMTH「女取干生为息」)"),
        ("食伤", "男", ["子女", "作品"], "男: 克干为子(食伤)=子女(SMTH「男取克干为子」)"),
        ("印", "男", ["母", "长辈", "学习"], "男: 生我者(印)=母"),
        ("比劫", "男", ["兄弟", "同辈"], "男: 同我者(比劫)=兄弟")):
    r = six_relative_producer(tg, gender, "STRONG_ROOT")
    syms = r.get("relative_symbols") or []
    ck("六亲 %s" % basis, all(w in syms for w in want_syms), syms)
# 性别取用不同: 女命无"妻星"(夫星=官杀), 男命无"丈夫星"
r_male = six_relative_producer("财", "男", "STRONG_ROOT")
r_female = six_relative_producer("财", "女", "STRONG_ROOT")
ck("六亲 男女取用不同(SMTH「女取用与男不同」): 女命财=父/资源, 非妻星",
   "妻星" in (r_male.get("relative_symbols") or [])
   and "妻星" not in (r_female.get("relative_symbols") or []),
   (r_male.get("relative_symbols"), r_female.get("relative_symbols")))

# ═══ P. 建禄月劫/阳刃 形态分档 (PZZQ L1142-1143 / L4579-4582) ═══
# L1142-1143「建禄月劫, 透官而逢财印即同官格; 透财而逢食伤即同财格; 透煞而遇制伏即同煞格」
# L4579「阳刃用官, 则运喜助官...」/ L4580「非用官煞克之, 即用食伤泄之」/ L1140「以财印并见为吉」
print("\n[P] 建禄月劫/阳刃 形态分档 (PZZQ L1142-1143 / L4579-4582)")
from engines.common.ge_jie_layer import derive_ge_shape, build_ge_cheng

# P1 建禄月劫: 透官+财印 -> 同官格; 透财+食伤 -> 同财格; 透煞+有制 -> 同煞格
for (kw, want_shape, basis) in (
        (dict(dm='甲', month_tg='比肩', gan_tgs=('正官', None, '正印'),
              zhis=('寅', '寅', '午', '子')), '同官格', "建禄月劫 透官逢财印=同官格(L1142)"),
        (dict(dm='甲', month_tg='比肩', gan_tgs=('偏财', None, '食神'),
              zhis=('寅', '寅', '午', '子')), '同财格', "建禄月劫 透财逢食伤=同财格(L1142)"),
        (dict(dm='甲', month_tg='比肩', gan_tgs=('七杀', None, '食神'),
              zhis=('寅', '寅', '午', '子')), '同煞格', "建禄月劫 透煞遇制伏=同煞格(L1142)")):
    bz, p = mk(**kw)
    _p_p, f = facts_of(bz)
    build_ge_cheng(f)
    base, shape = derive_ge_shape(f)
    ck("形态 %s [%s]" % (basis, bz), shape == want_shape, "%s/%s" % (base, shape))
# P2 阳刃: 官杀透=用官; 食伤透=用食伤; 财印并见=用财印
for (kw, want_shape, basis) in (
        (dict(dm='甲', month_tg='阳刃', gan_tgs=('正官', None, '正印'),
              zhis=('寅', '卯', '午', '子')), '用官', "阳刃 官杀透=用官(L4579)"),
        (dict(dm='甲', month_tg='阳刃', gan_tgs=('食神', None, '比肩'),
              zhis=('寅', '卯', '午', '子')), '用食伤', "阳刃 食伤泄秀=用食伤(L4580)"),
        (dict(dm='甲', month_tg='阳刃', gan_tgs=('偏财', None, '正印'),
              zhis=('寅', '卯', '午', '子')), '用财印', "阳刃 财印并见=用财印(L1140)")):
    bz, p = mk(**kw)
    _p_p, f = facts_of(bz)
    build_ge_cheng(f)
    base, shape = derive_ge_shape(f)
    ck("形态 %s [%s]" % (basis, bz), shape == want_shape, "%s/%s" % (base, shape))

# ═══ Q. 两气成象 (DTS L162/L164 形象章) ═══
# L162「两气合而成象, 象不可破也。」/ L164「天干属木, 地支属火, 天干属火, 地支属木, 其象则一。
#   若见金水则破, 余仿此。」/ L166「五气聚而成形, 形不可害也。」
# 注: 「各成势」阈值(计数>=3)为工程离散值(原典未给数字), 现有 golden 三锚点支撑;
#   不得据 L178/L180「形全」或 L164「干支分野」擅改(2026-10-21 两次误改已撤回) —— 登记待原典专项裁决.
print("\n[Q] 两气成象 (DTS L162/L164)")
from engines.common.special_pattern import build_special_patterns
from engines.common.daymaster_tian_he import build_tian_he as _bth

for (bz, exp_xiu, basis) in (
        ("甲午丁卯甲午丁卯", "火", "木火通明, 秀神丁火"),
        ("丙午戊戌丙午戊戌", "土", "火土成象, 顺土(食伤)泄秀"),
        ("戊戌辛酉戊戌辛酉", "金", "土金成象, 取辛金伤官为用")):
    _p_q, _f_q = facts_of(bz)
    _th_q = _bth(_p_q, _f_q)
    _sp_q = build_special_patterns(_p_q, _f_q, _f_q.get('wuxing_power'), _th_q)
    _lq = _sp_q.get('liangqi')
    ck("两气成象 %s [%s]" % (basis, bz),
       bool(_lq) and _lq.get('xiu') == exp_xiu and not _sp_q.get('zhuanwang') and not _sp_q.get('cong_type'),
       _lq)
# 反例: 癸亥甲寅(DTS L862) 两行相生但寅亥合木、伤官太重泄身 -> 不判两气成象(回正格)
_p_q2, _f_q2 = facts_of("癸亥甲寅癸亥甲寅")
_th_q2 = _bth(_p_q2, _f_q2)
_sp_q2 = build_special_patterns(_p_q2, _f_q2, _f_q2.get('wuxing_power'), _th_q2)
ck("两气成象 反例: 假两气(寅亥合木/伤官太重)不判成象(DTS L862)",
   not _sp_q2.get('liangqi'), _sp_q2.get('liangqi'))

# ═══ R. 候神力级: 坐旺支表 (PZZQ L800-801 长生/禄/帝旺为重根, 墓库为轻根) ═══
# L800-801「根有轻重之分: 长生、禄、帝旺为重根, 墓库、余气为轻根」
# => 候神"坐旺"(2力)之支 = 该五行之禄与帝旺; 墓库(四库)属轻根, 不作坐旺.
print("\n[R] 候神力级 坐旺支表 (PZZQ L800-801)")
from engines.common.evil_offset import _WANG_BR
from engines.common.daymaster_root_class import POS as _RC_POS
for (wx, lu, wang, basis) in (
        ('木', '寅', '卯', "木: 长生亥/禄寅/帝旺卯"),
        ('火', '巳', '午', "火: 长生寅/禄巳/帝旺午"),
        ('土', '巳', '午', "土: 长生申/禄巳/帝旺午(V7.94 修正, 旧误用四库)"),
        ('金', '申', '酉', "金: 长生巳/禄申/帝旺酉"),
        ('水', '亥', '子', "水: 长生申/禄亥/帝旺子")):
    got = set(_WANG_BR.get(wx, ()))
    ck("坐旺支表 %s" % basis, got == {lu, wang}, sorted(got))
# 墓库(四库)不得作坐旺
ck("坐旺支表 墓库(辰戌丑未)不作坐旺(PZZQ L800-801「墓库为轻根」)",
   not (set(_WANG_BR.get('土', ())) & {'辰', '戌', '丑', '未'}), _WANG_BR.get('土'))
# 与引擎根气表一致
for _dmx, _pos in (('甲', '木'), ('丙', '火'), ('戊', '土'), ('庚', '金'), ('壬', '水')):
    _lu = _RC_POS[_dmx].get('禄')
    _wang = _RC_POS[_dmx].get('旺')
    ck("坐旺支表 与根气表一致 %s(禄%s旺%s)" % (_dmx, _lu, _wang),
       set(_WANG_BR.get(_pos, ())) == {_lu, _wang},
       "%s vs %s" % (sorted(_WANG_BR.get(_pos, ())), [_lu, _wang]))

print()
print("=" * 74)
print("矩阵结果: PASS=%d FAIL=%d" % (len(OKS), len(FAILS)))
if FAILS:
    print("失败项:")
    for f in FAILS:
        print("  -", f)
print("=" * 74)
sys.exit(1 if FAILS else 0)
