# -*- coding: utf-8 -*-
"""六部经典 × 底层维度 交叉矩阵检索 —— 纯字符串, 不用 AI

规则(准神优先):
  底层维度 = DTS(刘基原注, 准神) 有明文 + 至少一本旁证同向
  单本出现的不入底层。 "?" 一律当"未核", 检索后消掉。

输出: dimension_cross_matrix.md  (维度 × 经典 × 明/弱/无 + 行号)
"""
import io, os, re, glob, collections

ROOT = r"D:/shuntian-ziping-p0"
RAW = os.path.join(ROOT, "registries/source/raw")
BOOKS = [("DTS", "DTS_滴天髓_京图撰刘基原注.md", "准"),
         ("PZZQ", "PZZQ_子平真诠_沈孝瞻原文.md", "旁"),
         ("QTBJ", "QTBJ_穷通宝鉴_原文.md", "旁"),
         ("YHZP", "YHZP_渊海子平_原文.md", "旁"),
         ("SFTK", "SFTK_神峰通考_原文.md", "旁"),
         ("SMTH", "SMTH_三命通会_原文.md", "旁")]

# V1~V18: 每维的核心判据词(明) 与 弱证词(弱)
DIMS = [
    ("V1", "月令/人元司令", ["月令", "人元", "司事", "提纲"],
     ["当令", "得令", "失令", "月建"]),
    ("V2", "生时司令", ["生时", "生时司令"],
     ["月令", "用事"]),
    ("V3", "进退方向", ["进退", "进气", "退气"],
     ["司令", "进神", "退神"]),
    ("V4", "冲对旺衰/根的作用", ["旺者冲衰", "衰者冲", "根拔", "冲则"],
     ["六冲", "相冲", "冲之", "逢冲"]),
    ("V5", "合对旺衰/根的作用", ["合绊", "合而不化", "化气", "六合"],
     ["三合", "三会", "逢合", "相合"]),
    ("V6", "寒暖", ["寒暖", "寒凝", "温暖", "取暖"],
     ["调候", "寒", "暖"]),
    ("V7", "燥湿", ["燥湿", "湿燥", "润", "不燥"],
     ["燥", "湿"]),
    ("V8", "众寡", ["众寡", "党众", "助寡", "强众敌寡"],
     ["众", "寡"]),
    ("V9", "阴阳从势", ["从势", "从旺", "从强", "阳刃"],
     ["阴", "阳", "从"]),
    ("V10", "方局(三会三合)", ["方局", "三合", "三会", "成象"],
     ["寅卯辰", "申子辰", "亥卯未", "巳酉丑"]),
    ("V11", "源流", ["源流", "通关", "源头上流"],
     ["流通", "源头"]),
    ("V12", "通关", ["通关", "通关药"],
     ["关", "碍"]),
    ("V13", "衰旺辩证", ["衰旺", "旺衰", "强弱"],
     ["旺", "衰", "强", "弱"]),
    ("V14", "中和", ["中和", "中正", "无过不及"],
     ["偏枯", "太过", "不及"]),
    ("V15", "隐显", ["隐显", "显隐", "藏而不露"],
     ["伏", "透"]),
    ("V16", "刚柔", ["刚柔", "刚", "柔"],
     ["性情"]),
    ("V17", "顺逆", ["顺逆", "顺局", "逆局", "顺用", "逆用"],
     ["顺", "逆"]),
    ("V18", "震兑坎离", ["震兑", "坎离", "震为雷", "兑为泽"],
     ["坎", "离", "震", "兑"]),
]


def scan():
    res = {}
    for code, dim, strong, weak in DIMS:
        res[code] = {}
        for bk, fn, tier in BOOKS:
            p = os.path.join(RAW, fn)
            if not os.path.exists(p):
                res[code][bk] = ("缺文件", [], tier)
                continue
            L = io.open(p, encoding="utf-8-sig", errors="ignore").read().split("\n")
            strong_hits, weak_hits = [], []
            for i, l in enumerate(L, 1):
                if any(k in l for k in strong):
                    strong_hits.append(i)
                elif any(k in l for k in weak):
                    weak_hits.append(i)
            if strong_hits:
                st = "明"
            elif weak_hits:
                st = "弱"
            else:
                st = "无"
            res[code][bk] = (st, (strong_hits or weak_hits)[:6], tier)
    return res


