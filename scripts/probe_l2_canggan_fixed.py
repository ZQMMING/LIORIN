# -*- coding: utf-8 -*-
"""修版解析器 + 来源核（裁一百二十七丙 / 一百二十八丙+乙 / 一百二十九甲）

★ 修法: 按【句式模板】定位支, 不按字符集
    错误: 遇「己」字符就切段 → 「己未宮」的己被当支名, 午偷到下一支的己
    正确: 只有「X+藏/宮/有/中」才切段（X ∈ 十二支）
★ PZZQ 体系核（唯一次序定义明文）:
    L2917「寅中藏甲丙戊三神，甲，当旺之气也；丙，方生之气也；戊，寄生之气也」
    L2918「次序先甲次丙次戊」
★ 歌诀语序不构成判据, PZZQ 体系才是（裁一百二十八乙）
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

# ── 源文（逐字抄, 不改一字）──
YHZP_SONG = ("子宫癸水在其中，丑癸辛金己土同，寅宫甲木兼丙戊，卯宫乙木独相逢，"
             "辰藏乙戊三分癸，巳中庚金丙戊丛，午宫丁火拼己土，未宫乙己丁其宗，"
             "申位庚金壬水戊，酉宫辛字独丰隆，戌宫辛金及丁戊，亥中壬甲是真踪。")
SFTK_L4057 = ("子藏癸水是祿位。丑己三分辛及癸。寅藏甲丙戊木火。辰有戊兮乙與癸。"
              "巳藏丙戊及庚金。午宮卻有丁火。己未宮丁乙己同臨。申宮庚金壬水戊。"
              "酉宮辛金一位美。戌有丁辛戊土至亥藏壬甲二天干。十二宮中須記取。")

# ★ 句式模板: 支名 + {藏|宮|宫|有|中|位|位}  —— 只有这些才算「支在此起段」
ANCHOR = re.compile(r"([子丑寅卯辰巳午未申酉戌亥])\s?(?:藏|宮|宫|有|中|位)")
# 备选: 歌诀里「申位」「酉宫」这类, 上面已含「位」「宫」; 「丑癸辛金己土同」无锚点 → 需回退


def parse_by_pattern(text):
    """★ 修版: 按句式锚点切段。返回 {支: [(干列表, 来源子串)]}"""
    marks = [(m.start(), m.end(), m.group(1)) for m in ANCHOR.finditer(text)]
    out = {}
    if not marks:
        return out
    for i, (s, e, z) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        # 来源子串 = 锚点之后到下一锚点之前, 但【不越过标点】(句读边界)
        raw = text[e:end]
        cut = re.split(r"[。，、；]", raw)[0]
        src = text[s:s + len(cut) + 2]        # 含锚点本身
        gans = []
        for g in re.findall(r"[%s]" % G, cut):
            if g not in gans:
                gans.append(g)
        out.setdefault(z, []).append((gans, src))
    return out


def merge(recs):
    out = {}
    for z, lst in recs.items():
        merged = []
        for gans, src in lst:
            for g in gans:
                if g not in merged:
                    merged.append(g)
        out[z] = merged
    return out


def main():
    print("=" * 104)
    print("修版解析器（句式定位）+ 来源核 + PZZQ 体系核")
    print("=" * 104)
    p = os.path.abspath(__file__)
    st = os.stat(p)
    print("P1  脚本 %s  %d B  %s"
          % (p, st.st_size,
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))))

    # P2 源文逐字核对
    yh = io.open(os.path.join(RAW, "YHZP_渊海子平_原文.md"),
                 encoding="utf-8-sig", errors="ignore").read().split("\n")
    raw_y = "".join(x.strip() for x in yh[2524:2527])
    ok2 = raw_y == YHZP_SONG
    print("P2  源文逐字核对   %s" % ("PASS" if ok2 else "★FAIL（我抄错）"))
    sf = io.open(os.path.join(RAW, "SFTK_神峰通考_原文.md"),
                 encoding="utf-8-sig", errors="ignore").read().split("\n")
    ok2b = (YHZP_SONG != SFTK_L4057) and (SFTK_L4057[:8] in sf[4056])
    print("P2b SFTK 源在位     %s" % ("PASS" if ok2b else "★FAIL"))

    # P3 修版解析器
    Ay_rec = parse_by_pattern(YHZP_SONG)
    Ay = merge(Ay_rec)
    miss_y = [z for z in Z if z not in Ay]
    ok3 = not miss_y
    print("P3  YHZP 句式解析  缺支 %s   %s" % (miss_y or "无", "PASS" if ok3 else "★FAIL"))

    # P4 SFTK 修版解析 —— 午应为 {丁}, 不再偷己
    As_rec = parse_by_pattern(SFTK_L4057)
    As = merge(As_rec)
    ok4 = (As.get("午") == ["丁"])
    print("P4  SFTK 句式解析  午=%s（修版后应只有丁）   %s"
          % (As.get("午"), "PASS" if ok4 else "★FAIL"))

    # P5 引擎表
    sys.path.insert(0, ROOT)
    _P0 = os.path.join(ROOT, "p0_v2")
    if _P0 in sys.path:
        sys.path.remove(_P0)
    from engines.common.l0_fact_builder import HIDDEN
    B = {z: list(HIDDEN.get(z) or []) for z in Z}
    ok5 = all(B.get(z) for z in Z)
    print("P5  引擎表 12 支有值   %s" % ("PASS" if ok5 else "★FAIL"))

    # ★Pn 来源核（裁用户第四节新增）: 值的来源子串不得跨支边界
    print("\n" + "-" * 104)
    print("Pn  来源核：每支的来源子串 + 跨支边界检查")
    print("-" * 104)
    bad = []
    for z in Z:
        for gans, src in Ay_rec.get(z, []):
            others = [o for o in Z if o != z and o in src[1:]]
            if others:
                bad.append((z, src, others))
            print("   %s = {%-10s} 来源: 「%s」%s"
                  % (z, "".join(gans), src,
                     ("  ★跨支:%s" % others) if others else ""))
    ok6 = not bad
    print("\nPn  跨支违规 = %d   %s" % (len(bad), "PASS" if ok6 else "★FAIL"))
    if bad:
        for z, src, o in bad:
            print("   ★%s 来源「%s」含他支 %s" % (z, src, o))

    allok = all([ok2, ok2b, ok3, ok4, ok5, ok6])
    print("\n探针总结: %s" % ("★ 全 PASS —— 出对照数" if allok else "★★ 有 FAIL"))

    if not allok:
        return

    # ══════ 集合对照 ══════
    print("\n" + "=" * 104)
    print("【集合对照】轨A(YHZP 修版) vs 轨B(引擎) —— 判据: 集合不同 = 真冲突")
    print("-" * 104)
    set_ne = []
    for z in Z:
        sa, sb = set(Ay.get(z, [])), set(B[z])
        if sa == sb:
            print("   %s  同 %s" % (z, sorted(sa)))
        else:
            set_ne.append((z, sorted(sa - sb), sorted(sb - sa)))
            print("   %s  ★不同: 轨A独有 %s / 轨B独有 %s"
                  % (z, sorted(sa - sb), sorted(sb - sa)))

    # ══════ 排序对照 + PZZQ 体系核（不用歌诀语序）══════
    print("\n" + "=" * 104)
    print("【排序核】★ 歌诀语序不构成判据; 用 PZZQ 体系（本气→次→末）核引擎")
    print("-" * 104)
    print("PZZQ L2917「寅中藏甲丙戊三神，甲，当旺之气也；丙，方生之气也；戊，寄生之气也」")
    print("PZZQ L2918「次序先甲次丙次戊」")
    print("PZZQ L2918「辰中藏戊乙癸三神，戊，土之本气也；乙木，春之余也；癸，水之墓」")
    print("\n★ PZZQ 明文定义了两支:  寅 = 甲→丙→戊   辰 = 戊→乙→癸")
    print("★ 引擎这两支:          寅 = %s   辰 = %s"
          % (" ".join(B["寅"]), " ".join(B["辰"])))
    ok_in = (B["寅"] == ["甲", "丙", "戊"])
    ok_chen = (B["辰"] == ["戊", "乙", "癸"])
    print("   寅 引擎 vs PZZQ: %s   辰 引擎 vs PZZQ: %s"
          % ("一致" if ok_in else "★不一致", "一致" if ok_chen else "★不一致"))

    print("\n各支引擎排序（本气/中气/余气）与 YHZP 歌诀语序对照:")
    order_ne = []
    for z in Z:
        a, b = Ay.get(z, []), B[z]
        same_set = set(a) == set(b)
        same_ord = (a == b)
        tag = "集合同·序同" if same_ord else (
            "集合同·★排序差" if same_set else "★集合不同")
        if same_set and not same_ord:
            order_ne.append(z)
        print("   %s  YHZP歌诀 %-10s 引擎 %-10s %s"
              % (z, " ".join(a), " ".join(b), tag))
    print("\n   集合冲突 %d 支 / 排序差 %d 支 %s"
          % (len(set_ne), len(order_ne), order_ne or ""))

    # ══════ SFTK 对照（修版后）══════
    print("\n" + "=" * 104)
    print("【SFTK 对照（修版解析）】—— 核 SFTK 缺陷两处")
    print("-" * 104)
    for z in Z:
        a, b = As.get(z, []), B[z]
        if set(a) != set(b):
            print("   %s  ★集合不同: SFTK=%s 引擎=%s"
                  % (z, "".join(sorted(a)) or "(无)", "".join(sorted(b))))
    print("   （无输出行 = SFTK 与引擎集合全同）")

    print("\n" + "=" * 104)
    print("汇总")
    print("=" * 104)
    print("   轨A(YHZP修版): 集合冲突 %d / 排序差 %d" % (len(set_ne), len(order_ne)))
    print("   PZZQ 体系核: 寅 %s / 辰 %s"
          % ("一致" if ok_in else "★不一致", "一致" if ok_chen else "★不一致"))
    print("   ★ 脚本不出最终结论, 只出对照事实。")


if __name__ == "__main__":
    main()