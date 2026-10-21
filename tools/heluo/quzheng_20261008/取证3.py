# -*- coding: utf-8 -*-
import io

P = (r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
     r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt")
D = (r"D:\顺天系统资料\河洛理数_OCR\续修四库本_点校转写.txt")

a = io.open(P, encoding="utf-8", errors="replace").read().split("\n")
b = io.open(D, encoding="utf-8", errors="replace").read().split("\n")

O = io.open("取证_原文段.txt", "w", encoding="utf-8")
for tag, lo, hi in [("L474-480 纳表", 470, 482),
                    ("L490-518 反表", 490, 519),
                    ("L519-542 又云表", 519, 543),
                    ("L555-572 化工窗口", 555, 573),
                    ("L676-696 干支纳卦", 676, 697),
                    ("L724-736 数格", 724, 737)]:
    O.write("\n" + "═" * 72 + "\n【%s】\n" % tag)
    O.write("── 原著(A) ──\n")
    for i in range(lo - 1, min(hi, len(a))):
        t = a[i].strip()
        if t:
            O.write("L%-5d %s\n" % (i + 1, t))
    O.write("── 续修四库点校(D) 对应该段 ──\n")
    # D 本行号不同，按关键词找同段
    for i in range(0, len(b)):
        t = b[i].strip()
        if not t:
            continue
        if (tag.startswith("L474") and "壬甲戌亥" in t) or \
           (tag.startswith("L490") and "反天道" in t) or \
           (tag.startswith("L519") and "又云乾卦干主辛" in t) or \
           (tag.startswith("L555") and "坎卦自冬至" in t) or \
           (tag.startswith("L676") and "十二干支纳乾兑金卦" in t) or \
           (tag.startswith("L724") and "以强凌弱" in t):
            for j in range(i, min(i + 26, len(b))):
                if b[j].strip():
                    O.write("L%-5d %s\n" % (j + 1, b[j].strip()))
            O.write("   ⋯\n")
            break
O.close()
print("ok")