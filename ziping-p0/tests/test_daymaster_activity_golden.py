# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, '.')
from engines.common.daymaster_activity import (
    build_activity_tou_cang, build_activity_clash_class, classify_clash_branch,
    ACTIVE_CANDIDATE, DORMANT, ABSENT_STATE,
    SHENGFANG_CLASH, KU_CLASH, BAI_CLASH)

fails = 0


def check(name, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('PASS' if cond else 'FAIL'), name, extra)


# ===== 模块① 透藏动静 =====
def tc_group(state, tou, cang):
    return {'state': state, 'tou': tou, 'cang': cang,
            'stem_pillars': [], 'hidden_pillars': []}


tc = {'groups': {
    'BIJIE': tc_group('TOU_CANG_BOTH', True, True),
    'YIN': tc_group('TOU_ONLY', True, False),
    'SHISHANG': tc_group('CANG_ONLY', False, True),
    'CAI': tc_group('ABSENT', False, False),
    'GUANSHA': tc_group('CANG_ONLY', False, True),
}}
a1 = build_activity_tou_cang(tc)
g = a1['groups']
check('透藏俱备->ACTIVE_CANDIDATE', g['BIJIE']['activity_state'] == ACTIVE_CANDIDATE)
check('只透->ACTIVE_CANDIDATE', g['YIN']['activity_state'] == ACTIVE_CANDIDATE)
check('只藏->DORMANT', g['SHISHANG']['activity_state'] == DORMANT)
check('不现->ABSENT', g['CAI']['activity_state'] == ABSENT_STATE)
check('官杀藏->DORMANT', g['GUANSHA']['activity_state'] == DORMANT)

# 边界: 判定字段无有力/无用/吉/凶/STRONG/WEAK
blob1 = json.dumps(g, ensure_ascii=False)
for bad in ['有力', '无力', '无用', '吉', '凶', 'STRONG', 'WEAK', 'score']:
    ok = bad not in blob1
    if not ok:
        fails += 1
    check('动静判定字段禁用词:' + bad, ok)

# ===== 模块② 冲支三类 =====
# 六冲: 寅申/巳亥(生方) 辰戌/丑未(库) 子午/卯酉(败)
check('寅=生方冲', classify_clash_branch('寅') == SHENGFANG_CLASH)
check('申=生方冲', classify_clash_branch('申') == SHENGFANG_CLASH)
check('巳=生方冲', classify_clash_branch('巳') == SHENGFANG_CLASH)
check('亥=生方冲', classify_clash_branch('亥') == SHENGFANG_CLASH)
check('辰=库冲', classify_clash_branch('辰') == KU_CLASH)
check('戌=库冲', classify_clash_branch('戌') == KU_CLASH)
check('丑=库冲', classify_clash_branch('丑') == KU_CLASH)
check('未=库冲', classify_clash_branch('未') == KU_CLASH)
check('子=败冲UNKNOWN', classify_clash_branch('子') == BAI_CLASH)
check('午=败冲UNKNOWN', classify_clash_branch('午') == BAI_CLASH)
check('卯=败冲UNKNOWN', classify_clash_branch('卯') == BAI_CLASH)
check('酉=败冲UNKNOWN', classify_clash_branch('酉') == BAI_CLASH)

# mock D8 输出: 月根寅逢申冲(生方), 日根辰逢戌冲(库), 时根子逢午冲(败)
rr = {'root_branch_relations': {
    'month': {'branch': '寅', 'is_root': True, 'relations': [
        {'relation': 'CLASH', 'with_branches': ['申']}]},
    'day': {'branch': '辰', 'is_root': True, 'relations': [
        {'relation': 'CLASH', 'with_branches': ['戌']}]},
    'hour': {'branch': '子', 'is_root': True, 'relations': [
        {'relation': 'CLASH', 'with_branches': ['午']}]},
    'year': {'branch': '午', 'is_root': False, 'relations': [
        {'relation': 'CLASH', 'with_branches': ['子']}]},
}}
a2 = build_activity_clash_class(rr)
p = a2['root_clash_pillars']
check('月寅生方冲', p['month']['clash_class'] == SHENGFANG_CLASH and p['month']['with_branches'] == ['申'])
check('日辰库冲', p['day']['clash_class'] == KU_CLASH)
check('时子败冲UNKNOWN', p['hour']['clash_class'] == BAI_CLASH)
check('非根支不标注', 'year' not in p)

# 合/刑关系不产生 clash 标注
rr2 = {'root_branch_relations': {
    'month': {'branch': '寅', 'is_root': True, 'relations': [
        {'relation': 'TRIPLE_COMBINE', 'with_branches': ['午', '戌']}]}}}
