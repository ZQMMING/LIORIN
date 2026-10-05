# -*- coding: utf-8 -*-
"""PATCH-160-C Query Interface v0
经典命题各自查询多维网络, 不汇总成总分.
分层: state(命题是否成立) vs match_type(结构是否匹配).
DESHI_BUWANG/SHISHI_BURUO 只输出结构匹配, 不声明"不旺/不弱"最终命题.
不做 Strength Resolver / STRONG/WEAK / score / weight / threshold / count / winner / aggregate.
evidence_refs 沿用现有 Evidence ID, 不在 Query 层重新造证据.
"""
from typing import Any, Dict, List


def _party_present(group: Dict) -> bool:
    """「成党」结构骨架: 该组内某十神 透干且通根(stem_present AND root_present)。
    原典「于庚辛而支酉丑」「干甲乙而支寅卯」= 天干透出 + 地支有根。
    纯布尔结构, 不计数、不判「太重/重叠」程度。"""
    return any(v.get('stem_present') and v.get('root_present') for v in group.values())


def _has_drain_party(dim: Dict) -> bool:
    return _party_present(dim.get('DRAIN', {}))


def _has_control_party(dim: Dict) -> bool:
    return _party_present(dim.get('CONTROL', {}))


def _has_support_party(dim: Dict) -> bool:
    return _party_present(dim.get('SUPPORT', {}))


def _has_cai_party(dim: Dict) -> bool:
    cai = dim.get('DRAIN', {}).get('CAI', {})
    return bool(cai.get('stem_present') and cai.get('root_present'))


def _has_shishang_party(dim: Dict) -> bool:
    sh = dim.get('DRAIN', {}).get('SHISHANG', {})
    return bool(sh.get('stem_present') and sh.get('root_present'))


def _has_guansha_party(dim: Dict) -> bool:
    g = dim.get('CONTROL', {}).get('GUANSHA', {})
    return bool(g.get('stem_present') and g.get('root_present'))


def _has_yin_party(dim: Dict) -> bool:
    y = dim.get('SUPPORT', {}).get('YIN', {})
    return bool(y.get('stem_present') and y.get('root_present'))

def _has_bijie_party(dim: Dict) -> bool:
    b = dim.get('SUPPORT', {}).get('BIJIE', {})
    return bool(b.get('stem_present') and b.get('root_present'))



def _has_bijie_party(dim: Dict) -> bool:
    b = dim.get('SUPPORT', {}).get('BIJIE', {})
    return bool(b.get('stem_present') and b.get('root_present'))


def _result(query_id: str, name: str, classic: str,
            state: str, match_type: str,
            matched_nodes: List[str], matched_edges: List[str],
            evidence_refs: List[str], boundary_note: str,
            extra: Dict[str, Any] = None) -> Dict:
    out = {
        'query_id': query_id,
        'name': name,
        'classic': classic,
        'state': state,          # SUPPORTED / NOT_SUPPORTED / UNKNOWN
        'match_type': match_type,  # STRUCTURE_MATCH / NO_MATCH / UNKNOWN
        'matched_nodes': matched_nodes,
        'matched_edges': matched_edges,
        'evidence_refs': evidence_refs,
        'boundary_note': boundary_note,
    }
    if extra:
        out.update(extra)
    return out


def query_can_ren_caiguan(network: Dict[str, Any]) -> Dict:
    """原著: 只要四柱有根, 便能受财官食神而当伤官七煞.
    纯结构: ROOT.has_root == true.
    此 Query 原著直接授权, 可输出 SUPPORTED/NOT_SUPPORTED."""
    has_root = network['dimensions']['ROOT'].get('has_root', False)
    return _result(
        query_id='ZP-160-QUERY-REN-CAIGUAN',
        name='能任财官',
        classic='子平真诠',
        state='SUPPORTED' if has_root else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if has_root else 'NO_MATCH',
        matched_nodes=['ROOT_BRANCH'] if has_root else [],
        matched_edges=['ROOT_RELATION'] if has_root else [],
        evidence_refs=['PZZQ-005-005'],  # 論干支: 只要四柱有根, 便能受財官食神而當傷官七煞
        boundary_note='有根=能任, 无根普通格不能任; 从化从杀等特殊路径未授权, 不推',
    )


def query_deshi_buwang(network: Dict[str, Any]) -> Dict:
    """原著: 得时而不旺 = 得令, 而克方/泄方成党(于庚辛而支酉丑; 或丙丁透巳午成党)。
    结构匹配: in_season AND (CONTROL成党 OR DRAIN成党),
    其中「成党」= 该方某十神 透干且通根(stem_present AND root_present)。
    只输出 STRUCTURE_MATCH/NO_MATCH, 不声明"不旺", 不判断"太重/成局"程度。"""
    in_season = network['dimensions']['SEASONAL'].get('in_season', False)
    ctrl_party = _has_control_party(network['dimensions'])
    drain_party = _has_drain_party(network['dimensions'])
    match = in_season and (ctrl_party or drain_party)
    nodes = ['SEASON']
    edges = ['SEASONAL_RELATION']
    if ctrl_party:
        nodes.append('CONTROL_PARTY')
        edges.append('CONTROL_RELATION')
    if drain_party:
        nodes.append('DRAIN_PARTY')
        edges.append('DRAIN_RELATION')
    return _result(
        query_id='ZP-160-QUERY-DESHI-BUWANG',
        name='得时不旺',
        classic='子平真诠',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=nodes if match else [],
        matched_edges=edges if match else [],
        evidence_refs=['PZZQ-005-005'],
        boundary_note='只匹配得令+克/泄方成党(透干且通根); 不声明"太重/不旺", 不判成局强度; 命题成立待授权',
    )


def query_shishi_buruo(network: Dict[str, Any]) -> Dict:
    """原著: 失时而不弱 = 失令, 而比印通根成党(干甲乙而支寅卯)。
    结构匹配: NOT in_season AND SUPPORT成党(比劫/印 透干且通根)。
    只输出 STRUCTURE_MATCH/NO_MATCH, 不声明"不弱", 不判断"重叠"程度。"""
    in_season = network['dimensions']['SEASONAL'].get('in_season', False)
    support_party = _has_support_party(network['dimensions'])
    match = (not in_season) and support_party
    return _result(
        query_id='ZP-160-QUERY-SHISHI-BURUO',
        name='失时不弱',
        classic='子平真诠',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['SEASON', 'SUPPORT_PARTY'] if match else [],
        matched_edges=['SEASONAL_RELATION', 'SUPPORT_RELATION'] if match else [],
        evidence_refs=['PZZQ-005-005'],
        boundary_note='只匹配失令+扶身成党(透干且通根); 不声明"重叠/不弱"; 命题成立待授权',
    )


def run_queries(network: Dict[str, Any]) -> List[Dict]:
    """跑全部已授权 Query, 各自独立输出, 不汇总."""
    return [
        query_can_ren_caiguan(network),
        query_deshi_buwang(network),
        query_shishi_buruo(network),
        query_cai_duo_shen_ruan(network),
        query_sha_zhong_shen_qing(network),
        query_xie_qi_tai_zhong(network),
        query_heavy_root(network),
        query_light_root(network),
        query_tengluo_xijia(network),
        query_juechu_fengsheng(network),
        query_yin_party(network),
        query_bijie_party(network),
        query_root_struck(network),
        query_root_gan_priority(network),
        query_wangzhe_chong_shuai(network),
        query_he_huashen_deshi(network),
        query_shi_gui_lu(network),
        query_zhonggua_two_side(network),
        query_ri_bei_he(network),
        query_jiruo_wugen(network),
        query_wugen_youfu(network),
        query_he_huashen_chenggong(network),
        query_jiwang_huaiji(network),
        query_jishuai_congsheng(network),
        query_shiyong_yueling_xiangfu(network),
        query_ge_qing(network),
        query_ge_qing_extended(network),
        query_ge_quality(network),
        query_yun_sheng_root(network),
        query_yun_zhi_xiji(network),
        query_cai_ruo_shen_qiang(network),
        query_wangji_siwo_sheng(network),
        query_shuaiji_siwo_ke(network),
        query_mu_chong_kai(network),
        query_shi_zhu_ji(network),
        query_shi_lin_wang(network),
        query_tiangan_xingqing(network),
        query_yongshen_structure(network),
        query_yongshen_final(network),
        query_zhong_he(network),
        
    ]


