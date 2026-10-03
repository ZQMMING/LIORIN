# -*- coding: utf-8 -*-
"""relations 统一关系表构建器 (阶段1)

依据: p0_v2/combination_facts_contract.md v1.1
      §1.1 schema / §1.7 四条硬约束 / §1.8 前置核1-B 结果(diff=0)

本模块是 L0 relations 的【唯一生成源】。旧九键在阶段1仍由 l0_fact_builder 原逻辑生成,
本模块不改它们; 阶段2 起旧键改由本模块的 relations 派生。

四条硬约束(落码时不得违反):
  ① positions 两层: 一般关系 [[pos_i],[pos_j]]; SELF 例外 = 扁平 [pos_a,pos_b,...]
  ② pos_i < pos_j  (year<month<day<hour)
  ③ 派生旧键必须【全局按 (pos_i,pos_j) 排序】, 不能按 relation 顺序展开
  ④ 不同 type 不合并 (同一柱位对可出 CHONG+HE 两条)

聚合键必须是【有序 tuple】, 不能用 frozenset:
  DT-0017 [[丑,未],[未,丑]] 是两种顺序, frozenset 并成一条后展开无法还原原序。
"""
from typing import Any, Dict, List

# ── 位置序 (硬约束②) ──
POSK = ("year", "month", "day", "hour")
POSI = {p: i for i, p in enumerate(POSK)}

# ── 六合/六冲 ──
LIUHE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
         "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
LIUCHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
            "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}

# ── 三合/三会 (branches 用标准序, 不跟盘序 —— 契约§1.3) ──
SANHE = [{"pair": ["申", "子", "辰"], "name": "申子辰合水"},
         {"pair": ["亥", "卯", "未"], "name": "亥卯未合木"},
         {"pair": ["寅", "午", "戌"], "name": "寅午戌合火"},
         {"pair": ["巳", "酉", "丑"], "name": "巳酉丑合金"}]
SANHUI = [{"pair": ["寅", "卯", "辰"], "name": "寅卯辰三会木"},
          {"pair": ["巳", "午", "未"], "name": "巳午未三会火"},
          {"pair": ["申", "酉", "戌"], "name": "申酉戌三会金"},
          {"pair": ["亥", "子", "丑"], "name": "亥子丑三会水"}]

# ── 半合 (生地/墓地) ──
BANHE_PAIRS = {frozenset(("申", "子")): "水", frozenset(("亥", "卯")): "木",
               frozenset(("寅", "午")): "火", frozenset(("巳", "酉")): "金",
               frozenset(("子", "辰")): "水", frozenset(("卯", "未")): "木",
               frozenset(("午", "戌")): "火", frozenset(("酉", "丑")): "金"}

# ── 害/破/刑 ──
LIUHAI = [{"pair": ["子", "未"], "name": "子未相害"}, {"pair": ["丑", "午"], "name": "丑午相害"},
          {"pair": ["寅", "巳"], "name": "寅巳相害"}, {"pair": ["卯", "辰"], "name": "卯辰相害"},
          {"pair": ["申", "亥"], "name": "申亥相害"}, {"pair": ["酉", "戌"], "name": "酉戌相害"}]
LIUPO = [{"pair": ["子", "酉"], "name": "子酉相破"}, {"pair": ["丑", "辰"], "name": "丑辰相破"},
         {"pair": ["寅", "亥"], "name": "寅亥相破"}, {"pair": ["卯", "午"], "name": "卯午相破"},
         {"pair": ["巳", "申"], "name": "巳申相破"}, {"pair": ["未", "戌"], "name": "未戌相破"}]
SANXING = [{"pair": ["寅", "巳", "申"], "name": "寅巳申三刑"},
           {"pair": ["丑", "戌", "未"], "name": "丑戌未三刑"},
           {"pair": ["子", "卯"], "name": "子卯相刑"}]

SELF_PUNISH_ZHI = {"辰", "午", "酉", "亥"}

