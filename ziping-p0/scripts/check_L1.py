# -*- coding: utf-8 -*-
"""L1 五行层核验

准神: 《五行精纪》卷八【五行旺相囚休死例】
  "论曰: 五行当时者旺，所生者相，所尅者死，生我者休，尅我者囚。"
  + 四时全表:
     春木旺、火相、金囚、水休、土死
     夏火旺、土相、水囚、木休、金死
     秋金旺、水相、火囚、土休、木死
     冬水旺、木相、土囚、金休、火死
  + "土于长夏时土旺" + "土旺四季, 一十八日" -> 辰未戌丑按本气土旺

核:
  1 wuxing_power 五行齐全 + 8 字段
  2 ling_state 与月令五行 + 《五行精纪》定义 逐格推
  3 四土月 = 土旺
  4 ben_n/zhong_n/yu_n 与藏干表逐柱对
  5 stem_n 与四天干五行对

用法:
  python scripts/check_L1.py --self-test    先自证(用 4 个已知盘手算对)
  python scripts/check_L1.py                六本全量
"""
import sys, os, json, glob, collections

ROOT = r"D:/shuntian-ziping-p0"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

# 藏干次序 = (本气, 中气, 余气)。
# 判据见 六部经典MD文库/01_公共依赖/02_透藏关系/_藏干次序判据.md:
#   主判据 三命通会《论人元司事》(TOU_CANG.BEN_QI_TOU.002) 用事日数降序;
#   日数并列时以 渊海子平藏遁歌(TOU_CANG.CANG_GAN_GE.001) 书写序为辅;
#   丑支两书分歧(庚 vs 辛) -> 取藏遁歌「丑癸辛金己土同」的辛。
CANGGAN = {
    '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'], '卯': ['乙'],
    '辰': ['戊', '乙', '癸'], '巳': ['丙', '戊', '庚'], '午': ['丁', '己'],
    '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'], '酉': ['辛'],
    '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲'],
}
WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
      '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
WXES = ('木', '火', '土', '金', '水')
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}   # 生我者=我生
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}      # 我克
F8 = ["ling_state", "ben_n", "zhong_n", "yu_n", "ju_n", "banhe_n",
      "stem_n", "root_detail"]


def month_wx(bz):
    """月令五行: 按藏干本气(辰未戌丑=土)"""
    return WX.get(CANGGAN.get(bz[3], [''])[0], '')   # bz 索引3 = 月支


def ling_ref(m):
    """按《五行精纪》定义推 五行 -> 旺相休囚死

    当时者旺; 所生者相; 所尅者死; 生我者休; 尅我者囚
    四土月(辰未戌丑)月令本气为土, 已在 month_wx 处理, 此处纯按定义推。
    """
    out = {}
    for w in WXES:
        if w == m:
            out[w] = '旺'
        elif SHENG[m] == w:      # m 所生 = 相
            out[w] = '相'
        elif KE[m] == w:         # m 所克 = 死
            out[w] = '死'
        elif SHENG[w] == m:      # 生 m 者 = 休
            out[w] = '休'
        else:                    # 克 m 者 = 囚
            out[w] = '囚'
    return out


def parse_bz(bz):
    bz = (bz or "").replace(" ", "")
    return [(bz[i], bz[i + 1]) for i in range(0, min(8, len(bz)), 2)]