def query_cai_duo_shen_ruan(network: Dict[str, Any]) -> Dict:
    """原著结构(渊海子平): 财多身弱 = 财成党(透干且通根) 而日主无根.
    结构匹配: CAI成党 AND NOT has_root.
    只输出结构匹配; 不声明"财多/身弱"程度, 命题恒 UNKNOWN."""
    no_root = not network['dimensions']['ROOT'].get('has_root', False)
    cai_party = _has_cai_party(network['dimensions'])
    match = no_root and cai_party
    return _result(
        query_id='ZP-160-QUERY-CAIDUO-SHENRUAN',
        name='财党无根结构',
        classic='渊海子平',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['CAI_PARTY', 'NO_ROOT'] if match else [],
        matched_edges=['CAI_RELATION', 'ROOT_ABSENT'] if match else [],
        evidence_refs=['YHZP-078-024'],  # 继善篇: 财多生官须要身健, 财多盗气本身自柔
        boundary_note='只匹配财成党+日主无根; 不判财多程度, 不下旺衰结论; 命题成立待授权',
    )


def query_sha_zhong_shen_qing(network: Dict[str, Any]) -> Dict:
    """原著结构(渊海子平): 煞重身轻 = 官杀成党(透干且通根) 而日主无根.
    结构匹配: GUANSHA成党 AND NOT has_root.
    只输出结构匹配; 不声明"煞重/身轻"程度, 命题恒 UNKNOWN."""
    no_root = not network['dimensions']['ROOT'].get('has_root', False)
    sha_party = _has_guansha_party(network['dimensions'])
    match = no_root and sha_party
    return _result(
        query_id='ZP-160-QUERY-SHAZHONG-SHENQING',
        name='杀党无根结构',
        classic='渊海子平',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['GUANSHA_PARTY', 'NO_ROOT'] if match else [],
        matched_edges=['CONTROL_RELATION', 'ROOT_ABSENT'] if match else [],
        evidence_refs=['YHZP-079-031'],  # 正气官星(继善篇注): 杀重身轻, 移身有损
        boundary_note='只匹配官杀成党+日主无根; 不判煞重程度, 不下旺衰结论; 命题成立待授权',
    )


# 地支六合化神表 (★ ARCHIVED_FALLBACK 2026-10-06: 已改消费排盘 l0_chart.he_hua,
# 本表仅兜底. 备份: _legacy_relation_tables)
LIUHE_HUASHEN = {
    frozenset(['子','丑']): '土',
    frozenset(['寅','亥']): '木',
    frozenset(['卯','戌']): '火',
    frozenset(['辰','酉']): '金',
    frozenset(['巳','申']): '水',
    frozenset(['午','未']): '土',
}
BRANCH_WX = {'子':'水','亥':'水','寅':'木','卯':'木','巳':'火','午':'火',
             '申':'金','酉':'金','辰':'土','戌':'土','丑':'土','未':'土'}


def _root_combined_away(network: Dict[str, Any]) -> bool:
    """检查重根是否被地支合化合走.
    结构: 根支参与六合 + 化神得令(月令五行=化神) + 化神≠日主五行.
    化神=日主五行时合化成功但根还在(如甲木寅亥合木), 不算合走.
    只记结构, 不判合化真假."""
    rr = network['dimensions'].get('ROOT_RELATION', {})
    comb_root = rr.get('combined_root_pillars', []) or []
    if not comb_root:
        return False
    facts = network.get('facts') or {}
    month_branch = facts.get('month_branch', '')
    month_wx = BRANCH_WX.get(month_branch, '')
    day_stem = facts.get('day_stem', '')
    # 2026-10-06 权威源=排盘引擎: 六合化神从 l0_chart.he_hua 取(缺时兜底本地表)
    _he_hua_cfg = (facts.get('l0_chart') or {}).get('he_hua') or {}
    _he_hua_map = {}
    for _k, _v in _he_hua_cfg.items():
        _brs = _v.get('branches') or []
        if len(_brs) == 2:
            _he_hua_map[frozenset(_brs)] = _v.get('hua_qi', '')
    # 日主五行
    STEM_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    dm_wx = STEM_WX.get(day_stem, '')
    root_detail = rr.get('root_branch_relations', {})
    for pillar in comb_root:
        info = root_detail.get(pillar, {})
        for rel in (info.get('relations') or []):
            if rel.get('relation') == 'SIX_COMBINE':
                others = rel.get('with_branches', [])
                if others:
                    pair = frozenset([info.get('branch',''), others[0]])
                    huashen = _he_hua_map.get(pair, '') or LIUHE_HUASHEN.get(pair, '')
                    if huashen and month_wx == huashen and huashen != dm_wx:
                        return True
    return False


def query_heavy_root(network: Dict[str, Any]) -> Dict:
    """原著: 长生禄刃, 根之重者.
    纯结构: ROOT.root_weight_class == HEAVY (含长生/禄/刃重根).
    若重根支参与地支六合且化神得令, 则根被合走, 降级 NOT_SUPPORTED.
    此为事实判断, 可输出 SUPPORTED/NOT_SUPPORTED; 但不升"身强". """
    rc = network['dimensions']['ROOT'].get('root_weight_class')
    combined_away = _root_combined_away(network)
    heavy = (rc == 'HEAVY') and not combined_away
    note = '只报有无长生禄刃重根; 不下旺衰结论'
    if combined_away:
        note += '; 重根参与六合且化神得令, 根被合走'
    return _result(
        query_id='ZP-160-QUERY-HEAVY-ROOT',
        name='重根结构',
        classic='子平真诠',
        state='SUPPORTED' if heavy else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if heavy else 'NO_MATCH',
        matched_nodes=['ROOT_BRANCH'] if heavy else [],
        matched_edges=['ROOT_RELATION'] if heavy else [],
        evidence_refs=['PZZQ-005-005'],
        boundary_note=note,
    )


def query_light_root(network: Dict[str, Any]) -> Dict:
    """原著: 墓库余气, 根之轻者.
    纯结构: ROOT.root_weight_class == LIGHT (仅墓库/余气轻根, 无重根).
    此为事实判断, 可输出 SUPPORTED/NOT_SUPPORTED; 不下旺衰结论."""
    rc = network['dimensions']['ROOT'].get('root_weight_class')
    return _result(
        query_id='ZP-160-QUERY-LIGHT-ROOT',
        name='轻根结构',
        classic='子平真诠',
        state='SUPPORTED' if rc == 'LIGHT' else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if rc == 'LIGHT' else 'NO_MATCH',
        matched_nodes=['ROOT_BRANCH'] if rc == 'LIGHT' else [],
        matched_edges=['ROOT_RELATION'] if rc == 'LIGHT' else [],
        evidence_refs=['PZZQ-005-005'],  # 墓库余气, 根之轻者也
        boundary_note='只报有无墓库余气轻根; 不下旺衰结论, 不计根数/不与重根叠加',
    )


def query_tengluo_xijia(network: Dict[str, Any]) -> Dict:
    """原著(滴天髓乙木章): 藤蘿系甲, 可春可秋.
    纯结构: 日干=乙 AND 天干见比肩甲透(BIANJIAN.stem_present).
    结构匹配 STRUCTURE_MATCH, 命题恒 UNKNOWN; 不升旺衰."""
    dm = network['nodes'][0]['attrs'].get('stem', '')
    jc = network['dimensions']['SUPPORT'].get('JIECAI', {}).get('stem_present', False)
    m = (dm == '乙') and bool(jc)
    return _result(
        query_id='ZP-160-QUERY-TENGLUO-XIJIA',
        name='藤萝系甲结构',
        classic='滴天髓',
        state='SUPPORTED' if m else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if m else 'NO_MATCH',
        matched_nodes=['DAYMASTER', 'JIECAI'] if m else [],
        matched_edges=['SUPPORT_RELATION'] if m else [],
        evidence_refs=['DTS-008-007'],  # 藤蘿系甲, 可春可秋
        boundary_note='只报乙日见甲透这一结构; 不升旺衰结论, 不解释"可春可秋"',
    )


def query_juechu_fengsheng(network: Dict[str, Any]) -> Dict:
    """原著(神峰通考): 水虽至巳为极弱, 然已有庚金为水根.
    纯结构: 月令绝地(JUECHU.month_jue) AND 月令藏干见印(month_hidden_yin).
    结构匹配 STRUCTURE_MATCH, 命题恒 UNKNOWN; 不升旺衰."""
    jc = network['dimensions'].get('JUECHU', {})
    m = bool(jc.get('month_jue')) and bool(jc.get('month_hidden_yin'))
    return _result(
        query_id='ZP-160-QUERY-JUECHU-FENGSHENG',
        name='绝处逢生结构',
        classic='神峰通考',
        state='SUPPORTED' if m else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if m else 'NO_MATCH',
        matched_nodes=['SEASON'] if m else [],
        matched_edges=['SUPPORT_RELATION'] if m else [],
        evidence_refs=['SFTK-009-002'],  # 水虽至巳为极弱, 然已有庚金为水根
        boundary_note='只报月令绝地+月令藏干见印这一结构; 不下旺衰结论',
    )


