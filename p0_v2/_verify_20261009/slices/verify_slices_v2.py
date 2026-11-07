#!/usr/bin/env python3
"""六部经典切片库核对验证脚本 v2.0
切片文件格式：无YAML frontmatter，使用 > **切片ID**：XXX 格式
"""
import os, re, sys, json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:/shuntian-ziping-p0/p0_v2/六部经典MD文库")
ENG_DIR = Path(r"D:/shuntian-ziping-p0/engines/common")
VERIFY_DIR = Path(r"D:/shuntian-ziping-p0/p0_v2/_verify_20261009")
VERIFY_SLICES = VERIFY_DIR / "slices"
ORIG_ROOT = Path(r"D:/顺天系统资料/豆包资料/六部经典最终原著版")

VERIFY_DIR.mkdir(parents=True, exist_ok=True)
VERIFY_SLICES.mkdir(parents=True, exist_ok=True)

def read_md(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except:
        return ""

def extract_slice_id(content):
    """Extract slice_id from > **切片ID**：XXX format"""
    m = re.search(r'>\s*\*\*切片ID\*\*[：:]\s*([A-Za-z][A-Za-z0-9._-]*)', content)
    if m:
        return m.group(1)
    # Fallback: look for slice_id anywhere
    m = re.search(r'slice_id[\"\':\s]+([A-Za-z][A-Za-z0-9._-]*)', content)
    return m.group(1) if m else None

def extract_authority(content):
    """Extract authority from > **准神归属**：准/旁参/被否决 format"""
    m = re.search(r'>\s*\*\*准神归属\*\*[：:]\s*(.+)', content)
    if m:
        val = m.group(1).strip()
        if '准' in val:
            return 'primary'
        elif '旁参' in val:
            return 'support'
        elif '否决' in val:
            return 'vetoed'
    # Fallback: look for authority
    m = re.search(r'(?:authority|准神归属)[\"\':\s]*(primary|support|vetoed|准|旁参|被否决)', content, re.IGNORECASE)
    return m.group(1) if m else None

def extract_source_text(content):
    """Extract source text from ## 原文 section"""
    m = re.search(r'##\s*原文\s*\n(.-{3}\n)?(.+?)(?:\n---\n|\n##\s)', content, re.DOTALL)
    if m:
        return m.group(2).strip()[:200]  # First 200 chars
    return ""

def extract_fields(content):
    """Extract all relevant fields from slice content"""
    fields = {}
    patterns = {
        'slice_id': r'>\s*\*\*切片ID\*\*[：:]\s*(.+)',
        'book': r'>\s*\*\*来源\*\*[：:]\s*(.+)',
        'authority': r'>\s*\*\*准神归属\*\*[：:]\s*(.+)',
        'version': r'>\s*\*\*版本\*\*[：:]\s*(.+)',
        'location': r'>\s*\*\*页码/行号\*\*[：:]\s*(.+)',
        'category': r'>\s*\*\*G1-A Category\*\*[：:]\s*(.+)',
        'type': r'>\s*\*\*切片类型\*\*[：:]\s*(.+)',
        'scope': r'>\s*\*\*适用范围\*\*[：:]\s*(.+)',
        'status': r'>\s*\*\*校验状态\*\*[：:]\s*(.+)',
    }
    for key, pat in patterns.items():
        m = re.search(pat, content)
        if m:
            fields[key] = m.group(1).strip()
    # Also try broader match for source
    m = re.search(r'来源[：:]\s*(.+)', content)
    if m and 'book' not in fields:
        fields['book'] = m.group(1).strip()
    return fields

# ============================================================
# 1. 切片ID唯一性 + 目录统计
# ============================================================
print("=== 1. 切片ID唯一性 + 目录统计 ===")
all_slices = []  # (slice_id, filepath, content, fields)
dup_ids = defaultdict(list)

for dirpath, _, files in os.walk(ROOT):
    for f in sorted(files):
        if f.endswith('.md') and not f.startswith('_') and not f.endswith('.bak*'):
            fp = Path(dirpath) / f
            content = read_md(fp)
            sid = extract_slice_id(content)
            if sid:
                fields = extract_fields(content)
                all_slices.append((sid, fp, content, fields))
                dup_ids[sid].append(fp)

total_slices = len(all_slices)
unique_ids = len(set(s[0] for s in all_slices))
dup_list = {k: v for k, v in dup_ids.items() if len(v) > 1}

print(f"Total slices with IDs: {total_slices}")
print(f"Unique IDs: {unique_ids}")
print(f"Duplicate IDs: {len(dup_list)}")
for k, vs in list(dup_list.items())[:10]:
    print(f"  DUP: {k} in {len(vs)} files")
    for v in vs[:2]: print(f"    {v}")

# Per-directory counts
dir_counts = defaultdict(int)
dir_prefixes = defaultdict(set)
for sid, fp, _, _ in all_slices:
    rel = str(fp.relative_to(ROOT))
    top_dir = rel.split('/')[0]
    dir_counts[top_dir] += 1
    prefix = '.'.join(sid.split('.')[:2])
    dir_prefixes[top_dir].add(prefix)

print("\nPer-directory:")
for d in sorted(dir_counts):
    prefixes = dir_prefixes[d]
    print(f"  {d}: {dir_counts[d]} slices, prefixes: {sorted(prefixes)}")

# ============================================================
# 2. Frontmatter必备字段完整率
# ============================================================
print("\n=== 2. 字段完整率 ===")
required_fields = ['slice_id', 'book', 'authority', 'source_text']
field_counts = {f: 0 for f in required_fields}
field_counts['total'] = total_slices
field_counts['has_frontmatter'] = 0

for sid, fp, content, fields in all_slices:
    has_fm = any(k in fields for k in ['slice_id', 'book', 'authority'])
    if has_fm:
        field_counts['has_frontmatter'] += 1
    if fields.get('slice_id'):
        field_counts['slice_id'] += 1
    if fields.get('book'):
        field_counts['book'] += 1
    if fields.get('authority'):
        field_counts['authority'] += 1
    if fields.get('source_text') or extract_source_text(content):
        field_counts['source_text'] += 1

print(f"Total slices: {field_counts['total']}")
print(f"With identifier fields: {field_counts['has_frontmatter']}")
for f in required_fields:
    rate = field_counts[f] / max(field_counts['total'], 1) * 100
    print(f"  {f}: {field_counts[f]}/{field_counts['total']} ({rate:.1f}%)")

# Authority distribution
auth_dist = defaultdict(int)
for sid, fp, content, fields in all_slices:
    auth = fields.get('authority') or extract_authority(content)
    if auth:
        auth_dist[auth] += 1
print(f"\nAuthority distribution:")
for a, c in sorted(auth_dist.items(), key=lambda x: -x[1]):
    print(f"  {a}: {c}")

# ============================================================
# 3. 引擎引用提取 + 文库缺失对照
# ============================================================
print("\n=== 3. 引擎引用提取 ===")
engine_refs = set()
ref_files = []

for pydir in [ENG_DIR, Path(r"D:/shuntian-ziping-p0/p0_v2")]:
    if not pydir.exists():
        continue
    for dirpath, _, files in os.walk(pydir):
        for fn in files:
            if fn.endswith('.py'):
                fpath = Path(dirpath) / fn
                try:
                    content = open(fpath, encoding='utf-8', errors='replace').read()
                except:
                    continue
                # Match various reference patterns
                for pattern in [
                    r'\b(SFTK-\d{3}-\d{3})\b',
                    r'\b(PZZQ-\d{3}-\d{3})\b',
                    r'\b(DTS-\d{3}-\d{3})\b',
                    r'\b(YHZP-\d{3}-\d{3})\b',
                    r'\b(QTBJ-\d{3}-\d{3})\b',
                    r'\b(SMTH-\d{3}-\d{3})\b',
                    r'\b([A-Z]{2,10}\.[A-Z_]+\.[A-Z_]+\.\d+)\b',
                ]:
                    for m in re.finditer(pattern, content):
                        engine_refs.add(m.group(1))
                        ref_files.append((m.group(1), str(fpath.relative_to(pydir))))

print(f"Total unique engine refs: {len(engine_refs)}")

# Classify refs
by_type = defaultdict(list)
for r in sorted(engine_refs):
    if r.startswith('SFTK-'):
        by_type['SFTK-numbered'].append(r)
    elif r.startswith('PZZQ-'):
        by_type['PZZQ-numbered'].append(r)
    elif r.startswith('DTS-'):
        by_type['DTS-numbered'].append(r)
    elif r.startswith('YHZP-'):
        by_type['YHZP-numbered'].append(r)
    elif r.startswith('QTBJ-'):
        by_type['QTBJ-numbered'].append(r)
    elif r.startswith('SMTH-'):
        by_type['SMTH-numbered'].append(r)
    elif '.' in r:
        by_type['structured'].append(r)
    else:
        by_type['other'].append(r)

for t, refs in by_type.items():
    print(f"  {t}: {len(refs)} refs")

# Check which engine refs exist in library
slice_id_set = set(s[0] for s in all_slices)
missing_refs = []
for ref in sorted(engine_refs):
    if ref not in slice_id_set:
        # Try partial match for numbered format (e.g., SFTK-008-001 might be stored differently)
        found = False
        ref_base = ref.split('-')[0]
        for sid in slice_id_set:
            if ref_base in sid:
                found = True
                break
        if not found:
            missing_refs.append(ref)

print(f"\nEngine refs NOT found in library: {len(missing_refs)}")
for m in missing_refs[:30]:
    print(f"  MISSING: {m}")

# Key probes
sftk_008_in_lib = any('SFTK-008-001' in sid or 'SFTK-008' in sid for sid in slice_id_set)
print(f"\nSFTK-008-001 in library: {sftk_008_in_lib}")
print(f"SFTK-008 related IDs: {[sid for sid in slice_id_set if 'SFTK-008' in sid]}")

qi_hou_refs = [r for r in engine_refs if 'QI_HOU' in r]
qi_hou_008_in_lib = 'PATHOLOGY.QI_HOU.008' in slice_id_set
print(f"PATHOLOGY.QI_HOU refs in engine: {qi_hou_refs}")
print(f"PATHOLOGY.QI_HOU.008 in library: {qi_hou_008_in_lib}")

# ============================================================
# 4. 04和06目录枚举
# ============================================================
print("\n=== 4. 04_岁运人事 和 06_赋论 枚举 ===")
dir_04_slices = [(sid, fp) for sid, fp, _, _ in all_slices 
                 if any(p in str(fp) for p in ['04_岁运人事', '04_'])]
dir_06_slices = [(sid, fp) for sid, fp, _, _ in all_slices 
                 if any(p in str(fp) for p in ['06_赋论', '06_'])]

print(f"04_岁运人事: {len(dir_04_slices)} slices")
print(f"  Prefixes: {sorted(set('.'.join(sid.split('.')[:2]) for sid, _ in dir_04_slices))}")

print(f"06_赋论: {len(dir_06_slices)} slices")
print(f"  Prefixes: {sorted(set('.'.join(sid.split('.')[:2]) for sid, _ in dir_06_slices))}")

# ============================================================
# 5. 保存中间结果
# ============================================================
result = {
    "total_slices": total_slices,
    "unique_ids": unique_ids,
    "duplicate_count": len(dup_list),
    "dir_counts": dict(dir_counts),
    "dir_prefixes": {k: sorted(v) for k, v in dir_prefixes.items()},
    "field_counts": field_counts,
    "authority_distribution": dict(auth_dist),
    "engine_refs_count": len(engine_refs),
    "engine_refs_by_type": {t: len(refs) for t, refs in by_type.items()},
    "missing_refs_count": len(missing_refs),
    "missing_refs_sample": missing_refs[:50],
    "sftk_008_in_library": sftk_008_in_lib,
    "qi_hou_008_in_library": qi_hou_008_in_lib,
}
with open(VERIFY_SLICES / "verification_data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\n=== Verification data saved ===")
print(f"Output: {VERIFY_SLICES / 'verification_data.json'}")
