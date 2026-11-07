# -*- coding: utf-8 -*-
"""基准集构建: EXTREME_WEAK 11 盘 + 反向验证 4 盘(不作旺论)

分类口径(严格按语境, 不按关键词):
  EXTREME_WEAK  「衰之极者不可益」 DTS L235 的案例体现
                —— 必须指向【日主】衰极, 不能是「某五行衰极」
  反向验证      「不作旺论」/「强旺…不作旺论」
                —— DTS L245「不必论当令不令」的案例体现(有令但不旺)
  EXTREME_STRONG 不入基准集(值域已否决, 见契约 §x)
"""
import sys, os, json, re, collections
ROOT = r"D:/shuntian-ziping-p0"
# ★ 输出目录 p0_v2/baseline/ 而非 p0_v2/case_audit/:
#   case_audit/ = 六本案例【输入数据】(不可改动的源数据, .gitignore 排除)
#   baseline/   = 引擎【产物/基准】(可迭代, 进 git)
#   两者混在一处是边界污染 —— 基准集是我们构建的, 不是输入。
OUT = os.path.join(ROOT, "p0_v2", "baseline", "strength_baseline.jsonl")

# 衰极: 关键词 + 必须含「日主/天/身」等主体指向, 排除「某五行衰极」
WEAK_KW = ["衰极", "衰之极"]
STRONG_NEG = ["不作旺论", "不作成旺", "不得旺"]


def classify(cid, bz, txt):
    """返回 (类别, 命中词, 上下文)"""
    out = []
    for kw in STRONG_NEG:
        if kw in txt:
            i = txt.find(kw)
            out.append(("REVERSE_NOT_WANG", kw,
                        txt[max(0, i - 45):i + 35].replace("\n", " ")))
    for kw in WEAK_KW:
        for m in re.finditer(kw, txt):
            ctx = txt[max(0, m.start() - 45):m.start() + 35].replace("\n", " ")
            # ★ 主体判定收紧: 只认【日主/日元/日干/天(干)/身】指向衰极
            #   排除「某五行衰极」(木/水/金/时支…衰极) —— 那是五行自身, 非日主旺衰档
            #   反例: DT-0105「木衰极者」DT-0117「金衰极者」DT-0121「水衰极者」
            #        DT-0402「时支子水衰极」 → 四盘全部排除
            subj = any(w in ctx for w in ["日主", "日元", "日干", "天衰", "身衰", "身弱"])
            # 且必须排除「五行字 + 衰极」句式
            elem_weak = re.search(r"[木火土金水][衰之]?极", ctx)
            if subj and not elem_weak:
                out.append(("EXTREME_WEAK", kw, ctx))
    return out


def main():
    rows = []
    st = collections.Counter()
    for bk in ["DTS", "PZZQ", "YHZP", "QTBJ", "SFTK", "SMTH"]:
        fp = os.path.join(ROOT, "p0_v2", "case_audit", "%s_clean.jsonl" % bk)
        for line in open(fp, encoding="utf-8-sig"):
            if not line.strip():
                continue
            d = json.loads(line)
            bz = (d.get("bazi") or "").replace(" ", "")
            if len(bz) != 8:
                continue
            txt = str(d.get("analysis") or "") + " " + str(d.get("raw") or "")
            hits = classify(d["case_id"], bz, txt)
            if not hits:
                continue
            seen = set()
            for cat, kw, ctx in hits:
                key = (cat, kw)
                if key in seen:
                    st["%s(%s) 多处" % (cat, kw)] += 1
                    continue
                seen.add(key)
                st[cat] += 1
                rows.append({
                    "case_id": d["case_id"], "bazi": bz, "book": d.get("book"),
                    "category": cat, "keyword": kw, "context": ctx,
                    "label": d.get("label"), "verdict": d.get("verdict"),
                })
    # 去重: 同 case 同 category 只留一条
    uniq = {}
    for r in rows:
        uniq.setdefault((r["case_id"], r["category"]), r)
    final = sorted(uniq.values(), key=lambda x: (x["category"], x["case_id"]))
    with open(OUT, "w", encoding="utf-8") as f:
        for r in final:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("=" * 96)
    print("基准集构建   输出 %s" % OUT)
    print("=" * 96)
    c = collections.Counter(r["category"] for r in final)
    for k in sorted(c):
        print("  %-22s %3d 盘" % (k, c[k]))
    print("  %-22s %3d 盘" % ("TOTAL", len(final)))
    print("\n  命中统计(含多处):")
    for k in sorted(st):
        print("    %-30s %3d" % (k, st[k]))
    print("\n【EXTREME_WEAK 明细】")
    for r in final:
        if r["category"] == "EXTREME_WEAK":
            print("  %-9s %-17s [%s] …%s…" % (r["case_id"], r["bazi"], r["keyword"], r["context"]))
    print("\n【反向验证 REVERSE_NOT_WANG 明细】")
    for r in final:
        if r["category"] == "REVERSE_NOT_WANG":
            print("  %-9s %-17s [%s] …%s…" % (r["case_id"], r["bazi"], r["keyword"], r["context"]))


if __name__ == "__main__":
    main()