# ── ★ PATCH-REL-05 (阶段3b) 位置距离 / 阻隔 / 暗会 ──
#   自包含搬自 daymaster_branch_relations.py(核3: 该函数 facts 参数从未被使用, 无循环风险)
#   字段矩阵(2026-10-03 裁定, 显式约束不留下游猜):
#       distance / intervening_branches : 全 type 通用(位置即可算)
#       blocking_branches / has_blocking: 仅 HE 生成; 其余 type = [] (不是 None)
POSITION_DISTANCE = {
    frozenset(('year', 'month')): 'adjacent',
    frozenset(('month', 'day')): 'adjacent',
    frozenset(('day', 'hour')): 'adjacent',
    frozenset(('year', 'day')): 'span_one',
    frozenset(('month', 'hour')): 'span_one',
    frozenset(('year', 'hour')): 'remote',
}
POS_ORDER = {'year': 0, 'month': 1, 'day': 2, 'hour': 3}

# 暗会六局 (滴天髓秘传体系, WEAK 级)
ANHUI_PAIRS = {
    frozenset(('子', '巳')): '庚', frozenset(('午', '亥')): '甲',
    frozenset(('卯', '申')): '乙', frozenset(('酉', '寅')): '丙',
    frozenset(('辰', '巳')): '丑', frozenset(('未', '申')): '辰',
}

# 阻隔判定用表 (化神克星 / 冲神)
_WX_KE_ME = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}   # 化神 -> 克化神者
_WX_KE_ME_BACK = {'金': '木', '水': '火', '木': '土', '火': '金', '土': '水'}
_BENQI_WUXING = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
                 '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
                 '戌': '土', '亥': '水'}
_LIUCHONG_MAP = {'子': '午', '丑': '未', '寅': '申', '卯': '酉', '辰': '戌', '巳': '亥',
                 '午': '子', '未': '丑', '申': '寅', '酉': '卯', '戌': '辰', '亥': '巳'}


def _geom(pa, pb):
    """两柱之间的位置事实: (distance, intervening 的柱位名列表)
    distance/intervening 是【位置语义】, 与支名无关 -> 全 type 通用。
    """
    ia, ib = POSI[pa], POSI[pb]
    dist = POSITION_DISTANCE.get(frozenset((pa, pb)), 'unknown')
    inter = [POSK[k] for k in range(min(ia, ib) + 1, max(ia, ib))]
    return dist, inter


def _blocking_of(interv_zhi, a, b, huashen):
    """阻隔支收集 (仅 HE): 中间支为「化神克星」或「冲神」
    严格复刻 daymaster_branch_relations.py L97-116。
    """
    ke_wx = _WX_KE_ME.get(huashen, '')
    out = []
    for ib in interv_zhi:
        if _BENQI_WUXING.get(ib) == ke_wx:
            out.append(ib)
        if _LIUCHONG_MAP.get(ib) in (a, b) and ib not in out:
            out.append(ib)
    return out


