# -*- coding: utf-8 -*-
"""FAN_JU 阈值反标定 —— 取全部原文提反局的盘, 抄断语+取实值

不预设阈值, 只观测: 原文说触发时, 我/克我者/生我者/我生者 各是多少。
"""
import sys, os, json, re, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]
KW = {
    '君赖臣生': ['君赖臣生', '水泛木浮', '土重金埋', '木旺火炽', '火旺土焦', '金旺则水浊'],
    '儿能救母': ['儿能救母', '儿能生母'],
    '母慈灭子': ['母慈灭子', '慈母', '灭子', '灭母'],
    '夫健怕妻': ['夫健', '怕妻'],
}
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
SHENG_BACK = {'木': '水', '火': '木', '土': '火', '金': '土', '水': '金'}
KE_BACK = {'木': '金', '火': '水', '土': '木', '金': '火', '水': '土'}


def mass(facts, wx):
    if not wx:
        return 0
    wp = (facts.get('wuxing_power') or {}).get('wuxing_power') or {}
    row = wp.get(wx) or {}
    return (int(row.get('ben_n', 0) or 0) + int(row.get('zhong_n', 0) or 0)
            + int(row.get('yu_n', 0) or 0) + int(row.get('stem_n', 0) or 0))


def main():
    # 收集全部原文提反局的盘
    rows = []
    for bk in BOOKS:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            raw = (d.get("raw") or "") + (d.get("liu_annotation") or "")
            tags = []
            for jl, kws in KW.items():
                if any(k in raw for k in kws):
                    tags.append(jl)
            if tags:
                rows.append((bk, d["case_id"], bz, tags, raw))
    print("原文提反局的盘: %d" % len(rows))
    print("  分布: %s" % dict(collections.Counter(t for _, _, _, ts, _ in rows for t in ts)))

    obs = collections.defaultdict(list)   # 反局名 -> [(我, 克我, 生我, 我生, cid)]
    for bk, cid, bz, tags, raw in rows:
        try:
            r = paipan(bz)
        except Exception:
            continue
        f = r.get("raw_facts") or {}
        dm = bz[4]
        dwx = GAN_WX.get(dm, "")
        m_dm = mass(f, dwx)
        m_chen = mass(f, KE_BACK.get(dwx, ""))
        m_yin = mass(f, SHENG_BACK.get(dwx, ""))
        m_zi = mass(f, SHENG.get(dwx, ""))
        fj = (r.get("l3_contract") or {}).get("fan_ju") or {}
        eng = set(fj.get("types") or [])
        for t in tags:
            obs[t].append((m_dm, m_chen, m_yin, m_zi, cid, t in eng))

    for t in ("君赖臣生", "儿能救母", "母慈灭子", "夫健怕妻"):
        v = obs.get(t) or []
        print("\n" + "=" * 92)
        print("【%s】原文提及 %d 盘" % (t, len(v)))
        print("  %-9s %-17s %4s %4s %4s %4s  %s" % ("case", "bazi", "我", "克我", "生我", "我生", "引擎触发"))
        for m_dm, m_chen, m_yin, m_zi, cid, ok in v[:26]:
            print("  %-9s %-17s %4d %4d %4d %4d  %s"
                  % (cid, "", m_dm, m_chen, m_yin, m_zi, "✓" if ok else "✗"))
        if v:
            print("  --- 实值范围 ---")
            for idx, nm in ((0, "我"), (1, "克我"), (2, "生我"), (3, "我生")):
                vals = [x[idx] for x in v]
                print("    %-4s min=%d max=%d 平均=%.1f  分布=%s"
                      % (nm, min(vals), max(vals), sum(vals) / len(vals),
                         dict(sorted(collections.Counter(vals).items()))))
            print("  引擎触发 %d/%d" % (sum(1 for x in v if x[5]), len(v)))


if __name__ == "__main__":
    main()