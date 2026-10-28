# -*- coding: utf-8 -*-
"""第二轮取证：把第一轮的疑点钉死。"""
import io
import os
import re

SRC = {
    "A_原著(在用)": r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
                     r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
    "C_河洛真数OCR": r"D:\顺天系统资料\河洛真数OCR.txt",
    "D_续修四库点校": r"D:\顺天系统资料\河洛理数_OCR\续修四库本_点校转写.txt",
    "E_河洛数待整理": r"D:\顺天系统资料\河洛数待整理.txt",
}
T = {}
for k, p in SRC.items():
    T[k] = io.open(p, encoding="utf-8", errors="replace").read().split("\n")

OUT = io.open("取证_交叉核对2.txt", "w", encoding="utf-8")


def show(title, needles, span=12, limit=6):
    OUT.write("\n" + "═" * 78 + "\n【%s】\n" % title)
    for k, lines in T.items():
        rx = re.compile(pat_of(needles, span))
        hits = [(i + 1, l.strip()) for i, l in enumerate(lines) if rx.search(l)]
        if hits:
            OUT.write("  ── %s（%d 处）\n" % (k, len(hits)))
            for ln, t in hits[:limit]:
                OUT.write("     L%-5d %s\n" % (ln, t if len(t) <= 190 else t[:190] + "…"))
    if not any(re.search(pat_of(needles, span), "\n".join(l)) for l in T.values()):
        OUT.write("  ⚠ 各本零命中\n")


def pat_of(needles, span):
    return (".{0,%d}?" % span).join(re.escape(c) for c in needles)


# ① L732 完整句：各本到底作「水以后」还是「冬水以后」
show("① L732 完整句（以卑逾尊之后）", ["以卑逾尊", "最恶下贱"], 26)
# ② 「又云」在全书出现几次——确认 L519 段确是「另有一说」
show("② 「又云」全书分布", ["又云", "相反"], 20, 12)
# ③ 元堂「安位 / 非其位 / 得位」是否有定义条文
show("③ 元堂安位/非其位 判据", ["元堂", "位"], 4, 14)
# ④ 以强伏弱（已实现那条）的原文
show("④ 以强伏弱 卷之中", ["以强伏弱"], 30)
# ⑤ 以强凌弱/以下犯上 前后文（有无并列小标题）
show("⑤ L729 上下文", ["名以强凌弱"], 60)
# ⑥ 元气相反表完整八条（逐条抓）
for g, zhi, sym in [("乾", "乙癸未申", "夭寿"), ("坤", "壬甲戌亥", "贫贱"),
                    ("艮", "丁酉", "瘫疽"), ("兑", "丙丑寅", "缺唇"),
                    ("震", "辛辰", "跛"), ("巽", "庚卯", "痼疾"),
                    ("坎", "己午", "聋"), ("离", "戊子", "瞽眇")]:
    show("⑥ 元气相反·%s（反%s/%s）" % (g, zhi, sym), [g + "反", zhi[:2], sym], 4, 3)
# ⑦ 干支纳卦五组，逐条
for zhi, gua in [("乾兑金卦", "金"), ("坎水卦", "水"), ("离火卦", "火"),
                 ("坤艮土卦", "土"), ("震巽木卦", "木")]:
    show("⑦ 干支纳%s" % gua, ["十二干支纳", gua], 14, 3)
# ⑧ 四正卦化工窗口逐条
for g in ("坎", "震", "离", "兑"):
    show("⑧ %s卦自X至Y终止" % g, [g + "卦自"], 22, 3)
# ⑨ 爻辞取象三组带条件的完整句
show("⑨ 言龙+二月至八月", ["言龙则必贵", "二月至八月"], 14, 3)
show("⑩ 言木生春夏", ["言木", "春夏"], 14, 3)
show("⑪ 言月生望前", ["言月生望前"], 14, 3)
OUT.close()
print("done")