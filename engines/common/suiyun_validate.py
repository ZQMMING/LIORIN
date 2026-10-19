# -*- coding: utf-8 -*-
"""岁运验层 (suiyun_validate) —— "算→辩→转归→解→验"之"验".

职责(在原局诊断结果上做增量重评, 不另起炉灶):
1. 把大运(及大运下流年)干支作为岁运柱加入, 用 transit_power / build_tian_he 重算
   五行计数 / 根 / 天干合(解绊·新合) / 地支冲合.
2. 在复合局上重跑 算→辩→转归→解, 与原局链对比:
   主病是否变化 / 病机增减 / 主药变化 / 药是否解合或新受制.
3. 裁决该步岁运对日主为【吉 / 凶 / 平 / 平】并给方向.

岁运药理(锚定原局主病 bw, 与原局药方严格一致):
- 制: 岁运克 bw(KE_BACK[bw]), 克病恒正向不看量.
- 化: 岁运 = bw 所生(SHENG[bw]), 泄病/通关(化出不反克日主).
- 暖: bw=水时, 火暖化寒湿.
- 帮: 日主弱时, 岁运比劫/印帮身且不助病.
- 助病(凶): 岁运 = bw 或 生 bw.

命理边界:
- 岁运不改变原局月令与日干; 月令仍取原局, 岁运柱为外加动态因素.
- 主病锚定原局; 复合局"主病变None"=病解(吉), "新主病=岁运自身"=药被计入(不记坏),
  仅"新主病为原局另一固有病机"才算引动(凶).
- 全程布尔枚举 + 序数等级, 无浮点加权.
- 动态解合/争合为工程初判(非原典显式), 待 YHZP/SMTH 真实命例回归校准.
"""
import copy
from typing import Any, Dict, List

from engines.common.l0_fact_builder import build as l0build, ten_god, WUXING
from engines.common.transit_power import (
    build_transit_power, element_power_tier, BRANCH_WX)
from engines.common.daymaster_tian_he import build_tian_he
from engines.common.bingyao_layer import build_bingyao_layer
from engines.common.bing_debate import resolve_primary_bing
from engines.common.zhuangui_layer import resolve_zhuangui
from engines.common.qtbj_climate_candidates import build_climate_candidates
from engines.common.yongyao_resolve import resolve_yongyao
from engines.common.engineering_assumptions import TIER_PING

# 五行关系(原典常量)
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
SHENG_BACK = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
KE_BACK = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}


def _norm_root_class(rcv):
    if rcv and str(rcv).startswith('HEAVY'):
        return 'HEAVY'
    if rcv and (str(rcv).startswith('LIGHT') or rcv == 'SPECIAL_LONGSHENG_YIN'):
        return 'LIGHT'
    return 'NONE'


def _norm_extra(extra) -> List[List[str]]:
    out = []
    for gz in extra or []:
        if isinstance(gz, str):
            gz = [gz[0], gz[1]]
        out.append([gz[0], gz[1]])
    return out


# =============================================================
# 复合 facts 构造
# =============================================================
def build_compound_facts(pillars, base_facts, extra):
    """原局 facts + 岁运柱 → 复合 facts."""
    extra = _norm_extra(extra)
    cf = copy.deepcopy(base_facts)
    cf['transit_extra'] = extra

    tp = build_transit_power(pillars, extra)
    th = build_tian_he(pillars, base_facts, extra_pillars=extra)
    cf['wuxing_power'] = tp['wuxing_power']
    cf['tian_he'] = th

    # 根: 原局四柱 + 岁运支
    rw = cf.setdefault('root_weight_class_facts', {})
    for i, (_eg, ez) in enumerate(extra):
        rcv = tp['root_class_detail'].get(ez)
        rw['t%d' % i] = {'branch': ez, 'class': _norm_root_class(rcv)}

    # 十神成员: 追加岁运干
    dm = pillars['day'][0]
    tgm = cf.setdefault('ten_god_members', [])
    for i, (eg, ez) in enumerate(extra):
        tgm.append({'pillar': 't%d' % i, 'type': 'stem', 'stem': eg, 'branch': ez,
                    'hidden_index': None, 'qi_position': None,
                    'ten_god': ten_god(dm, eg)})
    return cf, tp, th


