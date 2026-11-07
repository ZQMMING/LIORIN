# -*- coding: utf-8 -*-
"""裁七十四丙: 255 盘日主向样本在 support_state 三档上的分布

★ 独立进程跑(禁 execute_code 持久 kernel)。
★ 目的: 反标定能不能用 support_state 当唯一输入(裁七十五甲)——
  先看三档分布够不够, 不够则该维度不成立。

样本来源: 六本案例库中「断语对象是日主」的盘(核2 实测 255 盘)
  判据: 逐句切分后, 词所在句的左窗(12字)含日主指称 或 词本身以「身」开头
"""
import sys, os, json, re, collections
ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from p0_v2.bazi_gate import paipan

CA = os.path.join(ROOT, "p0_v2", "case_audit")
BOOKS = ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]

SPLIT = re.compile(r"[。；\n]")
NON_SUBJ = ["财", "官", "杀", "印", "食", "伤", "比", "劫", "财官", "印绶",
            "木", "火", "土", "金", "水", "地", "天", "气", "元", "用神", "喜", "忌",
            "财星", "官星", "食神", "伤官", "印绶", "比肩", "劫财"]

# 断语 -> 目标档
WORDS = [
    ("STRONG", ("身旺", "身强", "日元旺", "日主旺", "得时为旺")),
    ("WEAK",   ("身弱", "身衰", "日元弱", "日主弱")),
    ("EXTREME_STRONG", ("太旺", "旺极", "旺之极")),
    ("EXTREME_WEAK",   ("衰极", "衰之极", "弱极")),
    ("NEUTRAL", ("中和",)),
    ("PARTIAL", ("偏旺", "偏枯", "偏强")),
]


def classify(sent, word):
    """断语对象 = 日主? 返回 (是否日主, 理由)"""
    i = sent.find(word)
    if i < 0:
        return False, "?"
    left = sent[:i]
    lw = left[-12:]
    if any(x in lw for x in ["日元", "日主", "日干"]):
        return True, "左窗含日主指称"
    if word.startswith("身") and word in ("身旺", "身弱", "身衰", "身强"):
        return True, "词本身即身X"
    if any(x in lw for x in NON_SUBJ):
        return False, "左窗含非日主指称"
    return False, "左窗无指称(不计入)"


def main():
    # 1) 收集日主向样本
    samples = {}   # case_id -> (book, bazi, label, 断语, 理由)
    for bk in BOOKS:
        fp = os.path.join(CA, "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            txt = " ".join(str(d.get(k) or "") for k in
                           ("analysis", "raw", "liu_annotation"))
            for s in [x for x in SPLIT.split(txt) if x.strip()]:
                for label, words in WORDS:
                    hit = None
                    for w in words:
                        if w in s:
                            hit = w
                            break
                    if not hit:
                        continue
                    ok, why = classify(s, hit)
                    if ok and d["case_id"] not in samples:
                        samples[d["case_id"]] = (bk, d["bazi"], label, hit, why)
                    break

    print("=" * 96)
    print("裁七十四丙  日主向样本 × support_state 三档分布")
    print("=" * 96)
    print("日主向样本 = %d 盘（核2 实测 255，含一盘多标签取首个）" % len(samples))

    # 2) 跑引擎取 support_state
    dist = collections.Counter()
    cross = collections.defaultdict(collections.Counter)
    n = 0
    miss = 0
    for cid, (bk, bazi, label, word, why) in samples.items():
        bz = (bazi or "").replace(" ", "")
        if len(bz) != 8:
            miss += 1
            continue
        n += 1
        lc = (paipan(bz).get("l3_contract") or {})
        ss = lc.get("support_state") or "MISSING"
        dist[ss] += 1
        cross[label][ss] += 1

    print("有效跑盘 = %d（四柱不合跳过 %d）" % (n, miss))

    print("\n【support_state 三档分布】")
    TOT = {"SHENG_FU_CHENG_SHI": "同党成势", "KE_XIE_CHENG_SHI": "异党成势",
           "PINGHENG": "平横"}
    for k in ["SHENG_FU_CHENG_SHI", "KE_XIE_CHENG_SHI", "PINGHENG"]:
        print("    %-22s %-6s %5d  (%.1f%%)"
              % (k, TOT.get(k, ""), dist[k], dist[k] * 100.0 / n))
    if dist["MISSING"]:
        print("    MISSING %d" % dist["MISSING"])

    print("\n【断语档 × support_state 三档 交叉表】")
    cols = ["SHENG_FU_CHENG_SHI", "KE_XIE_CHENG_SHI", "PINGHENG"]
    print("    %-16s %s" % ("断语档", "".join("%22s" % c[:20] for c in cols)))
    for lb in ["STRONG", "WEAK", "EXTREME_STRONG", "EXTREME_WEAK", "NEUTRAL", "PARTIAL"]:
        row = cross.get(lb)
        if not row:
            continue
        tot = sum(row.values())
        print("    %-16s %s   小计%d" % (lb, "".join("%22d" % row[c] for c in cols), tot))

    print("\n【关键: 各 support_state 档内的断语构成 —— 相关性有多强】")
    for c in cols:
        tot = dist[c]
        if not tot:
            continue
        comp = collections.Counter()
        for lb, row in cross.items():
            comp[lb] = row[c]
        top = comp.most_common(3)
        print("\n    %s (%d 盘):" % (c, tot))
        for lb, v in top:
            print("        %-18s %4d  (%.1f%% of 档内)" % (lb, v, v * 100.0 / tot))

    print("\n【结论判据】")
    mn = min(dist[c] for c in cols if dist[c]) if any(dist[c] for c in cols) else 0
    if all(dist[c] >= 30 for c in cols):
        print("    甲: 三档各 ≥30 盘 → 一维 support_state 反标定【可行】")
    elif mn < 10:
        print("    乙: 最小档 %d <10 盘 → 该档样本不足" % mn)
    else:
        print("    丙: 三档均有样本但非均匀(最小 %d) → 需看档内断语构成再定" % mn)


if __name__ == "__main__":
    main()