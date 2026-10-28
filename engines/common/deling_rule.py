# -*- coding: utf-8 -*-
"""PATCH-141H-IMPLEMENT-B 得令/失令 PZZQ语义Rule
仅消费L0 month_supports_daymaster, 输出得令/失令语义. 不推身强/身弱."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def eval_de_ling(condition_text, facts):
    if condition_text == '得令':
        v = facts.get('month_supports_daymaster')
        if v is None:
            return {"condition": "得令", "status": "UNKNOWN", "reason": "missing_month_supports_fact"}
        return {"condition": "得令", "status": "SATISFIED" if v else "UNSATISFIED",
                "checked": "month_supports_daymaster", "value": v}
    if condition_text == '失令':
        v = facts.get('month_supports_daymaster')
        if v is None:
            return {"condition": "失令", "status": "UNKNOWN", "reason": "missing_month_supports_fact"}
        # 失令 = 非生扶/同类 (注意: 仅语义, 非身弱)
        return {"condition": "失令", "status": "SATISFIED" if not v else "UNSATISFIED",
                "checked": "month_supports_daymaster", "value": v}
    return {"condition": condition_text, "status": "UNKNOWN", "reason": "not_de_ling"}


if __name__ == '__main__':
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.path.insert(0, str(ROOT))
    from engines.common.l0_fact_builder import build
    gc = build({'year': ['癸','亥'], 'month': ['壬','戌'], 'day': ['乙','未'], 'hour': ['壬','午']})
    yi = build({'year': ['甲','子'], 'month': ['甲','寅'], 'day': ['乙','卯'], 'hour': ['丁','亥']})
    for c in ['得令','失令']:
        print('GC01(乙戌)', c, '->', json.dumps(eval_de_ling(c, gc), ensure_ascii=False))
        print('乙寅', c, '->', json.dumps(eval_de_ling(c, yi), ensure_ascii=False))
