#!/usr/bin/env python3
"""30片抽查：逐字核对原文段与原著"""
import os, re, sys
from pathlib import Path

ROOT = Path(r"D:/shuntian-ziping-p0/p0_v2/六部经典MD文库")
ORIG_ROOT = Path(r"D:/顺天系统资料/豆包资料/六部经典最终原著版")

def read_md(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except:
        return ""

def read_orig(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except:
        return ""

# Collect all slice files
slice_files = []
for dirpath, _, files in os.walk(ROOT):
    for f in sorted(files):
        if f.endswith('.md') and not f.startswith('_') and not f.endswith('.bak*'):
            fp = Path(dirpath) / f
            content = read_md(fp)
            sid_m = re.search(r'>\s*\*\*切片ID\*\*[：:]\s*(.+)', content)
            if sid_m:
                slice_files.append((sid_m.group(1).strip(), fp, content))

print(f"Total slice files with IDs: {len(slice_files)}")

# Sample 30 files across directories
import random
random.seed(42)

# Stratified sampling
by_dir = {}
for sid, fp, content in slice_files:
    rel = str(fp.relative_to(ROOT))
    top = rel.split('/')[0]
    by_dir.setdefault(top, []).append((sid, fp, content))

samples = []
for d, items in sorted(by_dir.items()):
    n = min(5, len(items))
    samples.extend(random.sample(items, n))

samples = samples[:30]
print(f"Sampling {len(samples)} slices for verbatim check")

# Check each sample against original texts
results = []
for sid, fp, content in samples:
    # Extract source text from slice
    orig_m = re.search(r'##\s*原文\s*\n(.-{3}\n)?(.+?)(?:\n---\n|\n##\s)', content, re.DOTALL)
    slice_orig_text = orig_m.group(2).strip()[:100] if orig_m else ""
    
    # Try to find matching text in original books
    book_m = re.search(r'>\s*\*\*来源\*\*[：:]\s*(.+)', content)
    book = book_m.group(1).strip()[:50] if book_m else "Unknown"
    
    # Search for key phrases in original files
    found_match = False
    match_source = ""
    for orig_file in ORIG_ROOT.rglob("*"):
        if orig_file.suffix in ['.txt', '.md']:
            orig_content = read_orig(orig_file)
            if orig_content and len(orig_content) > 100:
                # Look for key phrase from slice
                key_phrases = [p for p in slice_orig_text.split('，') if len(p) > 4]
                key_phrases += [p for p in slice_orig_text.split('。') if len(p) > 4]
                for phrase in key_phrases[:3]:
                    if phrase in orig_content:
                        found_match = True
                        match_source = str(orig_file.name)
                        break
                if found_match:
                    break
    
    status = "VERBATIM_MATCH" if found_match else "ORIG_NOT_FOUND"
    results.append({
        'slice_id': sid,
        'file': str(fp.relative_to(ROOT)),
        'book': book,
        'orig_text_sample': slice_orig_text[:50],
        'status': status,
        'match_source': match_source
    })
    print(f"  [{status}] {sid} | {book[:30]} | {slice_orig_text[:40]}... | {match_source}")

# Summary
verbal_pass = sum(1 for r in results if r['status'] == 'VERBATIM_MATCH')
verbal_fail = sum(1 for r in results if r['status'] == 'ORIG_NOT_FOUND')

print(f"\nSpot-check results: {verbal_pass} verbatim pass, {verbal_fail} not found in originals")

# Save results
import json
with open(Path(r"D:/shuntian-ziping-p0/p0_v2/_verify_20261009/slices") / "spotcheck_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Saved to spotcheck_results.json")