def check_one(bz):
    """返回 (错误列表, 观测)"""
    from p0_v2.bazi_gate import paipan
    pz = parse_bz(bz)
    if len(pz) != 4:
        return ["四柱解析失败 %r" % bz], {}
    r = paipan(bz)
    raw = r.get("raw_facts") or {}
    wp = raw.get("wuxing_power") or {}
    errs = []

    # 1 五行齐全 + 8 字段
    inner = wp.get("wuxing_power") or {}
    for w in WXES:
        if w not in inner:
            errs.append("wuxing_power 缺五行 %s" % w)
            continue
        v = inner[w] or {}
        for f in F8:
            if f not in v:
                errs.append("wuxing_power[%s] 缺字段 %s" % (w, f))

    # 2 ling_state
    m = month_wx(bz)
    ref = ling_ref(m)
    for w in WXES:
        got = (inner.get(w) or {}).get("ling_state")
        if got != ref[w]:
            errs.append("ling_state[%s]=%s 月令%s 应为%s" % (w, got, m, ref[w]))

    # 3 四土月土旺
    if bz[3] in ('辰', '未', '戌', '丑') and ref.get('土') != '旺':
        errs.append("四土月(%s) 土应旺, 实为%s" % (bz[3], ref.get('土')))

    # 4 ben/zhong/yu 与藏干表
    want = {w: {'BEN': 0, 'ZHONG': 0, 'YU': 0} for w in WXES}
    for g, z in pz:
        cg = CANGGAN.get(z, [])
        for idx, sg in enumerate(cg):
            w = WX.get(sg)
            if w:
                tag = ('BEN', 'ZHONG', 'YU')[idx] if idx < 3 else 'YU'
                want[w][tag] += 1
    for w in WXES:
        v = inner.get(w) or {}
        if v.get("ben_n") != want[w]['BEN']:
            errs.append("ben_n[%s]=%s 应为%s" % (w, v.get("ben_n"), want[w]['BEN']))
        if v.get("zhong_n") != want[w]['ZHONG']:
            errs.append("zhong_n[%s]=%s 应为%s" % (w, v.get("zhong_n"), want[w]['ZHONG']))
        if v.get("yu_n") != want[w]['YU']:
            errs.append("yu_n[%s]=%s 应为%s" % (w, v.get("yu_n"), want[w]['YU']))

    # 5 stem_n 与四天干
    ws = collections.Counter(WX.get(g, '') for g, _ in pz)
    for w in WXES:
        if (inner.get(w) or {}).get("stem_n") != ws[w]:
            errs.append("stem_n[%s]=%s 应为%s" % (w, (inner.get(w) or {}).get("stem_n"), ws[w]))

    return errs, {"月令": m}


# ---------------- 自证盘: 按规则筛, 不手选 ----------------
# 筛法: 从案例表挑【含巳支】的盘(巳是本次唯一改动支), 优先结构不同者。
# 依据: 改的是巳支 zhong/yu, 只有含巳的盘才会触发 -> 必须筛含巳盘。
def pick_self_tests(n=5):
    import json as _j
    fp = os.path.join(ROOT, "p0_v2", "case_audit", "DTS_clean.jsonl")
    rows = []
    for line in open(fp, encoding="utf-8-sig"):
        if not line.strip():
            continue
        d = _j.loads(line)
        bz = (d.get("bazi") or "").replace(" ", "")
        if len(bz) != 8:
            continue
        zhis = [bz[1], bz[3], bz[5], bz[7]]
        if "巳" not in zhis:
            continue
        rows.append((d["case_id"], bz, "含巳支(%s位)" % zhis.index("巳")))
    # 按巳所在柱位分散, 覆盖年月日时四种情形
    seen = {}
    out = []
    for cid, bz, why in rows:
        k = bz[3:4] and bz.index("巳")
        if k not in seen:
            seen[k] = (cid, bz, why)
            out.append(seen[k])
        if len(out) >= n:
            break
    return out


