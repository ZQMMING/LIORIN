# -*- coding: utf-8 -*-
"""坑③ 真实影响面: N_role_diff

问: 165 盘里, 有多少盘存在「同一柱位参与多个 CHONG 实例, 且这些实例给该柱算出的
    (role, adj, chong_by, library_open) 不完全相同」?
    —— 只有这种盘, branch_chong[pos] 单值后写覆盖才会真正改变结果。

覆盖无损的两种情形:
  ① 同一柱多次参与, 但每次算出的值完全相同 (如两处都是 PASSIVE/adj 同)
  ② 重复支但只有一处参与冲 (另一处 role 本就是 NO_CHONG, 不冲突)
"""
import sys, os, json, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
if os.path.join(ROOT, "p0_v2") in sys.path:
    sys.path.remove(os.path.join(ROOT, "p0_v2"))

POSK = ("year", "month", "day", "hour")
POSI = {p: i for i, p in enumerate(POSK)}
CHONG = {frozenset(x) for x in [("子", "午"), ("丑", "未"), ("寅", "申"),
                                ("卯", "酉"), ("辰", "戌"), ("巳", "亥")]}
WX = {'子': '水', '亥': '水', '寅': '木', '卯': '木', '巳': '火', '午': '火',
      '申': '金', '酉': '金', '辰': '土', '戌': '土', '丑': '土', '未': '土'}
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}


def simulate(zlis, month_wx):
    """按 relations 语义枚举该盘每柱收到的所有 CHONG 写入, 检出冲突"""
    writes = collections.defaultdict(list)   # pos -> [(role, adj, by, lib)]
    # 原局实例(i<j)
    for i in range(4):
        for j in range(i + 1, 4):
            a, b = zlis[i], zlis[j]
            if frozenset((a, b)) not in CHONG:
                continue
            wa, wb = WX[a], WX[b]
            if WX_KE.get(wa) == wb:
                ka, kb = 'ACTIVE', 'PASSIVE'
            elif WX_KE.get(wb) == wa:
                ka, kb = 'PASSIVE', 'ACTIVE'
            else:
                ka, kb = 'BROTHER', 'BROTHER'
            pa, pb = POSK[i], POSK[j]
            if ka == 'BROTHER':
                writes[pa].append(('BROTHER_CHONG', 0, b, True))
                writes[pb].append(('BROTHER_CHONG', 0, a, True))
                continue
            cf_p, bc_p, cf_z, bc_z = (pa, pb, a, b) if ka == 'ACTIVE' else (pb, pa, b, a)
            writes[cf_p].append(('CHONG_ACTIVE', 0, bc_z, False))
            # _compare_both 复刻
            def ling(w):
                if w == month_wx: return '旺'
                sh = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
                if sh[month_wx] == w: return '相'
                if sh[w] == month_wx: return '休'
                if WX_KE[w] == month_wx: return '囚'
                return '死'
            lb, lc = ling(WX[bc_z]), ling(WX[cf_z])   # ★ 传五行, 不是支名
            adj = 1 if (lc in ('囚', '死') and lb in ('旺', '相')) else (
                -1 if (lc in ('旺', '相') and lb in ('囚', '死')) else 0)
            writes[bc_p].append(('CHONG_PASSIVE', adj, cf_z, False))
    return writes


def main():
    from engines.common.transit_power import BRANCH_WX
    st = collections.Counter()
    detail = []
    n165 = 0
    for bk in ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            zlis = [bz[1], bz[3], bz[5], bz[7]]
            cnt = collections.Counter(zlis)
            inst = [(i, j) for i in range(4) for j in range(i + 1, 4)
                    if frozenset((zlis[i], zlis[j])) in CHONG]
            if not inst:
                continue
            zh = {zlis[i] for i, _ in inst} | {zlis[j] for _, j in inst}
            if not any(cnt[z] >= 2 for z in zh):
                continue
            n165 += 1
            month_wx = BRANCH_WX[zlis[1]]
            w = simulate(zlis, month_wx)
            multi = {p: v for p, v in w.items() if len(v) >= 2}
            if not multi:
                st["①同柱多写但值全同(覆盖无损)"] += 1
                continue
            # 有同柱多写: 核值是否全同
            diffp = {p: v for p, v in multi.items() if len(set(v)) > 1}
            if diffp:
                st["★N_role_diff 覆盖有损"] += 1
                detail.append((d["case_id"], bz, "".join(zlis), diffp))
            else:
                st["②同柱多写值全同(覆盖无损)"] += 1
    print("=" * 96)
    print("坑③ 影响面   有重复支且参与真冲 = %d 盘" % n165)
    print("=" * 96)
    for k in sorted(st):
        print("  %-32s %5d" % (k, st[k]))
    print("\n  ★ N_role_diff = %d / %d" % (st["★N_role_diff 覆盖有损"], n165))
    print("\n  【前 5 盘明细】")
    for cid, bz, zs, dp in detail[:5]:
        print("\n  %s  %s  支(年月日时)=%s" % (cid, bz, zs))
        for p, v in dp.items():
            uniq = list(dict.fromkeys(v))
            print("    %-6s 收到 %d 次写入, %d 种不同值:" % (p, len(v), len(uniq)))
            for u in uniq:
                print("        role=%-14s adj=%-3s by=%-5s lib=%s   ×%d"
                      % (u[0], u[1], u[2], u[3], v.count(u)))
            print("        → 单值后写覆盖只留最后一条: %s"
                  % json.dumps(list(v[-1]), ensure_ascii=False))
    if not detail:
        print("    (无)")


if __name__ == "__main__":
    main()