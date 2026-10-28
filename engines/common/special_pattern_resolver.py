# -*- coding: utf-8 -*-
"""
PATCH-048 Special Pattern Resolver
外格竞争机制：多外格同时命中时的裁决顺序与互斥表

铁律：
1. 无评分/无权重——按经典铁律谓词优先级，非投票
2. 从格(日主无根) 与 专旺格(单行成势有根) 天然互斥
3. 外格成格则弃正格
4. 无法唯一裁决 → CONFLICT_UNRESOLVED → FAIL_CLOSED
"""
import sys
sys.path.insert(0, r'engines\common')
from gc002_builder import HIDDEN

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}


# 外格互斥表：同组内互斥，只能取一个
MUTEX_GROUPS = {
    'CONG': {  # 從格组：日主无根
        'members': ['從財格', '從殺格', '從兒格', '從勢格'],
        'principle': '日主无根铁律；多從格同时命中→按成格纯度(单行成势者优先)；无法区分→CONFLICT'
    },
    'ZHUANWANG': {  # 专旺组：单行成势有根
        'members': ['曲直格', '炎上格', '稼穡格', '從革格', '潤下格'],
        'principle': '单行成势铁律；互斥于從格组'
    },
    'HUAQI': {  # 化气组：日干合化
        'members': ['甲己化土', '乙庚化金', '丙辛化水', '丁壬化木', '戊癸化火'],
        'principle': '合化成功则弃原局；与其他外格互斥'
    }
}

# 裁决顺序（优先级高者先裁）
RESOLVE_ORDER = [
    ('HUAQI', '化气格', '日干合化成功者最高优先（化气则弃原局）'),
    ('CONG', '從格组', '日主无根者成從格'),
    ('ZHUANWANG', '专旺组', '单行成势有根者成专旺'),
    ('ZHENG', '正格', '以上皆不成→回PZZQ正格'),
]


def resolve(candidates, c):
    """
    candidates: list of {"pattern_state": "DETERMINED(從財格)", ...}
    c: 命局事实
    return: {"resolved_pattern": ..., "conflict_log": [...], "resolve_order": [...]}
    """
    if not candidates:
        return {"resolved_pattern": None, "conflict_log": ["无外格命中"], "resolve_order": []}

    hit = {x["pattern_state"].split("(")[1].rstrip(")"): x for x in candidates}
    logs = []

    # 1) 化气组
    huaqi_hits = [k for k in hit if k in MUTEX_GROUPS['HUAQI']['members']]
    if huaqi_hits:
        return {"resolved_pattern": hit[huaqi_hits[0]]["pattern_state"],
                "conflict_log": [f"化气组命中{huaqi_hits[0]}，最高优先，弃原局"],
                "resolve_order": ["HUAQI"]}

    # 2) 從格组
    cong_hits = [k for k in hit if k in MUTEX_GROUPS['CONG']['members']]
    if cong_hits:
        if len(cong_hits) == 1:
            return {"resolved_pattern": hit[cong_hits[0]]["pattern_state"],
                    "conflict_log": [f"從格组唯一命中{cong_hits[0]}"],
                    "resolve_order": ["CONG"]}
        # 多從格同命中——按成格纯度：单行成势者(從兒/從財/從殺)优先于從勢(多行)
        pure = [k for k in cong_hits if k != '從勢格']
        if pure:
            logs.append(f"多從格同命中{cong_hits}，取单行成势者{pure[0]}")
            return {"resolved_pattern": hit[pure[0]]["pattern_state"],
                    "conflict_log": logs, "resolve_order": ["CONG"]}
        return {"resolved_pattern": "CONFLICT_UNRESOLVED",
                "conflict_log": [f"從勢格与{cong_hits}同命中，无法唯一裁决→FAIL_CLOSED"],
                "resolve_order": ["CONG"]}

    # 3) 专旺组
    zw_hits = [k for k in hit if k in MUTEX_GROUPS['ZHUANWANG']['members']]
    if zw_hits:
        if len(zw_hits) == 1:
            return {"resolved_pattern": hit[zw_hits[0]]["pattern_state"],
                    "conflict_log": [f"专旺组唯一命中{zw_hits[0]}"],
                    "resolve_order": ["ZHUANWANG"]}
        return {"resolved_pattern": "CONFLICT_UNRESOLVED",
                "conflict_log": [f"专旺组多格同命中{zw_hits}，单行互斥→FAIL_CLOSED"],
                "resolve_order": ["ZHUANWANG"]}

    # 4) 正格
    return {"resolved_pattern": "ZHENG_GE_FALLBACK",
            "conflict_log": [f"外格{list(hit.keys())}未归入互斥组，回正格"],
            "resolve_order": ["ZHENG"]}


if __name__ == '__main__':
    # 竞争测试
    print("=== 048 Special Pattern Resolver 竞争机制自测 ===")
    # 测1：從財+從殺同命中（不可能同时，因为月令唯一）
    r1 = resolve([{"pattern_state": "DETERMINED(從財格)"}, {"pattern_state": "DETERMINED(從殺格)"}], None)
    print(f"测1 從財+從殺: {r1['resolved_pattern']} | {r1['conflict_log']}")
    # 测2：专旺单命中
    r2 = resolve([{"pattern_state": "DETERMINED(曲直格)"}], None)
    print(f"测2 曲直: {r2['resolved_pattern']} | {r2['conflict_log']}")
    # 测3：无命中
    r3 = resolve([], None)
    print(f"测3 无命中: {r3['resolved_pattern']} | {r3['conflict_log']}")
    # 测4：化气最高优先
    r4 = resolve([{"pattern_state": "DETERMINED(從財格)"}, {"pattern_state": "DETERMINED(甲己化土)"}], None)
    print(f"测4 化气优先: {r4['resolved_pattern']} | {r4['conflict_log']}")
