# -*- coding: utf-8 -*-
"""甲②③ 探针 P8–P17（L2 十神层 · 天干 × 地支藏干）

★ 立规 2h: 报数前先确认「我跑的是哪个文件」+ 探针结果, 才报真实数据。

探针设计（覆盖三藏干层 × 五类十神 + 藏干表结构）:
  P8-P14  已知锚点 7 条
          P8  子中癸（本气）→ 正印    P9  丑中己（本气）→ 正财
          P10 丑中辛（中气）→ 正官    P11 丑中癸（余气）→ 正印
          P12 寅中甲（本气）→ 比肩    P13 寅中丙（中气）→ 食神
          P14 寅中戊（余气）→ 偏财
  P15  HIDDEN 藏干表结构（12 支 × 三层齐）
  P16  ten_god 对藏干输入不报错、不返回 None
  P17  12 支 × 全部藏干 全有值（无 '?'）

★ 全 PASS 才报真实数据（甲②③ 的 12 支 × 藏干总表）。
"""
import sys
import os

ROOT = r"D:/shuntian-ziping-p0"
sys.path.insert(0, ROOT)
_P0 = os.path.join(ROOT, "p0_v2")
if _P0 in sys.path:
    sys.path.remove(_P0)

from engines.common.l0_fact_builder import ten_god, HIDDEN

ZHI = list("子丑寅卯辰巳午未申酉戌亥")
LAYER = ["本气", "中气", "余气"]


def main():
    print("=" * 100)
    print("甲②③ 探针 P8–P17（立规 2f：全 PASS 才报真实数据）")
    print("=" * 100)
    print("★ 脚本: D:/shuntian-ziping-p0/scripts/probe_l2_canggan.py")

    allok = True

    # ── P15: 藏干表结构 ──
    print("\n【P15】HIDDEN 藏干表结构")
    print("-" * 100)
    n_zhi = len(HIDDEN)
    layers = {z: len(HIDDEN.get(z) or []) for z in ZHI}
    bad15 = []
    for z in ZHI:
        v = HIDDEN.get(z)
        if not v:
            bad15.append((z, "缺失"))
        elif len(v) not in (1, 2, 3):
            bad15.append((z, "%d 层(异常)" % len(v)))
    ok15 = (n_zhi >= 12) and not bad15
    allok = allok and ok15
    print("支数 = %d (期望 ≥12)   层数分布 = %s" % (n_zhi, sorted(set(layers.values()))))
    print("异常支 = %d  %s   %s" % (len(bad15), bad15[:5],
                                    "PASS" if ok15 else "★FAIL"))
    print("表内容:")
    for z in ZHI:
        print("   %s: %s" % (z, " ".join("%s(%s)" % (g, LAYER[i])
                                       for i, g in enumerate(HIDDEN.get(z) or []))))

    # ── P8–P14: 已知锚点 ──
    print("\n【P8–P14】已知锚点（三藏干层 × 五类十神）")
    print("-" * 100)
    anchors = [
        ("P8", "甲", "子", 0, "正印", "生我·异阴阳"),
        ("P9", "甲", "丑", 0, "正财", "我克·异阴阳"),
        ("P10", "甲", "丑", 1, "正官", "克我·异阴阳"),
        ("P11", "甲", "丑", 2, "正印", "生我·异阴阳"),
        ("P12", "甲", "寅", 0, "比肩", "同我·同阴阳"),
        ("P13", "甲", "寅", 1, "食神", "我生·同阴阳"),
        ("P14", "甲", "寅", 2, "偏财", "我克·同阴阳"),
    ]
    print("%-5s %-6s %-8s %-10s %-8s %-14s %-8s %s"
          % ("探针", "日主", "支", "藏干", "预期", "关系", "实测", "通过?"))
    print("-" * 100)
    for pid, dm, z, idx, exp, rel in anchors:
        hg = (HIDDEN.get(z) or ["?"] * 3)[idx] if idx < len(HIDDEN.get(z) or []) else "?"
        got = ten_god(dm, hg) if hg != "?" else "?"
        ok = got == exp
        allok = allok and ok
        print("%-5s %-6s %-8s %-10s %-8s %-14s %-8s %s"
              % (pid, dm, z, hg, exp, rel, got, "PASS" if ok else "★FAIL"))

    # ── P16: 不报错/不返回 None ──
    print("\n【P16】ten_god 对藏干输入的健壮性")
    print("-" * 100)
    errs = []
    for dm in "甲乙丙丁戊己庚辛壬癸":
        for z in ZHI:
            for hg in (HIDDEN.get(z) or []):
                try:
                    v = ten_god(dm, hg)
                except Exception as e:
                    errs.append((dm, hg, "异常:%s" % e))
                    continue
                if v is None:
                    errs.append((dm, hg, "None"))
                elif v == "?":
                    errs.append((dm, hg, "'?'"))
    ok16 = not errs
    allok = allok and ok16
    print("输入组合 = 10 日主 × 全部藏干   异常 = %d   %s"
          % (len(errs), "PASS" if ok16 else "★FAIL"))
    for e in errs[:8]:
        print("      %s" % (e,))

    # ── P17: 12 支 × 全部藏干 全有值 ──
    print("\n【P17】12 支 × 全部藏干 覆盖")
    print("-" * 100)
    total = 0
    q = 0
    for z in ZHI:
        for hg in (HIDDEN.get(z) or []):
            total += 1
            for dm in "甲乙丙丁戊己庚辛壬癸":
                if ten_god(dm, hg) == "?":
                    q += 1
    ok17 = (total > 0) and q == 0
    allok = allok and ok17
    print("藏干条目 = %d   '?' 出现 = %d   %s"
          % (total, q, "PASS" if ok17 else "★FAIL"))

    print("\n" + "=" * 100)
    print("探针总结: %s"
          % ("★ 全 PASS —— 可报甲②③ 真实数据"
             if allok else "★★ 有 FAIL —— 按 2f, 不报任何真实数据"))
    print("=" * 100)


if __name__ == "__main__":
    main()