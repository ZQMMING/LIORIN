# -*- coding: utf-8 -*-
"""L3 旺衰层核验 —— §2.5 契约字段的值

§2.5 契约:
  dm_ben_eff       来源 L0 root_weight_class_facts  日主本气根有无(布尔/计数)
  ling_state       来源 L1 wuxing_power[日主].ling_state  禁重算
  root_grade       来源 L0 root_weight_class_facts  无/余/中/本
  support_state    同党 vs 异党
  strength_verdict 强/弱/中和 (已知 NOT_AUTHORIZED, 不核)

来源(先钉死, 已读源码):
  dm_ben_eff / yin_ben_eff 实现在 L4 special_pattern, 三层修正:
    ① 起点 dm_ben / yin_ben (本气根数)
    ② 孤根被冲拔 T30 (special_pattern L102-121): 身/印本气仅一支 且 被六冲
       且 对立成势 且 日主不当令 -> 该支从根数扣除
    ③ 合局化去根 (L123 起): 入完整三合/三会且化神为财或官杀的支, 该根从化神
  本检查器【独立复刻这三层】, 不读引擎中间量, 再比对引擎输出。

用法:
  python scripts/check_L3.py --self-test
  python scripts/check_L3.py
"""
import sys, os, io, json, glob, collections, subprocess

ROOT = r"D:/shuntian-ziping-p0"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

CANGGAN = {
    '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'], '卯': ['乙'],
    '辰': ['戊', '乙', '癸'], '巳': ['丙', '戊', '庚'], '午': ['丁', '己'],
    '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'], '酉': ['辛'],
    '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲'],
}   # 次序依据 _藏干次序判据.md
WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
      '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
WXES = ('木', '火', '土', '金', '水')
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
KE = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}
LIUCHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
            '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
SANHE = [('申', '子', '辰', '水'), ('亥', '卯', '未', '木'), ('寅', '午', '戌', '火'),
         ('巳', '酉', '丑', '金')]
SANHUI = [('寅', '卯', '辰', '木'), ('巳', '午', '未', '火'), ('申', '酉', '戌', '金'),
          ('亥', '子', '丑', '水')]


def ling(m, w):
    if w == m: return '旺'
    if SHENG[m] == w: return '相'
    if KE[m] == w: return '死'
    if SHENG[w] == m: return '休'
    return '囚'


def parse(bz):
    bz = (bz or "").replace(" ", "")
    return [(bz[i], bz[i + 1]) for i in range(0, len(bz), 2)]