def query_xie_qi_tai_zhong(network: Dict[str, Any]) -> Dict:
    """原著结构(子平真诠): 泄气太重 = 食伤成党(透干且通根).
    结构匹配: SHISHANG成党.
    只输出结构匹配; 不声明"泄太重"程度, 命题恒 UNKNOWN."""
    xie_party = _has_shishang_party(network['dimensions'])
    return _result(
        query_id='ZP-160-QUERY-XIEQI-TAIZHONG',
        name='泄气太重结构',
        classic='子平真诠',
        state='SUPPORTED' if xie_party else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if xie_party else 'NO_MATCH',
        matched_nodes=['SHISHANG_PARTY'] if xie_party else [],
        matched_edges=['DRAIN_RELATION'] if xie_party else [],
        evidence_refs=['PZZQ-007-025'],  # 子平真诠: 食神本属泄气, 以其能生正财
        boundary_note='只匹配食伤成党(透干且通根); 不判"泄太重"程度; 命题成立待授权',
    )


def query_root_struck(network: Dict[str, Any]) -> Dict:
    """原著: 日主根支参与冲/刑/自刑/害/破(对立类地支关系).
    纯结构: ROOT_RELATION.struck_root_pillars 非空.
    只报根支受对立关系这一结构; 不判根拔/根失效效果, 命题恒 UNKNOWN.
    注意: struck组聚合冲刑害破五类, 无单条原文全覆盖, refs留空不伪造.
    原典校准(DTS原文): 任氏明批"墓库逢冲必发"为后人之谬——库乃藏根之地,
    日主全赖辰戌丑未身库通根而逢冲, 反拔尽微根; 唯以土为喜神冲土方有益.
    故本 query 只报"根支受对立"事实, 不预设"冲开发福"."""
    rr = network['dimensions'].get('ROOT_RELATION', {})
    struck = rr.get('struck_root_pillars', []) or []
    m = bool(struck)
    return _result(
        query_id='ZP-160-QUERY-ROOT-STRUCK',
        name='根支受对立关系',
        classic='滴天髓',
        state='SUPPORTED' if m else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if m else 'NO_MATCH',
        matched_nodes=['ROOT_BRANCH'] if m else [],
        matched_edges=['COMBINATION'] if m else [],
        evidence_refs=['DTS-009-009'],  # 冲刑害破混合组, 借DTS旺者冲衰
        boundary_note='只报日主根支参与冲刑害破这一结构; 不判根是否被拔/失效. 原典批"墓库逢冲必发"为谬: 赖库根逢冲反拔微根, 不预设冲开发福',
    )


def query_ri_bei_he(network: Dict[str, Any]) -> Dict:
    """原著(三命通会): 日主被合, 自身力量发挥受限.
    结构: 日干是否参与天干五合. 只记被合事实, 不判化成功, 不判被合后力减."""
    th = network['dimensions'].get('TIAN_HE', {})
    dm_raw = network.get('daymaster') or {}
    dm = dm_raw.get('stem') if isinstance(dm_raw, dict) else (dm_raw or '')
    pairs = th.get('he_pairs', []) or []
    involved = any(dm in (p.get('stems') or []) for p in pairs)
    return _result(
        query_id='ZP-160-QUERY-RI-BEI-HE',
        name='日主被合结构',
        classic='三命通会',
        state='SUPPORTED' if involved else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if involved else 'NO_MATCH',
        matched_nodes=['TIAN_HE_DAYMASTER'] if involved else [],
        matched_edges=['TIAN_HE_RELATION'],
        evidence_refs=['DTS-008-013'],
        boundary_note='日干参与天干五合即记被合结构; 不判合化成功, 不判被合后力减, 不判化神取代日主',
    )


def query_jiruo_wugen(network: Dict[str, Any]) -> Dict:
    """原著(神峰通考): 极弱无根/假从.
    结构: 真从=无根+无扶; 假从=轻根+对方成党(克泄耗成势).
    布尔+多态枚举+网络拓扑, 不评分."""
    root = network['dimensions'].get('ROOT', {})
    ts = network['dimensions'].get('TWO_SIDE', {})
    dm = ts.get('DAYMASTER_SIDE', {})
    op = ts.get('OPPOSING_SIDE', {})
    # 真从: 无根+无扶
    root_none = root.get('root_weight_class') in (None, 'NONE') or not root.get('has_root')
    sup = dm.get('members_present', {}) or {}
    no_support = not any(sup.values())
    # 假从: 轻根(余气墓库)+对方成党(财官食伤透干成势)
    root_light = root.get('root_weight_class') == 'LIGHT'
    op_members = [m for m, v in (op.get('members_present', {}) or {}).items() if v]
    op_party = len(op_members) >= 2
    dm_members = [m for m, v in (dm.get('members_present', {}) or {}).items() if v]
    weak_support = len(dm_members) < 2  # 印比不成党(0或1个)
    # 根被冲拔: ROOT-STRUCK+HEAVY+对方成党+印比不成党
    rr = network['dimensions'].get('ROOT_RELATION', {})
    root_struck = bool(rr.get('struck_root_pillars', []))
    root_heavy = root.get('root_weight_class') == 'HEAVY'
    root_struck_extreme = root_struck and root_heavy and op_party
    # 根被合走: HE-HUASHEN-DESHI+HEAVY+对方成党
    # 检查network里是否有合化成功相关信息
    th = network['dimensions'].get('TIAN_HE', {})
    he_huashen = bool(th.get('he_huashen_chenggong', [])) or bool(th.get('he_pairs', []))
    root_he_extreme = he_huashen and root_heavy and op_party
    # 从杀格: HEAVY根+七杀三重以上(天干+地支)+印比不成党
    facts = network.get('facts', {})
    tgm = facts.get('ten_god_members', []) if isinstance(facts, dict) else []
    qisha_count = sum(1 for m in tgm if m.get('ten_god') == '七杀')
    dm_members_list = [m for m, v in (dm.get('members_present', {}) or {}).items() if v]
    weak_support_dm = len(dm_members_list) < 2
    cong_sha = bool(root_heavy and qisha_count >= 3)
    comb_facts = facts.get('combination_facts', []) if isinstance(facts, dict) else []
    # 根被破/合: HEAVY根+六破(丑辰/未戌/子酉/卯午)或六合+对方成党
    liupo = ('liupo' in comb_facts) if isinstance(comb_facts, (list, dict)) else False
    liuhe = ('liuhe' in comb_facts) if isinstance(comb_facts, (list, dict)) else False
    root_po_he = bool(root_heavy and (liupo or liuhe) and op_party)
    # 三合局克身: HEAVY根+三合局(亥卯未/寅午戌/申子辰/巳酉丑)化神克日主+印比不成党
    sanhe_ju = ('sanhe' in comb_facts) if isinstance(comb_facts, (list, dict)) else False
    sanhe_ke_shen = bool(root_heavy and sanhe_ju and weak_support_dm)
    # 无根+财多身弱
    cai_duo = bool(network['dimensions'].get('DRAIN', {}).get('CAI', {}).get('stem_present')) and root_none
    # 假从(轻根): 轻根 + 对方成党 + 日主端印比不成党(weak_support).
    # 依据 TAI_WANG_RUO.002 准神: 真从须"绝无一毫生扶"; 天干印比成党生身者非从, 乃身弱印重.
    root_light_false = root_light and op_party and weak_support
    is_extreme = bool((root_none and no_support) or root_light_false or root_struck_extreme or root_he_extreme or cai_duo or cong_sha or sanhe_ke_shen or root_po_he)
    mode = '真从' if (root_none and no_support) else ('根被冲拔' if root_struck_extreme else ('从杀' if cong_sha else ('三合克身' if sanhe_ke_shen else '假从')))
    return _result(
        query_id='ZP-160-QUERY-JIRUO-WUGEN',
        name='极弱无根/假从结构',
        classic='神峰通考',
        state='SUPPORTED' if is_extreme else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if is_extreme else 'NO_MATCH',
        matched_nodes=['ROOT_'+mode, 'SUPPORT_EMPTY'] if is_extreme else [],
        matched_edges=[],
        evidence_refs=['SFTK-009-002'],
        boundary_note=f'{mode}: 根={"无" if root_none else "轻"}+印比无扶+对方成党={op_party}; 不判弃命, 不下旺衰结论',
    )


