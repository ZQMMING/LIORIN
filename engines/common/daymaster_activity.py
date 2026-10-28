# -*- coding: utf-8 -*-
"""PATCH-160 作用发动层 ACTIVITY（审计报告 governance/audit_effectiveness_report.md §4）

只描述"作用有没有发动的结构前提"(动/静/引动候选), 不描述作用成败/吉凶/强弱/用神.
全部状态为中性结构态(ACTIVE_CANDIDATE / DORMANT / *_CANDIDATE / UNKNOWN),
不含"有用/无用/成/败/拔/伤/吉/凶"等结论词.

本文件当前实现五个模块:
  ① 透藏动静 build_activity_tou_cang
  ② 冲支三类 build_activity_clash_class
  ③ 合去归属 build_activity_combine_away
  ④ 通关候选 build_activity_pass_through
  ⑤ 成势候选 build_activity_formation
化气候选 留 D10 专题, 默认不启用.

原典边界:
- 透=动候选: PZZQ-007-031(露而根深/藏而不露, A级); SFTK-006-002(透出方动物, B级病药派)
- 藏=静但非永无效: DTS-027-002(伏藏之神岁运冲扶则为患; 岁运属 PATCH-215 冻结, 本层不做引发)
- 冲三类: DTS-009-003/004/005/006
  四生方寅申巳亥逢冲=生方怕动(根动候选); 四库辰戌丑未逢冲=库宜开(开候选);
  四败子午卯酉逢冲=败地逢冲仔细推(UNKNOWN, 不硬判).
"""
from typing import Any, Dict, List, Optional

# ---- 通用发动态 ----
ACTIVE_CANDIDATE = 'ACTIVE_CANDIDATE'   # 发动前提具备(如透干于外), 仅"动候选", 非有力/有用
DORMANT = 'DORMANT'                     # 静(如藏而不透), 原局发动不彰, 非无力/无用
ABSENT_STATE = 'ABSENT'                 # 不现
UNKNOWN_STATE = 'UNKNOWN'               # 原典要求 case-by-case, fail-closed

# ---- 冲支三类 ----
SHENG_FANG = set('寅申巳亥')   # 四生方
KU = set('辰戌丑未')           # 四库
BAI_DI = set('子午卯酉')       # 四败(四旺)

SHENGFANG_CLASH = 'SHENGFANG_CLASH_ROOT_MOVED_CANDIDATE'  # 生方冲, 根动候选(不判伤)
KU_CLASH = 'KU_CLASH_OPENED_CANDIDATE'                    # 库冲, 开候选(不判吉凶)
BAI_CLASH = 'BAI_CLASH_UNKNOWN'                           # 败地冲, 原典命细推, UNKNOWN

_CLASH_NOTE = {
    SHENGFANG_CLASH: '四生方逢冲, 原典"生方怕动/冲则根动", 仅根动候选, 不判根拔伤根',
    KU_CLASH: '四库逢冲, 原典"库宜开", 仅开库候选, 不判开库吉凶',
    BAI_CLASH: '四败逢冲, 原典"败地逢冲仔细推", case-by-case, 不硬判',
}


def classify_clash_branch(branch: str) -> str:
    if branch in SHENG_FANG:
        return SHENGFANG_CLASH
    if branch in KU:
        return KU_CLASH
    if branch in BAI_DI:
        return BAI_CLASH
    return UNKNOWN_STATE


