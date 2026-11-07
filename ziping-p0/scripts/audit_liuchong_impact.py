# -*- coding: utf-8 -*-
"""liuchong 消费者清单 + N_lost / N_cover 两数 + 兼容性矩阵(一份脚本四行输出)"""
import io, os, re, json, subprocess, collections

ROOT = r"D:/shuntian-ziping-p0"
BW = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
POS = ("year","month","day","hour")


# ── 1/2. 消费者清单 ──
def consumers():
    print("=" * 96)
    print("① liuchong 直接消费者 (engines/ + p0_v2/)")
    print("=" * 96)
    r = subprocess.run(["grep","-rn","liuchong","--include=*.py","engines","p0_v2"],
                       cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
    direct = [x for x in r if x.strip() and "_archive" not in x and "scripts" not in x]
    for x in direct:
        print("  " + x[:150])
    print("\n  → 直接消费者 %d 处, %d 个文件" % (
        len(direct), len({x.split(":")[0] for x in direct})))

    print("\n" + "=" * 96)
    print("② combination_facts 间接消费者")
    print("=" * 96)
    r2 = subprocess.run(["grep","-rn","combination_facts","--include=*.py","engines","p0_v2"],
                        cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
    ind = [x for x in r2 if x.strip() and "_archive" not in x and "scripts" not in x]
    for x in ind:
        print("  " + x[:150])
    print("\n  → 间接消费者 %d 处, %d 个文件" % (
        len(ind), len({x.split(":")[0] for x in ind})))
    return direct, ind


# ── 3. N_lost / N_cover ──
def measure():
    sys_path = ROOT
    import sys
    sys.path.insert(0, sys_path)
    _P0 = os.path.join(ROOT, "p0_v2")
    if _P0 in sys.path:
        sys.path.remove(_P0)
    from p0_v2.bazi_gate import paipan

    st = collections.Counter()
    ex_lost, ex_cover = [], []
    CHONG = {frozenset(x) for x in [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]}
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
            zlis = [bz[1], bz[3], bz[5], bz[7]]
            # 理论实例数 N×M (按支实例)
            inst = []
            for i in range(4):
                for j in range(i+1, 4):
                    if frozenset((zlis[i], zlis[j])) in CHONG:
                        inst.append((i, j))
            if not inst:
                continue
            try:
                r = paipan(bz)
            except Exception:
                st["崩溃"] += 1
                continue
            lc = ((r.get("raw_facts") or {}).get("combination_facts") or {}).get("liuchong") or []
            bc = (r.get("wangshuai_matrix") or {}).get("branch_chong") or {}
            # N_lost: 理论实例 > 引擎实际写入 branch_chong 的柱位对数
            written = set()
            for p, v in (bc or {}).items():
                if (v or {}).get("role") != "NO_CHONG":
                    written.add(p)
            # 引擎实际配出的对(用 _by_pos 首见口径独立复算)
            byz = {}
            for i, p in enumerate(POS):
                if zlis[i] not in byz:
                    byz[zlis[i]] = i
            eng_pairs = set()
            for pr in lc:
                a, b = pr[0], pr[1]
                ia, ib = byz.get(a), byz.get(b)
                if ia is None or ib is None or ia == ib:
                    continue
                eng_pairs.add(frozenset((ia, ib)))
            if len(inst) > len(eng_pairs):
                st["N_lost ★(实例>引擎配对)"] += 1
                if len(ex_lost) < 6:
                    ex_lost.append((d["case_id"], bz, zlis, len(inst), len(eng_pairs)))
            else:
                st["无丢失"] += 1
            # N_cover: 某柱位参与多个冲实例 但 branch_chong[pos] 单值只记一条
            cover = False
            pos_cnt = collections.Counter()
            for i, j in inst:
                pos_cnt[POS[i]] += 1
                pos_cnt[POS[j]] += 1
            if any(c >= 2 for c in pos_cnt.values()):
                cover = True
            if cover:
                st["N_cover ★(单柱多冲)"] += 1
                if len(ex_cover) < 6:
                    ex_cover.append((d["case_id"], bz, zlis, dict(pos_cnt)))
    return n, st, ex_lost, ex_cover


def main():
    d, i = consumers()
    n, st, ex_lost, ex_cover = measure()
    print("\n" + "=" * 96)
    print("③ N_lost / N_cover 六本 %d 盘" % n)
    print("=" * 96)
    for k in sorted(st):
        print("  %-26s %5d" % (k, st[k]))
    print("\n  N_lost 样本:")
    for e in ex_lost:
        print("    %-9s %-17s 支=%s 理论实例=%d 引擎配对=%d" % e)
    print("\n  N_cover 样本:")
    for e in ex_cover:
        print("    %-9s %-17s 支=%s 每柱冲次数=%s" % e)


if __name__ == "__main__":
    main()