check('合局不产生冲类', build_activity_clash_class(rr2)['root_clash_pillars'] == {})

# 边界: 判定字段无根拔/伤/发/吉/凶/STRONG/WEAK
blob2 = json.dumps(p, ensure_ascii=False)
for bad in ['根拔', '伤根', '旺者发', '衰者拔', '吉', '凶', 'STRONG', 'WEAK']:
    ok = bad not in blob2
    if not ok:
        fails += 1
    check('冲类判定字段禁用词:' + bad, ok)



# ===== 模块③ 合去归属(真实 L0 build) =====
from engines.common.l0_fact_builder import build as _build
from engines.common.daymaster_activity import build_activity_combine_away, DAYMASTER_BOUND_COMBINE, COMBINE_AWAY, CONTROL_NEGOTIATED

def _comb(p):
    return build_activity_combine_away(_build(p))['adjacent_combines']

# 年己月甲 甲日主: 年月相邻, 己财被甲比肩合走, 日主非合方
c1 = _comb({'year':'己丑','month':'甲子','day':'甲寅','hour':'丙寅'})
k1 = [x for x in c1 if x['pillars']==['year','month']][0]
check('年己月甲=合去候选', k1['kind']==COMBINE_AWAY and '正财' in k1['combined_ten_gods'])
check('财被合非克神', k1['control_negotiated'] is False)

# 年丁月壬 丙日主: 壬七杀被丁合, 贪合忘克前提
c2 = _comb({'year':'丁酉','month':'壬辰','day':'丙寅','hour':'甲午'})
k2 = c2[0]
check('七杀被合=贪合忘克候选', k2['control_negotiated'] is True and k2['control_kind']==CONTROL_NEGOTIATED)

# 月己日甲 甲日主: 月日相邻日主被合(同时年月也有比肩合财)
c3 = _comb({'year':'甲子','month':'己巳','day':'甲寅','hour':'丙寅'})
kinds3 = [(tuple(x['pillars']), x['kind']) for x in c3]
check('月日=日主被合候选', (('month','day'), DAYMASTER_BOUND_COMBINE) in kinds3)
check('年月=比肩合财去', any(p==('year','month') and k==COMBINE_AWAY for p,k in kinds3))

# 隔位(年己日甲, 月丙时甲): 无相邻合
c4 = _comb({'year':'己丑','month':'丙寅','day':'甲寅','hour':'甲子'})
check('隔位不论合', c4==[])

# 边界: 判定字段无成败/化真/争合/吉凶/STRONG/WEAK
blob3 = json.dumps(c3, ensure_ascii=False)
for bad in ['无用','化真','争合','妒合','吉','凶','STRONG','WEAK','喜神']:
    ok = bad not in blob3
    if not ok: fails+=1
    check('合去判定字段禁用词:'+bad, ok)


# ===== 模块④ 通关候选 =====
from engines.common.daymaster_activity import (
    build_activity_pass_through,
    PASS_THROUGH_CANDIDATE as _PTC, PASS_THROUGH_DORMANT as _PTD,
    NO_PASS_THROUGH as _NPT, SIDES_INACTIVE as _SI, OBSTRUCTED_BY_COMBINE as _OBC)
from engines.common.daymaster_tou_cang import build_tou_cang as _btc


def _pt(pl):
    _f = _build(pl)
    _tc = _btc(_f)
    _ca = build_activity_combine_away(_f)
    return build_activity_pass_through(_tc, _ca)['pass_through']


def _row(rows, pair):
    return [x for x in rows if x['pair'] == list(pair)][0]


# 杀-身 印通关: 印透=CANDIDATE / 印藏=DORMANT / 真无印=NO_PASS
r_a = _row(_pt({'year': '庚午', 'month': '壬申', 'day': '甲寅', 'hour': '乙亥'}),
           ('GUANSHA', 'BIJIE'))
check('杀身两端透+印透=通关候选', r_a['state'] == _PTC)
r_b = _row(_pt({'year': '庚午', 'month': '甲申', 'day': '甲寅', 'hour': '乙亥'}),
           ('GUANSHA', 'BIJIE'))
check('杀身透+印仅藏=DORMANT', r_b['state'] == _PTD)
r_c = _row(_pt({'year': '庚戌', 'month': '甲卯', 'day': '甲寅', 'hour': '乙巳'}),
           ('GUANSHA', 'BIJIE'))
check('杀身透+真无印=NO_PASS', r_c['state'] == _NPT)

# 一端未透发动 -> SIDES_INACTIVE (杀仅藏, 身透)
r_d = _row(_pt({'year': '甲戌', 'month': '甲卯', 'day': '甲寅', 'hour': '乙亥'}),
           ('GUANSHA', 'BIJIE'))