def self_test():
    print("=" * 80)
    print("L1 检查器自证 —— 用手算全表比对引擎, 先确认检查器逻辑对")
    print("=" * 80)
    ok = True
    # 先验证定义表本身: 四时全表 vs 函数
    QUARTER = [
        ('春木', '木', ['旺', '相', '死', '囚', '休']),   # 木火土金水
        ('夏火', '火', ['休', '旺', '相', '死', '囚']),
        ('秋金', '金', ['死', '囚', '休', '旺', '相']),
        ('冬水', '水', ['相', '死', '囚', '休', '旺']),
    ]
    print("\n[1] 验证《五行精纪》四时全表 vs ling_ref() 推导")
    for nm, m, exp in QUARTER:
        got = [ling_ref(m)[w] for w in WXES]
        flag = "✓" if got == exp else "✗"
        if got != exp:
            ok = False
        print("  %s %s  原典=%s  推导=%s" % (flag, nm, exp, got))
    print("  (木火土金水 顺序)")

    print("\n[2] 验证引擎输出 vs 推导 (筛出的含巳盘)")
    for cid, bz, why in pick_self_tests(5):
        from p0_v2.bazi_gate import paipan
        m = month_wx(bz); mz = bz[3]
        exp = [ling_ref(m)[w] for w in WXES]
        r = paipan(bz)
        inner = ((r.get("raw_facts") or {}).get("wuxing_power") or {}).get("wuxing_power") or {}
        got = [(inner.get(w) or {}).get("ling_state") for w in WXES]
        errs, _ = check_one(bz)
        good = (got == exp) and (not errs)
        if not good:
            ok = False
        print("  %s %s %s  月柱支%s 月令%s" % ("✓" if good else "✗", cid, bz, mz, m))
        print("      引擎=%s" % got)
        print("      推导=%s" % exp)
        if errs:
            print("      错误 %d 条: %s" % (len(errs), errs[:3]))

    print("\n[3] 四土月全查 (辰未戌丑 -> 土旺)")
    for bz in ["甲子乙丑丙寅丁卯",      # 月支 丑
               "戊辰壬辰甲寅丙辰",      # 月支 辰
               "乙丑辛未丁未己卯",      # 月支 未
               "辛丑壬辰甲戌丙子"]:     # 月柱 壬戌 -> 月支 戌
        from p0_v2.bazi_gate import paipan
        r = paipan(bz)
        inner = ((r.get("raw_facts") or {}).get("wuxing_power") or {}).get("wuxing_power") or {}
        m = month_wx(bz)
        tu = (inner.get('土') or {}).get("ling_state")
        good = (m == '土' and tu == '旺')
        if not good:
            ok = False
        print("  %s %s  月支%s -> 月令%s 土=%s" % ("✓" if good else "✗", bz, bz[3], m, tu))

    print()
    print("=" * 80)
    print("自证结果: %s" % ("✓ 检查器逻辑正确, 可全量跑" if ok else "✗ 检查器有问题, 不得全量跑"))
    print("=" * 80)
    return 0 if ok else 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    CA = os.path.join(ROOT, "p0_v2", "case_audit")
    books = [b for b in ("DTS", "PZZQ", "QTBJ", "YHZP", "SMTH", "SFTK")]
    total = bad = 0
    cat = collections.defaultdict(list)
    for bk in books:
        fp = os.path.join(CA, "%s_clean.jsonl" % bk)
        if not os.path.exists(fp):
            continue
        n = berr = 0
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if not bz:
                continue
            n += 1
            try:
                errs, _ = check_one(bz)
            except Exception as e:
                errs = ["★抛异常 %s: %s" % (type(e).__name__, str(e)[:80])]
            if errs:
                berr += 1
                for e in errs:
                    cat[e.split("=")[0].split("[")[0]].append((d["case_id"], bz, e))
        total += n
        bad += berr
        print("  %-6s %5d 盘   有错 %d" % (bk, n, berr))
    print("  %-6s %5d 盘   有错 %d" % ("合计", total, bad))
    if cat:
        print("\n=== 错误分类 ===")
        for k in sorted(cat, key=lambda x: -len(cat[x])):
            v = cat[k]
            print("  %-32s %d 盘" % (k, len(v)))
            for cid, bz, e in v[:3]:
                print("      %-9s %-17s %s" % (cid, bz, e[:90]))
    else:
        print("\n✓ L1 五行层 六本全量 通过")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())