# -*- coding: utf-8 -*-
"""修版2解析器：分句 + 三层规则（裁一百三十丙）

★ 三层规则（互斥）:
    规则1 锚点优先: 句内有「X宮/X藏/X有/X中/X位」→ 归属 X（一句可含多个锚点）
    规则2 句首兜底: 无锚点且句首是地支 → 归属句首
    规则3 未解析  : 无锚点且句首非地支 → UNRESOLVED，不静默丢
    规则1 与规则2 互斥：同句既有锚点又有句首支名 → 用锚点

★ 分句标点集: 逗号「，」+ 句号「。」+ 分号「；」+ 顿号「、」
    YHZP 用逗号（「丑癸辛金己土同」），SFTK 用句号（「丑己三分辛及癸。」）
    两个源混用标点，分句函数两种都处理。

★ 探针 P3 判据（裁一百三十丙·第三节）:
    12 支【全】解析出 = PASS；11/12 = FAIL。差一支也算 FAIL。
★ 元教训（立规）：修「用错结构标识」的 bug 时，新结构标识本身也要过全样例验证。
"""
import sys
import os
import io
import re
import time

ROOT = r"D:/shuntian-ziping-p0"
RAW = os.path.join(ROOT, "registries", "source", "raw")
Z = list("子丑寅卯辰巳午未申酉戌亥")
G = "甲乙丙丁戊己庚辛壬癸"

YHZP_SONG = ("子宫癸水在其中，丑癸辛金己土同，寅宫甲木兼丙戊，卯宫乙木独相逢，"
             "辰藏乙戊三分癸，巳中庚金丙戊丛，午宫丁火拼己土，未宫乙己丁其宗，"
             "申位庚金壬水戊，酉宫辛字独丰隆，戌宫辛金及丁戊，亥中壬甲是真踪。")
SFTK_L4057 = ("子藏癸水是祿位。丑己三分辛及癸。寅藏甲丙戊木火。辰有戊兮乙與癸。"
              "巳藏丙戊及庚金。午宮卻有丁火。己未宮丁乙己同臨。申宮庚金壬水戊。"
              "酉宮辛金一位美。戌有丁辛戊土至亥藏壬甲二天干。十二宮中須記取。")

SENT_SPLIT = re.compile(r"[，。；、]")
ANCHOR = re.compile(r"([%s])\s?(?:藏|宮|宫|有|中|位)" % "".join(Z))


def parse_three_layers(text):
    """分句 + 三层规则。返回 {支: [(干列表, 来源句)]}与 UNRESOLVED 列表"""
    out = {}
    unresolved = []
    sents = [s for s in SENT_SPLIT.split(text) if s.strip()]
    for sent in sents:
        anchors = [(m.start(), m.group(1)) for m in ANCHOR.finditer(sent)]
        if anchors:
            # 规则1: 锚点优先; 一句多锚点 → 按锚点位置切
            for i, (pos, z) in enumerate(anchors):
                end = anchors[i + 1][0] if i + 1 < len(anchors) else len(sent)
                seg = sent[pos:end]
                # 去掉锚点那两字再抽干
                body = re.sub(r"^([%s])\s?(?:藏|宮|宫|有|中|位)" % "".join(Z),
                              "", seg)
                gans = []
                for g in re.findall(r"[%s]" % G, body):
                    if g not in gans:
                        gans.append(g)
                out.setdefault(z, []).append((gans, sent))
        else:
            # 规则2: 句首兜底
            first = sent.strip()[0]
            if first in Z:
                body = sent.strip()[1:]
                gans = []
                for g in re.findall(r"[%s]" % G, body):
                    if g not in gans:
                        gans.append(g)
                out.setdefault(first, []).append((gans, sent))
            else:
                # 规则3: 未解析
                unresolved.append(sent)
    return out, unresolved


def merge(recs):
    out = {}
    for z, lst in recs.items():
        m = []
        for gans, src in lst:
            for g in gans:
                if g not in m:
                    m.append(g)
        out[z] = m
    return out


