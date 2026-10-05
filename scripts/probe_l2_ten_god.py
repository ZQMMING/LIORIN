# -*- coding: utf-8 -*-
"""L2 探针 P1-P7（先跑锚点, 全 PASS 才跑真实数据 —— 立规 2f）

★ 十神是全仓最基础的一张表: 它错 → L3 三布尔 / support_state 全错 → L4 八格全错。
★ 但从未专项核过。前七次同类错都出在「用文本模式代替结构」——
  十神核最易踩: 查表 vs 算法 / 藏干十神 vs 天干十神 / 主气 vs 中余气。

探针:
  P1 甲日主 见 庚 → 七杀    （克我, 同阴阳）
  P2 甲日主 见 癸 → 正印    （生我, 异阴阳）
  P3 甲日主 见 丙 → 食神    （我生, 同阴阳）
  P4 甲日主 见 己 → 正财    （我克, 异阴阳）
  P5 甲日主 见 乙 → 劫财    （同五行, 异阴阳）
  P6 ten_god 函数签名
  P7 全十类都有产出（10 个值）
"""
import sys
import os
import collections

ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)
from engines.common.l0_fact_builder import ten_god, WUXING, YANG

GAN = "甲乙丙丁戊己庚辛壬癸"


def main():
    print("=" * 96)
    print("L2 探针 P1-P7（锚点全 PASS 才跑真实数据）")
    print("=" * 96)

    # ── P6: 函数签名 ──
    import inspect
    sig = str(inspect.signature(ten_god))
    ok6 = sig == "(day_stem, other_stem)"
    print("P6  ten_god 签名   预期 (day_stem, other_stem)   实测 %s   %s"
          % (sig, "PASS" if ok6 else "★FAIL"))

    # ── P1-P5: 五类生克各一锚点 ──
    anchors = [
        ("P1", "甲", "庚", "七杀", "克我·同阴阳"),
        ("P2", "甲", "癸", "正印", "生我·异阴阳"),
        ("P3", "甲", "丙", "食神", "我生·同阴阳"),
        ("P4", "甲", "己", "正财", "我克·异阴阳"),
        ("P5", "甲", "乙", "劫财", "同五行·异阴阳"),
    ]
    allok = ok6
    print("\n%-4s %-6s %-6s %-8s %-14s %-6s %s"
          % ("探针", "日主", "对方", "预期", "关系", "实测", "通过?"))
    print("-" * 96)
    for pid, dm, other, exp, rel in anchors:
        got = ten_god(dm, other)
        ok = got == exp
        allok = allok and ok
        print("%-4s %-6s %-6s %-8s %-14s %-6s %s"
              % (pid, dm, other, exp, rel, got, "PASS" if ok else "★FAIL"))

    # ── P7: 全十类 ──
    vals = set()
    for a in GAN:
        for b in GAN:
            vals.add(ten_god(a, b))
    vals.discard("?")
    EXP10 = {"比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官",
             "偏印", "正印"}
    ok7 = vals == EXP10
    allok = allok and ok7
    print("\nP7  全十类产出   预期 10 类   实测 %d 类   %s"
          % (len(vals), "PASS" if ok7 else "★FAIL"))
    print("    实测值域: %s" % sorted(vals))
    if not ok7:
        print("    ★ 缺: %s / 多: %s" % (EXP10 - vals, vals - EXP10))

    # ── 附: 自同与异阴阳对称性（算法自检, 非用户锚点）──
    print("\n附  算法自检")
    bad = []
    for a in GAN:
        for b in GAN:
            v = ten_god(a, b)
            if v == "比肩" and a != b:
                bad.append((a, b, v, "异干却同十神"))
    print("    异干误判比肩 = %d 处 %s" % (len(bad), "PASS" if not bad else "★FAIL"))
    for x in bad[:5]:
        print("      %s-%s = %s (%s)" % x)

    print("\n" + "=" * 96)
    print("探针总结: %s" % ("★ 全 PASS —— 可跑真实数据" if allok
                            else "★★ 有 FAIL —— 按 2f, 不报任何真实数据"))
    print("=" * 96)


if __name__ == "__main__":
    main()