def ref_l3(bz):
    """独立复刻 §2.5 三个字段"""
    pz = parse(bz)
    dm = pz[2][0]
    dm_wx = WX[dm]
    mz = pz[1][1]
    mqi = CANGGAN[mz][0]
    m = WX[mqi]                       # 月令五行
    yin_wx = SHENG[dm_wx]             # 生我 = 印  (SHENG[x]=x生, 故印=dm生)
    yin_wx = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[dm_wx]
    zhis = [z for _, z in pz]

    # 本气根必须按【柱位个数】计, 不能用 set —— 四柱可同支重复(如辰辰),
    #   set 会把两条辰并成一条, 少算根数(上一版就是这么把 庚申庚辰戊辰戊午
    #   的 dm_ben 算成 1, 而引擎 ben_n=2 是对的)。
    #   故: 根数按柱位 list 计数; 「与某集合求交」时才转 set。
    _BEN_POS = {w: [z for z in zhis if CANGGAN[z][0] and WX[CANGGAN[z][0]] == w]
                for w in WXES}

    def ben_branches(wx):
        return set(_BEN_POS[wx])          # 求交用

    def ben_count(wx):
        return len(_BEN_POS[wx])          # 计数用: 按柱位

    dm_ben = ben_count(dm_wx)
    yin_ben = ben_count(yin_wx)

    # ② 孤根被冲拔 T30
    # 「孤根」判定用【支种类】(set) 长度 —— 这是引擎实际口径:
    #   engine special_pattern L111 `if len(self_br) <= 1`, self_br 为 set。
    #   9 盘(DT-0133/DT-0230/DT-0381/DT-0517/PZ-0133/QT-0043/QT-0149/
    #        QT-0159/QT-0632)都是「两个同支根」(申申/子子/卯卯/寅寅):
    #   引擎视其为 1 种根 -> 孤根 -> 冲方在盘则拔 1 根 -> dm_ben_eff 2->1。
    #   【注意】与「根数按柱位计」不矛盾: 根数 ben_eff 按柱位, 但孤根判定按种类。
    #   (上一版改成按柱位判孤根, 9 盘全反转为 手算2/引擎1, 已回退。)
    self_br = ben_branches(dm_wx) | ben_branches(yin_wx)
    struck = set()
    if len(self_br) <= 1:
        # 对立成势? 克泄方(财/食伤/官杀)当令/成局/根多
        cai_wx = KE[dm_wx]           # 财
        gs_wx = SHENG[dm_wx]         # 食伤
        sha_wx = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}[dm_wx]
        opp_dom = (m == gs_wx) or (m == cai_wx) or (m == sha_wx)
        self_dom = (m == dm_wx)
        if opp_dom and not self_dom:
            for r in self_br:
                # 被拔须【冲方确实在盘上】。LIUCHONG.get(r) 只查表, 恒非空,
                #   等于「凡有冲表就拔」——上一版据此把 199 盘全误判为被拔
                #   (例 DT-0018 寅 的冲方是申, 本盘无申, 不该拔)。
                opp_branch = LIUCHONG.get(r)
                if opp_branch and opp_branch in zhis:
                    struck.add(r)
    # 被拔根的扣减按【支种类】(set 交集长度), 与引擎一致:
    #   engine L120 `dm_ben_eff = max(0, dm_ben - len(_ben_branches(pw,dm_wx) & struck))`
    #   _ben_branches 返回 set -> 两条申(申申)被冲只扣 1 种, 不扣 2 个柱位。
    #   故 9 盘(DT-0133 等): ben=2 -> 扣1 -> dm_ben_eff=1, 与引擎一致。
    #   (根数起点 dm_ben 按柱位计; 被拔扣减按种类计。两者口径不同, 是引擎原样。)
    _struck_kinds_dm = len(ben_branches(dm_wx) & struck)
    _struck_kinds_yin = len(ben_branches(yin_wx) & struck)
    dm_ben_eff = max(0, dm_ben - _struck_kinds_dm)
    yin_ben_eff = max(0, yin_ben - _struck_kinds_yin)

    # ③ 合局化根: 入完整三合/三会, 化神为财或官杀
    cai_wx = KE[dm_wx]
    sha_wx = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}[dm_wx]
    gs_wx = SHENG[dm_wx]
    # 化根必须按【柱位个数】扣, 不能按支种类(set)。四柱可同支重复(如辰辰),
    #   两条辰都入局 -> 两根都被化去; set 会并成一条只扣 1(同 dm_ben 那处 bug)。
    hh_dm, hh_yin = [], []
    for grp in SANHE + SANHUI:
        gz, hx = grp[:3], grp[3]
        if all(g in zhis for g in gz):
            # 只「化神为财或官杀(克泄方)」才化根 —— 依据引擎实现:
            #   special_pattern L123 注释「合局化去身根/印根: 入完整三合/三会、
            #   化神为财或官杀(克泄方)的支, 该根从化神」。
            #   【注意】化神为食伤【不】化根。上一版本检查器自造了「食伤成局
            #   则身根被泄去」这条规则, 导致 226 盘全部误报(例 DT-0008 申子辰
            #   水局把申中庚金根扣掉 -> 手算0 而引擎1)。合局里申不再当金根
            #   是「化局」性质, 与「食伤泄气」是两回事, 不在本判据内。
            if hx in (cai_wx, sha_wx):
                for g in gz:
                    if g in ben_branches(dm_wx):
                        hh_dm.append(g)
                    if g in ben_branches(yin_wx):
                        hh_yin.append(g)
    dm_ben_eff = max(0, dm_ben_eff - len(hh_dm))
    yin_ben_eff = max(0, yin_ben_eff - len(hh_yin))

    # root_grade: L0 root_weight_class_facts HEAVY/LIGHT/NONE -> 本/余/无
    cls = set()
    for z in zhis:
        cg = CANGGAN[z]
        for i, tag in enumerate(('BEN', 'ZHONG', 'YU')):
            if i < len(cg) and WX.get(cg[i]):
                cls.add((z, WX[cg[i]], tag))
    has_heavy = any(t == 'BEN' for _z, _w, t in cls)
    has_light = any(t == 'ZHONG' for _z, _w, t in cls)
    root_grade = '本' if has_heavy else ('余' if has_light else '无')

    # support_state: 同党(日主+印) vs 异党(食伤+财+官杀) 计数
    def mass(w):
        c = {'BEN': 3, 'ZHONG': 2, 'YU': 1}
        return sum(c[t] for _z, ww, t in cls if ww == w)
    tong = mass(dm_wx) + mass(yin_wx)
    yi = mass(gs_wx) + mass(cai_wx) + mass(sha_wx)
    ss = ('SHENG_FU_CHENG_SHI' if tong > yi
          else ('KE_XIE_CHENG_SHI' if yi > tong else 'PINGHENG'))
    return {'dm_ben_eff': dm_ben_eff, 'yin_ben_eff': yin_ben_eff,
            'ling_state': ling(m, dm_wx), 'root_grade': root_grade,
            'support_state': ss}


