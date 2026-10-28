# -*- coding: utf-8 -*-
"""從財格/從殺格判定（SFTK A級原文）"""
import sys, json
sys.path.insert(0, r'engines\common')
from gc002_builder import paipan, HIDDEN  # 已 wrap stdout

ELEM = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土',
        '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
GAN = '甲乙丙丁戊己庚辛壬癸'
BENQI = {k: v[0] for k, v in HIDDEN.items()}
gen = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}


def _ten_lists(day):
    de = ELEM[day]
    me_ke = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '木'}[de]
    yang_day = GAN.index(day) % 2 == 0
    def _li(elem, same):
        return [s for s in GAN if ELEM[s] == elem and (GAN.index(s) % 2 == 0) == same]
    return {
        'sha': _li(me_ke, yang_day), 'guan': _li(me_ke, not yang_day),
        'cai': [s for s in GAN if ELEM[s] == ke[de]],
        'shi_shang': [s for s in GAN if ELEM[s] == gen[de]],
        'cai_elem': ke[de],
    }


def dm_rootless(day, branches):
    """日主无根：四支藏干中无日主五行"""
    de = ELEM[day]
    return all(ELEM[h] != de for b in branches.values() for h in HIDDEN[b])


def no_shengfu(day, stems):
    """天干无印无比劫（从格铁律）"""
    de = ELEM[day]
    ke_me = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}[de]  # 生我=印
    return all(ELEM[s] not in (de, ke_me) for i, s in enumerate(stems.values()) if i != 2)


def cong_cai(c):
    """從財格（SFTK-020-002 A）：日主无根无生扶+财星成势"""
    day = c["day_master"]; stems = c["stems"]; branches = c["branches"]
    tl = _ten_lists(day)
    benqi = BENQI[c["month_branch"]]
    rootless = dm_rootless(day, branches)
    no_fu = no_shengfu(day, stems)
    cai_dangling = benqi in tl["cai"]                       # 月令财当令
    cai_vis = any(i != 2 and stems[s] in tl["cai"] for i, s in enumerate(stems))
    cai_root = any(ELEM[h] == tl["cai_elem"] for b in branches.values() for h in HIDDEN[b])
    if rootless and no_fu and cai_dangling and (cai_vis or cai_root):
        return {"pattern_state": "DETERMINED(從財格)",
                "pattern_success_state": "SUCCESS(棄命從財)",
                "condition_context": "日主无根无生扶，财星成势",
                "evidence": ["SFTK-020-002"], "note": "從財格成：舍命從財；忌身旺印運"}
    return None


def cong_sha(c):
    """從殺格（SFTK-012-002 A）：日主无根无食制+官杀成势"""
    day = c["day_master"]; stems = c["stems"]; branches = c["branches"]
    tl = _ten_lists(day)
    benqi = BENQI[c["month_branch"]]
    rootless = dm_rootless(day, branches)
    no_fu = no_shengfu(day, stems)
    sha_dangling = benqi in tl["sha"] or benqi in tl["guan"]   # 月令官杀当令
    shang_vis = any(i != 2 and stems[s] in tl["shi_shang"] for i, s in enumerate(stems))  # 食伤制杀
    sha_root = any(ELEM[h] in [ELEM[g] for g in (tl["sha"] + tl["guan"])] for b in branches.values() for h in HIDDEN[b])
    if rootless and no_fu and sha_dangling and not shang_vis and sha_root:
        return {"pattern_state": "DETERMINED(從殺格)",
                "pattern_success_state": "SUCCESS(棄命從殺)",
                "condition_context": "日主无根无食制，官杀成势",
                "evidence": ["SFTK-012-002"], "note": "從殺格成：舍命從殺；忌根運制殺運"}
    return None


if __name__ == "__main__":
    # 扫描從財/從殺命局（1990-1996 全月全时辰）
    cai_hits, sha_hits = [], []
    for y in range(1990, 1997):
        for m in range(1, 13):
            for h in range(0, 24, 2):
                p = paipan(y, m, 15, h)
                stems = {"年": p["stems"]["年"], "月": p["stems"]["月"], "日": p["day_master"], "时": p["stems"]["时"]}
                c = {"day_master": p["day_master"], "month_branch": p["month_order"],
                     "stems": stems, "branches": p["branches"]}
                r1 = cong_cai(c)
                if r1:
                    cai_hits.append((y, m, h, p["pillars"], p["day_master"]))
                r2 = cong_sha(c)
                if r2:
                    sha_hits.append((y, m, h, p["pillars"], p["day_master"]))
    print("==== 從財格候選 ====")
    for y, m, h, pl, dm in cai_hits[:5]:
        print(f"  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}")
    print(f"  共 {len(cai_hits)} 个\n")
    print("==== 從殺格候選 ====")
    for y, m, h, pl, dm in sha_hits[:5]:
        print(f"  {y}-{m}-15 {h:02d}:00  {pl}  日主={dm}")
    print(f"  共 {len(sha_hits)} 个")