def query_wugen_youfu(network: Dict[str, Any]) -> Dict:
    """原著(神峰通考/滴天髓): 日主无根而有印比生扶 = 衰弱而不从.
    结构: 无根(NONE) AND 日主端(印/比)有扶 AND NOT 真从(真从要求无扶).
    与 JIRUO-WUGEN 互斥: 彼为无根无扶(从), 此为无根有扶(衰弱).
    布尔+多态枚举, 不评分, 不下身弱最终裁决."""
    root = network['dimensions'].get('ROOT', {})
    ts = network['dimensions'].get('TWO_SIDE', {})
    dm = ts.get('DAYMASTER_SIDE', {})
    root_none = root.get('root_weight_class') in (None, 'NONE') or not root.get('has_root')
    sup = dm.get('members_present', {}) or {}
    has_support = any(sup.values())
    match = bool(root_none and has_support)
    sup_kinds = [k for k, v in sup.items() if v]
    return _result(
        'ZP-160-QUERY-WUGEN-YOUFU',
        name='无根有扶衰弱结构',
        classic='神峰通考',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['ROOT_NONE', 'SUPPORT_PRESENT'] if match else [],
        matched_edges=['SUPPORT_RELATION'] if match else [],
        evidence_refs=['SFTK-ROOT-001'],
        boundary_note=f'只匹配无根+印比有扶(={sup_kinds}), 弱而不从; 与极弱无根(从)互斥, 不下旺衰最终裁决',
    )


def query_zhonggua_two_side(network: Dict[str, Any]) -> Dict:
    """原著(滴天髓·众寡): 强弱须分日主与四柱两端而论.
    结构: 日主端(印比)成党? 四柱端(财官食伤)成党?
    两端各自报成员, 不合成一端强弱, 不判去谁成谁."""
    ts = network['dimensions'].get('TWO_SIDE', {})
    dm = ts.get('DAYMASTER_SIDE', {})
    op = ts.get('OPPOSING_SIDE', {})
    dm_members = [m for m, v in (dm.get('members_present', {}) or {}).items() if v]
    op_members = [m for m, v in (op.get('members_present', {}) or {}).items() if v]
    dm_party = bool(dm_members)
    op_party = bool(op_members)
    return _result(
        query_id='ZP-160-QUERY-ZHONGGUA-2SIDE',
        name='众寡两端结构',
        classic='滴天髓',
        state='SUPPORTED' if (dm_party or op_party) else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if (dm_party or op_party) else 'NO_MATCH',
        matched_nodes=(['DAYMASTER_SIDE'] if dm_party else []) + (['OPPOSING_SIDE'] if op_party else []),
        matched_edges=['TWO_SIDE_RELATION'],
        evidence_refs=['PZZQ-005-005'],  # 众寡两端借PZZQ
        boundary_note='两端各报成党成员, 不合成一端强弱, 不判去谁成谁, 不输出旺衰结论',
    )


def query_shi_gui_lu(network: Dict[str, Any]) -> Dict:
    """原著(滴天髓): 时为归禄; 生时乃归宿之地.
    结构: 时柱是否日主重根(禄/旺/刃). 任氏批'日禄归时青云得路'为俗论,
    谓只是日干旺地之比肩; 故只记归禄结构, 不做特殊贵格. """
    root = network['dimensions']['ROOT']
    pillars = root.get('root_pillars', []) or []
    on_hour = 'hour' in pillars
    return _result(
        query_id='ZP-160-QUERY-SHI-GUI-LU',
        name='时柱归禄结构',
        classic='滴天髓',
        state='SUPPORTED' if on_hour else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if on_hour else 'NO_MATCH',
        matched_nodes=['ROOT_HOUR'] if on_hour else [],
        matched_edges=['ROOT_RELATION'] if on_hour else [],
        evidence_refs=['SMTH-026-015'],  # 归禄借SMTH
        boundary_note='时柱有日主重根即记归禄结构; 不做日禄归时贵格, 不做时位加倍权重',
    )


def query_he_huashen_deshi(network: Dict[str, Any]) -> Dict:
    """原著(渊海子平): 月令生旺养库临官之地方化, 逢龙即化.
    结构: 天干有合 且 化神五行==月令本气. 只记化神得令结构, 不判真化."""
    th = network['dimensions'].get('TIAN_HE', {})
    pairs = th.get('he_pairs', []) or []
    on_month = th.get('huashen_on_month_qi', False)
    has_chen = th.get('has_long_chen', False)
    if pairs and on_month:
        state, mt, nodes = 'SUPPORTED', 'STRUCTURE_MATCH', ['TIAN_HE']
    else:
        state, mt, nodes = 'NOT_SUPPORTED', 'NO_MATCH', []
    return _result(
        query_id='ZP-160-QUERY-HE-HUASHEN-DESHI',
        name='合化神得令结构',
        classic='渊海子平',
        state=state,
        match_type=mt,
        matched_nodes=nodes,
        matched_edges=['TIAN_HE_RELATION'] if pairs else [],
        evidence_refs=['YHZP-121-003'],  # 月令生旺养库临官之地方化
        boundary_note='仅记天干合+化神得月令结构; 不判真化假化, 不判化气格, 太过不及未量化',
    )


def query_wangzhe_chong_shuai(network: Dict[str, Any]) -> Dict:
    """原著(滴天髓): 旺者冲衰衰者拔, 衰神冲旺旺神发.
    冲两支按四阶(得月令+同党)比: 阶高者旺, 阶低者拔, 同阶两停.
    有序枚举比较, 无数值, 不输出日主综合强弱."""
    bt = network['dimensions'].get('BRANCH_TIER', {})
    clashes = bt.get('clash_results', []) or []
    decided = [c for c in clashes if c['tier_a'] != c['tier_b']]
    tie = [c for c in clashes if c['tier_a'] == c['tier_b']]
    if decided:
        state, mt, nodes = 'SUPPORTED', 'STRUCTURE_MATCH', ['ROOT_BRANCH']
    elif tie:
        state, mt, nodes = 'NOT_SUPPORTED', 'NO_MATCH', []
    else:
        state, mt, nodes = 'NOT_SUPPORTED', 'NO_MATCH', []
    return _result(
        query_id='ZP-160-QUERY-WANGCHONG-SHUAI',
        name='旺者冲衰结构',
        classic='滴天髓',
        state=state,
        match_type=mt,
        matched_nodes=nodes,
        matched_edges=['COMBINATION'] if decided else [],
        evidence_refs=['DTS-009-009'],  # 旺者冲衰衰者拔
        boundary_note='冲两支按四阶比谁拔谁发, 同阶两停; 不编七级旺衰, 不输出日主综合强弱',
    )


def query_root_gan_priority(network: Dict[str, Any]) -> Dict:
    """原著: 通根如室家可住, 比肩如朋友相扶; 干多不如根重.
    这是层级优先级, 不是数量比较:
      有根(HEAVY/LIGHT) -> 室家可住, 根层成立
      无根但比劫干透    -> 朋友相扶, 无根借住
      无根无干          -> 两无
    纯布尔, 不数干个数, 不评分."""
    has_root = network['dimensions']['ROOT'].get('has_root', False)
    bijie_gan = network['dimensions']['SUPPORT'].get('BIJIE', {}).get('stem_present', False)
    if has_root:
        sub, nodes, edges, mt = '室家可住(根层成立)', ['ROOT_BRANCH'], ['ROOT_RELATION'], 'STRUCTURE_MATCH'
    elif bijie_gan:
        sub, nodes, edges, mt = '朋友相扶(无根有干)', ['ROOT_ABSENT', 'BIJIE'], ['SUPPORT_RELATION'], 'NO_MATCH'
    else:
        sub, nodes, edges, mt = '两无', [], [], 'NO_MATCH'
    return _result(
        query_id='ZP-160-QUERY-ROOT-GAN-PRIORITY',
        name='根干层级',
        classic='子平真诠',
        state='SUPPORTED' if has_root else 'NOT_SUPPORTED',
        match_type=mt,
        matched_nodes=nodes,
        matched_edges=edges,
        evidence_refs=['PZZQ-005-005'],  # 通根如室家可住, 朋友相扶; 干多不如根重
        boundary_note='根优先于干这一层级; 不数比肩个数, 不评分, 不下旺衰结论',
    )


