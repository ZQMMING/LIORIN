# -*- coding: utf-8 -*-
"""Production Entry Gate (PATCH-ProdGate)
唯一生产入口: production_entry(chart: FrozenCanonicalBaziChart) -> EngineResult.
Gate 只验证身份/contract, 不排盘, 不重算; 失败 fail-closed, 不进入主链.
l0_fact_builder.build() 是内部计算 primitive, 不由外部直接调用作生产入口.
串联: L0 Fact → 160-B多维网络 → 160-C 38 Query (不判身强/用神/吉凶).
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import sys

import sys


@dataclass(frozen=True)
class FrozenCanonicalBaziChart:
    """Canonical/Frozen Bazi 身份对象.
    外部生产方必须构造此对象进入 gate; 普通 pillars dict / BaziChart / BirthInput 一律拒绝.
    本类不排盘, 只携带已冻结的 canonical pillars 与身份标记.
    可选 dayun/liunian 用于应期层."""
    pillars: Dict[str, list]
    canonical: bool = True
    frozen: bool = True
    source: str = "canonical_frozen"
    dayun: list = None
    liunian: str = None


def _fail_closed(reason: str, gate: str) -> Dict[str, Any]:
    return {
        "engine_result": None,
        "gate_passed": False,
        "gate": gate,
        "reason": reason,
        "boundary_note": "Gate 失败 fail-closed, 未执行任何 Rule/Judgment",
    }


def _validate_contract(pillars: Dict[str, list]) -> str:
    """验证 canonical contract 完整性. 返回 '' 表示通过, 否则错误原因."""
    required = ("year", "month", "day", "hour")
    if not isinstance(pillars, dict):
        return "pillars 不是 dict"
    for k in required:
        if k not in pillars:
            return f"缺 {k}"
        v = pillars[k]
        if not isinstance(v, (list, tuple)) or len(v) != 2:
            return f"{k} 不是 [干, 支]"
    return ""


def _build_l1_queries(pillars: Dict[str, list], facts: Dict[str, Any]) -> Dict[str, Any]:
    """串联 L1: 160-B多维网络 + 160-C 38 Query.
    只输出结构事实, 不判身强/用神/吉凶."""
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

    hidden_stems_table = {pillars[k][1]: facts['hidden_stems'][k] for k in ('year','month','day','hour')}
    pa = build_power_structure(pillars)
    rc = build_root_classes(pillars, hidden_stems_table)
    tc = build_tou_cang(facts)
    wx = build_wang_xiang(facts, facts['day_stem'])
    rr = build_root_relations(rc, facts['combination_facts'])
    ts = build_two_side(rc, tc, rr)
    bt = build_branch_tiers(pillars, facts)
    th = build_tian_he(pillars, facts)
    network = build_power_network(pa, rc, tc, wx, rr, ts, branch_tier=bt, tian_he=th, facts=facts)
    queries = run_queries(network)
    return {
        'power_network': network,
        'root_classes': rc,
        'tian_he': th,
        'queries': queries,
        'query_summary': {
            'total': len(queries),
            'supported': sum(1 for q in queries if q['state']=='SUPPORTED'),
            'not_supported': sum(1 for q in queries if q['state']=='NOT_SUPPORTED'),
            'unknown': sum(1 for q in queries if q['state']=='UNKNOWN'),
        },
    }


def _build_meta_outputs(pillars: Dict[str, list], facts: Dict[str, Any]) -> Dict[str, Any]:
    """Authority Matrix: 命理元统一输出层.
    6命理元(旺衰/强弱/格局/调候/病药/用神)多轨输出, 冲突保留不裁决.
    只输出结构事实和候选, 不输出综合裁决/最终用神/吉凶.
    """
    try:
        from engines.common.daymaster_root_class import build_root_classes
        from engines.common.root_effectiveness_filter import filter_root_effectiveness
        from engines.common.meta_unified_output import build_all_meta_outputs

        hidden_stems_table = {pillars[k][1]: facts['hidden_stems'][k] for k in ('year','month','day','hour')}
        root_classes = build_root_classes(pillars, hidden_stems_table)
        root_effectiveness = filter_root_effectiveness(root_classes, facts['combination_facts'], pillars, facts['day_stem'])

        # 构建用神四轨并行层需要的参数
        # PATCH-GAP1 (2026-09-30): 补 pillars / wuxing_power / spectrum / special。
        # 此前 extra_data 只传 climate + bingyao，而 _build_yongshen_tracks 的接入条件
        # 要求 pillars/wuxing_power/spectrum/special/climate 五项齐备，条件永不满足，
        # 致 ZPZQ/QTBJ/SFTK/DTS 四轨全部落进占位轨(note='待接入yongshen_multi_track')。
        # 这是接线缺口，不是字段缺失 —— yongshen_multi_track 本身已实现且可跑通。
        try:
            from engines.common.climate_structure import build_climate_structure
            from engines.common.bingyao_layer import build_bingyao_layer
            from engines.common.daymaster_power_structure import build_power_structure
            from engines.common.special_pattern import build_special_patterns

            climate = build_climate_structure(pillars, facts)
            bingyao = build_bingyao_layer(facts, [])

            # spectrum: 日主力量结构(160-A)，只组织已有 L0 Fact，不评分不权重
            try:
                spectrum = build_power_structure(pillars)
            except Exception:
                spectrum = None

            # special: 特殊格局结构定性(只打标签，不判用神吉凶成败)
            try:
                special = build_special_patterns(
                    pillars, facts, facts.get('wuxing_power'), facts.get('tian_he'), climate)
            except Exception:
                special = None

            extra_data = {
                'pillars': pillars,
                'wuxing_power': facts.get('wuxing_power'),
                'spectrum': spectrum,
                'special': special,
                'climate': climate,
                'bingyao': bingyao,
            }
        except Exception:
            extra_data = {}

        return build_all_meta_outputs(facts, root_effectiveness, root_classes, extra_data)
    except Exception as e:
        return {
            'authority_matrix_version': 'v0.1',
            'error': str(e),
            'meta_outputs': {},
            'meta_count': 0,
            'boundary_note': '命理元统一输出层构建失败, 不影响主链',
        }


def production_entry(chart: Any, climate_table: Optional[Dict] = None) -> Dict[str, Any]:
    """唯一生产入口.
    G-P01 类型 = FrozenCanonicalBaziChart
    G-P02 canonical/frozen 身份有效
    G-P03 必要 canonical contract 完整
    G-P04 通过 Gate 后才进入主链
    G-P05 失败 fail-closed, 不执行任何 Rule/Judgment
    串联: L0 Fact → 160-B网络 → 160-C 38 Query (不判身强/用神/吉凶)
    """
    # G-P01
    if not isinstance(chart, FrozenCanonicalBaziChart):
        return _fail_closed(
            "输入不是 FrozenCanonicalBaziChart; 普通 dict/BaziChart/BirthInput 不得作为生产入口",
            "G-P01")
    # G-P02
    if not (getattr(chart, "canonical", False) and getattr(chart, "frozen", False)):
        return _fail_closed("缺 canonical/frozen 身份标记", "G-P02")
    # G-P03
    err = _validate_contract(chart.pillars)
    if err:
        return _fail_closed(f"canonical contract 不完整: {err}", "G-P03")

    # G-P04 通过 Gate, 进入主链
    from engines.common.l0_fact_builder import build
    facts = build(chart.pillars)
    facts['pillars'] = chart.pillars   # 供辩层数透干/本根(数透干须排除日干)

    # 注入五行纯规则计数(wuxing_power), 供病药层识别"印多埋子/比劫成党"等力量驱动病机
    # 不注入则依赖力量计数的病机全部失效, 仅剩字面共现病机(如枭神夺食)
    try:
        from engines.common.wuxing_power import build_wuxing_power
        facts['wuxing_power'] = build_wuxing_power(chart.pillars, facts)
    except Exception as _e:
        facts['wuxing_power'] = {}

    # 格局成格判定(最小闭环: 食神生财格) -> facts['ge_cheng']
    try:
        from engines.common.ge_jie_layer import build_ge_cheng
        build_ge_cheng(facts)
    except Exception:
        facts['ge_cheng'] = None

    # L1: 160-B网络 + 160-C 38 Query
    l1 = _build_l1_queries(chart.pillars, facts)

    # 根分类单一数据源: 回写 build_root_classes(同五行+十二长生) 结果,
    # 覆盖 l0 旧 rt(只认日干同字, 漏同五行根如辰中乙, 致 root_weight_class_facts 为空)
    _rc = l1.get('root_classes')
    if _rc:
        def _norm(rcv):
            if rcv.startswith('HEAVY'):
                return 'HEAVY'
            if rcv.startswith('LIGHT') or rcv == 'SPECIAL_LONGSHENG_YIN':
                return 'LIGHT'
            return 'NONE'
        facts['root_weight_class_facts'] = {
            pos: {'branch': chart.pillars[pos][1],
                  'class': _norm(_rc['per_pillar'][pos]['root_class'])}
            for pos in ('year', 'month', 'day', 'hour')}
        facts['tian_he'] = l1.get('tian_he')

    # Authority Matrix: 命理元统一输出层 (6命理元多轨输出, 冲突保留不裁决)
    meta_outputs = _build_meta_outputs(chart.pillars, facts)

    # 算→辩→解 完整链 (用L1真实queries, 非空列表)
    zhenglun = None
    try:
        from engines.common.bingyao_layer import build_bingyao_layer
        from engines.common.bing_debate import resolve_primary_bing
        from engines.common.zhuangui_layer import resolve_zhuangui
        from engines.common.qtbj_climate_candidates import build_climate_candidates
        from engines.common.yongyao_resolve import resolve_yongyao
        _by = build_bingyao_layer(facts, l1.get('queries', []))
        _deb = resolve_primary_bing(facts, _by['bing_list'])
        _zg = resolve_zhuangui(facts, _deb)
        _cli = build_climate_candidates(facts, external_table=climate_table)
        _yy = resolve_yongyao(facts, _zg, _cli)
        zhenglun = {'bingyao': _by, 'debate': _deb, 'zhuangui': _zg,
                    'climate_static': _cli, 'yongyao': _yy}
    except Exception as _e:
        # 异常不再静默吞掉(曾导致格成案例bingyao崩被掩盖显示"无病"):
        # 完整保留 traceback 到 zhenglun, 并输出到 stderr 供回归显式捕获
        import traceback as _tb
        _tb.print_exc(file=sys.stderr)
        zhenglun = {'error': str(_e), 'traceback': _tb.format_exc()}

    result = {
        "engine_result": facts,
        "l1_result": l1,
        "meta_outputs": meta_outputs,
        "zhenglun": zhenglun,
        "gate_passed": True,
        "gate": "PASSED",
        "reason": "canonical/frozen 身份有效, contract 完整",
        "source": chart.source,
        "boundary_note": "L0 Fact + L1 Query + Authority Matrix + 算辩解(主病/用药方向); 用药为方向非吉凶裁决; Judgment 仍走 fail-closed gate",
    }
    # 可选大运/流年层
    if chart.dayun:
        from engines.common.dayun_summary import dayun_summary
        result['dayun_summary'] = dayun_summary(chart.pillars, chart.dayun)
    if chart.dayun and chart.liunian:
        from engines.common.liunian_summary import liunian_summary
        result['liunian_summary'] = liunian_summary(chart.pillars, chart.dayun, chart.liunian)
    return result
