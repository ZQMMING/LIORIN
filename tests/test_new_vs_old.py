# -*- coding: utf-8 -*-
# 冻结/已删除代码引用：zhonghe_structure/unified_overview已删除，本文件不再跑
"""L1规格断言：新层输出 vs cases期望值

用法：python -m tests.test_new_vs_old [--out report.jsonl]
"""
import json, sys, argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

# P0 已删除：unified_overview 模块已移除, 本 golden 冻结不再跑 (2026-09-29 接手核对)
try:
    from engines.common.unified_overview import build_unified_overview
except ModuleNotFoundError:
    print('SKIP test_new_vs_old: engines.common.unified_overview 已被 P0 删除, 本 golden 冻结')
    sys.exit(0)

from engines.axis_xiuqi   import xiuqi_axis
from engines.axis_fude    import fude_axis
from engines.special_merge import merge

CASES= json.load(Path("tests/cases_l1_v1.json").open(encoding="utf-8-sig"))

# 白名单已于 2026-09-22 随 oracle 切换清零；原 6 条见 docs/l2_divergences.md
EXPECTED_MISMATCH = {}

def parse_key(key):
    """'癸亥乙卯乙未壬午' -> {'year':('癸','亥'), ...}"""
    gans = key[0::2]
    zhis = key[1::2]
    keys = ["year", "month", "day", "hour"]
    return {k: (gans[i], zhis[i]) for i, k in enumerate(keys)}

def build_facts(pillars):
    """从build_unified_overview提取facts"""
    result = build_unified_overview(pillars)
    facts = {
        "month_branch": pillars["month"][1],
        "combination_facts": result.get("daymaster_power_network", {}).get("facts", {}).get("combination_facts", {}),
    }
    return facts, result

# ---------- 新层归一化 ----------
def norm_new(out):
    """新层merge返回元组(pattern_claimed, pattern_type, confidence, score)"""
    claimed, ptype, conf, score = out
    claimed = claimed or "无"
    ptype = ptype or "无"
    conf = conf or "REJECT"
    return {"pattern_claimed": claimed, "pattern_type": ptype, "confidence": conf, "score": score}

def run_new(pillars, facts, gate_debug):
    x = xiuqi_axis(pillars, facts, gate_debug)
    f = fude_axis(pillars, facts, gate_debug)
    return merge(x, f, "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="tests/new_vs_spec.jsonl")
    args = ap.parse_args()

    rows, summary = [], defaultdict(int)
    for c in CASES:
        try:
            pillars = parse_key(c["key"])
            facts, raw_old = build_facts(pillars)
            gate_debug = raw_old.get("special_pattern", {}).get("_gate_debug", [])
            got = norm_new(run_new(pillars, facts, gate_debug))
        except Exception as e:
            rows.append({"id": c["id"], "key": c["key"], "status": "ERROR", "msg": str(e)})
            summary["ERROR"] += 1
            continue

        expect = {
            "pattern_claimed": c.get("expect_pattern") or "无",
            "pattern_type": c.get("expect_type") or "无",
            "confidence": c.get("expect_confidence") or "REJECT",
        }

        diffs = [f"{k}: expect={expect[k]!r} got={got[k]!r}" for k in expect if got[k] != expect[k]]
        in_wl = c["id"] in EXPECTED_MISMATCH
        status = "MATCH" if not diffs else ("WL_EXPECTED" if in_wl else "UNEXPECTED")
        summary[status] += 1

        row = {"id": c["id"], "key": c["key"], "status": status,
               "expect": expect,
               "got": {k: got[k] for k in ("pattern_claimed","pattern_type","confidence")},
               "diffs": diffs}
        rows.append(row)
        print(f"{c['id']:8s} {status:12s} expect={expect['pattern_claimed']}/{expect['confidence']:<9s} "
              f"got={got['pattern_claimed']}/{got['confidence']:<9s}" + (f" | {'; '.join(diffs)}" if diffs else ""))

    Path(args.out).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    print(f"\n汇总: {dict(summary)}  产物: {args.out}")

    unexpected = [r for r in rows if r["status"]=="UNEXPECTED"]
    if unexpected:
        print(f"意外差异（需登记 divergence）:")
        for r in unexpected: print(f"  {r['id']}: {r['diffs']}")

    sys.exit(0 if not unexpected else 1)

if __name__ == "__main__":
    main()