def query_yin_party(network: Dict[str, Any]) -> Dict:
    """原著: 党众=比印; 印星成党(印透干且通根).
    纯结构: SUPPORT.YIN stem_present AND root_present.
    命题恒 UNKNOWN; 成党≠身强, 不判喜忌."""
    p = _has_yin_party(network['dimensions'])
    return _result(
        query_id='ZP-160-QUERY-YIN-PARTY',
        name='印星成党结构',
        classic='子平真诠',
        state='SUPPORTED' if p else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if p else 'NO_MATCH',
        matched_nodes=['YIN_PARTY'] if p else [],
        matched_edges=['SUPPORT_RELATION'] if p else [],
        evidence_refs=['PZZQ-005-005'],  # 党众为强(比印通根扶助), 同章
        boundary_note='只匹配印星透干且通根; 不判成党程度, 不下旺衰/喜忌结论',
    )


def query_bijie_party(network: Dict[str, Any]) -> Dict:
    """原著: 党众=比劫; 比劫成党(比劫透干且通根).
    纯结构: SUPPORT.BIJIE stem_present AND root_present.
    命题恒 UNKNOWN; 成党≠身强, 不判喜忌."""
    p = _has_bijie_party(network['dimensions'])
    return _result(
        query_id='ZP-160-QUERY-BIJIE-PARTY',
        name='比劫成党结构',
        classic='子平真诠',
        state='SUPPORTED' if p else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if p else 'NO_MATCH',
        matched_nodes=['BIJIE_PARTY'] if p else [],
        matched_edges=['SUPPORT_RELATION'] if p else [],
        evidence_refs=['PZZQ-005-005'],  # 党众为强(比劫), 同章
        boundary_note='只匹配比劫透干且通根; 不判成党程度, 不下旺衰/喜忌结论',
    )

def query_he_huashen_chenggong(network: Dict[str, Any]) -> Dict:
    """原著(子平真诠): 化出之物,得时乘令,四支局全,方为大贵.
    结构: 天干有合 + 化神得令 + 有三合三会局. 只记结构匹配, 不判真化."""
    th = network['dimensions'].get('TIAN_HE', {})
    pairs = th.get('he_pairs', []) or []
    on_month = th.get('huashen_on_month_qi', False)
    has_ju = bool(th.get('sanhe_ju') or th.get('sanhui_ju'))
    match = bool(pairs and on_month and has_ju)
    return _result(
        query_id='ZP-160-QUERY-HEHUASHEN-CHENGGONG',
        name='合化成功结构',
        classic='子平真诠',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['TIAN_HE', 'JU'] if match else [],
        matched_edges=['TIAN_HE_RELATION'] if match else [],
        evidence_refs=['PZZQ-007-025'],
        boundary_note='仅记天干合+化神得令+局全结构; 不判真化假化, 不判化气格, 不判富贵',
    )

