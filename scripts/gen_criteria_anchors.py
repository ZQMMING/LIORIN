# -*- coding: utf-8 -*-
"""重建 引擎判据 -> 切片 锚点对照表(V7.100 后引擎新增原典引用点, 闸门须同步).
与 _p97b 同法: 引擎 (书,行号) -> 原典章节 -> 切片 chapter 匹配.
"""
import os, re, json, glob, io, collections

ROOT = r"D:\shuntian-ziping-p0"
RAW = os.path.join(ROOT, "registries", "source", "raw")
BOOK_DIR = {'PZZQ': 'PZZQ', 'DTS': 'DTS_LB', 'QTBJ': 'QTBJ', 'SFTK': 'SFTK',
            'SMTH': 'SMTH', 'YHZP': 'YHZP'}
BOOK_CN = {'PZZQ': '子平真诠', 'DTS': '滴天髓', 'QTBJ': '穷通宝鉴',
           'SFTK': '神峰通考', 'SMTH': '三命通会', 'YHZP': '渊海子平'}
RAW_FILE = {'PZZQ': 'PZZQ_子平真诠_沈孝瞻原文.md',
            'DTS': 'DTS_滴天髓_京图撰刘基原注.md',
            'QTBJ': 'QTBJ_穷通宝鉴_原文.md',
            'YHZP': 'YHZP_渊海子平_原文.md'}
RAW_ALT = {'SFTK': os.path.join(RAW, "_archive", "SFTK_神峰通考.txt"),
           'SMTH': os.path.join(RAW, "_archive", "SMTH_三命通会.txt")}


def load_lines(book):
    fn = RAW_FILE.get(book)
    p = os.path.join(RAW, fn) if fn else RAW_ALT.get(book)
    if not p or not os.path.exists(p):
        return None
    return open(p, encoding='utf-8', errors='ignore').read().split('\n')


def chapter_at(lines, row):
    if not lines or row > len(lines):
        return ''
    for i in range(min(row, len(lines)) - 1, max(-1, min(row, len(lines)) - 140), -1):
        ln = lines[i].strip()
        if ln.startswith('###') or ln.startswith('##') or ln.startswith('#'):
            return ln.lstrip('#').strip()
    return ''


def _norm(s):
    s = re.sub(r'第\s*\d+\s*章', '', s or '')
    s = re.sub(r'[\s·、,，。.:：;；()（）「」《》"\'\'’]+', '', s)
    return s


slices = collections.defaultdict(list)
for fp in glob.glob(os.path.join(ROOT, "p0_v2", "output", "*", "*_slices.jsonl")):
    d = os.path.basename(os.path.dirname(fp))
    with open(fp, encoding='utf-8', errors='ignore') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                it = json.loads(line)
            except Exception:
                continue
            if not isinstance(it, dict):
                continue
            slices[d].append({'slice_id': it.get('slice_id', ''),
                               'chapter': it.get('chapter'),
                               'loc': str(it.get('source_location') or '')})

PAT = re.compile(r'(PZZQ|DTS|QTBJ|SFTK|SMTH|YHZP)\s*L(\d+)')
eng = collections.defaultdict(list)
for fp in (glob.glob(os.path.join(ROOT, "engines", "common", "*.py"))
           + glob.glob(os.path.join(ROOT, "p0_v2", "*.py"))):
    if '.bak' in fp:
        continue
    rel = os.path.relpath(fp, ROOT)
    with open(fp, encoding='utf-8', errors='ignore') as fh:
        for i, ln in enumerate(fh, 1):
            for m in PAT.finditer(ln):
                eng[(m.group(1), int(m.group(2)))].append('%s:%d' % (rel, i))

LINES = {b: load_lines(b) for b in BOOK_DIR}
anchors = []
for (book, row), locs in sorted(eng.items(), key=lambda x: (x[0][0], x[0][1])):
    d = BOOK_DIR.get(book, book)
    chap = chapter_at(LINES.get(book), row)
    cands = slices.get(d, [])
    nc = _norm(chap)
    hit = [s for s in cands if nc and _norm(s.get('chapter')) and
           (_norm(s['chapter']) in nc or nc in _norm(s['chapter']))]
    anchors.append({
        'book': book, 'book_cn': BOOK_CN.get(book, book), 'row': row,
        'ref_count': len(locs), 'engine_refs': locs[:12],
        'source_chapter': chap,
        'slice_match': 'EXACT_CHAPTER' if hit else ('CHAPTER' if cands else 'NONE'),
        'slice_ids': [s['slice_id'] for s in (hit or cands)[:8]],
        'slice_count': len(hit or cands),
    })

out = io.open(os.path.join(ROOT, "p0_v2", "output", "ENGINE_CRITERIA_ANCHORS.json"), "w", encoding="utf-8")
json.dump({
    'purpose': 'AGENTS.md v3 公理三落地: 引擎判据 -> 原典章节 -> 切片ID 锚点对照(不改判定)',
    'total_anchor_groups': len(anchors),
    'total_refs': sum(a['ref_count'] for a in anchors),
    'match_modes': dict(collections.Counter(a['slice_match'] for a in anchors)),
    'anchors': anchors,
}, out, ensure_ascii=False, indent=1)
out.close()
print("groups=%d refs=%d modes=%s" % (
    len(anchors), sum(a['ref_count'] for a in anchors),
    dict(collections.Counter(a['slice_match'] for a in anchors))))
