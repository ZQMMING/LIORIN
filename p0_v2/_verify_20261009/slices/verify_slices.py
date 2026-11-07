#!/usr/bin/env python3
"""六部经典切片库核对验证脚本 v1.0"""
import os, re, sys, json
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:/shuntian-ziping-p0/p0_v2/六部经典MD文库")
ENG_DIR = Path(r"D:/shuntian-ziping-p0/engines/common")
OUT_DIR = Path(r"D:/shuntian-ziping-p0/p0_v2/output")
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

def extract_frontmatter(content):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip().strip('"\'')
    return fm

def get_slice_id(content):
    m = re.search(r'slice_id[\"\':\s]+([A-Za-z][A-Za-z0-9._-]*)', content)
    return m.group(1) if m else None

def get_source_location(content, filepath):
    rel = str(filepath.relative_to(ROOT))
    m = re.search(r'source(?:_location|_file)[\"\':\s]+([^\"\n]+)', content)
    loc = m.group(1).strip() if m else None
    return loc, rel

# ============================================================
# 1. 切片ID唯一性 + 目录统计
# ============================================================
print("=== 1. 切片ID唯一性 + 目录统计 ===")
all_slices = []  # (slice_id, filepath, fm)
dup_ids = defaultdict(list)

for dirpath, _, files in os.walk(ROOT):
    for f in sorted(files):
        if f.endswith('.md') and not f.startswith('_'):
            fp = Path(dirpath) / f
            content = read_md(fp)
            sid = get_slice_id(content)
            if sid:
                all_slices.append((sid, fp, content))
                dup_ids[sid].append(fp)

total_slices = len(all_slices)
unique_ids = len(set(s[0] for s in all_slices))
dup_list = {k: v for k, v in dup_ids.items() if len(v) > 1}

print(f"Total slices with IDs: {total_slices}")
print(f"Unique IDs: {unique_ids}")
print(f"Duplicate IDs: {len(dup_list)}")
for k, vs in list(dup_list.items())[:10]:
    print(f"  DUP: {k} in {len(vs)} files")

# Per-directory counts
dir_counts = defaultdict(int)
dir_prefixes = defaultdict(set)
for sid, fp, _ in all_slices:
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
print("\n=== 2. Frontmatter必备字段完整率 ===")
required_fields = ['slice_id', 'book', 'authority', 'source_text']
field_counts = {f: 0 for f in required_fields}
field_counts['total'] = total_slices
field_counts['no_frontmatter'] = 0

for sid, fp, content in all_slices:
    fm = extract_frontmatter(content)
    if not fm:
        field_counts['no_frontmatter'] += 1
        continue
    for f in required_fields:
        if f in fm and fm[f]:
            field_counts[f] += 1

print(f"Total slices: {field_counts['total']}")
print(f"No YAML frontmatter: {field_counts['no_frontmatter']}")
for f in required_fields:
    rate = field_counts[f] / max(field_counts['total'], 1) * 100
    print(f"  {f}: {field_counts[f]}/{field_counts['total']} ({rate:.1f}%)")

# Authority distribution
auth_dist = defaultdict(int)
for sid, fp, content in all_slices:
    fm = extract_frontmatter(content)
    if fm and 'authority' in fm:
        auth_dist[fm['authority']] += 1
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
                content = read_md(fpath) if False else open(fpath, encoding='utf-8', errors='replace').read()
                # Match SFTK-XXX-XXX, PZZQ-XXX, DTS-XXX, STRUCTURE.XXX, PATHOLOGY.XXX, STATE.XXX
                for pattern in [
                    r'\b(SFTK-\d{3}-\d{3})\b',
                    r'\b(PZZQ-\d{3}-\d{3})\b',
                    r'\b(DTS-\d{3}-\d{3})\b',
                    r'\b(YHZP-\d{3}-\d{3})\b',
                    r'\b(QTBJ-\d{3}-\d{3})\b',
                    r'\b(SMTH-\d{3}-\d{3})\b',
                    r'\b([A-Z]{2,10}\.[A-Z_]+\.+[A-Z_]+\.\d+)\b',
                ]:
                    for m in re.finditer(pattern, content):
                        engine_refs.add(m.group(1))
                        ref_files.append((m.group(1), str(fpath.relative_to(pydir))))

print(f"Total unique engine refs: {len(engine_refs)}")
# Print refs by type
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
    elif '.' in r:
        by_type['structured'].append(r)
    else:
        by_type['other'].append(r)

for t, refs in by_type.items():
    print(f"  {t}: {len(refs)} refs")
    for r in refs[:5]:
        print(f"    - {r}")
    if len(refs) > 5:
        print(f"    ... and {len(refs)-5} more")

# Check which engine refs exist in library
slice_id_set = set(s[0] for s in all_slices)
missing_refs = []
for ref in sorted(engine_refs):
    if ref not in slice_id_set:
        # Try partial match for numbered format
        found = False
        for sid in slice_id_set:
            if ref.split('-')[0] in sid or sid in ref:
                found = True
                break
        if not found:
            missing_refs.append(ref)

print(f"\nEngine refs NOT found in library: {len(missing_refs)}")
for m in missing_refs[:30]:
    print(f"  MISSING: {m}")

# Check SFTK-008-001 specifically
sftk_008 = [r for r in engine_refs if 'SFTK-008' in r]
print(f"\nSFTK-008 refs in engine: {sftk_008}")
print(f"SFTK-008-001 in library: {'SFTK-008-001' in slice_id_set}")

# Check PATHOLOGY.QI_HOU.008
qi_hou_008 = [r for r in engine_refs if 'QI_HOU' in r]
print(f"\nPATHOLOGY.QI_HOU refs in engine: {qi_hou_008}")
print(f"PATHOLOGY.QI_HOU.008 in library: {'PATHOLOGY.QI_HOU.008' in slice_id_set}")

# ============================================================
# 4. 保存中间结果
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
    "engine_refs_sample": sorted(list(engine_refs))[:100],
    "missing_refs": missing_refs[:50],
    "sftk_008_in_library": "SFTK-008-001" in slice_id_set,
    "qi_hou_008_in_library": "PATHOLOGY.QI_HOU.008" in slice_id_set,
}
with open(VERIFY_SLICES / "verification_data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("\n=== Verification data saved ===")
print(f"Output: {VERIFY_SLICES / 'verification_data.json'}")