def eng_l3(bz):
    from p0_v2.bazi_gate import paipan
    r = paipan(bz)
    raw = r.get("raw_facts") or {}
    lc = raw.get("l3_contract") or {}
    if not lc:                        # 若无契约位, 退化取 daymaster_power/root_weight_class
        dp = r.get("daymaster_power") or {}
        sp = ((r.get("special") or {}))
        lc = {"dm_ben_eff": sp.get("dm_ben_eff"), "ling_state": dp.get("ling_state")}
    return lc


def self_test():
    print("=" * 88)
    print("L3 检查器自证 —— 筛盘规则: 取 dm_ben_eff 三档各若干(按引擎输出筛, 不手选)")
    print("=" * 88)
    import subprocess
    probe = os.path.join(ROOT, "scripts", "_l3_pick.py")
    io.open(probe, "w", encoding="utf-8", newline="").write(_L3_PICK)
    r = subprocess.run([sys.executable, probe], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    picks = json.loads((r.stdout or "[]").strip() or "[]")
    try:
        os.remove(probe)
    except Exception:
        pass
    if not picks:
        print("  (筛盘失败: %s)" % (r.stderr or "")[:200])
        return 1
    print("\n  入选盘(依据: 引擎 dm_ben_eff 分档, 每档取首盘):")
    for p in picks:
        print("    %-9s %-17s 引擎 dm_ben_eff=%s" % (p["cid"], p["bz"], p["dm_ben_eff"]))
    print()
    ok = True
    for p in picks:
        ref = ref_l3(p["bz"])
        e = eng_l3(p["bz"])
        same = (int(ref["dm_ben_eff"]) == int(e.get("dm_ben_eff", -1))
                and ref["ling_state"] == e.get("ling_state"))
        if not same:
            ok = False
        print("  %s %-17s 手算=%s 引擎=%s" % (
            "✓" if same else "✗", p["bz"],
            {k: ref[k] for k in ("dm_ben_eff", "ling_state")},
            {k: e.get(k) for k in ("dm_ben_eff", "ling_state")}))
    print("\n自证结果: %s" % ("✓ 可全量" if ok else "✗ 不可全量"))
    return 0 if ok else 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    import subprocess
    probe = os.path.join(ROOT, "scripts", "_l3_run.py")
    io.open(probe, "w", encoding="utf-8", newline="").write(_L3_RUN)
    r = subprocess.run([sys.executable, probe], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try:
        os.remove(probe)
    except Exception:
        pass
    print(r.stdout or "")
    if r.returncode != 0:
        print("stderr:", (r.stderr or "")[:300])
    return r.returncode


_L3_PICK = r'''
import sys, os, json, glob
sys.path.insert(0, r"D:/shuntian-ziping-p0")
_P0 = os.path.join(r"D:/shuntian-ziping-p0", "p0_v2")
sys.path.remove(_P0) if _P0 in sys.path else None
from p0_v2.bazi_gate import paipan
seen = {}
for fp in glob.glob(os.path.join(r"D:/shuntian-ziping-p0", "p0_v2", "case_audit",
                                 "DTS_clean.jsonl")):
    for line in open(fp, encoding="utf-8-sig"):
        if not line.strip(): continue
        d = json.loads(line)
        bz = (d.get("bazi") or "").replace(" ", "")
        if len(bz) != 8: continue
        try: r = paipan(bz)
        except Exception: continue
        lc = (r.get("raw_facts") or {}).get("l3_contract") or {}
        v = lc.get("dm_ben_eff")
        if v is None: continue
        k = "0" if v == 0 else ("1" if v == 1 else "2+")
        if k not in seen:
            seen[k] = {"cid": d["case_id"], "bz": bz, "dm_ben_eff": v}
out = []
for k in sorted(seen): out.append(seen[k])
# 再各补一个 ling_state 非囚 的
for line in open(fp, encoding="utf-8-sig"):
    if not line.strip(): continue
    d = json.loads(line)
    bz = (d.get("bazi") or "").replace(" ", "")
    if len(bz) != 8: continue
    try: r = paipan(bz)
    except Exception: continue
    lc = (r.get("raw_facts") or {}).get("l3_contract") or {}
    if lc.get("ling_state") == "旺" and len(out) < 5:
        cand = {"cid": d["case_id"], "bz": bz, "dm_ben_eff": lc.get("dm_ben_eff")}
        if all(c["bz"] != bz for c in out): out.append(cand)
    if len(out) >= 5: break
print(json.dumps(out, ensure_ascii=False))
'''

_L3_RUN = r'''
import sys, os, io, json, glob, collections
sys.path.insert(0, r"D:/shuntian-ziping-p0")
_P0 = os.path.join(r"D:/shuntian-ziping-p0", "p0_v2")
if _P0 in sys.path: sys.path.remove(_P0)
sys.path.insert(0, os.path.join(r"D:/shuntian-ziping-p0", "scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "chk", os.path.join(r"D:/shuntian-ziping-p0", "scripts", "check_L3.py"))
# 只取 ref_l3, 不跑 main
src = io.open(spec.origin, encoding="utf-8").read()
src = src[:src.index("def self_test()")]
ns = {"__name__": "chkmod", "ROOT": r"D:/shuntian-ziping-p0"}
exec(compile(src, "chk", "exec"), ns)
ref_l3 = ns["ref_l3"]

from p0_v2.bazi_gate import paipan
CA = os.path.join(r"D:/shuntian-ziping-p0", "p0_v2", "case_audit")
books = ["DTS", "PZZQ", "QTBJ", "YHZP", "SMTH", "SFTK"]
tot = bad = 0
cat = collections.defaultdict(list)
have_lc = 0
for bk in books:
    fp = os.path.join(CA, bk + "_clean.jsonl")
    if not os.path.exists(fp): continue
    n = berr = 0
    for line in open(fp, encoding="utf-8-sig"):
        if not line.strip(): continue
        d = json.loads(line)
        bz = (d.get("bazi") or "").replace(" ", "")
        if len(bz) != 8: continue
        n += 1
        try:
            r = paipan(bz)
            lc = (r.get("raw_facts") or {}).get("l3_contract")
            if not lc:
                cat["★无 l3_contract 契约位"].append((d["case_id"], bz, ""))
                berr += 1; continue
            have_lc += 1
            ref = ref_l3(bz)
            for k in ("dm_ben_eff", "ling_state"):
                if str(lc.get(k)) != str(ref[k]):
                    cat["%s: 引擎%s vs 手算%s" % (k, lc.get(k), ref[k])].append(
                        (d["case_id"], bz, k))
                    berr += 1
        except Exception as e:
            cat["★抛异常"].append((d["case_id"], bz, type(e).__name__))
            berr += 1
    tot += n; bad += berr
    print("  %-6s %5d 盘   不符 %d" % (bk, n, berr))
print("  %-6s %5d 盘   不符 %d" % ("合计", tot, bad))
print("  有 l3_contract 契约位的盘: %d" % have_lc)
if cat:
    print("\n=== 不符分类 ===")
    for k in sorted(cat, key=lambda x: -len(cat[x]))[:14]:
        v = cat[k]
        print("  %-40s %d 盘" % (k[:40], len(v)))
        for cid, bz, x in v[:2]:
            print("      %-9s %-17s %s" % (cid, bz, x))
sys.exit(0 if bad == 0 else 1)
'''

if __name__ == "__main__":
    sys.exit(main())