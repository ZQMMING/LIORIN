# -*- coding: utf-8 -*-
"""
PATCH-051 Special Pattern Runtime Integration
外格运行时集成：外格规则串成入口，与正格竞争裁决
流程: 排盘事实 → 外格规则全集 → Resolver裁决 → 正格兜底
"""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN
from wai_ge_rules import (cong_sha_rule, quzhi_rule, yan_shang_rule,
                          runxia_rule, conger_rule, congshi_rule, conge_rule, jiase_rule)
from huaqi_rules import huaqi_rule
from special_pattern_resolver import resolve

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}

# 外格规则全集（從格4+专旺4+化气）
WAI_GE_RULES = [cong_sha_rule, quzhi_rule, yan_shang_rule, runxia_rule,
                conger_rule, congshi_rule, conge_rule, jiase_rule, huaqi_rule]


def run_special_pattern(c):
    """外格运行时入口：跑全外格规则→Resolver裁决"""
    candidates = []
    for rule in WAI_GE_RULES:
        r = rule(c)
        if r:
            candidates.append(r)
    result = resolve(candidates, c)
    result["candidates"] = [x["pattern_state"] for x in candidates]
    return result


if __name__ == '__main__':
    print("=== 051 外格 Runtime 集成测试 ===\n")
    cases = [
        ("GC-001 正格财(应不触外格)", 1983, 11, 3, 11),
        ("GC-009 從殺", 1983, 12, 15, 0),
        ("GC-010 曲直", 1985, 7, 15, 22),
        ("GC-014 從勢", 1968, 5, 15, 10),
        ("GC-016 甲己化土", 1960, 7, 15, 10),
    ]
    for name, y, m, d, h in cases:
        p = paipan(y, m, d, h)
        c = {'dm': p['day_master'],
             'stems': [p['stems']['年'], p['stems']['月'], p['stems']['时']],
             'br': list(p['branches'].values()), 'month': p['month_order']}
        r = run_special_pattern(c)
        print(f'{name}: {p["pillars"]}')
        print(f'  命中: {r["candidates"]}')
        print(f'  裁决: {r["resolved_pattern"]}')
        print(f'  日志: {r["conflict_log"]}\n')