def main():
    print("=" * 104)
    print("修版2解析器：分句 + 三层规则 + P3 收紧（12 支全）")
    print("=" * 104)
    p = os.path.abspath(__file__)
    st = os.stat(p)
    print("P1  脚本 %s  %d B  %s"
          % (p, st.st_size,
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))))

    # P2 源文逐字核对
    yh = io.open(os.path.join(RAW, "YHZP_渊海子平_原文.md"),
                 encoding="utf-8-sig", errors="ignore").read().split("\n")
    ok2 = ("".join(x.strip() for x in yh[2524:2527]) == YHZP_SONG)
    sf = io.open(os.path.join(RAW, "SFTK_神峰通考_原文.md"),
                 encoding="utf-8-sig", errors="ignore").read().split("\n")
    ok2b = (SFTK_L4057[:8] in sf[4056])
    print("P2  源文逐字核对 YHZP=%s  SFTK=%s"
          % ("PASS" if ok2 else "★FAIL", "PASS" if ok2b else "★FAIL"))

    # P3 ★ 12 支全（11/12 也 FAIL）
    Ay_rec, un_y = parse_three_layers(YHZP_SONG)
    Ay = merge(Ay_rec)
    miss_y = [z for z in Z if z not in Ay]
    no_gans = [z for z in Z if z in Ay and not Ay[z]]
    ok3 = (not miss_y) and (not no_gans) and (not un_y)
    print("P3  YHZP 解析   缺支=%s  空干支=%s  未解析句=%d   %s"
          % (miss_y or "无", no_gans or "无", len(un_y),
             "PASS" if ok3 else "★FAIL"))
    print("   ★ 判据: 12 支全解析出才 PASS —— 11/12 也算 FAIL")
    if un_y:
        for s in un_y:
            print("      ★未解析: 「%s」" % s[:60])

    # P4 SFTK 修版: 午 应为 {丁}
    As_rec, un_s = parse_three_layers(SFTK_L4057)
    As = merge(As_rec)
    ok4 = (As.get("午") == ["丁"])
    print("P4  SFTK 解析   午=%s（应只有丁）  未解析句=%d   %s"
          % (As.get("午"), len(un_s), "PASS" if ok4 else "★FAIL"))

    # P5 引擎表
    sys.path.insert(0, ROOT)
    _P0 = os.path.join(ROOT, "p0_v2")
    if _P0 in sys.path:
        sys.path.remove(_P0)
    from engines.common.l0_fact_builder import HIDDEN
    B = {z: list(HIDDEN.get(z) or []) for z in Z}
    ok5 = all(B.get(z) for z in Z)
    print("P5  引擎表 12 支有值   %s" % ("PASS" if ok5 else "★FAIL"))

    # Pn 来源核（跨支检查）
    bad = []
    print("\nPn  来源核（YHZP）")
    print("-" * 104)
    for z in Z:
        srcs = " | ".join(repr(s) for _, s in Ay_rec.get(z, []))
        others = [o for o in Z if o != z and
                  any(o in s[1:] for _, s in Ay_rec.get(z, []))]
        if others:
            bad.append((z, others))
        print("   %s = {%-10s} 来源句: %s%s"
              % (z, "".join(Ay.get(z, [])), srcs,
                 ("  ★跨支:%s" % others) if others else ""))
    ok6 = not bad
    print("\nPn  跨支违规 = %d   %s" % (len(bad), "PASS" if ok6 else "★FAIL"))

    allok = all([ok2, ok2b, ok3, ok4, ok5, ok6])
    print("\n探针总结: %s" % ("★ 全 PASS —— 出对照数" if allok else "★★ 有 FAIL —— 不出数"))
    if not allok:
        return

    # ═══ 集合对照 ═══
    print("\n" + "=" * 104)
    print("【集合对照】轨A(YHZP) vs 轨B(引擎)")
    print("-" * 104)
    set_ne = []
    for z in Z:
        sa, sb = set(Ay[z]), set(B[z])
        if sa == sb:
            print("   %s  同 %s" % (z, sorted(sa)))
        else:
            set_ne.append(z)
            print("   %s  ★不同: 轨A独有 %s / 轨B独有 %s"
                  % (z, sorted(sa - sb), sorted(sb - sa)))

    # ═══ 排序核: PZZQ 体系 ═══
    print("\n" + "=" * 104)
    print("【排序核】★ 歌诀语序不构成判据; PZZQ 体系才是唯一次序定义")
    print("-" * 104)
    print("PZZQ L2918「次序先甲次丙次戊」   → 寅 本气=甲")
    print("PZZQ L2918「辰中藏戊乙癸三神，戊，土之本气也」 → 辰 本气=戊")
    ok_in = B["寅"] == ["甲", "丙", "戊"]
    ok_chen = B["辰"] == ["戊", "乙", "癸"]
    print("   寅 引擎=%s vs PZZQ 甲丙戊   %s"
          % (" ".join(B["寅"]), "一致" if ok_in else "★不一致"))
    print("   辰 引擎=%s vs PZZQ 戊乙癸   %s"
          % (" ".join(B["辰"]), "一致" if ok_chen else "★不一致"))

    order_ne = []
    print("\n   各支 YHZP 歌诀语序 vs 引擎本气/中气/余气序:")
    for z in Z:
        a, b = Ay[z], B[z]
        same_ord = (a == b)
        tag = "序同" if same_ord else "★排序差"
        if set(a) == set(b) and not same_ord:
            order_ne.append(z)
        print("      %s  YHZP %-10s 引擎 %-10s %s"
              % (z, " ".join(a), " ".join(b), tag))
    print("\n   集合冲突 %d 支 / 排序差 %d 支 %s"
          % (len(set_ne), len(order_ne), order_ne or ""))

    # ═══ SFTK 对照 ═══
    print("\n" + "=" * 104)
    print("【SFTK 对照（修版2）】—— 核 SFTK 缺陷")
    print("-" * 104)
    for z in Z:
        if set(As.get(z, [])) != set(B[z]):
            print("   %s  ★集合不同: SFTK=%s 引擎=%s"
                  % (z, "".join(sorted(As.get(z, []))) or "(无)",
                     "".join(sorted(B[z]))))

    print("\n" + "=" * 104)
    print("汇总: 集合冲突 %d / 排序差 %d / PZZQ 寅%s 辰%s"
          % (len(set_ne), len(order_ne),
             "一致" if ok_in else "不一致", "一致" if ok_chen else "不一致"))


if __name__ == "__main__":
    main()