def run_chain_on(pillars, base_facts, extra, queries):
    """在 原局+extra 复合局上重跑 算→辩→转归→解."""
    cf, tp, th = build_compound_facts(pillars, base_facts, extra)
    by = build_bingyao_layer(cf, queries)
    deb = resolve_primary_bing(cf, by['bing_list'])
    zg = resolve_zhuangui(cf, deb)
    cli = build_climate_candidates(cf)
    yy = resolve_yongyao(cf, zg, cli)
    return {'bingyao': by, 'debate': deb, 'zhuangui': zg,
            'climate': cli, 'yongyao': yy, 'facts': cf, 'tp': tp, 'th': th}


def base_chain_from_result(production_result):
    """从 production_entry 结果抽取原局链(复用, 不重算)."""
    z = production_result['zhenglun']
    return {'bingyao': z['bingyao'], 'debate': z['debate'],
            'zhuangui': z['zhuangui'], 'yongyao': z['yongyao']}


# =============================================================
# 差异对比
# =============================================================
def diff_chain(base, step):
    bp = base['debate'].get('primary_bing') or {}
    sp = step['debate'].get('primary_bing') or {}
    base_ids = {b['bing_id'] for b in base['bingyao']['bing_list']}
    step_ids = {b['bing_id'] for b in step['bingyao']['bing_list']}

    bmed = base['yongyao'].get('primary_medicine') or {}
    smed = step['yongyao'].get('primary_medicine') or {}
    bblk = (bmed.get('blocked') or {}).get('state')
    sblk = (smed.get('blocked') or {}).get('state')

    return {
        'primary_bing_changed': bp.get('bing_id') != sp.get('bing_id'),
        'base_primary': (bp.get('bing_id'), bp.get('bing_wx')),
        'step_primary': (sp.get('bing_id'), sp.get('bing_wx')),
        'bing_added': sorted(step_ids - base_ids),
        'bing_removed': sorted(base_ids - step_ids),
        'primary_medicine_changed': bmed.get('wuxing') != smed.get('wuxing'),
        'base_medicine_wx': bmed.get('wuxing'),
        'step_medicine_wx': smed.get('wuxing'),
        'base_medicine_blocked': bblk,
        'step_medicine_blocked': sblk,
        'block_released': bool(bblk) and not sblk and str(bblk).startswith('合绊'),
        'new_block': (not bblk) and bool(sblk) and str(sblk).startswith('合绊'),
    }


# =============================================================
# 裁决: 吉 / 凶 / 平
# =============================================================
def _heavy_root_branches(some_facts):
    rw = some_facts.get('root_weight_class_facts', {})
    return {v.get('branch') for v in rw.values() if v.get('class') == 'HEAVY'}