def main():
    res = scan()
    OUT = os.path.join(ROOT, "p0_v2", "dimension_cross_matrix.md")
    lines = []
    lines.append("# 六部经典 × 底层维度 交叉矩阵\n")
    lines.append("> 生成: `scripts/dimension_cross_matrix.py`（纯字符串检索, 不用 AI）\n")
    lines.append("> 规则: **底层维度 = DTS(准神) 明文 + ≥1 本旁证明/弱同向**；单本不入底层\n")
    lines.append("> 强度: 明=命中核心判据词 / 弱=仅命中相关词 / 无=未命中\n")

    # 主表
    hdr = "| 维 | 名称 | " + " | ".join("%s(%s)" % (b, t) for b, _, t in BOOKS) + " | 判定 |"
    lines.append("\n## 一、交叉矩阵\n")
    lines.append(hdr)
    lines.append("|" + "---|" * (len(BOOKS) + 3))
    verdict = {}
    for code, dim, _s, _w in DIMS:
        cells = []
        dts_st = res[code]["DTS"][0]
        side_strong = sum(1 for b, _, _ in BOOKS
                          if b != "DTS" and res[code][b][0] == "明")
        side_weak = sum(1 for b, _, _ in BOOKS
                        if b != "DTS" and res[code][b][0] == "弱")
        if dts_st == "明" and side_strong >= 1:
            v = "**底层**"
        elif dts_st == "明":
            v = "单本(DTS独有)"
        elif dts_st == "弱":
            v = "DTS弱"
        else:
            v = "DTS无"
        verdict[code] = (v, side_strong, side_weak, dts_st)
        for b, _, _t in BOOKS:
            st = res[code][b][0]
            lines.append("| %s | %s | %s | %s |"
                         % (code, dim, st, v) if b == BOOKS[0][0]
                         else "| | | %s |" % st)
    lines.append("\n")

    # 判定汇总
    lines.append("\n## 二、判定汇总\n")
    lines.append("| 维 | 名称 | DTS | 旁证明 | 旁证弱 | 判定 |")
    lines.append("|---|---|---|---|---|---|")
    for code, dim, _s, _w in DIMS:
        v, ss, sw, ds = verdict[code]
        lines.append("| %s | %s | %s | %d | %d | %s |" % (code, dim, ds, ss, sw, v))
    lines.append("\n")

    # 明文行号明细
    lines.append("\n## 三、明文行号明细（DTS 必出; 旁证列出前6处）\n")
    for code, dim, _s, _w in DIMS:
        lines.append("\n### %s %s —— 判定: %s\n" % (code, dim, verdict[code][0]))
        lines.append("| 书 | 强度 | 命中行号 |")
        lines.append("|---|---|---|")
        for b, _fn, t in BOOKS:
            st, hits, _ = res[code][b]
            lines.append("| %s(%s) | %s | %s |" % (
                b, t, st, ", ".join("L%d" % h for h in hits) if hits else "-"))

    io.open(OUT, "w", encoding="utf-8", newline="").write("\n".join(lines))

    # 控制台摘要
    print("=" * 96)
    print("六本 × V1~V18 检索完成 -> %s" % OUT)
    print("=" * 96)
    print("  %-4s %-16s %-6s %-6s %-6s %-8s" % ("维", "名称", "DTS", "旁明", "旁弱", "判定"))
    for code, dim, _s, _w in DIMS:
        v, ss, sw, ds = verdict[code]
        print("  %-4s %-16s %-6s %-6d %-6d %-8s" % (code, dim, ds, ss, sw, v))
    n_base = sum(1 for v in verdict.values() if v[0] == "**底层**")
    print("\n  底层 %d 维 / 共 %d 维" % (n_base, len(DIMS)))
    print("  '?' 已全部消掉（本表无 ? 列）")


if __name__ == "__main__":
    main()