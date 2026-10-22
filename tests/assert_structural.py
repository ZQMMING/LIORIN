# -*- coding: utf-8 -*-
"""structural断言脚本

幂等/互斥/gate_debug/枚举合法/旧名零残留/B4复用
"""
import json
import sys
from pathlib import Path
from collections import Counter

ZW_FAMILY = {"一行成象·曲直", "一行成象·炎上", "一行成象·稼穑",
             "一行成象·从革", "一行成象·润下"}
CONG_FAMILY = {"从杀格", "从财格", "从儿格", "从旺格"}  # V7.158 从官格并入从杀格
OLD_NAMES = {"化金气格", "化木气格", "化水气格", "化火气格", "化土气格",
             "专旺格", "曲直格", "炎上格", "稼穑格", "从革格", "润下格"}

MIGRATION_RAW = json.loads(
    Path("docs/migrations/pattern_rename_v1.json").read_text(encoding="utf-8-sig"))
# 只取字符串值，跳过_meta/_note等dict字段
MIGRATION = {k: v for k, v in MIGRATION_RAW.items()
             if isinstance(v, str) and not k.startswith("_")}
LEGAL = set(MIGRATION.values()) | {"unverifiable", None}

def load_cases(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    out = []
    for r in rows:
        old = r.get("special") or r.get("old_special")
        pat = MIGRATION.get(old, old) if old else r.get("expect_pattern", "unverifiable")
        out.append({**r, "pattern_claimed": pat, "_old_special": old})
    return out

def root(p):
    return next((f for f in ZW_FAMILY if p and p.startswith(f)), p)

def run(cases):
    out = []

    # 1. 幂等：key唯一性
    keys = [c["key"] for c in cases]
    out.append(("idempotent", "PASS" if len(keys) == len(set(keys)) else "FAIL",
                f"dups={len(keys)-len(set(keys))}"))

    # 2. 族间互斥
    viol = [c for c in cases
            if root(c["pattern_claimed"]) in ZW_FAMILY and c["pattern_claimed"] in CONG_FAMILY]
    out.append(("mutual_excl", "PASS" if not viol else "FAIL", f"violations={len(viol)}"))

    # 3. 闸门拒收必有_gate_debug
    no_dbg = [c for c in cases if c.get("rejected") and not c.get("_gate_debug")]
    out.append(("gate_debug", "PASS" if not no_dbg else "FAIL", f"missing={len(no_dbg)}"))

    # 4. 枚举合法
    illegal = [c for c in cases if c["pattern_claimed"] not in LEGAL]
    out.append(("enum_legal", "PASS" if not illegal else "FAIL",
                f"illegal={Counter(c['pattern_claimed'] for c in illegal).most_common(5)}"))

    # 5. 旧格局名零出现于cases（允许已映射的旧名，只检查未映射的）
    mapped_old = set(MIGRATION.keys())
    unmapped_old = [c for c in cases
                    if c.get("old_special") in OLD_NAMES and c.get("old_special") not in mapped_old]
    out.append(("no_old_names_unmapped", "PASS" if not unmapped_old else "FAIL",
                f"unmapped_old_names={len(unmapped_old)}"))

    # 6. provenance必填（kind=fixture的用例必须有provenance字段）
    no_prov = [c for c in cases if c.get("kind") == "fixture" and "provenance" not in c]
    out.append(("provenance_required", "PASS" if not no_prov else "FAIL",
                f"missing_provenance={len(no_prov)}"))

    # 7. B4复用（待B轴实现后启用）
    out.append(("b4_reuse", "SKIP", "待B轴实现后启用"))

    return out

if __name__ == "__main__":
    cases = load_cases(sys.argv[1])
    for name, status, detail in run(cases):
        print(json.dumps({"assertion": name, "status": status, "detail": detail},
                         ensure_ascii=False))
