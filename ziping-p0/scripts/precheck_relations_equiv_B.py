# -*- coding: utf-8 -*-
"""前置核1-B: relations 结构2(按实例枚举) + instance_count 聚合 下的派生等价性

与 precheck_relations_equiv.py(结构A) 的差别:
  A: 一实例一条 relation, positions=[[pa],[pb]], 无 instance_count
  B: 按【有序支名对】聚合为一条 relation, positions=[[pa,pb], ...每组实例一条], instance_count=N
     派生旧键时展开 count 次

聚合键必须是【有序 tuple】而非 frozenset:
  DT-0017 liuchong=[[丑,未],[未,丑]] 是两种顺序, frozenset 并成一条后展开无法还原原序。
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
if os.path.join(ROOT, "p0_v2") in sys.path:
    sys.path.remove(os.path.join(ROOT, "p0_v2"))
from p0_v2.bazi_gate import _pillars

LIUHE = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯",
         "辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
LIUCHONG = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
            "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
SANHE = [{"pair":["申","子","辰"],"name":"申子辰合水"},{"pair":["亥","卯","未"],"name":"亥卯未合木"},
         {"pair":["寅","午","戌"],"name":"寅午戌合火"},{"pair":["巳","酉","丑"],"name":"巳酉丑合金"}]
SANHUI = [{"pair":["寅","卯","辰"],"name":"寅卯辰三会木"},{"pair":["巳","午","未"],"name":"巳午未三会火"},
          {"pair":["申","酉","戌"],"name":"申酉戌三会金"},{"pair":["亥","子","丑"],"name":"亥子丑三会水"}]
BANHE_PAIRS = {frozenset(("申","子")):"水", frozenset(("亥","卯")):"木",
               frozenset(("寅","午")):"火", frozenset(("巳","酉")):"金",
               frozenset(("子","辰")):"水", frozenset(("卯","未")):"木",
               frozenset(("午","戌")):"火", frozenset(("酉","丑")):"金"}
LIUHAI = [{"pair":["子","未"],"name":"子未相害"},{"pair":["丑","午"],"name":"丑午相害"},
          {"pair":["寅","巳"],"name":"寅巳相害"},{"pair":["卯","辰"],"name":"卯辰相害"},
          {"pair":["申","亥"],"name":"申亥相害"},{"pair":["酉","戌"],"name":"酉戌相害"}]
LIUPO = [{"pair":["子","酉"],"name":"子酉相破"},{"pair":["丑","辰"],"name":"丑辰相破"},
         {"pair":["寅","亥"],"name":"寅亥相破"},{"pair":["卯","午"],"name":"卯午相破"},
         {"pair":["巳","申"],"name":"巳申相破"},{"pair":["未","戌"],"name":"未戌相破"}]
SANXING = [{"pair":["寅","巳","申"],"name":"寅巳申三刑"},{"pair":["丑","戌","未"],"name":"丑戌未三刑"},
           {"pair":["子","卯"],"name":"子卯相刑"}]
SELF_PUNISH_ZHI = {"辰","午","酉","亥"}
POSK = ("year", "month", "day", "hour")
POSI = {p: i for i, p in enumerate(POSK)}


def build_relations(zlis):
    """结构2 relations: 按有序支名对聚合, positions = 每组实例一条"""
    R = []           # 全部 relation
    _agg = {}        # (type, branches_tuple) -> relation 对象 (聚合桶)
    _seq = [0]      # 首见序号 (保证派生旧键时能还原原顺序)

    def put(t, brs, pos_inst, wx=None, meta=None, blocking=None, distance=None):
        key = (t, tuple(brs))
        r = _agg.get(key)
        if r is None:
            r = {'type': t, 'branches': list(brs), 'positions': [],
                 'wx': wx, 'meta': meta or {}, 'instance_count': 0,
                 '_seq': _seq[0]}
            _seq[0] += 1
            _agg[key] = r
            R.append(r)
        if blocking is not None:
            r['blocking'] = blocking
        if distance is not None:
            r['distance'] = distance
        r['positions'].append(pos_inst)
        r['instance_count'] = len(r['positions'])
        return r

    # ① 六合/六冲: i<j 实例遍历 → 聚合 (结构2)
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = zlis[i], zlis[j]
            if LIUHE.get(a) == b:
                put('HE', [a, b], [[POSK[i]], [POSK[j]]], wx='__HE__')
            if LIUCHONG.get(a) == b:
                put('CHONG', [a, b], [[POSK[i]], [POSK[j]]])

    zset = set(zlis)
    posof = lambda z: [p for p in POSK if zlis[POSK.index(p)] == z]

    # ② 三合/三会: 集合包含, 三支齐全才报, instance_count=1
    for s in SANHE:
        if set(s['pair']).issubset(zset):
            put('SANHE', list(s['pair']), [posof(z) for z in s['pair']],
                wx=s['name'][-1], meta={'name': s['name']})
    for s in SANHUI:
        if set(s['pair']).issubset(zset):
            put('HUI', list(s['pair']), [posof(z) for z in s['pair']],
                wx=s['name'][-1], meta={'name': s['name']})
    # ③ 半合: i<j + _seen 去重, instance_count=1
    seen = set()
    for i in range(4):
        for j in range(i + 1, 4):
            k = frozenset((zlis[i], zlis[j]))
            if k in BANHE_PAIRS and k not in seen:
                put('BANHE', [zlis[i], zlis[j]], [[POSK[i]], [POSK[j]]],
                    wx=BANHE_PAIRS[k])
                seen.add(k)
    # ④ 害/破/刑: 集合包含
    for t, S in (('HAI', LIUHAI), ('PO', LIUPO), ('XING', SANXING)):
        for s in S:
            if set(s['pair']).issubset(zset):
                put(t, list(s['pair']), [posof(z) for z in s['pair']],
                    meta={'name': s['name']})
    # ⑤ 自刑: 每支一条, positions 多值
    pb = {}
    for idx, z in enumerate(zlis):
        pb.setdefault(z, []).append(POSK[idx])
    for z, pos in pb.items():
        if z in SELF_PUNISH_ZHI and len(pos) >= 2:
            put('SELF', [z], sorted(pos))   # 【修正】不额外包列表, 否则 positions 变三层
    return R


def derive(R, key):
    """从 relations 派生旧键 (按 _seq 还原原顺序, CHONG/HE 按 count 展开)"""
    rs = sorted([r for r in R if r['type'] in
                 ('CHONG', 'HE', 'SANHE', 'HUI', 'BANHE', 'HAI', 'PO', 'XING', 'SELF')],
                key=lambda r: r['_seq'])
    if key in ('liuchong', 'liuhe'):
        T = 'CHONG' if key == 'liuchong' else 'HE'
        # 结构2 聚合后, relation 间会交错 → 必须按实例 (pos_i,pos_j) 全局排序还原 L0 原序
        inst = []
        for r in R:
            if r['type'] != T:
                continue
            for pair in r['positions']:          # pair = [[pos_i],[pos_j]] 结构2 实例枚举
                pi, pj = POSI[pair[0][0]], POSI[pair[1][0]]
                inst.append((min(pi, pj), max(pi, pj), list(r['branches'])))
        inst.sort(key=lambda x: (x[0], x[1]))
        return [x[2] for x in inst]
    if key == 'sanhe':
        return [r['meta']['name'] for r in rs if r['type'] == 'SANHE']
    if key == 'sanhui':
        return [r['meta']['name'] for r in rs if r['type'] == 'HUI']
    if key == 'banhe':
        return [{'pair': r['branches'], 'wx': r['wx']} for r in rs if r['type'] == 'BANHE']
    if key == 'liuhai':
        return [r['meta']['name'] for r in rs if r['type'] == 'HAI']
    if key == 'liupo':
        return [r['meta']['name'] for r in rs if r['type'] == 'PO']
    if key == 'sanxing':
        return [r['meta']['name'] for r in rs if r['type'] == 'XING']
    if key == 'self_punishment':
        return [{'branch': r['branches'][0], 'positions': sorted(r['positions'][0])}
                for r in rs if r['type'] == 'SELF']   # positions[0] 已脱一层 ✓
    return None


KEYS = ['liuchong', 'liuhe', 'sanhe', 'sanhui', 'banhe',
        'liuhai', 'liupo', 'sanxing', 'self_punishment']


def main():
    from engines.common.l0_fact_builder import build as l0build
    st = collections.Counter()
    diffs = collections.defaultdict(list)
    n = 0
    cnt_dist = collections.Counter()
    for bk in ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            n += 1
            pil = _pillars(bz)
            zlis = [pil[k][1] for k in POSK]
            old = l0build(pil).get("combination_facts", {}) or {}
            R = build_relations(zlis)
            for r in R:
                if r['type'] == 'CHONG':
                    cnt_dist[r['instance_count']] += 1
            for k in KEYS:
                o = old.get(k) or []
                nv = derive(R, k)
                if k == 'self_punishment':
                    eq = (sorted((x['branch'], tuple(x['positions'])) for x in o)
                          == sorted((x['branch'], tuple(x['positions'])) for x in nv))
                else:
                    eq = (o == nv)
                if eq:
                    st["%s 等价" % k] += 1
                else:
                    st["%s ★不等价" % k] += 1
                    if len(diffs[k]) < 4:
                        diffs[k].append((d["case_id"], bz, o, nv))
    print("=" * 96)
    print("前置核1-B  结构2(按实例枚举)+instance_count聚合  六本 %d 盘" % n)
    print("=" * 96)
    tot = 0
    for k in KEYS:
        a, b = st["%s 等价" % k], st["%s ★不等价" % k]
        tot += b
        print("  %s %-18s 等价 %5d   不等价 %4d" % ("OK  " if b == 0 else "DIFF", k, a, b))
    print("\n  差异总数 = %d" % tot)
    print("\n  CHONG relation 的 instance_count 分布 (结构2 生效证据):")
    for c in sorted(cnt_dist):
        print("    count=%d : %5d 条 relation" % (c, cnt_dist[c]))
    print("\n  证据: DT-0039 甲寅戊辰丙寅丙申 →")
    R = build_relations(list("寅辰寅申"))
    for r in R:
        if r['type'] == 'CHONG':
            print("    branches=%s count=%d positions=%s" %
                  (r['branches'], r['instance_count'], r['positions']))
    R17 = build_relations(list("丑未辰丑"))
    for r in R17:
        if r['type'] == 'CHONG':
            print("  证据: DT-0017 辛丑乙未庚辰丁丑 → branches=%s count=%d" %
                  (r['branches'], r['instance_count']))
    for k, v in diffs.items():
        print("\n  【%s 差异样本】" % k)
        for cid, bz, o, nw in v:
            print("    %-9s %-17s" % (cid, bz))
            print("      旧=%s" % json.dumps(o, ensure_ascii=False)[:140])
            print("      新=%s" % json.dumps(nw, ensure_ascii=False)[:140])


if __name__ == "__main__":
    main()