check('杀藏身透=两端未俱发动', r_d['state'] == _SI)

# 四组配对完备
_pairs = {tuple(x['pair']) for x in _pt({'year': '庚午', 'month': '壬申', 'day': '甲寅', 'hour': '乙亥'})}
check('通关四组完备', _pairs == {('GUANSHA', 'BIJIE'), ('BIJIE', 'CAI'),
                                 ('CAI', 'YIN'), ('SHISHANG', 'GUANSHA')})

# 阻隔 mock: 两端透+通关透, 但通关透干被相邻他干合走
_tc_mock = {'groups': {g: {'tou': True, 'cang': True} for g in
                       ['BIJIE', 'YIN', 'SHISHANG', 'CAI', 'GUANSHA']}}
_ca_mock = {'adjacent_combines': [
    {'kind': COMBINE_AWAY, 'combined_ten_gods': ['正印', '伤官'], 'pillars': ['year', 'month']}]}
_r_mock = _row(build_activity_pass_through(_tc_mock, _ca_mock)['pass_through'],
               ('GUANSHA', 'BIJIE'))
check('通关印被合=阻隔候选', _r_mock['obstructed_by_combine'] is True
      and _r_mock['obstruction_kind'] == _OBC)

# 边界禁用词(判定字段)
_blob = json.dumps([r_a, r_b, r_c, r_d, _r_mock], ensure_ascii=False)
for bad in ['有情', '通关成', '能胜', '吉', '凶', 'STRONG', 'WEAK', '用神']:
    ok = bad not in _blob
    if not ok:
        fails += 1
    check('通关判定字段禁用词:' + bad, ok)


# ===== 模块⑤ 成势候选 =====
from engines.common.daymaster_activity import (
    build_activity_formation, FORMATION_CANDIDATE as _FC,
    FORMED_NOT_TRANSPARENT as _FNT)


def _fm(pl):
    return build_activity_formation(_build(pl))['formations']


# 申子辰水局 壬透 戊日主: 水=财, 透年时
f1 = _fm({'year': '壬申', 'month': '甲子', 'day': '戊辰', 'hour': '壬子'})
z1 = [x for x in f1 if x['kind'] == 'SANHE'][0]
check('水局透干=成势候选', z1['state'] == _FC and z1['formed_element'] == '水')
check('水局相对戊=财', z1['daymaster_relation'] == 'CAI')
check('水透年时柱位', set(z1['transparent_pillars']) == {'year', 'hour'})

# 水局成而水不透
f2 = _fm({'year': '庚申', 'month': '丙子', 'day': '戊辰', 'hour': '戊午'})
z2 = [x for x in f2 if x['kind'] == 'SANHE'][0]
check('水局不透=未引候选', z2['state'] == _FNT and z2['transparent'] is False)

# 寅卯辰三会木 甲透 戊日主: 木=官杀
f3 = _fm({'year': '甲寅', 'month': '乙卯', 'day': '戊辰', 'hour': '甲寅'})
z3 = [x for x in f3 if x['kind'] == 'SANHUI'][0]
check('三会木透=成势候选', z3['state'] == _FC and z3['daymaster_relation'] == 'GUANSHA')

# 无局
f4 = _fm({'year': '庚午', 'month': '壬申', 'day': '甲寅', 'hour': '乙亥'})
check('无合会局=空', f4 == [])

# 多局并列不裁(mock: 同时给三合水+三会木, 皆透)
_mock = {
    'combination_facts': {'sanhe': ['申子辰合水'], 'sanhui': ['寅卯辰三会木']},
    'stem_relations': {'year': {'stem': '壬'}, 'month': {'stem': '甲'}, 'hour': {'stem': '乙'}},
    'day_stem': '戊', 'daymaster_element': '土'}
_fm_mock = build_activity_formation(_mock)['formations']
check('多局并列不裁(2条)', len(_fm_mock) == 2
      and {x['formed_element'] for x in _fm_mock} == {'水', '木'})

# 边界禁用词(判定字段): 无最旺/源头/去取/胜负/富贵/化真/STRONG/WEAK
_blob5 = json.dumps(f1 + f3 + _fm_mock, ensure_ascii=False)
for bad in ['最旺', '最多', '源头', '去取', '胜负', '富贵', '化真', 'STRONG', 'WEAK', 'score', 'count']:
    ok = bad not in _blob5
    if not ok:
        fails += 1
    check('成势判定字段禁用词:' + bad, ok)

print()
print('FAILS', fails)
sys.exit(1 if fails else 0)
