# -*- coding: utf-8 -*-
"""裁七十六丙(修正): 区分度改用【样本量加权】指标

★ 上一版指标的缺陷(实测):
  max over v |p(WANG)-p(SHUAI)| —— 极稀疏值天然得 1.000
    root_grade='余' 只有 3 盘 (3W/0S) → p差=1.000 但无统计意义
    dm_ben_eff=4 只有 2 盘 (2W/0S) → 同上
    yin_ben_eff=4 只有 3 盘 → 同上
  → 榜单被噪声占满, 掩盖了样本充足时的真实区分力。

修正: 只在 样本数 >= MIN_N 的值上取 max, 另报「二元切分准确率」。
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
FIELDS = ["ling_state", "root_grade", "dm_ben_eff", "yin_ben_eff",
          "de_ling", "de_di", "dang_duo", "support_state"]
MIN_N = 20

SPLIT = re.compile(r"[。；\n]")
NON_SUBJ = ["财", "官", "杀", "印", "食", "伤", "比", "劫", "财官", "印绶",
            "木", "火", "土", "金", "水", "地", "天", "气", "元", "用神", "喜", "忌",
            "财星", "官星", "食神", "伤官", "印绶", "比肩", "劫财"]
WORDS = [
    ("NEUTRAL", ("中和",)),
    ("WANG", ("身旺", "身强", "日元旺", "日主旺", "得时为旺",
              "太旺", "旺极", "旺之极", "偏旺", "偏枯", "偏强")),
    ("SHUAI", ("身弱", "身衰", "日元弱", "日主弱",
               "衰极", "衰之极", "弱极", "太弱")),
]


def classify(sent, word):
    i = sent.find(word)
    if i < 0:
        return False
    lw = sent[:i][-12:]
    if any(x in lw for x in ["日元", "日主", "日干"]):
        return True
    if word.startswith("身") and word in ("身旺", "身弱", "身衰", "身强"):
        return True
    if any(x in lw for x in NON_SUBJ):
        return False
    return False


def collect():
    out = {}
    for bk in BOOKS:
        for line in open(os.path.join(CA, "%s_clean.jsonl" % bk),
                         encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            txt = " ".join(str(d.get(k) or "") for k in
                           ("analysis", "raw", "liu_annotation"))
            for s in [x for x in SPLIT.split(txt) if x.strip()]:
                for label, words in WORDS:
                    hit = next((w for w in words if w in s), None)
                    if not hit:
                        continue
                    if classify(s, hit) and d["case_id"] not in out:
                        out[d["case_id"]] = (bk, d["bazi"], label)
                    break
    return out


def main():
    samples = collect()
    rows = []
    for cid, (bk, bazi, label) in samples.items():
        bz = (bazi or "").replace(" ", "")
        if len(bz) != 8 or label == "NEUTRAL":
            continue
        lc = paipan(bz).get("l3_contract") or {}
        rows.append((label, {f: lc.get(f) for f in FIELDS}))
    W = sum(1 for r in rows if r[0] == "WANG")
    S = len(rows) - W
    print("=" * 100)
    print("裁七十六丙(修正)  区分度 · 样本量加权版   WANG %d / SHUAI %d" % (W, S))
    print("=" * 100)
    print("★ 只在 样本数 >= %d 的值上取 max(上一版被 2~3 盘的稀疏值刷榜)" % MIN_N)

    print("\n%-18s %-9s %6s %6s %6s %8s %s" %
          ("字段", "值", "WANG", "SHUAI", "总", "p差", "计入?"))
    print("-" * 100)
    scores = {}
    for f in FIELDS:
        byval = collections.defaultdict(lambda: {"W": 0, "S": 0})
        for lab, d in rows:
            v = d[f]
            if lab == "WANG":
                byval[v]["W"] += 1
            else:
                byval[v]["S"] += 1
        best = 0.0
        best_v = None
        for v in sorted(byval, key=lambda x: str(x)):
            c = byval[v]
            tot = c["W"] + c["S"]
            pw = c["W"] / tot if tot else 0
            ps = c["S"] / tot if tot else 0
            ok = "✓" if tot >= MIN_N else "✗稀疏"
            print("%-18s %-9s %6d %6d %6d %+8.3f %s"
                  % (f, str(v)[:8], c["W"], c["S"], tot, pw - ps, ok))
            if tot >= MIN_N and abs(pw - ps) > abs(best):
                best = pw - ps
                best_v = v
        scores[f] = (abs(best), best_v, best)

    print("\n" + "=" * 100)
    print("【区分度排序】(样本量加权: 只看样本数>=%d 的值)" % MIN_N)
    print("=" * 100)
    for f, (sc, v, d) in sorted(scores.items(), key=lambda kv: -kv[1][0]):
        print("  %-18s %.3f  %-20s 最优值=%s (p差=%+.3f)"
              % (f, sc, "█" * int(sc * 20), str(v)[:14], d))

    print("\n" + "=" * 100)
    print("【二元切分准确率】以各字段的最优值为界, 判 WANG/SHUAI")
    print("=" * 100)
    acc = []
    for f in FIELDS:
        sc, v, _ = scores[f]
        if v is None:
            print("  %-18s 无样本充足的值" % f)
            continue
        best = None
        for direction in (0, 1):
            hit = 0
            for lab, d in rows:
                val = d[f]
                try:
                    num = float(val)
                except (TypeError, ValueError):
                    num = None
                if num is not None:
                    pred = "WANG" if ((num > float(v)) == (direction == 0)) else "SHUAI"
                else:
                    pred = "WANG" if ((str(val) == str(v)) == (direction == 1)) else "SHUAI"
                hit += (pred == lab)
            r = hit / len(rows)
            if best is None or r > best[0]:
                best = (r, direction)
        acc.append((f, best[0]))
        print("  %-18s 阈值=%-10s 准确率 %.1f%%" % (f, str(v)[:12], best[0] * 100))
    acc.sort(key=lambda x: -x[1])
    base = W * 100.0 / len(rows)
    print("\n  ★ 最佳: %s  %.1f%%" % (acc[0][0], acc[0][1] * 100))
    print("  ★ 基线(全判多数类 WANG): %.1f%%" % base)
    print("  ★ 提升: %+.1f 个百分点" % (acc[0][1] - base))


if __name__ == "__main__":
    main()