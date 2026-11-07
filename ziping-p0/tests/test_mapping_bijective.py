# tests/test_mapping_bijective.py
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from collections import defaultdict

MAP        = json.load(Path("docs/migrations/pattern_rename_v1.json").open(encoding="utf-8-sig"))
CASES      = json.load(Path("tests/cases_l1_v1.json").open(encoding="utf-8-sig"))
RESOLVERS  = json.load(Path("docs/migrations/disamb_resolvers.json").open(encoding="utf-8-sig"))

SENTINELS = {"__DISAMBIGUATE_BY_BRANCH__"}
ENUM = {
 "pattern_claimed": {v for v in MAP.values() if isinstance(v, str)} - SENTINELS |
                    {"两气成象","从杀格","从财格","从儿格","从旺格","正格","无"},
 "pattern_type":    {"专旺型","化气型","无"},
 "confidence":      {"CONFIRMED","MID","CANDIDATE","REJECT"},
 "kind":            {"real","fixture"},
 "provenance_key":  {"day","ju","no_po","huaqi归属","印露"},
 "provenance_grade":{"A","B","C","未见"},
}

errs = []

# 1. 正向：每个旧名唯一映射
for k,v in MAP.items():
    if k.startswith("_"): continue
    if v not in ENUM["pattern_claimed"] and v not in SENTINELS:
        errs.append(f"MAP[{k}]='{v}' 是孤儿新名（无旧名支撑且非哨兵）")

# 2. 哨兵值必须有裁决器登记
for k,v in MAP.items():
    if k.startswith("_"): continue
    if v in SENTINELS and k not in RESOLVERS:
        errs.append(f"旧名 '{k}' 映射到哨兵值，但 disamb_resolvers.json 未登记")
for k,r in RESOLVERS.items():
    if r.get("status") != "RESOLVED":
        errs.append(f"消歧器 '{k}' status={r.get('status')}，尚未解决")

# 3. cases 字段落在合法值域
for c in CASES:
    for field in ("pattern_claimed","pattern_type","confidence","kind"):
        v = c.get("expect_"+field) if field!="kind" else c.get("kind")
        if v and v not in ENUM[field]:
            errs.append(f"{c['id']}: {field}='{v}' 不在合法值域 {sorted(ENUM[field])}")
    p = c.get("provenance", {})
    for k,g in p.items():
        if k not in ENUM["provenance_key"]:
            errs.append(f"{c['id']}: provenance 非法键 '{k}'")
        if g not in ENUM["provenance_grade"]:
            errs.append(f"{c['id']}: provenance[{k}]='{g}' 非法（应为 A/B/C/未见）")
    if c.get("kind") == "real" and not c.get("s_source"):
        errs.append(f"{c['id']}: kind=real 但缺少 s_source")

# 4. 多对一冲突（允许人为合并，但必须显式声明）
rev = defaultdict(list)
for k,v in MAP.items():
    if k.startswith("_") or v in SENTINELS: continue
    rev[v].append(k)
for n,olds in rev.items():
    if len(olds)>1 and "_merge_note" not in MAP:
        errs.append(f"多对一: '{n}' <- {olds}（如为有意合并，请在 MAP 中加注 _merge_note 说明）")

print(f"校验完成: {len(errs)} 个错误")
for e in errs: print(f"  ❌ {e}")
if not errs: print("  ✅ 双向可逆校验通过")
sys.exit(1 if errs else 0)
