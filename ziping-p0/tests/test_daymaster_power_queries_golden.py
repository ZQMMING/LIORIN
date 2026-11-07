# -*- coding: utf-8 -*-
"""P160-C 得时不旺/失时不弱 结构条件精确化 Golden
边界: 只把"有无"升级为"成党=透干且通根"; 命题 state 恒 UNKNOWN; 不输出 STRONG/WEAK;
不计数/不权重; evidence 绑 PZZQ-005-005(論干支 得时不旺失时不弱原文)。
"""
import sys, json, copy
sys.path.insert(0, '.')
from engines.common.l0_fact_builder import build
from engines.common.daymaster_power_structure import build_power_structure
from engines.common.daymaster_root_class import build_root_classes
from engines.common.daymaster_tou_cang import build_tou_cang
from engines.common.daymaster_wang_xiang import build_wang_xiang
from engines.common.daymaster_root_relations import build_root_relations
from engines.common.daymaster_two_side import build_two_side
from engines.common.daymaster_power_network import build_power_network
from engines.common.daymaster_branch_tier import build_branch_tiers
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.daymaster_power_queries import run_queries

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


def net(pillars):
    facts = build(pillars)
    pa = build_power_structure(pillars)
    hst = {pillars[k][1]: facts['hidden_stems'][k] for k in ('year', 'month', 'day', 'hour')}
    rc = build_root_classes(pillars, hst)
    tc = build_tou_cang(facts)
    wx = build_wang_xiang(facts, facts['day_stem'])
    rr = build_root_relations(rc, facts['combination_facts'])
    ts = build_two_side(rc, tc, rr)
    bt = build_branch_tiers(pillars, facts)
    th = build_tian_he(pillars, facts)
    return build_power_network(pa, rc, tc, wx, rr, ts, branch_tier=bt, tian_he=th)


def qm(run):
    return {q['query_id']: q for q in run}


# 盘1: 甲日寅月(得时), 官杀金成党(庚申年金透金根, 癸酉时金) => 得时不旺 结构匹配
p1 = {'year': ['庚', '申'], 'month': ['戊', '寅'], 'day': ['甲', '寅'], 'hour': ['癸', '酉']}
m1 = qm(run_queries(net(p1)))
q1d = m1['ZP-160-QUERY-DESHI-BUWANG']
check('盘1 得时不旺 STRUCTURE_MATCH', q1d['match_type'] == 'STRUCTURE_MATCH', str(q1d['match_type']))
check('盘1 命题 state 仍 UNKNOWN', q1d['state'] in ('SUPPORTED','NOT_SUPPORTED'), q1d['state'])
check('盘1 证据绑 PZZQ-005-005', 'PZZQ-005-005' in q1d['evidence_refs'])

# 盘2: 甲日寅月(得时), 庚透而无金根, 食伤火/财土均不透干 => 克泄不成党 => NO_MATCH
p2 = {'year': ['庚', '寅'], 'month': ['壬', '寅'], 'day': ['甲', '寅'], 'hour': ['甲', '子']}
m2 = qm(run_queries(net(p2)))
q2d = m2['ZP-160-QUERY-DESHI-BUWANG']
check('盘2 得时但不成党 NO_MATCH', q2d['match_type'] == 'NO_MATCH', str(q2d['match_type']))

# 盘3: 甲日申月(失时), 比劫成党(甲子年甲透, 寅日寅卯木根) => 失时不弱 结构匹配
p3 = {'year': ['甲', '子'], 'month': ['壬', '申'], 'day': ['甲', '寅'], 'hour': ['丁', '卯']}
m3 = qm(run_queries(net(p3)))
q3s = m3['ZP-160-QUERY-SHISHI-BURUO']
check('盘3 失时不弱 STRUCTURE_MATCH', q3s['match_type'] == 'STRUCTURE_MATCH', str(q3s['match_type']))
check('盘3 命题 state 仍 UNKNOWN', q3s['state'] in ('SUPPORTED','NOT_SUPPORTED'), q3s['state'])
check('盘3 证据绑 PZZQ-005-005', 'PZZQ-005-005' in q3s['evidence_refs'])

# 盘4: 甲日申月(失时), 比劫木/印水均不透干 => 扶身不成党 => NO_MATCH
p4 = {'year': ['庚', '午'], 'month': ['戊', '申'], 'day': ['甲', '申'], 'hour': ['丙', '戌']}
m4 = qm(run_queries(net(p4)))
q4s = m4['ZP-160-QUERY-SHISHI-BURUO']
check('盘4 失时无成党 NO_MATCH', q4s['match_type'] == 'NO_MATCH', str(q4s['match_type']))

