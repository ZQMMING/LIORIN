# -*- coding: utf-8 -*-
"""地支关系事实层 (D1/D2).
原典依据:
  D1 六合: 子丑/寅亥/卯戌/辰酉/巳申/午未 (子平真诠/三命通会)
  D1 暗会: 子巳/午亥/卯申/酉寅/辰巳/未申 (滴天髓秘传体系, WEAK级)
  D2 位置距离: adjacent(相邻)/span_one(隔一位)/remote(遥隔)
  D2-B 阻隔: 中间支为化神克星或冲神

本层只记录结构事实: 关系对/类型/位置距离/阻隔.
不判吉凶, 不判合力大小(只记录距离事实).
"""
from typing import Any, Dict, List

# ★ ARCHIVED_FALLBACK (2026-10-06): 本文件已是 relations 派生视图,
#   六合/暗会实例由 relations_builder(L0 唯一源) 生成, 本表不再主链使用.
#   备份: _legacy_relation_tables.
# D1 六合六组
LIUHE_PAIRS = {
    frozenset(('子', '丑')): '土',
    frozenset(('寅', '亥')): '木',
    frozenset(('卯', '戌')): '火',
    frozenset(('辰', '酉')): '金',
    frozenset(('巳', '申')): '水',
    frozenset(('午', '未')): '土',  # 午未合土/火, 取土为主
}

# D1 暗会六局 (滴天髓秘传体系, WEAK级)
# 暗会形态: 两支贴近, 中间隔一支为引(如: 子巳←丑)
ANHUI_PAIRS = {
    frozenset(('子', '巳')): '庚',  # 子巳暗会庚局
    frozenset(('午', '亥')): '甲',  # 午亥暗会甲局
    frozenset(('卯', '申')): '乙',  # 卯申暗会乙局
    frozenset(('酉', '寅')): '丙',  # 酉寅暗会丙局
    frozenset(('辰', '巳')): '丑',  # 辰巳暗会丑局
    frozenset(('未', '申')): '辰',  # 未申暗会辰局
}

# D2 位置距离 (与天干M2-A同构, 但地支定义稍不同)
POSITION_DISTANCE = {
    frozenset(('year', 'month')): 'adjacent',      # 相邻
    frozenset(('month', 'day')): 'adjacent',       # 相邻
    frozenset(('day', 'hour')): 'adjacent',        # 相邻
    frozenset(('year', 'day')): 'span_one',        # 隔一位
    frozenset(('month', 'hour')): 'span_one',      # 隔一位
    frozenset(('year', 'hour')): 'remote',          # 遥隔
}

# 地支位置顺序
POS_ORDER = {'year': 0, 'month': 1, 'day': 2, 'hour': 3}


def build_branch_relations(pillars: Dict[str, Any], facts: Dict[str, Any],
                           l0_chart=None) -> Dict[str, Any]:
    """构建地支关系事实层.
    
    输入:
      pillars: {year:[干,支], month:[干,支], day:[干,支], hour:[干,支]}
      facts: l0_fact_builder的输出
    
    输出:
      {
        'zhi_relations': [
          {
            'branches': ['子', '丑'],
            'type': 'liuhe',  # liuhe/anhui
            'huashen': '土',  # 化神五行(六合)
            'position': 'adjacent',  # adjacent/span_one/remote
            'positions': ['year', 'day'],
            'intervening_branches': ['寅'],  # 中间支
            'blocking_branches': [],  # 阻隔支(化神克星或冲神)
            'has_blocking': False,
          },
        ],
      }
    """
    # ★ PATCH-REL-06 (阶段3c) branch_relations 降级为 relations 派生视图
    #   本函数【不再自行生成】六合/暗会 —— 改由 engines.common.relations_builder 产出,
    #   relations 是 L0 唯一源(架构 §2.2)。本函数只做【格式投影】, 输出格式与旧版逐字一致。
    #
    #   ⚠ 视图不是「一次降级永久安全」: 每次改 relations 的 schema, 本投影必须同步。
    #      已写入 p0_v2/combination_facts_contract.md §5 回归路径。
    #
    #   relations 的实例元素分两型(契约 §1.7-②):
    #     PAIR 型: {a_pos, b_pos, distance, intervening_branches, blocking_branches, has_blocking}
    #     SELF 型: {positions: [...]}   ← 不成对, 本投影不消费
    try:
        from engines.common.relations_builder import build_relations
        _z = [pillars[k][1] for k in ('year', 'month', 'day', 'hour')]
        _R = build_relations(_z, l0_chart)
        _view = []
        for _r in _R:
            _t = _r['type']
            for _iv in _r['instances']:
                if 'a_pos' not in _iv:
                    continue                      # SELF 型不成对, 不属本投影范围
                if _t == 'HE':
                    _view.append({
                        'branches': _r['branches'],
                        'type': 'liuhe',
                        'huashen': _r.get('wx'),
                        'position': _iv.get('distance'),
                        'positions': [_iv['a_pos'], _iv['b_pos']],
                        'intervening_branches': _iv.get('intervening_branches') or [],
                        'blocking_branches': _iv.get('blocking_branches') or [],
                        'has_blocking': _iv.get('has_blocking', False),
                    })
                elif _t == 'ANHUI':
                    _view.append({
                        'branches': _r['branches'],
                        'type': 'anhui',
                        'anhui_shen': _r.get('wx'),
                        'position': _iv.get('distance'),
                        'positions': [_iv['a_pos'], _iv['b_pos']],
                        'evidence_grade': 'WEAK',
                        'note': '暗会: 表面虚而实增强, 喜增吉忌添凶',
                    })
        return {'zhi_relations': _view}
    except Exception:
        # 投影失败不静默: relations 不可用时抛, 不回落到旧自行生成逻辑
        # (回落会造成「两个源」, 违反 L0 唯一源)
        raise

    return {'zhi_relations': relations}
