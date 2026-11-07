# -*- coding: utf-8 -*-
"""错1 影响面分析: ti_wx 规则归位 前后对比
规则(已钉死):
  ① 六格(正官/七煞/财/印/食神/伤官 及带条件变体) ti_wx = 该格之神五行
  ② 建禄月劫/阳刃          ti_wx = 月令透干之神; 无透干 -> []
     依据 DTS L210「建禄月劫羊刃, 亦当看月令中人元透于天干者取格」(准神)
          + PZZQ L4652「建禄月劫, 皆无取以为用之法, 另取财官煞食用神」(同向)
  ③ 从格/化气/专旺          ti_wx = 所从之神(引擎现状已符)

只算不改。
"""
import sys, os, io, json, glob, collections

ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
      '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
CANG = {'子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'], '卯': ['乙'],
        '辰': ['戊', '乙', '癸'], '巳': ['丙', '戊', '庚'], '午': ['丁', '己'],
        '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'], '酉': ['辛'],
        '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲']}
Y = set('甲丙戊庚壬')
SH = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}


def tg(dm, o):
    d, ov = WX[dm], WX[o]
    s = (dm in Y) == (o in Y)
    if ov == d:
        return '比肩' if s else '劫财'
    if SH[d] == ov:
        return '食神' if s else '伤官'
    if KE[d] == ov:
        return '偏财' if s else '正财'
    if KE[ov] == d:
        return '七杀' if s else '正官'
    if SH[ov] == d:
        return '偏印' if s else '正印'


# 格名 -> 格体五行(取自月令十神, 不取月支本气五行)
GE_BODY = {
    '正官格': {'正官'},
    '七煞格': {'七杀'},
    '七煞格(逢制)': {'七杀'},
    '财格': {'正财', '偏财'},
    '印格': {'正印', '偏印'},
    '印格(官印双全)': {'正印', '偏印'},
    '印格(印轻逢煞)': {'正印', '偏印'},
    '印格(印轻逢财)': {'正印', '偏印'},
    '印格(印多逢财)': {'正印', '偏印'},
    '食神格': {'食神'},
    '食神制杀格': {'食杀'},          # 旧名(应已改)
    '伤官格': {'伤官'},
    '伤官格(佩印)': {'伤官'},
    '伤官格(带煞无财)': {'伤官'},
}
# ② 建禄月劫/阳刃: ti_wx = 月令透干之神; 无透干 -> []
TRANSPARENT = {'建禄月劫格', '阳刃格'}


def rule_ti_wx(bz, ge):
    pz = [(bz[i], bz[i + 1]) for i in range(0, 8, 2)]
    dm = pz[2][0]
    mqi = CANG[pz[1][1]][0]
    mt = tg(dm, mqi)
    mwx = WX[mqi]
    if ge in TRANSPARENT:
        # 月令透干之神: 三透干里取 官/财/食伤/煞(成格用神), 无则 []
        tou = [pz[0][0], pz[2][0], pz[3][0]]   # 年/日/时干(月干=月支本气已含)
        gods = []
        for g in tou:
            if g == dm:
                continue
            t = tg(dm, g)
            if t in ('正官', '七杀', '正财', '偏财', '食神', '伤官'):
                gods.append(WX[g])
        return sorted(set(gods))
    body = GE_BODY.get(ge)
    if body is None:
        return None                     # 从格/化气/专旺等, 本轮不动
    return [mwx] if mt in body else None


def main():
    from p0_v2.bazi_gate import paipan
    CA = os.path.join(ROOT, "p0_v2", "case_audit")
    cases = {}
    for fp in glob.glob(os.path.join(CA, "*_clean.jsonl")):
        for l in open(fp, encoding="utf-8-sig"):
            if l.strip():
                d = json.loads(l)
                cases[d["case_id"]] = d

    changed = []
    unchanged = 0
    no_rule = collections.Counter()
    by_ge = collections.defaultdict(list)
    for cid, d in sorted(cases.items()):
        bz = (d.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        try:
            r = paipan(bz)
        except Exception:
            continue
        gc = r.get("ge_cheng") or {}
        ge = gc.get("ge") or ""
        base_ge = ge.replace("(破格)", "")
        want = rule_ti_wx(bz, base_ge)
        if want is None:
            no_rule[base_ge] += 1
            continue
        got = list(gc.get("ti_wx") or [])
        if got != want:
            changed.append({"cid": cid, "bz": bz, "ge": ge,
                            "got": got, "want": want,
                            "bing_ids": sorted(b.get("bing_id") for b in
                                               (r.get("bing_list") or []))})
            by_ge[base_ge].append(cid)
        else:
            unchanged += 1

    print("=" * 92)
    print("错1 ti_wx 影响面分析 (只算不改)")
    print("=" * 92)
    print("  会变的盘: %d    已符合规则的盘: %d" % (len(changed), unchanged))
    print("\n  按格名分布(会变):")
    for k, v in sorted(by_ge.items(), key=lambda x: -len(x[1])):
        print("    %-18s %4d" % (k, len(v)))
    print("\n  不在本轮规则范围(从/化/专旺等, 保持现状): %d 类" % len(no_rule))
    for k, v in no_rule.most_common(10):
        print("    %-18s %4d" % (k, v))
    print("\n  变法分类:")
    pat = collections.Counter()
    for c in changed:
        if not c["got"] and c["want"]:
            pat["空 -> 有值"] += 1
        elif c["got"] and not c["want"]:
            pat["有值 -> 空"] += 1
        else:
            pat["值改变(%s->%s)" % (c["got"], c["want"])] += 1
    for k, v in pat.most_common(12):
        print("    %-30s %4d" % (k, v))

    print("\n  抽样 10 盘:")
    for c in changed[:10]:
        print("    %-9s %-17s %-14s ti %s -> %s" % (
            c["cid"], c["bz"], c["ge"], c["got"], c["want"]))

    json.dump(changed, io.open(os.path.join(ROOT, "scripts", "_l4_ti_change.json"),
                               "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n  清单已落 scripts/_l4_ti_change.json (%d 盘)" % len(changed))


if __name__ == "__main__":
    main()