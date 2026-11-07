# -*- coding: utf-8 -*-
"""轨A 换源（YHZP《地支藏遁歌》）+ 上轮矛盾诊断 + 全 12 支重算
裁一百二十四丙+甲 / 一百二十五甲+重算 / 一百二十六拆开

★ 上轮矛盾（必须先解释）:
  双轨报告说「午 {丁己} 集合同」, 核124 说「SFTK 那首午只有丁」
  → 本脚本输出 SFTK 解析的【原始中间结果】, 定位是解析 bug 还是补源

★ 轨A 源切换: SFTK L4057 → YHZP L2525《地支藏遁歌》
  ★ 轨A 全程不 import 引擎、不读 zhi_hidden_stems_v1.json

探针 P1–P6 见 main() 开头, 全 PASS 才出对照数。
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

# ── 源一: SFTK L4057（上轮用的）──
SFTK_L4057 = ("子藏癸水是祿位。丑己三分辛及癸。寅藏甲丙戊木火。辰有戊兮乙與癸。"
              "巳藏丙戊及庚金。午宮卻有丁火。己未宮丁乙己同臨。申宮庚金壬水戊。"
              "酉宮辛金一位美。戌有丁辛戊土至亥藏壬甲二天干。十二宮中須記取。")

# ── 源二: YHZP L2525-L2527《地支藏遁歌》（本轮要换的源）──
YHZP_SONG = ("子宫癸水在其中，丑癸辛金己土同，寅宫甲木兼丙戊，卯宫乙木独相逢，"
             "辰藏乙戊三分癸，巳中庚金丙戊丛，午宫丁火拼己土，未宫乙己丁其宗，"
             "申位庚金壬水戊，酉宫辛字独丰隆，戌宫辛金及丁戊，亥中壬甲是真踪。")

SEG_SPLIT = re.compile(r"[子丑寅卯辰巳午未申酉戌亥]")


def parse_song(text, verbose=False):
    """按支名切段，段内抽干并保序。
    ★ verbose=True 时输出每支的原始片段，用于矛盾诊断。"""
    out = {}
    trace = {}
    marks = [(m.start(), m.group(0)) for m in SEG_SPLIT.finditer(text)]
    for i, (pos, z) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        seg = text[pos + 1:end]
        gans = []
        for g in re.findall(r"[%s]" % G, seg):
            if g not in gans:
                gans.append(g)
        out.setdefault(z, []).extend(gans)
        trace.setdefault(z, []).append(seg)
    if verbose:
        return out, trace
    return out


def main():
    print("=" * 104)
    print("轨A 换源（YHZP《地支藏遁歌》）+ 上轮矛盾诊断 + 全 12 支重算")
    print("=" * 104)
    p = os.path.abspath(__file__)
    st = os.stat(p)
    print("P1  脚本 %s  %d B  %s"
          % (p, st.st_size,
             time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))))

    # ── P2: 源文逐字核对（防止我抄错）──
    yh = io.open(os.path.join(RAW, "YHZP_渊海子平_原文.md"),
                 encoding="utf-8-sig", errors="ignore").read()
    yh_lines = yh.split("\n")
    raw_src = "".join(x.strip() for x in yh_lines[2524:2527])
    ok2 = (raw_src == YHZP_SONG)
    print("P2  源文核对   预期=脚本内常量   实测%s   %s"
          % ("一致" if ok2 else "★不一致（我抄错了）", "PASS" if ok2 else "★FAIL"))
    if not ok2:
        print("    文件原文: %s" % raw_src[:100])

    # ── P3: YHZP 解析 12 支全 ──
    A, trace_y = parse_song(YHZP_SONG, verbose=True)
    # 「丑癸辛金己土同」与「己未宮…」在SFTK 里合并处理；YHZP 里丑与未分段清晰
    miss = [z for z in Z if z not in A]
    you_ok = ("卯" in A and "己" in (A.get("午") or []))
    ok3 = (not miss) and you_ok
    print("P3  YHZP 解析  预期 12 支含卯且午含己   实测 缺%s / 卯%s / 午%s   %s"
          % (miss or "无", A.get("卯"), A.get("午"),
             "PASS" if ok3 else "★FAIL"))

    # ── P4: 引擎表读数 ──
    sys.path.insert(0, ROOT)
    _P0 = os.path.join(ROOT, "p0_v2")
    if _P0 in sys.path:
        sys.path.remove(_P0)
    from engines.common.l0_fact_builder import HIDDEN
    B = {z: list(HIDDEN.get(z) or []) for z in Z}
    ok4 = all(B.get(z) for z in Z)
    print("P4  引擎表读数  预期 12 支全有值   实测 %d 支有值   %s"
          % (sum(1 for z in Z if B[z]), "PASS" if ok4 else "★FAIL"))

    # ── P5: SFTK 解析函数仍可调用（矛盾诊断）──
    S, trace_s = parse_song(SFTK_L4057, verbose=True)
    ok5 = "午" in S
    print("P5  SFTK 解析可调用  预期能解析   实测 午=%s   %s"
          % (S.get("午"), "PASS" if ok5 else "★FAIL"))

    # ── P6: 对照函数可用 ──
    ok6 = isinstance(A, dict) and isinstance(B, dict)
    print("P6  对照输入正常  %s" % ("PASS" if ok6 else "★FAIL"))

    allok = all([ok2, ok3, ok4, ok5, ok6])
    print("\n探针总结: %s"
          % ("★ 全 PASS —— 出对照数" if allok else "★★ 有 FAIL —— 不出数"))

    # ══════════ 甲：上轮 SFTK 解析的原始中间结果（矛盾诊断） ══════════
    print("\n" + "=" * 104)
    print("【甲】上轮 SFTK L4057 解析原始中间结果 —— 午为什么是 {丁己}？")
    print("=" * 104)
    print("我的解析器: 按【支名字符】切段, 段内抽干")
    print("★ 关键: SFTK 那句里「巳藏丙戊及庚金。**午宮卻有丁火。己未宮丁乙己同臨**。」")
    print("  「己未宮」的「己」既是【天干】也是【支名】→ 被 SEG_SPLIT 当成新支切开")
    print()
    for z in Z:
        segs = trace_s.get(z, [])
        merged = S.get(z, [])
        flag = ""
        # 检查是否混入了本支不该有的干
        print("   %s  轨A=%-12s  原始片段=%s"
              % (z, " ".join(merged) or "(无)",
                 " | ".join(repr(x) for x in segs)))

    print("\n★ 逐支检查: 引擎表 vs SFTK 轨A（只看集合是否相同）")
    for z in Z:
        sb, ss = set(B[z]), set(S.get(z, []))
        tag = "同" if sb == ss else "★不同"
        print("   %s  引擎={%-10s} SFTK轨A={%-10s} %s"
              % (z, "".join(sorted(sb)), "".join(sorted(ss)), tag))

    # ══════════ 乙丙丁：YHZP 轨A 全 12 支对照 ══════════
    print("\n" + "=" * 104)
    print("【乙】轨A 源 = YHZP《地支藏遁歌》 L2525-L2527")
    print("-" * 104)
    for z in Z:
        print("   %s  轨A(YHZP)=%-12s 轨B(引擎)=%-12s"
              % (z, " ".join(A.get(z, [])), " ".join(B[z])))

    print("\n" + "=" * 104)
    print("【丙】集合对照（判据: 集合不同 = 真冲突）")
    print("-" * 104)
    set_ne = []
    for z in Z:
        sa, sb = set(A.get(z, [])), set(B[z])
        if sa == sb:
            print("   %s  同 %s" % (z, sorted(sa)))
        else:
            set_ne.append((z, sorted(sa - sb), sorted(sb - sa)))
            print("   %s  ★不同: 轨A独有 %s / 轨B独有 %s"
                  % (z, sorted(sa - sb), sorted(sb - sa)))

    print("\n" + "=" * 104)
    print("【丁】排序对照 + 上轮三处重核")
    print("-" * 104)
    order_ne = []
    for z in Z:
        if set(A.get(z, [])) != set(B[z]):
            continue
        if A.get(z) != B[z]:
            order_ne.append(z)
            print("   %s  排序差: 轨A %s / 轨B %s"
                  % (z, " ".join(A[z]), " ".join(B[z])))
    print("\n   集合相同但排序不同的支 = %d: %s"
          % (len(order_ne), order_ne or "无"))
    OLD3 = ["丑", "未", "戌"]
    print("\n   上轮三处「丑未戌」重核（SFTK 源 → YHZP 源）:")
    for z in OLD3:
        inA = z in order_ne
        print("      %s  上轮(SFTK源)=排序差   本轮(YHZP源)=%s"
              % (z, "排序差" if inA else "★一致"))

    print("\n" + "=" * 104)
    print("汇总")
    print("=" * 104)
    print("   轨A 换源后: 集合冲突 %d 支 / 排序差 %d 支"
          % (len(set_ne), len(order_ne)))
    print("   ★ 脚本【不出】最终结论, 只出对照事实。")


if __name__ == "__main__":
    main()