# ============ 模块① 透藏动静 ============
def build_activity_tou_cang(tou_cang: Dict[str, Any]) -> Dict[str, Any]:
    """输入 D13 build_tou_cang 输出. 透(含透藏俱备)=动候选; 藏而不透=静."""
    groups = {}
    for gname, g in (tou_cang or {}).get('groups', {}).items():
        tou = bool(g.get('tou'))
        cang = bool(g.get('cang'))
        if tou:
            state = ACTIVE_CANDIDATE
        elif cang:
            state = DORMANT
        else:
            state = ABSENT_STATE
        groups[gname] = {
            'activity_state': state,
            'tou': tou,
            'cang': cang,
            'tou_cang_state': g.get('state'),
        }
    return {
        'module': 'ACTIVITY_TOU_CANG',
        'patch': 'PATCH-160-ACTIVITY-1',
        'groups': groups,
        'judgment_status': 'ACTIVITY_STRUCTURE_ONLY',
        'boundary_note': (
            '透=发动候选(非有力/有用/吉), 藏不透=静(非无力/无用/废); '
            '藏者岁运引发属 PATCH-215 冻结不做; 盖头压制为 B 级涉运不做; 不输出 STRONG/WEAK'
        ),
        'evidence_refs': ['PZZQ-007-031', 'SFTK-006-002', 'DTS-027-002'],
    }


# ============ ACTIVITY 层组装(独立于 9 维结构网络, 消费已封板 D13/D8 输出) ============
def build_activity_layer(tou_cang: Dict[str, Any] = None,
                         root_relations: Dict[str, Any] = None,
                         facts: Dict[str, Any] = None) -> Dict[str, Any]:
    return {
        'layer': 'DAYMASTER_ACTIVITY',
        'patch': 'PATCH-160-ACTIVITY',
        'tou_cang_activity': build_activity_tou_cang(tou_cang or {'groups': {}}),
        'clash_class': build_activity_clash_class(root_relations or {}),
        'combine_away': build_activity_combine_away(facts or {}),
        'pass_through': build_activity_pass_through(
            tou_cang or {'groups': {}}, build_activity_combine_away(facts or {})),
        'formation': build_activity_formation(facts or {}),
        'judgment_status': 'ACTIVITY_STRUCTURE_ONLY_NO_EFFECT',
        'boundary_note': (
            '作用发动层: 仅记录动/静/引动前提(候选态); 不输出有用无用/成败/化真/成势/'
            '喜忌/吉凶/STRONG/WEAK; 成败层须另取用神授权; 岁运引发属 PATCH-215 冻结'
        ),
    }


# ============ 模块② 冲支三类 ============
def build_activity_clash_class(root_relations: Dict[str, Any]) -> Dict[str, Any]:
    """输入 D8 build_root_relations 输出. 对其中 relation=CLASH 的日主根支按地支三类标注."""
    per_pillar = {}
    for pillar, d in (root_relations or {}).get('root_branch_relations', {}).items():
        if not d.get('is_root'):
            continue
        for rel in d.get('relations', []):
            if rel.get('relation') == 'CLASH':
                cls = classify_clash_branch(d['branch'])
                per_pillar[pillar] = {
                    'branch': d['branch'],
                    'with_branches': rel.get('with_branches', []),
                    'clash_class': cls,
                }
    return {
        'module': 'ACTIVITY_CLASH_CLASS',
        'patch': 'PATCH-160-ACTIVITY-2',
        'root_clash_pillars': per_pillar,
        'judgment_status': 'ACTIVITY_STRUCTURE_ONLY',
        'boundary_note': (
            '仅按四生/四库/四败标注冲的发动类型; 不判根拔/伤根/衰者拔旺者发/开库吉凶; '
            '败地冲保持 UNKNOWN; 刑穿有动不动, 效力轻于冲, 不在本模块; 不输出 STRONG/WEAK'
        ),
        'evidence_refs': ['DTS-009-003', 'DTS-009-004', 'DTS-009-005', 'DTS-009-006', 'DTS-008-014'],
    }

# ============ 模块③ 合去归属(相邻天干五合) ============
# 五合无序对
_WUHE = {frozenset(p) for p in [('甲', '己'), ('乙', '庚'), ('丙', '辛'),
                                ('丁', '壬'), ('戊', '癸')]}
_POS = ['year', 'month', 'day', 'hour']
_ADJ = [('year', 'month'), ('month', 'day'), ('day', 'hour')]
_CONTROL_TG = {'正官', '七杀'}