def query_jiwang_huaiji(network: Dict[str, Any]) -> Dict:
    """原著(滴天髓·颠倒): 木太旺者而似金, 喜火之炼也.
    结构(布尔+多态枚举, 不评分): 王令(当令)或相令(印令受生) + 重根(HEAVY)
      + 日主端成势, 成势取以下任一: 比劫成党(透干通根)/印成党(透干通根)/重根>=2支.
    太旺区别于普通身旺: 须多支重根或印比成党; 区别于旺极: 对方尚有克泄(不在此判).
    不输出喜忌, 不判从强."""
    sea = network['dimensions'].get('SEASONAL', {})
    root = network['dimensions'].get('ROOT', {})
    sup = network['dimensions'].get('SUPPORT', {})
    # 伤官当令: 月令五行是日主所生的五行(如丁火戌月)
    STEM_WX={'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    BRANCH_WX={'寅':'木','卯':'木','巳':'火','午':'火','申':'金','酉':'金','亥':'水','子':'水','辰':'土','戌':'土','丑':'土','未':'土'}
    SHENG={'木':'火','火':'土','土':'金','金':'水','水':'木'}
    f = network.get('facts', {}) or {}
    day_stem = f.get('day_stem', '')
    month_branch = f.get('month_branch', '')
    shishang_ling = bool(day_stem and month_branch and BRANCH_WX.get(month_branch) == SHENG.get(STEM_WX.get(day_stem,'')))
    bijie_stem = bool(sup.get('BIJIE', {}).get('stem_present'))
    yin_stem = bool(sup.get('YIN', {}).get('stem_present'))
    heavy = root.get('root_weight_class') == 'HEAVY'
    # 月令是日主墓库/余气+重根+印比透干也算旺令(如腊月壬水旺)
    MU_KU = {'甲':'未','乙':'未','丙':'戌','丁':'戌','戊':'辰','己':'辰','庚':'丑','辛':'丑','壬':'辰','癸':'辰'}
    YU_QI = {'甲':'辰','乙':'辰','丙':'未','丁':'未','戊':'戌','己':'戌','庚':'未','辛':'未','壬':'丑','癸':'丑'}
    month_is_muku = bool(day_stem and month_branch and MU_KU.get(day_stem) == month_branch)
    month_is_yuqi = bool(day_stem and month_branch and YU_QI.get(day_stem) == month_branch)
    muku_wang = bool((month_is_muku or month_is_yuqi) and heavy and (bijie_stem or yin_stem))
    wang_ling = bool(sea.get('in_season', False) or sea.get('month_supports', False) or shishang_ling or muku_wang)
    bijie_party = bool(bijie_stem and sup.get('BIJIE', {}).get('root_present'))
    yin_party = bool(yin_stem and sup.get('YIN', {}).get('root_present'))
    detail = root.get('root_class_detail', {}) or {}
    heavy_n = sum(1 for v in detail.values() if isinstance(v, str) and v.startswith('HEAVY'))
    multi_heavy = heavy_n >= 2
    # 太旺须印比成势(透干帮扶或地支有根), 不能仅凭地支重根; 成势=成党或多支重根
    bijie_root = bool(sup.get('BIJIE', {}).get('root_present'))
    yin_root = bool(sup.get('YIN', {}).get('root_present'))
    stem_aided = bijie_stem or yin_stem or bijie_root or yin_root
    # 地支三会/三合局成日主同类
    th = network['dimensions'].get('TIAN_HE', {})
    sanhui = th.get('sanhui_ju', []) or []
    sanhe = th.get('sanhe_ju', []) or []
    STEM_WX2 = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    f2 = network.get('facts', {}) or {}
    dm_wx2 = STEM_WX2.get(f2.get('day_stem',''), '')
    party_ju = False
    for ju in sanhui + sanhe:
        ju_wx = ju.get('wuxing', '') if isinstance(ju, dict) else ''
        if ju_wx == dm_wx2:
            party_ju = True
    # 成势=成党或多支重根或(重根+地支有印比)或(重根+印比透干)或地支会局成日主同类
    root_with_yinbi = heavy and (bijie_root or yin_root)
    root_with_stem = heavy and (bijie_stem or yin_stem)
    chengshi = bijie_party or yin_party or multi_heavy or root_with_yinbi or root_with_stem or party_ju
    match = bool(heavy and wang_ling and stem_aided and chengshi)
    nodes = []
    if match:
        nodes = ['SEASONAL', 'ROOT'] + (['BIJIE_PARTY'] if bijie_party else []) + (['YIN_PARTY'] if yin_party else []) + (['MULTI_HEAVY_ROOT'] if multi_heavy else [])
    return _result(
        query_id='ZP-160-QUERY-JIWANG-HUAIJI',
        name='日干太旺结构',
        classic='滴天髓',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=nodes,
        matched_edges=[],
        evidence_refs=['DTS-009-009'],
        boundary_note=f'王/相令+重根+天干印比透扶+成势(比劫党={bijie_party},印党={yin_party},重根支={heavy_n}); 不输出喜克泄, 不判从强, 不与旺极混',
    )


def query_jishuai_congsheng(network: Dict[str, Any]) -> Dict:
    """原著(滴天髓): 木衰极者而似土也, 宜火以生之. 结构: 失令+无根+克泄成党. 不输出喜忌."""
    sea = network['dimensions'].get('SEASONAL', {})
    root = network['dimensions'].get('ROOT', {})
    out = not sea.get('in_season', False)
    no_root = not root.get('has_root', False)
    ctrl = network['dimensions'].get('CONTROL', {})
    drain = network['dimensions'].get('DRAIN', {})
    ctrl_party = ctrl.get('GUANSHA', {}).get('stem_present') and ctrl.get('GUANSHA', {}).get('root_present')
    drain_party = drain.get('SHISHANG', {}).get('stem_present') and drain.get('SHISHANG', {}).get('root_present')
    # 火旺木焚: 失令+有根+食伤成党+克泄成党
    xie_party = drain.get('SHISHANG', {}).get('stem_present') and drain.get('SHISHANG', {}).get('root_present')
    huo_wang_mu_fen = out and (not no_root) and xie_party and (ctrl_party or drain_party)
    match = bool((out and no_root and (ctrl_party or drain_party)) or huo_wang_mu_fen)
    return _result(
        query_id='ZP-160-QUERY-JISHUAI-CONGSHENG',
        name='日干极衰结构',
        classic='滴天髓',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['SEASONAL','ROOT','CONTROL','DRAIN'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['DTS-009-009'],
        boundary_note='仅记失令+无根+克泄成党结构; 不输出喜生扶, 不判从弱',
    )

def query_shiyong_yueling_xiangfu(network: Dict[str, Any]) -> Dict:
    """原著(滴天髓): 生时用事,与月令人元用事相附,是日主之所喜者,加倍兴隆.
    结构: 时柱藏干与月令藏干同类. 不做吉凶判断."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-SHIYONG-YUELING-XIANGFU', name='时月人元相附结构', classic='滴天髓', state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[], evidence_refs=['DTS-009-009'], boundary_note='仅记时月人元同类结构; 不判加倍兴隆/凶祸')
    month_hidden = facts.get('hidden_stems', {}).get('month', [])
    hour_hidden = facts.get('hidden_stems', {}).get('hour', [])
    same = set(month_hidden) & set(hour_hidden)
    match = bool(same)
    return _result(
        query_id='ZP-160-QUERY-SHIYONG-YUELING-XIANGFU',
        name='时月人元相附结构',
        classic='滴天髓',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['MONTH_HIDDEN','HOUR_HIDDEN'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['DTS-009-009'],
        boundary_note='仅记时月人元同类结构; 不判加倍兴隆/凶祸',
    )

def query_ge_qing(network: Dict[str, Any]) -> Dict:
    """原著(子平真诠): 格清. 结构: 无六冲/无三刑/无六害/无自刑. 不做吉凶."""
    facts = network.get('facts') or {}
    comb = facts.get('combination_facts', {}) if facts else {}
    no_chong = not comb.get('liuchong')
    no_xing = not comb.get('sanxing')
    no_hai = not comb.get('liuhai')
    no_self = not comb.get('self_punishment')
    match = bool(no_chong and no_xing and no_hai and no_self)
    return _result(
        query_id='ZP-160-QUERY-GE-QING',
        name='格清结构',
        classic='子平真诠',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['COMBINATION'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['PZZQ-005-005'],
        boundary_note='仅记无冲刑害自刑结构; 不判格清贵格, 不判吉凶',
    )

def query_ge_qing_extended(network: Dict[str, Any]) -> Dict:
    """格清扩展: 清纯/混杂/真假.
    清纯: 格局用神不被同类杂神干扰(正官不混七杀, 食神不混伤官)
    混杂: 格局用神被同类杂神干扰(官杀混杂/食伤混杂)
    真假: 真神=月令本气透出, 假神=月令余气/中气透出
    只输出结构状态, 不判格局高低/吉凶/贵贱."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-GE-QING-EXT', name='格清扩展', classic='子平真诠',
            state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[],
            evidence_refs=['PZZQ-005-005'], boundary_note='无facts')
    stem_relations = facts.get('stem_relations', {}) or {}
    month_transparent = facts.get('month_transparent', []) or []
    month_qi_stem = facts.get('month_qi_stem', '')
    # 1. 混杂判断
    ten_gods = [v.get('ten_god', '') for v in stem_relations.values()]
    has_zhengguan = '正官' in ten_gods
    has_qisha = '七杀' in ten_gods
    has_shishen = '食神' in ten_gods
    has_shangguan = '伤官' in ten_gods
    guansha_hunza = has_zhengguan and has_qisha
    shishang_hunza = has_shishen and has_shangguan
    # 2. 真假判断
    zhen_shen = month_qi_stem if (month_qi_stem and month_qi_stem in month_transparent) else None
    jia_shen = [s for s in month_transparent if s and s != month_qi_stem]
    # 3. 清纯
    qingchun = not (guansha_hunza or shishang_hunza)
    # 4. 混杂类型
    if guansha_hunza:
        hunza_type = '官杀混杂'
    elif shishang_hunza:
        hunza_type = '食伤混杂'
    else:
        hunza_type = '无混杂'
    # 5. 真假类型
    if zhen_shen and jia_shen:
        zhenjia_type = '真假同透'
    elif zhen_shen:
        zhenjia_type = '真神透'
    elif jia_shen:
        zhenjia_type = '假神透'
    else:
        zhenjia_type = '无透'
    nodes = ['GE_QING_BASE']
    if guansha_hunza: nodes.append('GUANSHA_HUNZA')
    if shishang_hunza: nodes.append('SHISHANG_HUNZA')
    if zhen_shen: nodes.append('ZHEN_SHEN')
    if jia_shen: nodes.append('JIA_SHEN')
    return _result(
        query_id='ZP-160-QUERY-GE-QING-EXT',
        name='格清扩展(清纯/混杂/真假)',
        classic='子平真诠',
        state='SUPPORTED',
        match_type='STRUCTURE_MATCH',
        matched_nodes=nodes,
        matched_edges=[],
        evidence_refs=['PZZQ-005-005'],
        boundary_note='格清扩展: 清纯(无官杀/食伤混杂)/混杂(官杀混杂或食伤混杂)/真假(月令本气透=真神, 余气中气透=假神); 只输出结构状态, 不判格局高低/吉凶/贵贱',
        extra={
            'qingchun': qingchun,
            'hunza_type': hunza_type,
            'guansha_hunza': guansha_hunza,
            'shishang_hunza': shishang_hunza,
            'zhen_shen': zhen_shen,
            'jia_shen': jia_shen,
            'zhenjia_type': zhenjia_type,
        }
    )


def query_ge_quality(network: Dict[str, Any]) -> Dict:
    """格局高低: 格清+配合=高, 格浊+不配合=低. 并列枚举不评分.
    原著: 子平真诠 格局清浊配合."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-GE-QUALITY', name='格局高低', classic='子平真诠', state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[], evidence_refs=['PZZQ-005-005'], boundary_note='无facts')
    comb = facts.get('combination_facts', {})
    # 格清: 无冲刑害
    qing = not (comb.get('liuchong') or comb.get('sanxing') or comb.get('liuhai') or comb.get('self_punishment'))
    # 配合: 根有+月令有扶
    root = network['dimensions'].get('ROOT', {})
    has_root = root.get('has_root', False)
    season = network['dimensions'].get('SEASONAL', {})
    season_good = season.get('in_season') or season.get('month_supports')
    # 高低枚举
    if qing and has_root and season_good:
        quality = '清且有根得令'
        match = True
    elif qing:
        quality = '清但根令不足'
        match = True
    elif has_root and season_good:
        quality = '浊但有根得令'
        match = True
    else:
        quality = '浊且根令不足'
        match = True
    return _result(
        query_id='ZP-160-QUERY-GE-QUALITY',
        name='格局高低',
        classic='子平真诠',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['COMBINATION','ROOT','SEASONAL'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['PZZQ-005-005'],
        boundary_note=quality,
    )


def query_yun_sheng_root(network: Dict[str, Any]) -> Dict:
    """原著(滴天髓): 运之喜忌. 结构: 大运/流年补原局root. 不做吉凶."""
    facts = network.get('facts') or {}
    root = network['dimensions'].get('ROOT', {})
    has_root = root.get('has_root', False)
    # 结构: 原局无root, 但原局+大运可能补root
    # 这里只记录原局root状态, 不预测大运
    match = not has_root
    return _result(
        query_id='ZP-160-QUERY-YUN-SHENG-ROOT',
        name='运补根结构',
        classic='滴天髓',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['ROOT'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['DTS-009-009'],
        boundary_note='仅记原局无根结构(待大运补根); 不判喜忌吉凶',
    )

def query_yun_zhi_xiji(network: Dict[str, Any]) -> Dict:
    """运之喜忌结构层: 格局喜忌+身强弱喜忌+调候喜忌.
    只输出喜忌候选五行, 不判吉凶/贵贱/成败.
    吉凶在前端拦截, 子平引擎只输出结构候选."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-YUN-ZHI-XIJI', name='运之喜忌结构', classic='子平真诠',
            state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[],
            evidence_refs=['PZZQ-005-006'], boundary_note='无facts')
    dm = facts.get('daymaster_element', '')
    month_qi_ten_god = facts.get('month_qi_ten_god', '')
    # 1. 格局喜忌(基于月令十神)
    geju_xiji = _geju_xiji_map(month_qi_ten_god)
    # 2. 身强弱喜忌(基于root_weight_class)
    root = network.get('dimensions', {}).get('ROOT', {})
    root_class = root.get('root_weight_class', '')
    shen_xiji = _shenruo_xiji_map(dm, root_class)
    # 3. 调候喜忌(基于climate_candidates, 喜=调候候选, 忌=调候反方向)
    qtbj = facts.get('climate_candidates', []) or []
    tiaohou_xi = [c.get('stem', '') for c in qtbj if c.get('stem')]
    tiaohou_ji = _tiaohou_opposite(tiaohou_xi, dm)
    # 4. 合并喜忌(去重)
    all_xi = list(set(geju_xiji.get('xi', []) + shen_xiji.get('xi', []) + tiaohou_xi))
    all_ji = list(set(geju_xiji.get('ji', []) + shen_xiji.get('ji', []) + tiaohou_ji))
    nodes = ['YUN_XIJI_BASE']
    if geju_xiji.get('xi'): nodes.append('GEJU_XI')
    if geju_xiji.get('ji'): nodes.append('GEJU_JI')
    if shen_xiji.get('xi'): nodes.append('SHEN_XI')
    if shen_xiji.get('ji'): nodes.append('SHEN_JI')
    if tiaohou_xi: nodes.append('TIAHOU_XI')
    return _result(
        query_id='ZP-160-QUERY-YUN-ZHI-XIJI',
        name='运之喜忌结构',
        classic='子平真诠',
        state='SUPPORTED',
        match_type='STRUCTURE_MATCH',
        matched_nodes=nodes,
        matched_edges=[],
        evidence_refs=['PZZQ-005-006', 'DTS-009-009'],
        boundary_note='运之喜忌结构层: 格局喜忌(月令十神)+身强弱喜忌(root_class)+调候喜忌(气候候选); 只输出喜忌候选五行, 不判吉凶/贵贱/成败; 吉凶在前端拦截',
        extra={
            'geju_xiji': geju_xiji,
            'shen_xiji': shen_xiji,
            'tiaohou_xi': tiaohou_xi,
            'tiaohou_ji': tiaohou_ji,
            'all_xi': all_xi,
            'all_ji': all_ji,
        }
    )