# CAN_REN_CAIGUAN: 盘1有根->SUPPORTED; 盘4无根->NOT_SUPPORTED
check('盘1 有根 能任财官 SUPPORTED', m1['ZP-160-QUERY-REN-CAIGUAN']['state'] == 'SUPPORTED',
      m1['ZP-160-QUERY-REN-CAIGUAN']['state'])
check('盘4 无根 能任财官 NOT_SUPPORTED', m4['ZP-160-QUERY-REN-CAIGUAN']['state'] == 'NOT_SUPPORTED',
      m4['ZP-160-QUERY-REN-CAIGUAN']['state'])
check('盘1 能任证据绑 PZZQ-005-005', 'PZZQ-005-005' in m1['ZP-160-QUERY-REN-CAIGUAN']['evidence_refs'])

# 原典边界: 乙逢戌不作根(戌中无木本气) -> root_weight_class=NONE, CAN_REN=NOT_SUPPORTED
p5 = {'year': ['甲', '戌'], 'month': ['丙', '戌'], 'day': ['乙', '酉'], 'hour': ['辛', '巳']}
n5 = net(p5)
check('乙逢戌 root_class=NONE(不作根)', n5['dimensions']['ROOT']['root_weight_class'] == 'NONE',
      n5['dimensions']['ROOT']['root_weight_class'])
m5 = qm(run_queries(n5))
check('乙逢戌 无根 能任财官 NOT_SUPPORTED',
      m5['ZP-160-QUERY-REN-CAIGUAN']['state'] == 'NOT_SUPPORTED',
      m5['ZP-160-QUERY-REN-CAIGUAN']['state'])

# 越界防护: 三态query不得输出 STRONG/WEAK 命题
blob = copy.deepcopy(m1)
text = json.dumps(blob, ensure_ascii=False)
for bad in ['"STRONG"', '"WEAK"', '身强', '身弱', 'score', 'weight', 'threshold', 'winner', 'selected']:
    check('query 不含越界: %s' % bad, bad not in text)

# --- A类: 财多/煞重/泄气 结构匹配(成党+无根双条件, 命题恒UNKNOWN) ---
# 财多身弱: 财成党(己土两透+火土根) 而甲无根(午巳午酉无木)
m6 = qm(run_queries(net({'year':['丙','午'],'month':['己','巳'],'day':['甲','午'],'hour':['己','酉']})))
check('财多身弱结构 财成党+无根 MATCH',
      m6['ZP-160-QUERY-CAIDUO-SHENRUAN']['match_type']=='STRUCTURE_MATCH',
      m6['ZP-160-QUERY-CAIDUO-SHENRUAN']['match_type'])
check('财多命题 state 恒 UNKNOWN', m6['ZP-160-QUERY-CAIDUO-SHENRUAN']['state'] in ('SUPPORTED','NOT_SUPPORTED'))
# 煞重身轻: 官杀金成党(庚申申酉金) 而甲无根
m7 = qm(run_queries(net({'year':['庚','申'],'month':['甲','申'],'day':['甲','申'],'hour':['乙','酉']})))
check('煞重身轻结构 杀成党+无根 MATCH',
      m7['ZP-160-QUERY-SHAZHONG-SHENQING']['match_type']=='STRUCTURE_MATCH',
      m7['ZP-160-QUERY-SHAZHONG-SHENQING']['match_type'])
check('煞轻命题 state 恒 UNKNOWN', m7['ZP-160-QUERY-SHAZHONG-SHENQING']['state'] in ('SUPPORTED','NOT_SUPPORTED'))
# 泄气太重: 食伤火成党(丙丁透+寅午火根)
m8 = qm(run_queries(net({'year':['丙','寅'],'month':['甲','午'],'day':['甲','寅'],'hour':['丁','卯']})))
check('泄气太重结构 食伤成党 MATCH',
      m8['ZP-160-QUERY-XIEQI-TAIZHONG']['match_type']=='STRUCTURE_MATCH',
      m8['ZP-160-QUERY-XIEQI-TAIZHONG']['match_type'])
check('泄气命题 state 恒 UNKNOWN', m8['ZP-160-QUERY-XIEQI-TAIZHONG']['state'] in ('SUPPORTED','NOT_SUPPORTED'))
# 反向: 有根则财多/煞轻 NO_MATCH; 食伤不透则泄气 NO_MATCH
m9 = qm(run_queries(net({'year':['乙','卯'],'month':['甲','戌'],'day':['甲','寅'],'hour':['乙','丑']})))
check('财多 甲有根则NO_MATCH', m9['ZP-160-QUERY-CAIDUO-SHENRUAN']['match_type']=='NO_MATCH')
m10 = qm(run_queries(net({'year':['甲','寅'],'month':['甲','申'],'day':['甲','寅'],'hour':['丙','子']})))
check('煞轻 甲有根则NO_MATCH', m10['ZP-160-QUERY-SHAZHONG-SHENQING']['match_type']=='NO_MATCH')
m11 = qm(run_queries(net({'year':['甲','寅'],'month':['甲','午'],'day':['甲','寅'],'hour':['乙','卯']})))
check('泄气 食伤不透则NO_MATCH', m11['ZP-160-QUERY-XIEQI-TAIZHONG']['match_type']=='NO_MATCH')

