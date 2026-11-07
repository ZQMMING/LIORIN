# -*- coding: utf-8 -*-
"""第二步+第三步: 案例批量跑 → 触发字段 → 映射 judge_point → 查切片索引 → 真缺口
唯一入口 tools/gate (只插 ROOT, 走 p0_v2.bazi_gate), 不双路径。"""
import sys, os, json
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

# 单实例核验 (记忆里的双路径陷阱): 关键模块在 sys.modules 只有一份
import engines.common.special_pattern as _sp
import engines.common.ge_jie_layer as _gj
from p0_v2 import bazi_gate as _bg
_same = []
for _mod, _fn in ((_sp, "build_special_patterns"), (_gj, "build_ge_cheng")):
    f2 = getattr(_mod, _fn, None)
    _same.append(f2 is getattr(_bg, _fn, None))
print("单实例核验:", "PASS" if all(_same) else "FAIL", _same)

# ── 输入 ──
m = json.load(open(f"{ROOT}/scripts/_judge_slice_map.json", encoding="utf-8"))
jp = m["judge_points"]
idx = json.load(open(f"{ROOT}/scripts/_slice_index.json", encoding="utf-8"))
lineidx = {}
for k, v in idx.get("_line_items", {}).items():
    lineidx[tuple(k.split(","))] = v
# 行号索引其实没存进 _slice_index, 这里重建: 用 slices 的 line_ranges
from collections import defaultdict
lineidx2 = defaultdict(set)
for s in idx["slices"]:
    for (a, b2) in s.get("line_ranges", []):
        for n in range(a, b2 + 1):
            lineidx2[(s["book"], n)].add(s["sid"])

# 切片概念词索引
kwidx = defaultdict(list)
for s in idx["slices"]:
    for c in s["concept_terms"]:
        kwidx[c].append(s["sid"])

# ── file → paipan 输出字段 (桥) ──
F2F = {
    "ge_jie_layer.py": ["ge_cheng", "jiu_ying"],
    "bingyao_layer.py": ["bing_yao", "bing_list", "bingyao_summary", "bing_debate", "zhuangui", "yongyao"],
    "fan_ju.py": ["wangshuai_matrix", "yongyao"],
    "special_pattern.py": ["special"],
    "topology_paths.py": ["topology", "combination_facts"],
    "transit_power.py": [],            # 岁运层, 原局 paipan 不触发
    "slice_conditions.py": [],
    "slice_loader.py": [],
    "l0_fact_builder.py": ["l0_chart", "raw_facts"],
    "wangshuai_multidim.py": ["structure", "wangshuai_matrix"],
    "wangshuai_structure.py": ["structure"],
    "daymaster_tian_he.py": ["tian_he", "root_relations"],
}

def get(d, path):
    cur = d
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur

def triggered(res, fields):
    """该引擎文件在本案是否触发: 任一映射字段非空"""
    for f in fields:
        v = get(res, f)
        if v:  # 非空
            return True, f
    return False, None

# ── 抽 20 盘 (每本 3-4 盘, 覆盖广) ──
cases = []
for book, path in [("DTS","DTS_clean"),("PZZQ","PZZQ_clean"),("QTBJ","QTBJ_clean"),
                   ("SFTK","SFTK_clean"),("SMTH","SMTH_clean"),("YHZP","YHZP_clean")]:
    lines = open(f"{ROOT}/p0_v2/case_audit/{path}.jsonl", encoding="utf-8").readlines()
    take = lines[:4] if book in ("DTS","PZZQ") else lines[:3]
    for ln in take:
        c = json.loads(ln)
        cases.append((book, c["case_id"], c["bazi"]))
print(f"\n抽样 {len(cases)} 盘: " + " ".join(f"{b}:{i}" for b,i,_ in cases[:6]) + " ...")

# ── 每盘跑 → 记录触发引擎文件集 → 映射到 judge_point → 查切片 ──
triggered_points = defaultdict(list)   # (file,origline) -> [case_ids]
field_hit = defaultdict(int)
crash = []
for book, cid, bazi in cases:
    try:
        res = paipan(bazi)
    except Exception as e:
        crash.append((cid, bazi, str(e)[:60]))
        continue
    for f, fields in F2F.items():
        trig, tf = triggered(res, fields)
        if trig:
            field_hit[f] += 1
            # 该文件的所有 judge_point
            for p in jp:
                if p["file"] == f:
                    for ol in p.get("origlines", []):
                        triggered_points[(f, ol)].append(cid)

print(f"\n═══ 20 盘跑完 | 崩溃 {len(crash)} 盘 ═══")
for c in crash[:5]: print("  CRASH", c)
print(f"\n各引擎文件被案例触发的盘数: {dict(field_hit)}")

# ── 第三步: 触发的 judge_point × 切片库查 ──
# judge_point 的真缺口 = 有 origline 但 切片库 (book,line) 未收该原典行
# 需要 (book,line): 从 origline 解析
BOOKS = ("DTS","PZZQ","QTBJ","SFTK","SMTH","YHZP")
def parse_code(tok):
    for bk in BOOKS:
        if tok.startswith(bk):
            rest = tok[len(bk):].lstrip("L")
            if rest.isdigit(): return bk, int(rest)
    return None, None

# 该 origline 在切片库 有真覆盖 (同(book,line) 命中) 或 概念词命中
def slice_covers(ol):
    bk, num = parse_code(ol)
    if not bk: return False, "no_book"
    if (bk, num) in lineidx2 and lineidx2[(bk, num)]:
        return True, f"line:{sorted(lineidx2[(bk,num)])[0]}"
    return False, "not_in_lineidx"

# 聚合: 案例触发的 (file,origline) 全集, 逐条查
gap, aligned = [], []
for (f, ol), cids in sorted(triggered_points.items()):
    cov, how = slice_covers(ol)
    rec = {"file": f, "origline": ol, "trigger_cases": cids, "n_cases": len(cids)}
    if cov:
        aligned.append({**rec, "how": how})
    else:
        gap.append({**rec, "reason": how})

print(f"\n═══ 案例触发的 judge_point 全集 = {len(triggered_points)} 个 (file,origline) ═══")
print(f"  已齐(切片库行号命中)   {len(aligned)}")
print(f"  真缺口(触发但切片没收)  {len(gap)}   ← 案例暴露的真缺口")
print(f"\n── 真缺口 {len(gap)} 条 (按触发盘数排序) ──")
for g in sorted(gap, key=lambda x: -x["n_cases"])[:25]:
    print(f"  {g['file']:<22} {g['origline']:<12} 触发{g['n_cases']}盘 {g['reason']}")

json.dump({"sampled": [ [b,c,bz] for b,c,bz in cases ],
          "field_hit": dict(field_hit), "crash": crash,
          "aligned": aligned, "gap": gap},
          open(f"{ROOT}/scripts/_案例驱动_20盘_缺口.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n存 scripts/_案例驱动_20盘_缺口.json")