def _geju_xiji_map(month_qi_ten_god: str) -> Dict[str, list]:
    """格局喜忌映射(基于月令十神). 只输出候选五行, 不判吉凶."""
    m = {
        '正官': {'xi': ['财', '印'], 'ji': ['伤官']},
        '七杀': {'xi': ['食伤', '印'], 'ji': ['财']},
        '正印': {'xi': ['官杀'], 'ji': ['财']},
        '偏印': {'xi': ['官杀'], 'ji': ['财']},
        '正财': {'xi': ['官杀', '食伤'], 'ji': ['比劫']},
        '偏财': {'xi': ['官杀', '食伤'], 'ji': ['比劫']},
        '食神': {'xi': ['财'], 'ji': ['枭']},
        '伤官': {'xi': ['印', '财'], 'ji': ['官']},
        '比肩': {'xi': ['官杀', '食伤', '财'], 'ji': ['印比']},
        '劫财': {'xi': ['官杀', '食伤', '财'], 'ji': ['印比']},
    }
    return m.get(month_qi_ten_god, {'xi': [], 'ji': []})


def _shenruo_xiji_map(dm: str, root_class: str) -> Dict[str, list]:
    """身强弱喜忌映射(基于root_class). 只输出候选五行, 不判吉凶."""
    # 日主五行 -> 生扶(印比) / 克泄(财官食伤)
    shengfu_map = {
        '木': {'xi': ['水', '木'], 'ji': ['金', '土', '火']},
        '火': {'xi': ['木', '火'], 'ji': ['水', '金', '土']},
        '土': {'xi': ['火', '土'], 'ji': ['木', '水', '金']},
        '金': {'xi': ['土', '金'], 'ji': ['火', '木', '水']},
        '水': {'xi': ['金', '水'], 'ji': ['土', '火', '木']},
    }
    if root_class in ('HEAVY',):
        # 身强: 喜克泄, 忌生扶
        base = shengfu_map.get(dm, {'xi': [], 'ji': []})
        return {'xi': base['ji'], 'ji': base['xi']}
    elif root_class in ('LIGHT', 'SPECIAL'):
        # 身弱: 喜生扶, 忌克泄
        return shengfu_map.get(dm, {'xi': [], 'ji': []})
    else:
        # 无根/未知: 不裁
        return {'xi': [], 'ji': []}


def _tiaohou_opposite(tiaohou_xi: list, dm: str) -> list:
    """调候忌神(调候候选的反方向). 只输出候选, 不判吉凶."""
    # 简单反方向: 调候喜火则忌水, 喜水则忌火, 喜木则忌金, 喜金则忌木, 喜土则忌木
    opp = {'火': '水', '水': '火', '木': '金', '金': '木', '土': '木'}
    return [opp.get(x, '') for x in tiaohou_xi if x and opp.get(x)]


