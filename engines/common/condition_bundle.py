# -*- coding: utf-8 -*-
"""PATCH-141H-C Condition Bundle 三态聚合器
required条件逐项三态 -> 聚合. 非评分/非多数决. 不判成格."""


def aggregate_required(items):
    """items: [{'condition','status'},...].
    规则: 全SATISFIED->SATISFIED; 任一UNSATISFIED->UNSATISFIED; 无UNSATISFIED但有UNKNOWN->UNKNOWN."""
    stats = {}
    for it in items:
        stats[it['status']] = stats.get(it['status'], 0) + 1
    if stats.get('UNSATISFIED', 0) > 0:
        return {'bundle_status': 'UNSATISFIED', 'reason': 'required_unsatisfied', 'stats': stats}
    if stats.get('UNKNOWN', 0) > 0:
        return {'bundle_status': 'UNKNOWN', 'reason': 'has_unknown_required', 'stats': stats}
    if stats.get('SATISFIED', 0) == len(items) and items:
        return {'bundle_status': 'SATISFIED', 'reason': 'all_required_satisfied', 'stats': stats}
    return {'bundle_status': 'UNKNOWN', 'reason': 'no_required_conditions', 'stats': stats}


def aggregate_blocked(items):
    """PATCH-146 blocked三态: 任一SATISFIED(破坏成立)->BLOCKED;
    全UNSATISFIED->CLEAR; 无SAT但有UNKNOWN->BLOCK_UNKNOWN; 空->BLOCK_UNKNOWN."""
    stats = {}
    for it in items:
        stats[it['status']] = stats.get(it['status'], 0) + 1
    if stats.get('SATISFIED', 0) > 0:
        return {'bundle_status': 'BLOCKED', 'reason': 'block_hit', 'stats': stats}
    if stats.get('UNKNOWN', 0) > 0 or not items:
        return {'bundle_status': 'BLOCK_UNKNOWN', 'reason': 'block_unknown', 'stats': stats}
    return {'bundle_status': 'CLEAR', 'reason': 'all_blocked_unsatisfied', 'stats': stats}


def synthesize(required_bundle, blocked_bundle, supported_records):
    """required x blocked -> candidate direction. supported纯记录不参与.
    不输出成格/破格布尔."""
    r = required_bundle['bundle_status']
    b = blocked_bundle['bundle_status']
    if r == 'UNSATISFIED' or b == 'BLOCKED':
        direction = 'NOT_SUPPORTED'
    elif r == 'SATISFIED' and b == 'CLEAR':
        direction = 'SUPPORTED'
    else:
        direction = 'PENDING'
    return {'candidate_direction': direction,
            'required_bundle': r, 'blocked_bundle': b,
            'supported': {'mode': 'RECORD_ONLY', 'items': supported_records}}


if __name__ == '__main__':
    import sys, io, json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    demo = [
        [{'condition':'有根','status':'SATISFIED'},{'condition':'财透','status':'SATISFIED'}],
        [{'condition':'有根','status':'SATISFIED'},{'condition':'财透','status':'UNSATISFIED'}],
        [{'condition':'有根','status':'SATISFIED'},{'condition':'财有根','status':'UNKNOWN'}],
        [],
    ]
    for items in demo:
        print(json.dumps(aggregate_required(items), ensure_ascii=False))
