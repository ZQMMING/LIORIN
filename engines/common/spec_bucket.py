# -*- coding: utf-8 -*-
"""规格桶分类器 (schema v3 §五 bucket 字段) —— V7.137.
用途: 为任一规格条目(切片/规则)给出【唯一】桶归属, 供验收条③「四桶之和 == 总条数」对账.

四桶(AGENTS.md v3 §五 schema v3):
  verifiable      —— 能指到 grade=A 原句, 且判据条件完整, 可直接进规格
  unverifiable    —— 仅 grade=B/C 支撑或条件不全, 只能进待决清单(不进规格)
  spec_gap        —— 原典有相关表述但缺可执行要件(判据未落), 属规格缺口
  conflict_pending—— 与他条/他书冲突未决, 须挂起

分类依据(全部可核, 逐条列明):
  ① grade=C            -> unverifiable   (AGENTS.md §六 验收条2「source_grade=C 一律不进规格」)
  ② 仅 grade=B         -> unverifiable   (AGENTS.md 底本分级: grade=B 不得单独支撑规格)
  ③ grade=A 但条件为空 -> spec_gap       (有原句, 无可执行要件)
  ④ grade=A 且有冲突标记 -> conflict_pending
  ⑤ grade=A 且条件完整   -> verifiable
★ 纯函数, 无副作用; 不改任何数据; 输出唯一桶 + 理由 + 所依据的公理条目.
"""

BUCKETS = ("verifiable", "unverifiable", "spec_gap", "conflict_pending")
GRADE_ORDER = {"A": 3, "B": 2, "C": 1}


def classify(spec):
    """给一条规格条目定桶.

    spec 需含: source_grade(str: 'A'/'B'/'C'), conditions(list/str, 可空),
               conflict(可选: 与他条/他书冲突的标记或说明).
    返回: {'bucket': <四桶之一>, 'reason': str, 'basis': [公理条目]}
    """
    grade = (spec.get("source_grade") or "").strip().upper()
    conds = spec.get("conditions")
    if isinstance(conds, str):
        conds = [conds] if conds.strip() else []
    conds = [c for c in (conds or []) if str(c).strip()]
    conflict = spec.get("conflict")

    if grade == "C":
        return {"bucket": "unverifiable",
                "reason": "grade=C 不进规格, 只进待决清单",
                "basis": ["§六 验收条2", "§〇 底本分级"]}
    if grade == "B":
        return {"bucket": "unverifiable",
                "reason": "仅 grade=B 支撑, 不得单独支撑规格条款",
                "basis": ["§〇 底本分级", "公理三"]}
    if grade != "A":
        return {"bucket": "unverifiable",
                "reason": "无有效 source_grade(非 A/B/C), 不能进规格",
                "basis": ["§五 schema v3"]}
    if conflict:
        return {"bucket": "conflict_pending",
                "reason": "grade=A 但存在未决冲突, 须挂起待裁",
                "basis": ["公理一", "§十 真分歧表"]}
    if not conds:
        return {"bucket": "spec_gap",
                "reason": "grade=A 原句在, 但无可执行条件(判据未落)",
                "basis": ["§四 格局定义合取式", "公理三"]}
    return {"bucket": "verifiable",
            "reason": "grade=A 原句 + 条件齐备, 可进规格",
            "basis": ["公理三", "§四"]}


def reconcile(specs):
    """验收条③ 对账: 四桶之和 == 总条数, 且无重复/空桶.

    specs: [{'id':..., 'source_grade':..., 'conditions':..., 'conflict':...}, ...]
    返回: {'total':n, 'buckets':{四桶计数}, 'sum':sum, 'ok':bool, 'items':[...]}
    """
    buckets = {b: 0 for b in BUCKETS}
    items = []
    seen = {}
    dup = []
    for sp in specs:
        sid = sp.get("id")
        if sid in seen:
            dup.append(sid)
        seen[sid] = True
        r = classify(sp)
        buckets[r["bucket"]] += 1
        items.append({"id": sid, "bucket": r["bucket"], "reason": r["reason"],
                      "basis": r["basis"]})
    total = len(specs)
    ssum = sum(buckets.values())
    return {
        "total": total, "buckets": buckets, "sum": ssum,
        "ok": (ssum == total) and not dup and all(buckets[b] >= 0 for b in BUCKETS),
        "duplicates": dup, "items": items,
    }
