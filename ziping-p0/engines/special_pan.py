# -*- coding: utf-8 -*-
"""特殊格局+正格 统一主入口"""
import sys
sys.path.insert(0, '.')

from spec.root_qi import STEM_WUXING, calc_root_qi
from spec.node_system import build_nodes, build_edges
from engines.zhengge_gates import zhengge_f0
from engines.zhengge_quge import l1_quge
from engines.zhengge_xiangshen import l2_xiangshen, l3_chengbai, zhengge_grade

# 新谓词版（唯一路径）
from engines.cong_ge_graph import cong_ge_pan_graph
from engines.zhuanwang_graph import zhuanwang_pan_graph
from engines.huaqi_graph import huaqi_pan_graph


def special_pan(stems, branches, day_stem, root_qi_val=None):
    """
    统一格局判定主入口
    优先级：化气 → 专旺 → 从格 → 正格

    返回：(family, grade, reason_tag)
    """
    if root_qi_val is None:
        root_qi_val = calc_root_qi(day_stem, branches, stems)
    
    # 构建节点图（唯一构建点）
    positions = ['年', '月', '日', '时']
    pillars = {}
    for i, pos in enumerate(positions):
        pillars[pos] = [stems[i], branches[i]]
    
    nodes = build_nodes(pillars, day_stem)
    edges = build_edges(pillars, nodes)
    
    # 第一步：化气族（优先级最高）
    huaqi_ok, huaqi_wx, huaqi_reasons = huaqi_pan_graph(day_stem, nodes, edges)
    if huaqi_ok:
        return (f"化气·{huaqi_wx}", "CONFIRMED", " | ".join(huaqi_reasons))
    
    # 第二步：专旺族
    zw_ok, zw_name, zw_reasons = zhuanwang_pan_graph(day_stem, nodes, edges)
    if zw_ok:
        return (f"专旺·{zw_name}", "CONFIRMED", " | ".join(zw_reasons))
    
    # 第三步：从格族
    cong_ok, cong_name, cong_reasons = cong_ge_pan_graph(day_stem, nodes, edges)
    if cong_ok:
        return (f"从格·{cong_name}", "CONFIRMED", " | ".join(cong_reasons))
    
    # 第四步：正格族（兜底）
    f0_ok, f0_reason = zhengge_f0(branches)
    if not f0_ok:
        return ("正格", "REJECT", f0_reason)
    
    ge, quge_reason = l1_quge(stems, branches, day_stem)
    if ge is None:
        return ("正格", "REJECT", quge_reason)
    
    day_wx = STEM_WUXING[day_stem]
    xiangshen, xs_reason = l2_xiangshen(ge, day_wx, stems, branches)
    poges, cb_reason = l3_chengbai(ge, day_wx, stems, branches)
    grade, demote, grade_reason = zhengge_grade(ge, xiangshen, poges, day_wx, stems, branches, branches[1])
    
    return (f"正格·{ge}", grade, f"{quge_reason} | {xs_reason} | {cb_reason} | {grade_reason}")
