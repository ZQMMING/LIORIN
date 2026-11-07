# -*- coding: utf-8 -*-
"""前置核1: relations 统一表能否 100% 派生出全部旧键 (2106盘逐字段 diff)

不落码, 只验等价性。relations 由【现有 L0 生成逻辑】重放, 不改引擎。
"""
import sys, os, json, collections, itertools
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import _pillars

# ── 复刻 L0 现有生成逻辑 (l0_fact_builder.py L176-181 / L338-388) ──
LIUHE = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯",
         "辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
LIUCHONG = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅",
            "卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
SANHE = [{"pair":["申","子","辰"],"name":"申子辰合水"},
         {"pair":["亥","卯","未"],"name":"亥卯未合木"},
         {"pair":["寅","午","戌"],"name":"寅午戌合火"},
         {"pair":["巳","酉","丑"],"name":"巳酉丑合金"}]
SANHUI = [{"pair":["寅","卯","辰"],"name":"寅卯辰三会木"},
          {"pair":["巳","午","未"],"name":"巳午未三会火"},
          {"pair":["申","酉","戌"],"name":"申酉戌三会金"},
          {"pair":["亥","子","丑"],"name":"亥子丑三会水"}]
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
SANXING = [{"pair":["寅","巳","申"],"name":"寅巳申三刑"},
           {"pair":["丑","戌","未"],"name":"丑戌未三刑"},
           {"pair":["子","卯"],"name":"子卯相刑"}]
SELF_PUNISH_ZHI = {"辰","午","酉","亥"}
POSK = ("year","month","day","hour")


def build_relations(zlis):
    """按统一 relations schema 重放 L0 全部地支关系"""
    R = []
    # ① 六合/六冲: i<j 实例遍历 (复刻 L177-181)
    for i in range(4):
        for j in range(i+1, 4):
            a, b = zlis[i], zlis[j]
            if LIUHE.get(a) == b:
                R.append({'type':'HE','branches':[a,b],
                          'positions':[[POSK[i]],[POSK[j]]],'wx':None,'meta':{}})
            if LIUCHONG.get(a) == b:
                R.append({'type':'CHONG','branches':[a,b],
                          'positions':[[POSK[i]],[POSK[j]]],'wx':None,'meta':{}})
    zset = set(zlis)
    # ② 三合/三会: 集合包含 (复刻 L348-349), 位置取盘内实有者
    for s in SANHE:
        if set(s['pair']).issubset(zset):
            hit = [z for z in s['pair'] if z in zset]
            R.append({'type':'SANHE','branches':list(s['pair']),
                      'positions':[[p for p in POSK if zlis[POSK.index(p)]==z] for z in s['pair']],
                      'wx':s['name'][-1],'meta':{'name':s['name']}})
    for s in SANHUI:
        if set(s['pair']).issubset(zset):
            R.append({'type':'HUI','branches':list(s['pair']),
                      'positions':[[p for p in POSK if zlis[POSK.index(p)]==z] for z in s['pair']],
                      'wx':s['name'][-1],'meta':{'name':s['name']}})
    # ③ 半合: i<j + _seen 去重 (复刻 L356-364)
    seen = set()
    for i in range(4):
        for j in range(i+1, 4):
            k = frozenset((zlis[i], zlis[j]))
            if k in BANHE_PAIRS and k not in seen:
                R.append({'type':'BANHE','branches':[zlis[i],zlis[j]],
                          'positions':[[POSK[i]],[POSK[j]]],
                          'wx':BANHE_PAIRS[k],'meta':{}})
                seen.add(k)
    # ④ 害/破/刑: 集合包含 (复刻 L375-377)
    for t, S in (('HAI',LIUHAI), ('PO',LIUPO), ('XING',SANXING)):
        for s in S:
            if set(s['pair']).issubset(zset):
                R.append({'type':t,'branches':list(s['pair']),
                          'positions':[[p for p in POSK if zlis[POSK.index(p)]==z] for z in s['pair']],
                          'wx':None,'meta':{'name':s['name']}})
    # ⑤ 自刑: 每支一条带 positions (复刻 L380-388)
    pb = {}
    for idx, z in enumerate(zlis):
        pb.setdefault(z, []).append(POSK[idx])
    for z, pos in pb.items():
        if z in SELF_PUNISH_ZHI and len(pos) >= 2:
            R.append({'type':'SELF','branches':[z],
                      'positions':[sorted(pos)],'wx':None,'meta':{}})
    return R


def derive(R, key):
    """从 relations 派生旧键"""
    if key == 'liuchong':
        return [r['branches'] for r in R if r['type']=='CHONG']
    if key == 'liuhe':
        return [r['branches'] for r in R if r['type']=='HE']
    if key == 'sanhe':
        return [r['meta']['name'] for r in R if r['type']=='SANHE']
    if key == 'sanhui':
        return [r['meta']['name'] for r in R if r['type']=='HUI']
    if key == 'banhe':
        return [{'pair':r['branches'],'wx':r['wx']} for r in R if r['type']=='BANHE']
    if key == 'liuhai':
        return [r['meta']['name'] for r in R if r['type']=='HAI']
    if key == 'liupo':
        return [r['meta']['name'] for r in R if r['type']=='PO']
    if key == 'sanxing':
        return [r['meta']['name'] for r in R if r['type']=='XING']
    if key == 'self_punishment':
        return [{'branch':r['branches'][0],'positions':sorted(r['positions'][0])}
                for r in R if r['type']=='SELF']
    return None


KEYS = ['liuchong','liuhe','sanhe','sanhui','banhe','liuhai','liupo','sanxing','self_punishment']


def main():
    from engines.common.l0_fact_builder import build as l0build
    st = collections.Counter()
    diffs = collections.defaultdict(list)
    n = 0
    for bk in ["DTS","PZZQ","YHZP","QTBJ","SFTK","SMTH"]:
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
            for k in KEYS:
                o = old.get(k)
                if k == 'self_punishment':
                    o = o or []
                newv = derive(R, k)
                if newv is None:
                    continue
                if k == 'self_punishment':
                    so = sorted([(x['branch'], tuple(x['positions'])) for x in o])
                    sn = sorted([(x['branch'], tuple(x['positions'])) for x in newv])
                    eq = (so == sn)
                else:
                    eq = (o == newv)
                if eq:
                    st["%s 等价" % k] += 1
                else:
                    st["%s ★不等价" % k] += 1
                    if len(diffs[k]) < 4:
                        diffs[k].append((d["case_id"], bz, o, newv))
    print("=" * 96)
    print("前置核1: relations 派生旧键 等价性   六本 %d 盘" % n)
    print("=" * 96)
    tot_diff = 0
    for k in KEYS:
        a, b = st["%s 等价" % k], st["%s ★不等价" % k]
        tot_diff += b
        flag = "OK  " if b == 0 else "DIFF"
        print("  %s %-18s 等价 %5d   不等价 %4d" % (flag, k, a, b))
    print("\n  差异总数 = %d" % tot_diff)
    for k, v in diffs.items():
        print("\n  【%s 差异样本】" % k)
        for cid, bz, o, nw in v:
            print("    %-9s %-17s" % (cid, bz))
            print("      旧=%s" % json.dumps(o, ensure_ascii=False)[:150])
            print("      新=%s" % json.dumps(nw, ensure_ascii=False)[:150])


if __name__ == "__main__":
    main()