def build_relations(zlis: List[str]) -> List[Dict[str, Any]]:
    """按统一 schema 构建 relations。

    输入: 四支地支名, 盘序 [year, month, day, hour]
    输出: relations 列表, 每条 {type, branches, positions, wx, meta, instance_count}

    硬约束①: positions 恒两层; SELF 例外为扁平
    硬约束②: 一般关系每组实例 pos_i < pos_j
    硬约束④: 不同 type 不合并(聚合键含 type)

    ★ PATCH-REL-04 (阶段3a) instances 升为主字段
      instances: [{a_pos, b_pos, ...可选 distance/blocking}]   ← 真源
      positions: [[a_pos],[b_pos]]                              ← 派生视图
      理由: distance/blocking 是【实例级】语义(聚合后 N 实例各不同),
            relation 级单值会丢 N-1 份。
    """
    R: List[Dict[str, Any]] = []
    _agg: Dict[tuple, Dict[str, Any]] = {}

    def put(t, brs, pos_inst, wx=None, meta=None, distance=None,
            intervening=None, blocking=None, extra=None):
        """聚合同一 (type, 有序支名对) 的所有实例为一条 relation

        instances 是主字段(真源); positions 由 instances 派生(视图)。
        SELF 的 pos_inst 是扁平柱位列表(硬约束①例外), 走 _put_flat 分支。
        """
        if t == 'SELF':
            # SELF 单支不成对: positions 元素本身是柱位集合, 非实例对
            key = (t, tuple(brs))
            r = _agg.get(key)
            if r is None:
                r = {'type': t, 'branches': list(brs), 'positions': [],
                     'instances': [], 'wx': wx, 'meta': meta or {},
                     'instance_count': 0}
                _agg[key] = r
                R.append(r)
            r['positions'].append(pos_inst)      # 扁平, 供旧键派生
            r['instances'].append({'positions': list(pos_inst)})  # 集合语义
            r['instance_count'] = len(r['positions'])
            return r
        key = (t, tuple(brs))
        r = _agg.get(key)
        if r is None:
            r = {'type': t, 'branches': list(brs), 'positions': [],
                 'instances': [], 'wx': wx, 'meta': meta or {},
                 'instance_count': 0}
            _agg[key] = r
            R.append(r)
        # 主字段: instances
        pa, pb = pos_inst[0][0], pos_inst[1][0]
        inst = {'a_pos': pa, 'b_pos': pb}
        # distance / intervening_branches: 【全 type 通用】(位置语义, 与支名无关)
        d, ik = _geom(pa, pb)
        inst['distance'] = distance if distance is not None else d
        inst['intervening_branches'] = [zlis[POSI[k]] for k in ik]   # ik 为柱位名
        # blocking / has_blocking: 【仅 HE 生成】, 其余 type 恒 [] (不是 None)
        if t == 'HE' and blocking is not None:
            inst['blocking_branches'] = list(blocking)
            inst['has_blocking'] = len(blocking) > 0
        else:
            inst['blocking_branches'] = []
            inst['has_blocking'] = False
        r['instances'].append(inst)
        # 派生视图: positions（保持 v1.1 格式 [[a_pos],[b_pos]]）
        r['positions'].append([[inst['a_pos']], [inst['b_pos']]])
        r['instance_count'] = len(r['instances'])
        return r

    # ① 六合 / 六冲: i<j 实例遍历 (复刻 l0_fact_builder L177-181)
    #    六合额外算 blocking(化神克星/冲神); 六冲无化神 -> blocking=[]
    _HE_WX = {frozenset(('子', '丑')): '土', frozenset(('寅', '亥')): '木',
              frozenset(('卯', '戌')): '火', frozenset(('辰', '酉')): '金',
              frozenset(('巳', '申')): '水', frozenset(('午', '未')): '土'}
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = zlis[i], zlis[j]
            if LIUHE.get(a) == b:
                hs = _HE_WX.get(frozenset((a, b)))
                _, ik = _geom(POSK[i], POSK[j])       # ik 为柱位名列表
                blk = _blocking_of([zlis[POSI[k]] for k in ik], a, b, hs) if hs else []
                put('HE', [a, b], [[POSK[i]], [POSK[j]]], wx=hs, blocking=blk)
            if LIUCHONG.get(a) == b:
                put('CHONG', [a, b], [[POSK[i]], [POSK[j]]])
    # ★ ANHUI 暗会: 支对∈ANHUI_PAIRS 且 distance=='adjacent' 才成立
    #   条件②「不混杂(无刑冲)」—— daymaster_branch_relations L131 注释有, 代码未实现。
    #   裁定(2026-10-03): 不实现(保 diff=0), 但在 meta 显式记 condition_2_pending=True。
    #   该状态含义是「待核」不是「故意不做」: 等核刘基原注有无「暗会忌刑冲」明文再裁。
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = zlis[i], zlis[j]
            k = frozenset((a, b))
            if k not in ANHUI_PAIRS:
                continue
            d, _ = _geom(POSK[i], POSK[j])
            if d != 'adjacent':
                continue
            put('ANHUI', [a, b], [[POSK[i]], [POSK[j]]],
                wx=ANHUI_PAIRS[k],
                meta={'anhui_shen': ANHUI_PAIRS[k],
                      'evidence_grade': 'WEAK',
                      'note': '暗会: 表面虚而实增强, 喜增吉忌添凶',
                      'condition_2_pending': True})

    zset = set(zlis)

    def posof(z):
        """支名 z 在盘内的全部柱位 (硬约束②: 已按 POSK 序, 天然 i<j)"""
        return [p for p in POSK if zlis[POSI[p]] == z]

    # ② 三合 / 三会: 集合包含, 三支齐全才报 (契约§1.5)
    for s in SANHE:
        if set(s['pair']).issubset(zset):
            put('SANHE', list(s['pair']), [posof(z) for z in s['pair']],
                wx=s['name'][-1], meta={'name': s['name']})
    for s in SANHUI:
        if set(s['pair']).issubset(zset):
            put('HUI', list(s['pair']), [posof(z) for z in s['pair']],
                wx=s['name'][-1], meta={'name': s['name']})

    # ③ 半合: i<j + _seen 去重 (契约§1.4 去重口径)
    seen = set()
    for i in range(4):
        for j in range(i + 1, 4):
            k = frozenset((zlis[i], zlis[j]))
            if k in BANHE_PAIRS and k not in seen:
                put('BANHE', [zlis[i], zlis[j]], [[POSK[i]], [POSK[j]]],
                    wx=BANHE_PAIRS[k])
                seen.add(k)

    # ④ 害 / 破 / 刑: 集合包含
    for t, S in (('HAI', LIUHAI), ('PO', LIUPO), ('XING', SANXING)):
        for s in S:
            if set(s['pair']).issubset(zset):
                put(t, list(s['pair']), [posof(z) for z in s['pair']],
                    meta={'name': s['name']})

    # ⑤ 自刑: 单支不成对 —— 【硬约束① 的例外, 不额外包列表】
    pb: Dict[str, List[str]] = {}
    for idx, z in enumerate(zlis):
        pb.setdefault(z, []).append(POSK[idx])
    for z, pos in pb.items():
        if z in SELF_PUNISH_ZHI and len(pos) >= 2:
            # SELF positions 是【集合语义】, 列表仅是 JSON 承载(JSON 无 set)。
            # 此处 sorted() 按字母序仅为稳定输出(同集合每次同样的列表), 【非语义约束】。
            # 消费者按集合读, 不按顺序读。要位置序请自行按 POSK 重排。
            put('SELF', [z], sorted(pos))
    return R


