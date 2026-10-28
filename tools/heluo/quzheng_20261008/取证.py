# -*- coding: utf-8 -*-
"""多本本地转录本交叉取证。

对每条待证项，在**每一本**可用转录里找对应句子，打印命中行，
让人眼裁决「同一句在各本是否一致」。单本无法定谳，多本一致才可采信。
"""
import io
import os
import re

SRC = {
    "A_原著(在用)": r"C:\Users\ming\.minimax\v2\assets\2026\10\06"
                     r"\22-08-20-122-asset_20261006-220820-122_67b40448a1e6_07333092-河洛真数——原著.txt",
    "B_D盘原著": r"D:\顺天系统资料\河洛真数——原著.txt",
    "C_河洛真数OCR": r"D:\顺天系统资料\河洛真数OCR.txt",
    "D_续修四库点校": r"D:\顺天系统资料\河洛理数_OCR\续修四库本_点校转写.txt",
    "E_河洛数待整理": r"D:\顺天系统资料\河洛数待整理.txt",
    "F_河洛理数总集": r"D:\顺天系统资料\河洛理数-总集.md",
}

OUT = io.open("取证_交叉核对.txt", "w", encoding="utf-8")

TEXTS = {}
for k, p in SRC.items():
    if os.path.exists(p):
        TEXTS[k] = io.open(p, encoding="utf-8", errors="replace").read().split("\n")
    else:
        OUT.write("【缺失】%s → %s\n" % (k, p))
OUT.write("可用转录本：%s\n\n" % "、".join(TEXTS))

# 允许中间夹标点/空白：把 needle 拆成字符，匹配时用 .*? 连接
CASES = [
    ("待证A-1", "乾卦元气干支（L474 一套）", ["乾", "甲", "戌", "亥"]),
    ("待证A-2", "乾卦干主辛（L519 一套）", ["乾卦干主辛"]),
    ("待证A-3", "巽卦元气辛辰巳（L477 一套）", ["巽", "辛", "辰", "巳"]),
    ("待证A-4", "巽卦干主壬甲（L540 一套）", ["巽卦干主壬甲"]),
    ("待证A-5", "坤反壬甲戌亥（L498）", ["坤反", "壬", "甲", "戌", "亥"]),
    ("讹字1", "震反辛辰己/巳（L507）", ["震反辛辰"]),
    ("讹字2", "以强凌弱（L729）", ["以强凌弱"]),
    ("讹字3", "以下犯上（L732）", ["以下犯上"]),
    ("讹字4", "冬至以后夏至前 / 冬水（L732）", ["冬至以后夏至前"]),
    ("讹字5", "水为智（L105）", ["水为智"]),
    ("讹字6", "木为智（L105 异读）", ["木为智"]),
    ("待证C", "更元堂安非其位（L726）", ["元堂安非其位"]),
    ("可实现1", "元气相反·乾（L495）", ["乾反", "夭寿"]),
    ("可实现2", "元气相反·坎（L513）", ["坎反", "聋"]),
    ("可实现3", "干支纳乾兑金卦（L681）", ["十二干支纳", "乾兑金卦"]),
    ("可实现4", "坎化工窗口（L558）", ["坎卦自冬至"]),
    ("可实现5", "坤艮各旺十八日（L570）", ["各旺十八日"]),
    ("可实现6", "爻辞取象 言龙（L741）", ["言龙则必贵"]),
]


def probe(lines, chars, span=6):
    """找出含全部 chars（允许间隔 <=span 个非空字符）的行。"""
    pat = ".{0,%d}?" % span + ".{0,%d}?" % span
    pat = pat.join(re.escape(c) for c in chars)
    rx = re.compile(pat)
    return [(i + 1, l.strip()) for i, l in enumerate(lines) if rx.search(l)]


for tag, title, chars in CASES:
    OUT.write("═" * 78 + "\n")
    OUT.write("【%s】%s\n" % (tag, title))
    any_hit = False
    for name, lines in TEXTS.items():
        hits = probe(lines, chars)
        if hits:
            any_hit = True
            OUT.write("  ── %s（%d 处）\n" % (name, len(hits)))
            for ln, text in hits[:4]:
                t = text if len(text) <= 150 else text[:150] + "…"
                OUT.write("     L%-6d %s\n" % (ln, t))
    if not any_hit:
        OUT.write("  ⚠ 各本均零命中\n")

OUT.close()
print("done ->", os.path.abspath("取证_交叉核对.txt"))