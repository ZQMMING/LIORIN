# -*- coding: utf-8 -*-
"""判据锚点闸门: 引擎每条原典判据必须能锚到切片(AGENTS.md v3 公理三落地).
规则:
  ① 引擎源码中出现的 (书, 行号) 引用点, 必须全部能锚到该书切片(不得 NONE);
  ② 引用点的原典章节必须与切片 chapter 对得上(EXACT_CHAPTER 或至少 CHAPTER);
  ③ 锚点对照表产物须存在且条数与源码引用点一致(防表过期).
失败即红 —— 新增判据若忘记登记原典出处, 本闸门即报.
"""
import os, re, json, glob, sys, collections

ROOT = r"D:\shuntian-ziping-p0"
BOOK_DIR = {'PZZQ': 'PZZQ', 'DTS': 'DTS_LB', 'QTBJ': 'QTBJ', 'SFTK': 'SFTK',
            'SMTH': 'SMTH', 'YHZP': 'YHZP'}
FAILS = []
OKS = []


def ck(name, ok, extra=""):
    (OKS if ok else FAILS).append(name)
    print(("PASS " if ok else "FAIL ") + name + (("  " + str(extra)) if (extra and not ok) else ""))


# 1) 收集引擎引用点
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

# 2) 切片库存在性
slice_ids = set()
per_book = collections.Counter()
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
            if isinstance(it, dict) and it.get('slice_id'):
                slice_ids.add(it['slice_id'])
                per_book[d] += 1

print("=" * 74)
print("判据锚点闸门 (AGENTS.md v3 公理三)")
print("=" * 74)
print("引擎原典引用点: %d 组 / %d 次" % (len(eng), sum(len(v) for v in eng.values())))
print("切片库: %s (合计 %d)" % (dict(per_book), sum(per_book.values())))

# 3) 锚点对照表产物
ap = os.path.join(ROOT, "p0_v2", "output", "ENGINE_CRITERIA_ANCHORS.json")
ck("锚点对照表产物存在", os.path.exists(ap), ap)
if os.path.exists(ap):
    A = json.load(open(ap, encoding='utf-8'))
    ck("锚点表条数 == 源码引用点数(防表过期)",
       A.get('total_anchor_groups') == len(eng),
       "%s vs %s" % (A.get('total_anchor_groups'), len(eng)))
    ck("锚点表无 NONE(每组皆可锚到切片)",
       all(a.get('slice_match') != 'NONE' for a in A.get('anchors', [])),
       [a for a in A.get('anchors', []) if a.get('slice_match') == 'NONE'][:3])
    ex = [a for a in A.get('anchors', []) if a.get('slice_match') == 'EXACT_CHAPTER']
    ck("存在精确章节锚定(DTS L250 通关等核心判据)", len(ex) >= 20, len(ex))
    # 核心判据抽样核对
    byk = {(a['book'], a['row']): a for a in A.get('anchors', [])}
    for (bk, rw), want_in in ((('DTS', 250), 'DTS_LB.上篇.20_二十、通关'),
                              (('DTS', 235), 'DTS_LB.上篇.17_十七、衰旺'),
                              (('DTS', 245), 'DTS_LB.上篇.19_十九、源流')):
        a = byk.get((bk, rw))
        ck("核心判据 %s L%d 锚到 %s" % (bk, rw, want_in),
           bool(a) and any(want_in in sid for sid in a.get('slice_ids', [])),
           (a or {}).get('slice_ids', [])[:3])

# 4) 引擎引用的书必须在切片库中有条目
for (bk, rw), locs in eng.items():
    d = BOOK_DIR.get(bk, bk)
    ck("引用书 %s 有切片条目(L%d, %d处)" % (bk, rw, len(locs)), per_book.get(d, 0) > 0,
       per_book.get(d, 0))

print()
print("=" * 74)
print("结果: PASS=%d FAIL=%d" % (len(OKS), len(FAILS)))
if FAILS:
    for f in FAILS:
        print("  -", f)
print("=" * 74)
sys.exit(1 if FAILS else 0)