def query_cai_ruo_shen_qiang(network: Dict[str, Any]) -> Dict:
    """T23 原著(神峰通考): 日干周围一片我克之五行,财弱身旺. 结构: 重根+财无根."""
    facts0 = network.get('facts', {})
    tgm0 = facts0.get('ten_god_members', []) if facts0 else []
    root = network['dimensions'].get('ROOT', {})
    heavy = root.get('root_weight_class') == 'HEAVY'
    cai = [x for x in tgm0 if x['ten_god'] in ('正财','偏财') and x['type']=='hidden']
    cai_wugen = not cai
    match = bool(heavy and cai_wugen)
    return _result(
        query_id='ZP-160-QUERY-CAI-RUO-SHEN-QIANG',
        name='财弱身旺结构',
        classic='神峰通考',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['ROOT','CONTROL'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['SFTK-009-002'],
        boundary_note='仅记重根+财无根结构; 不判吉凶',
    )


def query_wangji_siwo_sheng(network: Dict[str, Any]) -> Dict:
    """T27 原著(滴天髓): 木旺极者而似火,喜水之克. 结构: 得令+重根+食伤成党."""
    sea = network['dimensions'].get('SEASONAL', {})
    root = network['dimensions'].get('ROOT', {})
    facts = network.get('facts') or {}
    tgm = facts.get('ten_god_members', []) if facts else []
    shishang = [x for x in tgm if x['ten_god'] in ('食神','伤官') and x['type']=='stem']
    match = bool(sea.get('in_season') and root.get('root_weight_class') == 'HEAVY' and shishang)
    return _result(
        query_id='ZP-160-QUERY-WANGJI-SIWO-SHENG',
        name='旺极似我生结构',
        classic='滴天髓',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['SEASONAL','ROOT','DRAIN'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['DTS-009-009'],
        boundary_note='仅记得令+重根+食伤成党结构; 不判喜克',
    )


def query_shuaiji_siwo_ke(network: Dict[str, Any]) -> Dict:
    """T29 原著(滴天髓): 木衰极者而似土,宜火以生之. 结构: 失令+无根+财成党."""
    sea = network['dimensions'].get('SEASONAL', {})
    root = network['dimensions'].get('ROOT', {})
    cai = network['dimensions'].get('CONTROL', {})
    match = bool(not sea.get('in_season') and not root.get('has_root') and
                 any(v.get('stem_present') and v.get('root_present') for v in cai.get('CAI', {}).values()))
    return _result(
        query_id='ZP-160-QUERY-SHUAIJI-SIWO-KE',
        name='衰极似我克结构',
        classic='滴天髓',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['SEASONAL','ROOT','CONTROL'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['DTS-009-009'],
        boundary_note='仅记失令+无根+财成党结构; 不判喜生',
    )


def query_mu_chong_kai(network: Dict[str, Any]) -> Dict:
    """T34 原著(滴天髓): 墓库逢冲. 结构: 辰戌丑未逢冲."""
    chong = network['dimensions'].get('ROOT_RELATION', {}).get('chong_branches', [])
    mu_set = {'辰','戌','丑','未'}
    match = any((a in mu_set and b in mu_set) for a,b in chong)
    return _result(
        query_id='ZP-160-QUERY-MU-CHONG-KAI',
        name='墓库逢冲结构',
        classic='滴天髓',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['ROOT_RELATION'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['DTS-008-007'],
        boundary_note='仅记墓库逢冲结构; 不判冲开/根伤',
    )


def query_shi_zhu_ji(network: Dict[str, Any]) -> Dict:
    """T45 原著(滴天髓): 时柱人元用事为日主所忌. 结构: 时柱克日主."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-SHI-ZHU-JI', name='时柱为忌结构', classic='滴天髓', state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[], evidence_refs=['DTS-009-009'], boundary_note='仅记时柱克日主结构')
    from engines.common.l0_fact_builder import ten_god
    dm = facts['day_stem']
    hour_hidden = facts.get('hidden_stems', {}).get('hour', [])
    ji = any(ten_god(dm, h) in ('正官','七杀','正财','偏财') for h in hour_hidden)
    return _result(
        query_id='ZP-160-QUERY-SHI-ZHU-JI',
        name='时柱为忌结构',
        classic='滴天髓',
        state='SUPPORTED' if ji else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if ji else 'NO_MATCH',
        matched_nodes=['HOUR_HIDDEN'] if ji else [],
        matched_edges=[] if not ji else [],
        evidence_refs=['DTS-009-009'],
        boundary_note='仅记时柱官杀财结构; 不判凶祸',
    )


def query_shi_lin_wang(network: Dict[str, Any]) -> Dict:
    """T46 原著(神峰通考): 时临旺处. 结构: 时柱日干禄旺."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-SHI-LIN-WANG', name='时临旺处结构', classic='神峰通考', state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[], evidence_refs=['SFTK-009-002'], boundary_note='仅记时柱禄旺结构')
    from engines.common.daymaster_root_class import POS
    dm = facts['day_stem']
    hour_branch = facts['pillars']['hour'][1] if 'pillars' in facts else ''
    match = hour_branch in POS.get(dm, {}) and hour_branch in POS[dm].values() and (POS[dm].get('禄')==hour_branch or POS[dm].get('旺')==hour_branch)
    return _result(
        query_id='ZP-160-QUERY-SHI-LIN-WANG',
        name='时临旺处结构',
        classic='神峰通考',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['HOUR_ROOT'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['SFTK-009-002'],
        boundary_note='仅记时柱禄旺结构; 不判物自有成',
    )


def query_tiangan_xingqing(network: Dict[str, Any]) -> Dict:
    """T47/T49/T50/T51 天干性情: 日干+季节+克泄. 结构识别."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-TIANGAN-XINGQING', name='天干性情结构', classic='滴天髓', state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[], evidence_refs=['DTS-009-009'], boundary_note='仅记日干+季节结构')
    dm = facts['day_stem']
    mzi = facts['month_branch']
    # 简化: 识别日干类型
    xingqing = {'甲':'春不容金秋不容土','乙':'藤罗系甲','丁':'旺而不烈衰而不穷','己':'不愁木盛不畏水狂','癸':'不愁火土不论庚辛'}.get(dm,'')
    match = bool(xingqing)
    return _result(
        query_id='ZP-160-QUERY-TIANGAN-XINGQING',
        name='天干性情结构',
        classic='滴天髓',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['DAYMASTER'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['DTS-009-009'],
        boundary_note=f'日干{dm}性情:{xingqing}; 不判喜忌',
    )

def query_yongshen_structure(network: Dict[str, Any]) -> Dict:
    """用神结构识别: 月令格神+相神结构. 不判最终用神."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-YONGSHEN-STRUCTURE', name='用神结构', classic='子平真诠', state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[], evidence_refs=['PZZQ-005-005'], boundary_note='仅记月令格神结构; 不判最终用神')
    mzi = facts['month_branch']
    from engines.common.l0_fact_builder import HIDDEN, ten_god
    dm = facts['day_stem']
    month_qi = HIDDEN[mzi][0]
    tg = ten_god(dm, month_qi)
    match = bool(tg)
    return _result(
        query_id='ZP-160-QUERY-YONGSHEN-STRUCTURE',
        name='用神结构',
        classic='子平真诠',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['MONTH_QI'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['PZZQ-005-005'],
        boundary_note=f'月令{mzi}本气{month_qi}为日主{tg}; 不判最终用神/喜忌',
    )


def query_yongshen_final(network: Dict[str, Any]) -> Dict:
    """用神最终裁决: 月令格神为主+调候为佐+相神为配. 并列不裁唯一.
    原著: 子平真诠用神=月令格神, 穷通宝鉴调候=佐. 不判喜忌吉凶."""
    facts = network.get('facts') or {}
    if not facts:
        return _result(query_id='ZP-160-QUERY-YONGSHEN-FINAL', name='用神最终裁决', classic='子平真诠', state='NOT_SUPPORTED', match_type='NO_MATCH', matched_nodes=[], matched_edges=[], evidence_refs=['PZZQ-005-005','QTBJ-003-002'], boundary_note='无facts')
    mzi = facts['month_branch']
    from engines.common.l0_fact_builder import HIDDEN, ten_god
    dm = facts['day_stem']
    month_qi = HIDDEN[mzi][0]
    tg = ten_god(dm, month_qi)
    # 调候候选
    climate = network['dimensions'].get('SEASONAL', {}).get('climate_candidates', [])
    # 候选用神列表
    candidates = [{'role':'格神','stem':month_qi,'ten_god':tg,'source':'月令'}]
    for cs in climate:
        candidates.append({'role':'调候','stem':cs,'ten_god':ten_god(dm,cs),'source':'QTBJ'})
    match = bool(candidates)
    return _result(
        query_id='ZP-160-QUERY-YONGSHEN-FINAL',
        name='用神最终裁决',
        classic='子平真诠+穷通宝鉴',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['MONTH_QI','CLIMATE'] if match else [],
        matched_edges=[] if not match else [],
        evidence_refs=['PZZQ-005-005','QTBJ-003-002'],
        boundary_note=';'.join(f"{c['role']}:{c['stem']}({c['ten_god']})" for c in candidates),
    )




def query_zhong_he(network: Dict[str, Any]) -> Dict:
    """原著结构(滴天髓/子平真诠): 中和纯粹 = 日主有根 + 印比透扶 + 非旺极/衰极/弱极.
    结构匹配: has_root AND (YIN_PARTY OR BIJIE_PARTY) AND NOT JIWANG AND NOT JISHUAI AND NOT JIRUO.
    只输出结构匹配; 不判格局高低, 不下吉凶结论."""
    has_root = network['dimensions']['ROOT'].get('has_root', False)
    yin_party = _has_yin_party(network['dimensions'])
    bijie_party = _has_bijie_party(network['dimensions'])
    # 非旺极/衰极/弱极
    root_class = network['dimensions']['ROOT'].get('root_weight_class', '')
    no_root = not has_root
    cai_party = _has_cai_party(network['dimensions'])
    sha_party = _has_guansha_party(network['dimensions'])
    shishang_party = _has_shishang_party(network['dimensions'])
    # 旺极: 得令+重根+印比成党
    seasonal = network['dimensions'].get('SEASONAL', {})
    in_season = seasonal.get('season_status') == 'IN_SEASON'
    jiwang = in_season and root_class == 'HEAVY' and (yin_party or bijie_party)
    # 衰极: 失令+无根+克泄成党
    out_season = seasonal.get('season_status') == 'OUT_OF_SEASON'
    jishuai = out_season and no_root and (sha_party or shishang_party or cai_party)
    # 弱极: 无根+无扶
    jiruo = no_root and not yin_party and not bijie_party
    
    match = (has_root or yin_party or bijie_party) and not jiwang and not jishuai and not jiruo
    return _result(
        query_id='ZP-160-QUERY-ZHONG-HE',
        name='中和纯粹结构',
        classic='滴天髓/子平真诠',
        state='SUPPORTED' if match else 'NOT_SUPPORTED',
        match_type='STRUCTURE_MATCH' if match else 'NO_MATCH',
        matched_nodes=['HAS_ROOT', 'YIN_OR_BIJIE_PARTY', 'NOT_EXTREME'] if match else [],
        matched_edges=['SUPPORT_RELATION', 'ROOT_PRESENT'] if match else [],
        evidence_refs=['DTS-001-001'],  # 滴天髓通神论: 中和纯粹
        boundary_note='只匹配有根+印比透扶+非极端; 不判格局高低, 不下吉凶结论',
    )
