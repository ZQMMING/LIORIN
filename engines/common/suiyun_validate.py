# -*- coding: utf-8 -*-
"""岁运验层 (suiyun_validate) —— "算→辩→转归→解→验"之"验".

职责(在原局诊断结果上做增量重评, 不另起炉灶):
1. 把大运(及大运下流年)干支作为岁运柱加入, 用 transit_power / build_tian_he 重算
   五行计数 / 根 / 天干合(解绊·新合) / 地支冲合.
2. 在复合局上重跑 算→辩→转归→解, 与原局链对比:
   主病是否变化 / 病机增减 / 主药变化 / 药是否解合或新受制.
3. 裁决该步岁运对日主为【良药 / 毒药 / 平战 / 平】并给方向.

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
# 裁决: 良药 / 毒药 / 平战 / 平
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

    # --- 良药·制: 克主病(恒正向, 不看量) ---
    zhi = KE_BACK.get(bw)
    if bw and zhi in transit_wx:
        good.append('制主病%s(%s)' % (bw, zhi))
    # --- 良药·化: 病所生, 泄病/通关(化出不反克日主) ---
    hua = SHENG.get(bw)
    if bw and hua in transit_wx and KE_BACK.get(dm_wx) != hua:
        good.append('化泄主病%s(%s)' % (bw, hua))
    # --- 良药·暖: 水病火暖寒湿 ---
    if bw == '水' and '火' in transit_wx:
        good.append('暖化寒湿(火)')
    # --- 良药·帮: 比劫/印帮身(日主需帮, 且不助病) ---
    help_wx = {dm_wx, SHENG_BACK.get(dm_wx)}
    if need_help:
        hb = sorted(x for x in transit_wx
                    if x in help_wx and x not in (bw, SHENG_BACK.get(bw)))
        if hb:
            good.append('帮身(%s)' % '/'.join(hb))

    # --- 毒药·助病: 同病 / 生病 ---
    #   V7.28 候神/炼金豁免: 候神(食伤泄秀/制药)与炼金官火(金日主土重局, 丁火正官坐巳=候)是药非助病之源,
    #   不入助病/克伐. 真值 丁卯庚戌庚戌庚辰: 丁巳/戊午运火=炼金候神(用神), 旧口径"火生土助主病"误判毒药.
    from engines.common import tiaohou_rank
    _cli_s = {}
    _hou_th = (base.get('yongyao') or {}).get('tiaohou_yongshen') or {}
    if _hou_th.get('hou_stems'):
        _cli_s['climate_candidates'] = [
            {'stem': s, 'order': i} for i, s in enumerate(_hou_th['hou_stems'])]
    _rank_step = tiaohou_rank._tiaohou_primary_rank(_cli_s, bw, dm_wx, pillars)
    _houshen_wx = _rank_step['wx'] if _rank_step['rank'] == 'PROMOTE' else ''
    # 炼金候: 金日主+土主病+岁运有火 -> 火=炼金药(候干表120格已录丁, 金土局炼金). 候干表未候火时兜底.
    _lianjin_wx = ''
    if dm_wx == '金' and bw == '土' and '火' in transit_wx:
        _lianjin_wx = '火'
    if bw:
        z = sorted(x for x in transit_wx
                   if x in (bw, SHENG_BACK.get(bw)) and x not in (_houshen_wx, _lianjin_wx))
        if z:
            bad.append('助主病%s(%s)' % (bw, '/'.join(z)))
    # --- 毒药·克伐弱主 ---
    #   V7.28 候神/炼金豁免: 炼金官火克日主是炼金非克伐, 不入 bad.
    ke_dm = KE_BACK.get(dm_wx)
    if need_help and ke_dm in transit_wx and ke_dm not in (_houshen_wx, _lianjin_wx):
        bad.append('克伐日主(%s)' % ke_dm)
    # --- 毒药·新合绊主药 ---
    d = diff_chain(base, step)
    if d['new_block']:
        bad.append('主药被合绊(%s)' % d['step_medicine_blocked'])
    # --- 毒药·冲: 岁运支冲主药根 / 月令提纲 / 日主重根 ---
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

    # --- 毒药·三刑(岁运支参与成刑; 原典寅巳申/丑戌未须三支俱全, 子卯两支即成).
    #     自刑(辰午酉亥同支再见)非战克、主小自扰, 不入毒药 hard_bad ---
    for _x in step['tp'].get('combination_facts', {}).get('sanxing', []):
        _label = _x.get('type', '')
        _brs = _x.get('branches') or []
        if cur_z in _brs and not _label.endswith('自刑'):
            bad.append('三刑(%s)' % _label)

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

    # --- 毒药·格局破格: 原局成格 + 岁运触发 po_ge 路径 ---
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

    if shorthand == '良药' and evil_offset.verdict_arbitrate(good, bad)['level'] == 2 \
            and any(('制主病' in x or '化泄' in x or '暖化' in x) for x in good):
        direction = '病得制化/暖解, 可顺势进取'
    elif shorthand == '良药':
        direction = '身得帮, 宜稳守蓄力'
    elif shorthand == '毒药':
        direction = '忌妄动, 防%s, 宜守待时' % ';'.join(bad)
    elif shorthand == '平战':
        direction = '吉凶交战(干%s支%s), 大事缓图' % (cur_g, cur_z)
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