DAYMASTER_BOUND_COMBINE = 'DAYMASTER_BOUND_COMBINE_CANDIDATE'   # 日主在合中, 被合/合它牵制候选
COMBINE_AWAY = 'COMBINE_AWAY_CANDIDATE'                         # 日主非合方, 他干相邻合, 日主无分候选
NO_SHARE = 'DAYMASTER_NO_SHARE_CANDIDATE'
CONTROL_NEGOTIATED = 'CONTROL_NEGOTIATED_BY_COMBINE_CANDIDATE'  # 克神(官杀)被合, 贪合忘克结构前提


def _is_wuhe(s1: str, s2: str) -> bool:
    return s1 and s2 and s1 != s2 and frozenset((s1, s2)) in _WUHE


def build_activity_combine_away(facts: Dict[str, Any]) -> Dict[str, Any]:
    """只认相邻三对(年月/月日/日时)的天干五合; 隔位不论(L0 wuhe 为跨柱全配对, 此处按贴身收束).

    日主在合中 -> DAYMASTER_BOUND_COMBINE_CANDIDATE(牵制候选, 不展开).
    日主非合方 -> COMBINE_AWAY_CANDIDATE(被合十神日主无分候选);
                  合中含官杀则另记 CONTROL_NEGOTIATED(贪合忘克结构前提).
    不判化真/争合妒合(D10 专题)/无用/吉凶/喜神.
    """
    sr = (facts or {}).get('stem_relations', {}) or {}
    day_stem = (facts or {}).get('day_stem')
    stem_at, tg_at = {'day': day_stem}, {'day': None}
    for pos in ('year', 'month', 'hour'):
        d = sr.get(pos) or {}
        stem_at[pos] = d.get('stem')
        tg_at[pos] = d.get('ten_god')

    combines: List[Dict[str, Any]] = []
    for p1, p2 in _ADJ:
        s1, s2 = stem_at.get(p1), stem_at.get(p2)
        if not _is_wuhe(s1, s2):
            continue
        in_combine = 'day' in (p1, p2)
        if in_combine:
            other_pos = p2 if p1 == 'day' else p1
            combines.append({
                'pillars': [p1, p2], 'stems': [s1, s2],
                'kind': DAYMASTER_BOUND_COMBINE,
                'other_pillar': other_pos,
                'other_stem': stem_at.get(other_pos),
                'other_ten_god': tg_at.get(other_pos),
            })
        else:
            t1, t2 = tg_at.get(p1), tg_at.get(p2)
            control = bool(_CONTROL_TG & {t1, t2})
            combines.append({
                'pillars': [p1, p2], 'stems': [s1, s2], 'ten_gods': [t1, t2],
                'kind': COMBINE_AWAY,
                'daymaster_share': NO_SHARE,
                'combined_ten_gods': [t for t in (t1, t2) if t],
                'control_negotiated': control,
                'control_kind': CONTROL_NEGOTIATED if control else None,
            })
    return {
        'module': 'ACTIVITY_COMBINE_AWAY',
        'patch': 'PATCH-160-ACTIVITY-3',
        'adjacent_combines': combines,
        'judgment_status': 'ACTIVITY_STRUCTURE_ONLY',
        'boundary_note': (
            '只认相邻天干五合(年月/月日/日时), 隔位不论; COMBINE_AWAY 仅表他干合去、日主无分候选, '
            '不指定谁夺谁/不判因合无用; control_negotiated 仅表官杀克神被合牵制(贪合忘克前提), '
            '不判制刃成败; 日主在合中仅记牵制候选; 化真/争合妒合归 D10; 不输出 STRONG/WEAK/用神/吉凶'
        ),
        'evidence_refs': ['PZZQ-005-004', 'PZZQ-007-031'],
    }


