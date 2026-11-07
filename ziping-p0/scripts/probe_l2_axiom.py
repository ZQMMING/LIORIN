# -*- coding: utf-8 -*-
"""探针 10: 五行生克表在六本中的使用一致性（AXIOM 成立与否）

★ 立规 2f: 报数前跑探针。本探针决定 AXIOM 分级能否成立。
方法: 六本底本中检索【显式生克表述】的句子, 逐句拆出「X生Y / X克Y」,
      与引擎 sheng/ke 表对撞。不一致 → AXIOM 不成立。

判定口径(结构标识优先):
  只认显式「X生Y」「X克Y」「X生X」这类【显式配对】;
  不从「母生子」「君赖臣生」等隐含表述反推 —— 那是关系不是次序。
"""
import io
import os
import re
import collections

ROOT = r"D:/shuntian-ziping-p0"
RAW = os.path.join(ROOT, "registries", "source", "raw")

CODE_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CODE_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

WX = "木火土金水"
# 显式配对: 两个字 + 生/克/制/化 + 一个字
RX = re.compile(r"([木火土金水])\s*(?:生|克|制)\s*([木火土金水])")


def main():
    print("=" * 100)
    print("探针 10  五行生克表在六本中的使用一致性")
    print("=" * 100)

    per_book = collections.defaultdict(lambda: {"sheng": [], "ke": []})
    for f in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, f)
        if not os.path.isfile(p):
            continue
        try:
            s = io.open(p, encoding="utf-8-sig", errors="ignore").read()
        except Exception:
            continue
        for i, l in enumerate(s.split("\n"), 1):
            if len(l) < 8:
                continue
            for m in RX.finditer(l):
                seg = l[max(0, m.start(1) - 1):m.end(2) + 1]
                mm = re.match(r"([木火土金水])\s*(生|克|制)\s*([木火土金水])", seg)
                if not mm:
                    continue
                a, op, b = mm.group(1), mm.group(2), mm.group(3)
                rec = (i, l.strip()[:74])
                if op == "生":
                    per_book[f]["sheng"].append((a, b, rec))
                else:
                    per_book[f]["ke"].append((a, b, rec))

    print("\n六本显式配对统计")
    print("-" * 100)
    print("%-44s %6s %6s" % ("底本", "生", "克"))
    for f, d in per_book.items():
        print("%-44s %6d %6d" % (f[:42], len(d["sheng"]), len(d["ke"])))
    total_s = sum(len(d["sheng"]) for d in per_book.values())
    total_k = sum(len(d["ke"]) for d in per_book.values())
    print("%-44s %6d %6d" % ("合计", total_s, total_k))

    # ── 一致性对撞 ──
    print("\n" + "=" * 100)
    print("与引擎 sheng / ke 表对撞")
    print("=" * 100)
    ok_s = collections.Counter()
    ok_k = collections.Counter()
    bad = []
    for f, d in per_book.items():
        for a, b, rec in d["sheng"]:
            exp = CODE_SHENG.get(a)
            if exp == b:
                ok_s[a] += 1
            else:
                bad.append(("生", f[:22], a, b, exp, rec))
        for a, b, rec in d["ke"]:
            exp = CODE_KE.get(a)
            if exp == b:
                ok_k[a] += 1
            else:
                bad.append(("克", f[:22], a, b, exp, rec))

    print("\n相生一致命中（按「源五行」）:")
    for a in WX:
        print("   %s生%s  引擎表=%s  六本一致命中 %d 处" % (a, CODE_SHENG[a],
                                                  CODE_SHENG[a], ok_s.get(a, 0)))
    print("\n相克一致命中（按「源五行」）:")
    for a in WX:
        print("   %s克%s  引擎表=%s  六本一致命中 %d 处" % (a, CODE_KE[a],
                                                  CODE_KE[a], ok_k.get(a, 0)))

    print("\n★ 不一致 %d 处" % len(bad))
    for t in bad[:24]:
        op, f, a, b, exp, rec = t
        print("   [%s] %-22s 原文「%s%s%s」 引擎表=「%s%s」  %s L%d"
              % (op, f, a, op, b, a, exp, rec[1], rec[0]))

    print("\n" + "=" * 100)
    # 探针判据: 五行生克 10 对是否在六本中【全部】有至少一处一致使用
    covered_s = {a for a in WX if ok_s.get(a, 0) > 0}
    covered_k = {a for a in WX if ok_k.get(a, 0) > 0}
    miss_s = set(WX) - covered_s
    miss_k = set(WX) - covered_k
    print("相生 5 源被六本覆盖 = %d/5   缺: %s" % (len(covered_s), sorted(miss_s) or "无"))
    print("相克 5 源被六本覆盖 = %d/5   缺: %s" % (len(covered_k), sorted(miss_k) or "无"))
    print("\n探针 10 判定: %s"
          % ("★ PASS —— 十对全部有六本一致使用, AXIOM 成立"
             if not miss_s and not miss_k else
             "★ FAIL —— 覆盖不全, AXIOM 立不住, 须核缺口 %s/%s"
             % (sorted(miss_s), sorted(miss_k))))


if __name__ == "__main__":
    main()