def derive_pair_key(relations: List[Dict[str, Any]], rtype: str) -> List[List[str]]:
    """【硬约束③】派生成对类旧键(liuhe/liuchong)。

    必须汇总所有 relation 的所有实例后【全局按 (pos_i,pos_j) 排序】,
    不能按 relation 顺序展开 —— 否则双子盘(count>=3)会丢失实例交错序。
    """
    inst = []
    for r in relations:
        if r['type'] != rtype:
            continue
        # 优先读 instances(主字段); 无 instances 时回落 positions(视图)
        src = r.get('instances') or []
        if src and 'a_pos' in src[0]:
            for iv in src:
                pi, pj = POSI[iv['a_pos']], POSI[iv['b_pos']]
                inst.append((min(pi, pj), max(pi, pj), list(r['branches'])))
        else:
            for pair in r['positions']:
                pi, pj = POSI[pair[0][0]], POSI[pair[1][0]]
                inst.append((min(pi, pj), max(pi, pj), list(r['branches'])))
    inst.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in inst]


def derive_by_name(relations: List[Dict[str, Any]], rtype: str) -> List[str]:
    """派生按名类旧键(sanhe/sanhui/liuhai/liupo/sanxing)"""
    return [r['meta']['name'] for r in relations if r['type'] == rtype]


def derive_banhe(relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """派生 banhe"""
    return [{'pair': r['branches'], 'wx': r['wx']}
            for r in relations if r['type'] == 'BANHE']


def derive_self_punishment(relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """派生 self_punishment (positions 扁平, 已脱一层)"""
    return [{'branch': r['branches'][0], 'positions': sorted(r['positions'][0])}
            for r in relations if r['type'] == 'SELF']


def derive_all(relations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """从 relations 派生全部九个旧键(阶段2 用)"""
    return {
        'liuhe': derive_pair_key(relations, 'HE'),
        'liuchong': derive_pair_key(relations, 'CHONG'),
        'sanhe': derive_by_name(relations, 'SANHE'),
        'sanhui': derive_by_name(relations, 'HUI'),
        'banhe': derive_banhe(relations),
        'liuhai': derive_by_name(relations, 'HAI'),
        'liupo': derive_by_name(relations, 'PO'),
        'sanxing': derive_by_name(relations, 'XING'),
        'self_punishment': derive_self_punishment(relations),
    }