def verdict_step(pillars, base, step, extra, base_tier):
    dm = pillars['day'][0]
    dm_wx = WUXING[dm]
    cur_g, cur_z = extra[-1]                  # 当前岁运柱(流年场景为流年)
    gw, zw = WUXING.get(cur_g), BRANCH_WX.get(cur_z)
    transit_wx = {gw, zw}

    bp = base['debate'].get('primary_bing') or {}
    bw = bp.get('bing_wx', '')               # 原局主病五行(锚定)
    bid = bp.get('bing_id', '')
    need_help = base_tier['tier'] <= TIER_PING

    good, bad = [], []

    # --- 吉·制: 克主病(恒正向, 不看量) ---
    zhi = KE_BACK.get(bw)
    if bw and zhi in transit_wx:
        good.append('制主病%s(%s)' % (bw, zhi))
    # --- 吉·化: 病所生, 泄病/通关(化出不反克日主) ---
    hua = SHENG.get(bw)
    if bw and hua in transit_wx and KE_BACK.get(dm_wx) != hua:
        good.append('化泄主病%s(%s)' % (bw, hua))
    # --- 吉·暖: 水病火暖寒湿 ---
    if bw == '水' and '火' in transit_wx:
        good.append('暖化寒湿(火)')
    # --- 吉·帮: 比劫/印帮身(日主需帮, 且不助病) ---
    #   V7.31 得势(党众)接帮身: 原局日主透干成党(同类干>=3)=得势帮身(帮身力+),
    #   庚盘"三庚透干=得势"由此体现; 岁运帮身(比劫/印)叠加成党更助日主.
    help_wx = {dm_wx, SHENG_BACK.get(dm_wx)}
    _dm_same_stems = sum(1 for pos in ('year', 'month', 'day', 'hour')
                         if WUXING.get(pillars[pos][0], '') == dm_wx)
    _dashe = _dm_same_stems >= 3   # 透干同类>=3 = 得势成党
    if need_help:
        hb = sorted(x for x in transit_wx
                    if x in help_wx and x not in (bw, SHENG_BACK.get(bw)))
        if hb:
            good.append(('帮身(得势党众%d干)' % _dm_same_stems if _dashe else '帮身') +
                        ('(%s)' % '/'.join(hb)))

    # --- 凶·助病: 同病 / 生病 ---
    #   V7.28 候神/炼金豁免: 候神职能表(evil_offset.houchou_roles)命中的岁运五行是药非助病之源,
    #   不入助病/克伐. 真值 丁卯庚戌庚戌庚辰: 丁巳/戊午运火=炼金候神(用神), 旧口径"火生土助主病"误判凶.
    from engines.common import evil_offset
    _roles_ex = evil_offset.houchou_roles(dm_wx, bw)
    _houshen_exempt = set(_roles_ex.keys())
    if bw:
        z = sorted(x for x in transit_wx
                   if x in (bw, SHENG_BACK.get(bw)) and x not in _houshen_exempt)
        # V7.30 抵消规则统一表: 交战(主病+候神药同运被制)/合绊/冲开 收敛为 offset_kind 查表,
        #   替换 case 补丁. 交战=平(0), 合绊/冲开=凶(-2, 药失制力).
        _offsets = evil_offset.offset_kind(dm_wx, bw, transit_wx)
        if z:
            if '交战' in _offsets:
                bad.append('交战(主病%s+候神%s同运, 药制主病吉凶交战)' % (bw, '/'.join(sorted(_houshen_exempt & transit_wx))))
            else:
                bad.append('助主病%s(%s)' % (bw, '/'.join(z)))
    # --- 凶·克伐弱主 ---
    #   V7.28 候神/炼金豁免: 炼金官火克日主是炼金非克伐, 不入 bad.
    ke_dm = KE_BACK.get(dm_wx)
    if need_help and ke_dm in transit_wx and ke_dm not in _houshen_exempt:
        bad.append('克伐日主(%s)' % ke_dm)
    # --- 凶·新合绊主药 ---
    d = diff_chain(base, step)
    if d['new_block']:
        bad.append('主药被合绊(%s)' % d['step_medicine_blocked'])
    # --- 凶·冲: 岁运支冲主药根 / 月令提纲 / 日主重根 ---
    month_z = pillars['month'][1]
    heavy_br = _heavy_root_branches(step['facts'])
    base_med = base['yongyao'].get('primary_medicine') or {}
    med_wx = base_med.get('wuxing')
    medicine_pulled = False
    _chong_reported = set()
    for pair in step['tp'].get('combination_facts', {}).get('liuchong', []):
        if cur_z not in pair:
            continue
        other = pair[0] if pair[1] == cur_z else pair[1]
        if other in _chong_reported:
            continue
        _chong_reported.add(other)
        if med_wx and med_wx != dm_wx and BRANCH_WX.get(other) == med_wx:
            medicine_pulled = True
            bad.append('冲拔主药根(%s冲%s·药%s根拔)' % (cur_z, other, med_wx))
        elif other == month_z:
            bad.append('冲月令提纲(%s冲%s)' % (cur_z, other))
        elif other in heavy_br:
            bad.append('冲日主重根(%s冲%s)' % (cur_z, other))

    # --- 凶·三刑(岁运支参与成刑; 原典寅巳申/丑戌未须三支俱全, 子卯两支即成).
    #     自刑(辰午酉亥同支再见)非战克、主小自扰, 不入凶 hard_bad ---
    for _x in step['tp'].get('combination_facts', {}).get('sanxing', []):
        _label = _x.get('type', '')
        _brs = _x.get('branches') or []
        if cur_z in _brs and not _label.endswith('自刑'):
            bad.append('三刑(%s)' % _label)

    # --- 凶·合: 岁运支与原局支 六合(查表, 原局L0已备组合事实).
    #     合走主药根=药根拔(凶); 合走日主重根=根被合走失力(凶); 合月令提纲=提纲被合走(交战性, 平);
    #     合走闲神=该运支本气"化泄"为合假象(不记吉). 冲已消费(liuchong), 合(新缺口)补齐 -> 大运基于原局地支.
    #     V7.31 例外: 合走月令但合支【化神是候神药】(炼金/泄秀/疏病) -> 合提纲非提纲伤, 提纲反被药化 -> 不记凶(吉).
    #       真值: 丁卯运卯戌合化火(癸盘候神=火,食伤泄秀)/乙卯运卯戌合化火(庚盘候神=火,炼金), 真值皆吉.
    _cf_step = step['tp'].get('combination_facts', {})
    for _pair in (_cf_step.get('liuhe') or []):
        if len(_pair) != 2 or cur_z not in _pair:
            continue
        _oth = _pair[0] if _pair[1] == cur_z else _pair[1]
        if med_wx and BRANCH_WX.get(_oth) == med_wx:
            medicine_pulled = True
            bad.append('合走主药根(%s合%s·药%s根拔)' % (cur_z, _oth, med_wx))
        elif _oth in heavy_br:
            bad.append('合日主重根(%s合%s·根被合走)' % (cur_z, _oth))
        elif _oth == month_z:
            # 六合化神表: 卯戌合火/寅亥合木/子丑合土/午未合土/巳申合水/辰酉合金
            _LHE_HUA = {'卯': '火', '戌': '火', '寅': '木', '亥': '木', '子': '土', '丑': '土',
                         '午': '土', '未': '土', '巳': '水', '申': '水', '辰': '金', '酉': '金'}
            _h = _LHE_HUA.get(cur_z) or _LHE_HUA.get(_oth)
            if _h and _h in _houshen_exempt:
                good.append('合提纲化%s候神(%s合%s·提纲反得药化, 吉)' % (_h, cur_z, _oth))
            else:
                bad.append('合月令提纲(%s合%s)' % (cur_z, _oth))
        else:
            # 合走闲神: 该运支本气"化泄"为合假象(不记吉)
            good = [g for g in good if not (g.startswith('化泄') and g.endswith('(%s)' % zw))]

    # --- V7.27 刑不入抵消: 岁运食伤(我生)泄秀功 抵消刑伤(原典"泄秀暖局为用") ---
    #     食伤=我生(dm_wx所生), 主病=印(生我)时食伤泄秀暖局是药, 刑伤不抵消药之功 -> 剔三刑.
    #     真值 丁卯庚戌庚戌庚辰: 壬子(壬水食神=金生之水, 子水伤官=食伤泄秀)被"子卯刑"误杀 -> 食伤泄秀抵消刑.
    _shishang_wx = SHENG.get(dm_wx, '')
    if _shishang_wx and (_shishang_wx in transit_wx) and any('三刑' in x for x in bad):
        bad = [b for b in bad if '三刑' not in b]

    # 冲拔主药根时, 该岁运支本气的"化泄"为冲药假象, 剔除(不抵冲药之凶)
    if medicine_pulled:
        good = [g for g in good
                if not (g.startswith('化泄') and g.endswith('(%s)' % zw))]

    # --- 引动原局另一固有病机: 须岁运【生助】新病(岁运为其印, 滋养原局潜伏病).
    #     岁运克新病=反制(非引动); 同气/岁运自身被计入不记坏; 主病None=病解(吉) ---
    sp = step['debate'].get('primary_bing') or {}
    sp_id, sp_wx = sp.get('bing_id'), sp.get('bing_wx')
    if sp_id and sp_id != bid and sp_wx and any(
            SHENG.get(x) == sp_wx for x in transit_wx):
        bad.append('引动另一病机(%s·岁运生助)' % sp_id)

    # --- V7.28 伤官见官: 岁运伤官(我生克官)见原局官星 -> 恶神(官非/失用), 压倒候神力级.
    #     原典"伤官见官为祸"(PZZQ). 真值 丁卯庚戌庚戌庚辰: 癸丑运(癸=伤官, 丑=印土)见
    #     原局丁火正官 -> 伤官见官+丑戌刑 -> 凶. 伤官(我生)=SHENG[dm_wx], 官星=KE[dm_wx]在局.
    _shang_wx = SHENG.get(dm_wx, '')
    _guan_wx = KE.get(dm_wx, '')
    _guan_in_natal = any(
        (WUXING.get(p[0]) == _guan_wx) for p in pillars.values() if p[0])
    if _shang_wx and _guan_wx and _guan_in_natal and _shang_wx in transit_wx:
        bad.append('伤官见官(%s伤官克%s官)' % (_shang_wx, _guan_wx))

    # --- V7.33 无根日主印为药(原著 PZZQ L4882/4936 无根日主须印比扶身; DTS 体用章):
    #   日主失令(ling_state=囚/死/休) 且 原局四柱全无根(root_detail空) 时, 印(生我)=药(扶身+化病),
    #   岁运 克伐日主/冲月令提纲/三刑 被印化抵消(药力); 印运升吉.
    #   真值 DTS 丙子丙申丙子丙申(四柱无根丙火, 须木运和之): 寅卯甲辰(印木)=吉发财,
    #   己亥庚子辛丑(金水)=凶. 查表派生: 失令+全无根 -> 印运豁免克伐/冲提纲, 非case.
    #   (预计算标记, 实际裁决在 verdict_arbitrate 之后)
    # 日主失令 + 无根: 直接查原局支 (查表派生, 非case)
    #   失令: 日主五行 在 月令支 的 旺相休囚死 = 休/囚/死
    #   无根: 原局四柱支 都无 日主五行 的本气/中气根
    _ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
               '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
    _month_b = pillars['month'][1]
    # 失令查表: 五行×月支 -> 旺相休囚死
    _WANG_XIANG_XIU = {
        '木': {'寅': '旺', '卯': '旺', '亥': '相', '子': '相', '巳': '休', '午': '休',
               '申': '囚', '酉': '囚', '辰': '死', '戌': '死', '丑': '死', '未': '死'},
        '火': {'午': '旺', '巳': '旺', '寅': '相', '卯': '相', '申': '休', '酉': '休',
               '戌': '囚', '亥': '囚', '丑': '死', '辰': '死', '未': '死', '子': '死'},
        '土': {'辰': '旺', '戌': '旺', '丑': '旺', '未': '旺', '午': '相', '巳': '相',
               '寅': '休', '卯': '休', '子': '囚', '亥': '囚', '申': '死', '酉': '死'},
        '金': {'申': '旺', '酉': '旺', '巳': '相', '午': '相', '子': '休', '亥': '休',
               '丑': '囚', '辰': '囚', '寅': '死', '卯': '死', '戌': '死', '未': '死'},
        '水': {'子': '旺', '亥': '旺', '申': '相', '酉': '相', '巳': '休', '午': '休',
               '辰': '囚', '戌': '囚', '丑': '死', '未': '死', '寅': '死', '卯': '死'}}
    _pos = _WANG_XIANG_XIU.get(dm_wx, {}).get(_month_b, '')
    _shi_ling = _pos in ('囚', '死', '休')
    # 无根: 原局四柱支 都无 日主五行 的本气
    _natal_branches = [pillars[pos][1] for pos in ('year', 'month', 'day', 'hour')]
    _no_root = all(_ZHI_WX.get(b, '') != dm_wx for b in _natal_branches)
    _yin_wx = SHENG_BACK.get(dm_wx, '')        # 印 = 生我 (火日主=木, 金日主=土, ...)
    # 主病锚定印(生我, 印重主病)时, 印运=助病非扶身药, 不豁免
    _bing_gen_me = bw and SHENG.get(bw, '') == dm_wx
    _wugenyin_mark = _shi_ling and _no_root and bool(_yin_wx) and (_yin_wx in transit_wx) and not _bing_gen_me

    # --- 凶·格局破格: 原局成格 + 岁运触发 po_ge 路径 ---
    # match 语义(ge_jie_layer 落盘): ANY=required 任一神即破格(该神本身是忌);
    #                               ALL=required 全部神齐备才破格(组合条件, 单神非忌, 不可作忌神用);
    #                               缺失类(forbidden)=缺失才破格, 不参与十神触发.
    gc = step['facts'].get('ge_cheng') or {}
    po_paths = gc.get('po_ge') or []
    _ge_name = gc.get('ge','') or ''
    # 幂等: 已破格的格不再重复报
    if po_paths and isinstance(po_paths, list) and '破格' not in _ge_name:
        dm0 = pillars['day'][0]
        cur_god = ten_god(dm0, cur_g)
        # 原局四柱已备之十神(不含日干), 供 ALL 组合判"其余条件是否已在原局齐备"
        _natal_gods = set()
        for _pos in ('year', 'month', 'hour'):
            try:
                _g = pillars[_pos][0]
            except (KeyError, IndexError, TypeError):
                continue
            if _g:
                _tg = ten_god(dm0, _g)
                if _tg:
                    _natal_gods.add(_tg)
        for pp in po_paths:
            if not isinstance(pp, dict) or pp.get('type') != '组合':
                continue
            req = pp.get('required') or []
            if not req:
                continue
            if pp.get('match') == 'ALL':
                # 组合条件: 全部 required 须齐备(原局 + 本步岁运)才算破格
                avail = _natal_gods | ({cur_god} if cur_god else set())
                if req and all(g in avail for g in req):
                    bad.append('格局破格(%s·岁运%s(%s)触发组合%s)' % (
                        gc.get('ge',''), cur_g, cur_god, '＋'.join(req)))
                    break
                continue
            if cur_god in req:
                bad.append('格局破格(%s·岁运%s(%s)触发)' % (gc.get('ge',''), cur_g, cur_god))
                break
        # 地支形态: 岁运支冲格体支(地支本气五行=ti_wx) -> 破格
        for pp in po_paths:
            if not isinstance(pp, dict) or pp.get('type') != '地支':
                continue
            ti_wx_list = gc.get('ti_wx') or []
            ZHI_WX_LOCAL = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
            chong_map_local = {'子':'午','午':'子','丑':'未','未':'丑','寅':'申','申':'寅','卯':'酉','酉':'卯','辰':'戌','戌':'辰','巳':'亥','亥':'巳'}
            ge_branches = [z for z in [pillars['year'][1],pillars['month'][1],pillars['day'][1],pillars['hour'][1]] if ZHI_WX_LOCAL.get(z,'') in ti_wx_list]
            for gb in ge_branches:
                if chong_map_local.get(cur_z) == gb:
                    bad.append('格局破格(%s·岁运%s冲格体%s)' % (gc.get('ge',''), cur_z, gb))
                    break
            else:
                continue
            break

    # 裁决 (V7.25 恶神抵消表 evil_offset: 刑/冲提纲/冲药根/破格 不抵消制化之功)
    from engines.common import evil_offset
    _v = evil_offset.verdict_arbitrate(good, bad)
    level, shorthand = _v['level'], _v['shorthand']

    # V7.33 无根日主印为药(原著 PZZQ L4882/4936 无根日主须印比扶身; DTS 体用章):
    #   日主失令(ling_state=囚/死/休) 且 原局四柱全无根(root_detail空) 时, 印(生我)=药(扶身+化病),
    #   岁运 克伐日主/冲月令提纲/三刑 被印化抵消(药力); 印运升吉.
    #   真值 DTS 丙子丙申丙子丙申(四柱无根丙火, 须木运和之): 寅卯甲辰(印木)=吉发财,
    #   己亥庚子辛丑(金水)=凶. 查表派生: 失令+全无根 -> 印运豁免克伐/冲提纲, 非case.
    if _wugenyin_mark:
        bad = [b for b in bad if not (b.startswith('克伐日主') or b.startswith('冲月令') or '三刑' in b
                                      or b.startswith('助主病') or b.startswith('交战') or b.startswith('格局破格'))]
        good.append('无根日主印运扶身化病(%s)' % _yin_wx)
        _v2 = evil_offset.verdict_arbitrate(good, bad)
        level = _v2['level']; shorthand = _v2['shorthand']
        _v['note'] = '无根日主失令, 印运扶身化病(药)'
        if level < 2:
            level = 2
            shorthand = '吉'

    # V7.32 专旺格喜忌接 verdict (原著 PZZQ L4888-4894 专旺格论, 全五行查表派生, 非case):
    #   "气纯势强, 可顺而不可逆. 运以食伤泄其秀气为最美, 原局有食伤则财运亦美.
    #    印比之运, 从其旺神, 固为适宜. 官煞逆其旺势, 最犯格局之忌, 若无印生化, 则为祸非轻."
    #   喜序: 食伤(我生,泄秀) > 财(原局有食伤时) > 印比(顺旺神); 忌: 官杀(克我,逆旺势).
    #   特例: "原局露食伤泄秀, 则印运为忌"(印克食伤); "比劫透而无食伤, 则财运亦忌"(财坏比劫顺势).
    gc = step['facts'].get('ge_cheng') or {}
    ge = gc.get('ge') or ''
    cheng = gc.get('cheng_bai') or ''
    _zhuanwang = any(k in ge for k in ('炎上', '曲直', '稼穑', '从革', '润下'))
    _congs = any(k in ge for k in ('从财', '从杀', '从官', '从儿', '从势'))
    if (_zhuanwang or _congs) and cheng == 'CHENG' and level in (0, 1):
        _ti_wx = (gc.get('ti_wx') or [''])[0] or dm_wx
        if _ti_wx:
            _shi = SHENG.get(_ti_wx, '')          # 食伤=我生(泄秀, 最美)
            _cai = KE.get(_ti_wx, '')             # 财=我克
            _yin = SHENG_BACK.get(_ti_wx, '')      # 印=生我(顺旺神)
            _guan = KE_BACK.get(_ti_wx, '')        # 官杀=克我(逆旺势, 忌)
            # 原局是否已有食伤(决定财运/印运喜忌切换)
            _shi_in_natal = any(WUXING.get(p[0], '') == _shi for p in pillars.values() if p[0])
            _hit_shi = _shi in transit_wx          # 食伤运=最美
            _hit_cai = _cai in transit_wx          # 财运
            _hit_yin_bi = (_yin in transit_wx) or (_ti_wx in transit_wx)  # 印/比劫运
            _hit_guan = _guan in transit_wx        # 官杀运=忌
            if _hit_guan:
                # 官煞逆旺势(最犯格局忌); 有印生化=祸轻, 无印=祸重
                _has_yin_save = _hit_yin_bi or _shi_in_natal
                level = -1 if _has_yin_save else -2
                shorthand = '平偏凶' if _has_yin_save else '凶'
                _v['note'] = '专旺格官煞逆旺势%s' % ('(有印生化, 祸轻)' if _has_yin_save else '(无印生化, 祸重)')
            elif _hit_shi:
                level = 2; shorthand = '吉'; _v['note'] = '专旺格食伤泄秀(最美), 升吉'
            elif _hit_cai:
                # 原局有食伤则财运亦美; 比劫透而无食伤则财运亦忌
                if _shi_in_natal:
                    level = 2; shorthand = '吉'; _v['note'] = '专旺格财运(原局有食伤, 财亦美), 升吉'
                else:
                    level = -2; shorthand = '凶'; _v['note'] = '专旺格财运(原局无食伤, 财坏顺势), 忌'
            elif _hit_yin_bi:
                # 印比顺旺神固为适宜; 原局露食伤泄秀则印运为忌
                if _shi_in_natal:
                    level = -2; shorthand = '凶'; _v['note'] = '专旺格印运(原局食伤泄秀, 印克食伤为忌)'
                else:
                    level = 2; shorthand = '吉'; _v['note'] = '专旺格印比顺旺神, 升吉'

    # V7.30 候神升格: 岁运命中候神(药)且力级精算(坐旺/原局得根/该运冲合状态) -> 升吉(level=2).
    #   候神职能表×力级精算集中算理, 替换 case-by-case 级别微调.
    #   力级=坐旺2力 + 原局候神得根+1(3力) - 该运候神被冲开/合绊-1; 力级>=2 且无恶神 -> 升吉.
    #   交战性 bad(主病+候神同运被药制) 不走候神升格, 保持平(level0, 真值戊午=平).
    _bw = (bp.get('bing_wx') or '')
    _has_conflict_bad = any('交战' in x for x in bad)
    # 力级精算入参: 原局候神得根(候神五行在原局支有本气/中气根) + 该运候神被冲开/合绊
    _roles_ex2 = evil_offset.houchou_roles(dm_wx, _bw)
    _zhi_brs = [pillars[pos][1] for pos in ('year', 'month', 'hour')] if pillars else []
    _zhi_ben_wx = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
                   '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
    _natal_root = {wx: any(_zhi_ben_wx.get(b, '') == wx for b in _zhi_brs)
                   for wx in _roles_ex2}
    # 该运候神被冲开/合绊: 岁运支冲开候神坐旺根, 或岁运干支与候神药成合走
    _lc_blocked = bool(medicine_pulled) or d.get('new_block', False)
    if level == 0 and not bad and _bw:
        _hc = evil_offset.houchou_verdict(transit_wx, cur_z, dm_wx, _bw, bad,
                                          natal_has_root=_natal_root, transit_blocked=_lc_blocked)
        if _hc['promote']:
            level = _hc['level']
            shorthand = '吉'
            _v['note'] = _hc['reason']
    elif level == 0 and not good and _has_conflict_bad and evil_offset.evil_no_offset(bad):
        # 恶神(刑/伤官见官)压倒候神力级 -> 凶
        level = -2
        shorthand = '凶'
        _v['note'] = '恶神压倒候神力级, 判主凶'

    if shorthand == '吉' and evil_offset.verdict_arbitrate(good, bad)['level'] == 2 \
            and any(('制主病' in x or '化泄' in x or '暖化' in x) for x in good):
        direction = '病得制化/暖解, 可顺势进取'
    elif shorthand == '吉' and _dashe:
        # V7.31 身强弱(得势)接方向: 日主透干成党=得势帮身 -> 身强宜克泄
        direction = '身强(得势党众%d干), 岁运帮身更盛, 宜克泄不宜再扶' % _dm_same_stems
    elif shorthand == '吉':
        direction = '身得帮, 宜稳守蓄力'
    elif shorthand == '凶':
        direction = '忌妄动, 防%s, 宜守待时' % ';'.join(bad)
    elif shorthand == '平' and _has_conflict_bad:
        direction = '吉凶交战(干%s支%s), 大事缓图' % (cur_g, cur_z)
    elif shorthand == '平偏吉':
        direction = '身得帮(非主药), 小吉, 宜稳守'
    elif shorthand == '平偏凶':
        direction = '小凶, 宜守待时, 防%s' % ';'.join(bad)
    else:
        direction = '平淡无大关目, 常守'

    return {'level': level, 'shorthand': shorthand,
            'good': good, 'bad': bad, 'direction': direction,
            'arbitration_note': _v.get('note', '')}