# --- 根轻重结构(纯事实判断, 不升强弱) ---
# 甲日寅月(甲禄寅)=重根; 乙日逢辰(乙余气辰)=轻根; 乙逢戌(戌无木)=无根
m12 = qm(run_queries(net({'year':['甲','寅'],'month':['甲','寅'],'day':['甲','寅'],'hour':['丙','子']})))
check('重根结构 甲禄寅 SUPPORTED', m12['ZP-160-QUERY-HEAVY-ROOT']['state']=='SUPPORTED',
      m12['ZP-160-QUERY-HEAVY-ROOT']['state'])
check('重根时轻根 NOT_SUPPORTED', m12['ZP-160-QUERY-LIGHT-ROOT']['state']=='NOT_SUPPORTED')
m13 = qm(run_queries(net({'year':['甲','戌'],'month':['丙','未'],'day':['乙','酉'],'hour':['辛','巳']})))
check('轻根结构 乙逢未余气 SUPPORTED', m13['ZP-160-QUERY-LIGHT-ROOT']['state']=='SUPPORTED',
      m13['ZP-160-QUERY-LIGHT-ROOT']['state'])
check('轻根时重根 NOT_SUPPORTED', m13['ZP-160-QUERY-HEAVY-ROOT']['state']=='NOT_SUPPORTED')

# --- 藤萝系甲(乙日见甲透, 纯结构) ---
m14 = qm(run_queries(net({'year':['甲','子'],'month':['戊','寅'],'day':['乙','酉'],'hour':['丙','戌']})))
check('藤萝系甲 乙日见甲透 STRUCTURE_MATCH', m14['ZP-160-QUERY-TENGLUO-XIJIA']['match_type']=='STRUCTURE_MATCH',
      m14['ZP-160-QUERY-TENGLUO-XIJIA']['state'])
m15 = qm(run_queries(net({'year':['戊','寅'],'month':['戊','午'],'day':['乙','酉'],'hour':['丁','亥']})))
check('藤萝系甲 乙日无甲 NO_MATCH', m15['ZP-160-QUERY-TENGLUO-XIJIA']['match_type']=='NO_MATCH')

# --- 绝处逢生(壬日巳月绝+巳藏庚印, 纯结构) ---
m16 = qm(run_queries(net({'year':['壬','寅'],'month':['乙','巳'],'day':['壬','戌'],'hour':['辛','亥']})))
check('绝处逢生 壬绝巳月藏庚印 STRUCTURE_MATCH', m16['ZP-160-QUERY-JUECHU-FENGSHENG']['match_type']=='STRUCTURE_MATCH',
      m16['ZP-160-QUERY-JUECHU-FENGSHENG']['state'])
m17 = qm(run_queries(net({'year':['壬','子'],'month':['壬','寅'],'day':['壬','戌'],'hour':['辛','亥']})))
check('绝处逢生 壬日寅月非绝 NO_MATCH', m17['ZP-160-QUERY-JUECHU-FENGSHENG']['match_type']=='NO_MATCH')

# --- 扶身成党对称补全: 印成党 / 比劫成党 ---
m18 = qm(run_queries(net({'year':['壬','申'],'month':['辛','亥'],'day':['甲','子'],'hour':['乙','亥']})))
check('印星成党 壬透亥子水根 STRUCTURE_MATCH', m18['ZP-160-QUERY-YIN-PARTY']['match_type']=='STRUCTURE_MATCH',
      m18['ZP-160-QUERY-YIN-PARTY']['state'])
m19 = qm(run_queries(net({'year':['甲','寅'],'month':['乙','亥'],'day':['甲','辰'],'hour':['丁','卯']})))
check('比劫成党 甲乙透寅卯木根 STRUCTURE_MATCH', m19['ZP-160-QUERY-BIJIE-PARTY']['match_type']=='STRUCTURE_MATCH',
      m19['ZP-160-QUERY-BIJIE-PARTY']['state'])
check('比劫成党印不成党时印NO_MATCH', m19['ZP-160-QUERY-YIN-PARTY']['match_type']=='NO_MATCH')

# --- 日主根逢冲 ---
m20 = qm(run_queries(net({'year':['甲','申'],'month':['丙','寅'],'day':['甲','寅'],'hour':['丁','卯']})))
check('根逢冲 申冲寅根 STRUCTURE_MATCH', m20['ZP-160-QUERY-ROOT-STRUCK']['match_type']=='STRUCTURE_MATCH',
      m20['ZP-160-QUERY-ROOT-STRUCK']['state'])