# ============ 模块④ 通关候选 ============
PASS_THROUGH_CANDIDATE = 'PASS_THROUGH_CANDIDATE'   # 相战两端俱透发动 + 通关神透干
PASS_THROUGH_DORMANT = 'PASS_THROUGH_DORMANT'       # 两端俱透 + 通关神仅藏(不引)
NO_PASS_THROUGH = 'NO_PASS_THROUGH_STRUCTURE'       # 两端俱透 + 通关神不现
SIDES_INACTIVE = 'SIDES_INACTIVE'                   # 相战两端未俱透发动(藏/缺), 原局不论通关
OBSTRUCTED_BY_COMBINE = 'OBSTRUCTED_BY_COMBINE_CANDIDATE'

_TG_TO_GROUP = {
    '比肩': 'BIJIE', '劫财': 'BIJIE',
    '正印': 'YIN', '偏印': 'YIN',
    '食神': 'SHISHANG', '伤官': 'SHISHANG',
    '正财': 'CAI', '偏财': 'CAI',
    '正官': 'GUANSHA', '七杀': 'GUANSHA',
}
# (端A, 端B, 通关神): 相邻相克链以通关五行桥接(对齐 DTS-019 木土得火/火金得土/土水得金/金木得水)
_PASS_THROUGH = [
    ('GUANSHA', 'BIJIE', 'YIN'),       # 官杀克身, 印通关(杀印相生)
    ('BIJIE', 'CAI', 'SHISHANG'),      # 比劫-财(夺财/耗身), 食伤通关(身生食伤生财)
    ('CAI', 'YIN', 'GUANSHA'),         # 财坏印, 官杀通关(财生官杀生印)
    ('SHISHANG', 'GUANSHA', 'CAI'),    # 食伤制杀, 财通关(食伤生财生官杀)
]


def _grp_state(tou_cang: Dict[str, Any], grp: str) -> str:
    g = (tou_cang or {}).get('groups', {}).get(grp)
    if not g:
        return 'absent'
    if g.get('tou'):
        return 'tou'
    if g.get('cang'):
        return 'cang'
    return 'absent'


def build_activity_pass_through(tou_cang: Dict[str, Any],
                                combine_away: Dict[str, Any] = None) -> Dict[str, Any]:
    # 确定性阻隔之一: 通关透干被相邻他干合走(复用模块③ COMBINE_AWAY)
    away_groups = set()
    for c in (combine_away or {}).get('adjacent_combines', []):
        if c.get('kind') == COMBINE_AWAY:
            for tg in c.get('combined_ten_gods', []):
                if tg in _TG_TO_GROUP:
                    away_groups.add(_TG_TO_GROUP[tg])

    rows = []
    for side_a, side_b, pt in _PASS_THROUGH:
        sa, sb, sp = (_grp_state(tou_cang, side_a),
                      _grp_state(tou_cang, side_b),
                      _grp_state(tou_cang, pt))
        if sa != 'tou' or sb != 'tou':
            state = SIDES_INACTIVE       # 相战两端未俱透发动, 原局静, 不论通关
        elif sp == 'tou':
            state = PASS_THROUGH_CANDIDATE
        elif sp == 'cang':
            state = PASS_THROUGH_DORMANT
        else:
            state = NO_PASS_THROUGH
        rows.append({
            'pair': [side_a, side_b],
            'pass_through_group': pt,
            'side_states': [sa, sb],
            'pass_state': sp,
            'state': state,
            'obstructed_by_combine': bool(state == PASS_THROUGH_CANDIDATE and pt in away_groups),
            'obstruction_kind': OBSTRUCTED_BY_COMBINE
                if (state == PASS_THROUGH_CANDIDATE and pt in away_groups) else None,
        })
    return {
        'module': 'ACTIVITY_PASS_THROUGH',
        'patch': 'PATCH-160-ACTIVITY-4',
        'pass_through': rows,
        'judgment_status': 'ACTIVITY_STRUCTURE_ONLY',
        'boundary_note': (
            '相战两端须俱透发动方论通关(仅藏/缺=SIDES_INACTIVE); 通关神透干仅引化前提, 非通关成; '
            '两端俱透不等于真成相战; obstructed_by_combine 仅表通关透干被相邻合走; '
            '悬隔/间物/刑冲/劫占/能胜补缺/通关有情成功均未评估并 HOLD; 不输出 STRONG/WEAK/用神/吉凶'
        ),
        'evidence_refs': ['DTS-019-001', 'DTS-019-002'],
    }