# =============================================================
# 顶层: 逐步大运 + 可选流年
# =============================================================
def validate_suiyun(pillars, production_result, dayun_list, liunian_map=None):
    """production_result: production_entry 返回.
    dayun_list: ['甲子','乙丑',...].
    liunian_map: {大运下标: '流年干支'} 在指定大运下叠加流年."""
    base_facts = production_result['engine_result']
    queries = production_result['l1_result']['queries']
    base = base_chain_from_result(production_result)
    dm_wx = WUXING[pillars['day'][0]]
    base_tier = element_power_tier(base_facts['wuxing_power'], dm_wx)

    steps = []
    for i, gz in enumerate(dayun_list):
        extra = [[gz[0], gz[1]]]
        step = run_chain_on(pillars, base_facts, extra, queries)
        d = diff_chain(base, step)
        v = verdict_step(pillars, base, step, extra, base_tier)
        tier = element_power_tier(step['tp']['wuxing_power'], dm_wx)
        entry = {'index': i, 'dayun': gz, 'dm_tier': tier['name'],
                 'diff': d, 'verdict': v}
        if liunian_map and i in liunian_map:
            ln = liunian_map[i]
            lextra = extra + [[ln[0], ln[1]]]
            lstep = run_chain_on(pillars, base_facts, lextra, queries)
            ld = diff_chain(base, lstep)
            lv = verdict_step(pillars, base, lstep, lextra, base_tier)
            entry['liunian'] = {'ganzhi': ln, 'diff': ld, 'verdict': lv}
        steps.append(entry)

    return {
        'layer': 'SUIYUN_VALIDATE',
        'base_dm_tier': base_tier['name'],
        'dayun_steps': steps,
        'boundary_note': ('岁运在原局结果上增量重评; 不改变原局月令/日干; '
                          '动态解合/争合为工程初判, 待真实命例回归校准'),
    }