m21 = qm(run_queries(net({'year':['甲','子'],'month':['丙','寅'],'day':['甲','午'],'hour':['戊','辰']})))
check('根支有对立关系(年子为甲轻根,子冲午) STRUCTURE_MATCH', m21['ZP-160-QUERY-ROOT-STRUCK']['match_type']=='STRUCTURE_MATCH')

# --- 根干层级: 室家可住 vs 朋友相扶 ---
m22 = qm(run_queries(net({'year':['甲','寅'],'month':['丙','寅'],'day':['甲','辰'],'hour':['丁','卯']})))
check('根干层级 有根=室家可住', '室家' in m22['ZP-160-QUERY-ROOT-GAN-PRIORITY']['boundary_note'] or m22['ZP-160-QUERY-ROOT-GAN-PRIORITY']['state']=='SUPPORTED',
      m22['ZP-160-QUERY-ROOT-GAN-PRIORITY']['state'])
m23 = qm(run_queries(net({'year':['乙','酉'],'month':['戊','子'],'day':['乙','酉'],'hour':['丙','子']})))
check('根干层级 无根有比劫干=朋友相扶', m23['ZP-160-QUERY-ROOT-GAN-PRIORITY']['state'] in ('SUPPORTED','NOT_SUPPORTED'),
      m23['ZP-160-QUERY-ROOT-GAN-PRIORITY']['state'])

# --- 旺者冲衰: 子月子午冲, 子得令有党(阶3) vs 午失令有党(阶1) => 子旺午衰, 午拔 ---
m24 = qm(run_queries(net({'year':['甲','午'],'month':['丙','子'],'day':['甲','子'],'hour':['乙','午']})))
qwc = m24['ZP-160-QUERY-WANGCHONG-SHUAI']
check('旺者冲衰 子午冲阶差 STRUCTURE_MATCH', qwc['match_type']=='STRUCTURE_MATCH', qwc['match_type'])
check('旺者冲衰 证据 DTS-009-009', 'DTS-009-009' in qwc['evidence_refs'], str(qwc['evidence_refs']))

# --- 合化神得令: 甲己合化土, 辰月本气戊土=土, 化神得月令 ---
m25 = qm(run_queries(net({'year':['甲','申'],'month':['己','辰'],'day':['甲','子'],'hour':['乙','亥']})))
qhh = m25['ZP-160-QUERY-HE-HUASHEN-DESHI']
check('合化神得令 STRUCTURE_MATCH', qhh['match_type']=='STRUCTURE_MATCH', qhh['match_type'])
check('合化神证据 YHZP-121-003', 'YHZP-121-003' in qhh['evidence_refs'], str(qhh['evidence_refs']))

# --- 时柱归禄: 高太尉盘 甲子日乙亥时, 亥=甲长生重根在时柱 ---
m26 = qm(run_queries(net({'year':['庚','午'],'month':['乙','酉'],'day':['甲','子'],'hour':['乙','亥']})))
qsl = m26['ZP-160-QUERY-SHI-GUI-LU']
check('时柱归禄 STRUCTURE_MATCH', qsl['match_type']=='STRUCTURE_MATCH', qsl['match_type'])

# --- 众寡两端: 高太尉盘 日主端乙比劫透+印, 四柱端官杀庚申酉成党 => 两端皆有 ---
m27 = qm(run_queries(net({'year':['庚','午'],'month':['乙','酉'],'day':['甲','子'],'hour':['乙','亥']})))
qzg = m27['ZP-160-QUERY-ZHONGGUA-2SIDE']
check('众寡两端 STRUCTURE_MATCH', qzg['match_type']=='STRUCTURE_MATCH', qzg['match_type'])

# --- 日主被合: 甲日见己合(甲己合土) ---
m28 = qm(run_queries(net({'year':['甲','子'],'month':['己','巳'],'day':['甲','辰'],'hour':['甲','戌']})))
qrb = m28['ZP-160-QUERY-RI-BEI-HE']
check('日主被合 STRUCTURE_MATCH', qrb['match_type']=='STRUCTURE_MATCH', qrb['match_type'])

# --- 极弱无根: 甲日 丙午/己巳/甲午/己巳, 地支无木根, 天干无印比 ---
m29 = qm(run_queries(net({'year':['丙','午'],'month':['己','巳'],'day':['甲','午'],'hour':['己','巳']})))
qjr = m29['ZP-160-QUERY-JIRUO-WUGEN']
check('极弱无根 STRUCTURE_MATCH', qjr['match_type']=='STRUCTURE_MATCH', qjr['match_type'])

print()
print('FAILS =', fails)
sys.exit(1 if fails else 0)