# ============ 模块⑤ 成势候选(三合/三会全成局 + 透干引化) ============
FORMATION_CANDIDATE = 'FORMATION_TRANSPARENT_CANDIDATE'        # 全三支成局 + 局五行透干引化
FORMED_NOT_TRANSPARENT = 'FORMED_NOT_TRANSPARENT_CANDIDATE'    # 全三支成局但局五行未透(未引)

_STEM_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
            '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
_WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 我生
_WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}      # 我克
_BRANCH_WX = {'寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火',
              '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水',
              '子': '水', '丑': '土'}


def _wx_to_group(day_wx: str, target_wx: str) -> Optional[str]:
    """局五行相对日主五行的十神大类(同我/生我/我生/克我/我克)."""
    if not day_wx or not target_wx:
        return None
    if day_wx == target_wx:
        return 'BIJIE'
    if _WX_SHENG.get(day_wx) == target_wx:
        return 'SHISHANG'
    if _WX_KE.get(day_wx) == target_wx:
        return 'CAI'
    if _WX_KE.get(target_wx) == day_wx:
        return 'GUANSHA'
    if _WX_SHENG.get(target_wx) == day_wx:
        return 'YIN'
    return None


def _parse_formation(text: str, kind: str):
    """'申子辰合水'/'寅卯辰三会木' -> (支列表, 局五行)."""
    elem = text[-1]
    key = '三会' if kind == 'SANHUI' else '合'
    head = text.split(key)[0]
    branches = [ch for ch in head if ch in _BRANCH_WX]
    return branches, elem


def build_activity_formation(facts: Dict[str, Any]) -> Dict[str, Any]:
    comb = (facts or {}).get('combination_facts', {}) or {}
    sr = (facts or {}).get('stem_relations', {}) or {}
    day_stem = (facts or {}).get('day_stem')
    day_wx = (facts or {}).get('daymaster_element')

    # 天干五行 -> 柱位
    stem_wx_pillars = {}
    for pos in ('year', 'month', 'hour'):
        st = (sr.get(pos) or {}).get('stem')
        if st:
            stem_wx_pillars.setdefault(_STEM_WX.get(st), []).append(pos)
    if day_stem:
        stem_wx_pillars.setdefault(_STEM_WX.get(day_stem), []).append('day')

    formations = []
    for kind, key in (('SANHE', 'sanhe'), ('SANHUI', 'sanhui')):
        for text in (comb.get(key) or []):
            branches, elem = _parse_formation(text, kind)
            tou_pillars = stem_wx_pillars.get(elem, [])
            transparent = len(tou_pillars) > 0
            formations.append({
                'kind': kind,
                'text': text,
                'branches': branches,
                'formed_element': elem,
                'transparent': transparent,
                'transparent_pillars': tou_pillars,
                'daymaster_relation': _wx_to_group(day_wx, elem),
                'state': FORMATION_CANDIDATE if transparent else FORMED_NOT_TRANSPARENT,
            })
    return {
        'module': 'ACTIVITY_FORMATION',
        'patch': 'PATCH-160-ACTIVITY-5',
        'formations': formations,
        'judgment_status': 'ACTIVITY_STRUCTURE_ONLY',
        'boundary_note': (
            '仅记录三合/三会全三支成局及局五行是否透干引化; 多局并列不裁; 不做"最多最旺"计数, '
            '不判源头归属/势在去取/众寡胜负/顺局富贵; 局五行是组合属性, 非日干化气(化气归 D10); '
            '成局未透仅未引, 不判不成; 不输出 STRONG/WEAK/用神/吉凶'
        ),
        'evidence_refs': ['DTS-018-001', 'DTS-018-002', 'DTS-009-005'],
    }
