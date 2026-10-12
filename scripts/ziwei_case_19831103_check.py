# -*- coding: utf-8 -*-
"""校对：外部微信公众号案例（1983-11-03 12:00 女）实跑比对。

案例来源：公众号《坤造，癸亥壬戌乙未壬午（1983.11.3）》
预期基准（文章原文）：
  四柱：癸亥 壬戌 乙未 壬午
  五行局：土五局
  来因宫：疾厄宫（癸亥）
  命宫=身宫：丙辰【七杀庙旺】
  命主：廉贞；身主：天机
  癸干生年四化：破军化禄(官禄)、巨门化权(子女)、太阴化科(疾厄)、贪狼化忌(财帛)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["TONGSHU_ALLOW_ZIWEI_STUB"] = "1"

from tongshu.engines.ziwei_engine import ZiweiEngine
from tongshu.engines.ziwei.rules.answer_layer import build_answer
from tongshu.engines.ziwei.rules.interpretation import (
    DIMENSION_ORDER,
    build_life_reading,
)
from tongshu.engines.ziwei.rules.multi_method import compute_multi_method_signals

# 文章案例：公历 1983-11-03 12:00 女（= 农历 癸亥年九月廿九 午时）
# 注意：ZiweiEngine.full_chart 入参为**农历**，故此处传农历 (1983, 9, 29)。
CASE = (1983, 9, 29)
HOUR = 12
GENDER = "female"
CASE_SOLAR = "1983-11-03 12:00"

SEP = "=" * 72

# 文章原文基准（逐项）
EXPECT_PALACES = {
    # 宫名: (宫干支, 主星集合)
    "命宫":   ("丙辰", {"七杀"}),
    "兄弟":   ("乙卯", {"太阳", "天梁"}),
    "夫妻":   ("甲寅", {"武曲", "天相"}),
    "子女":   ("乙丑", {"天同", "巨门"}),
    "财帛":   ("甲子", {"贪狼"}),
    "疾厄":   ("癸亥", {"太阴"}),
    "迁移":   ("壬戌", {"廉贞", "天府"}),
    "仆役":   ("辛酉", set()),          # 无主星，借贪狼
    "官禄":   ("庚申", {"破军"}),
    "田宅":   ("己未", set()),          # 无主星，借紫微
    "福德":   ("戊午", {"紫微"}),
    "父母":   ("丁巳", {"天机"}),
}
EXPECT_WUXING = "土五局"
EXPECT_SIHUA = {  # 癸干生年四化：星 → 落宫
    "破军": ("禄", "官禄"),
    "巨门": ("权", "子女"),
    "太阴": ("科", "疾厄"),
    "贪狼": ("忌", "财帛"),
}


def main():
    eng = ZiweiEngine()
    chart = eng.full_chart(CASE, HOUR, GENDER)

    print(SEP)
    print(f"案例：公历 {CASE_SOLAR} 女（农历 {CASE} 午时）")
    print(SEP)

    # ── 1. 排盘基础核对 ──
    print("\n【1. 排盘基础 — 与文章比对】")
    print(f"  命宫地支/宫名：{getattr(chart, 'soulPalaceBranch', 'N/A')}")
    print(f"  身宫地支：{getattr(chart, 'bodyPalaceBranch', 'N/A')}")
    print(f"  五行局：{getattr(chart, 'wuxingJu', getattr(chart, 'fiveElementsClass', 'N/A'))}")
    print(f"  命主：{getattr(chart, 'soulStar', 'N/A')}  身主：{getattr(chart, 'bodyStar', 'N/A')}")
    print(f"  四柱：{getattr(chart, 'lunarYearGanZhi', '?')} "
          f"{getattr(chart, 'lunarMonthGanZhi', '?')} "
          f"{getattr(chart, 'lunarDayGanZhi', '?')} "
          f"{getattr(chart, 'lunarHourGanZhi', '?')}")

    # 十二宫主星
    print("\n  十二宫主星分布：")
    for pn, pd in chart.palaces.items():
        major = pd.get("major", []) if isinstance(pd, dict) else getattr(pd, "major", [])
        stems = pd.get("stem", "") if isinstance(pd, dict) else ""
        branch = pd.get("branch", "") if isinstance(pd, dict) else ""
        print(f"    {pn:4s} {stems}{branch}  {'/'.join(major) if major else '（空）'}")

    # ── 2. 生年四化核对 ──
    print("\n【2. 生年四化 — 与文章比对】")
    print("  文章：破军禄→官禄、巨门权→子女、太阴科→疾厄、贪狼忌→财帛")
    try:
        from tongshu.engines.ziwei_engine import GAN_SIHUA
        sihua = GAN_SIHUA.get(getattr(chart, "yearGan", ""), None)
        print(f"  引擎 yearGan={getattr(chart, 'yearGan', '?')} 四化表：{sihua}")
    except Exception as e:
        print(f"  (取四化表失败: {e})")

    # ── 3. 答案层分层结构 ──
    print("\n【3. 答案层分层结构】")
    ans = build_answer(chart)
    print(f"  顶层键：{sorted(ans.keys())}")
    print(f"  dimensions（宫位维，{len(ans['dimensions'])} 个）：{ans['dimensions']}")
    print(f"  宫位维计数：{ans['summary']['dimension_counts']}")
    print(f"  body_use（体用层）：{ans['summary']['body_use_counts']}")

    # ── 4. 12 维断语（interpretation）—— 与文章六大领域/宫位对比 ──
    print("\n【4. 十二维断语（interpretation）】")
    sig = compute_multi_method_signals(chart)
    reading = build_life_reading(chart, sig, target_year=2026)
    for d in reading.dimensions:
        concl = (d.conclusion or "").strip()
        print(f"\n  ▎{d.dimension}（宫={d.palace}）")
        print(f"    {concl[:200] if concl else '（空）'}")

    # ── 5. 领域层（domain_reading）—— 对应文章「六大领域」 ──
    print("\n【5. 领域层（domain_reading）】")
    try:
        from tongshu.engines.ziwei.rules.domain_reading import build_domain_readings
        domains = build_domain_readings(chart, eng.get_all_zihua(chart))
        for dr in getattr(domains, "domain_readings", []):
            print(f"\n  ▎{dr.domain}")
            print(f"    结论：{(dr.conclusion or '')[:180]}")
            if dr.risk_points:
                print(f"    风险：{'；'.join(dr.risk_points[:3])}")
    except Exception as e:
        print(f"  (domain_reading 失败: {e})")

    print("\n" + SEP)
    print("【6. 自动校对 — 与文章逐项比对】")
    print(SEP)
    ok, fail = 0, 0

    # 6.1 五行局
    ju = getattr(chart, "wuxingJu", getattr(chart, "fiveElementsClass", ""))
    hit = (ju == EXPECT_WUXING)
    ok, fail = (ok + 1, fail) if hit else (ok, fail + 1)
    print(f"  [{'✓' if hit else '✗'}] 五行局：期望 {EXPECT_WUXING}，实得 {ju}")

    # 6.2 命宫/身宫地支
    soul_br = getattr(chart, "soulPalaceBranch", "")
    body_br = getattr(chart, "bodyPalaceBranch", "")
    hit = (soul_br == "辰" and body_br == "辰")
    ok, fail = (ok + 1, fail) if hit else (ok, fail + 1)
    print(f"  [{'✓' if hit else '✗'}] 命宫=身宫同宫：期望 辰/辰，实得 {soul_br}/{body_br}")

    # 6.3 十二宫主星
    print("\n  ── 十二宫主星/干支 ──")
    for pn, (exp_gz, exp_stars) in EXPECT_PALACES.items():
        pd = chart.palaces.get(pn, {})
        got_gz = f"{pd.get('stem','')}{pd.get('branch','')}"
        got_stars = set(pd.get("major", []) or [])
        hit_gz = (got_gz == exp_gz)
        hit_st = (got_stars == exp_stars)
        hit = hit_gz and hit_st
        ok, fail = (ok + 1, fail) if hit else (ok, fail + 1)
        mark = "✓" if hit else "✗"
        detail = ""
        if not hit_gz:
            detail += f" 干支期望{exp_gz}实得{got_gz};"
        if not hit_st:
            detail += f" 主星期望{sorted(exp_stars)}实得{sorted(got_stars)};"
        print(f"  [{mark}] {pn:4s} {got_gz} {'/'.join(sorted(got_stars)) or '（空）'}{detail}")

    # 6.4 生年四化落宫
    print("\n  ── 生年四化（癸干）落宫 ──")
    try:
        from tongshu.engines.ziwei_engine import GAN_SIHUA
        year_gan = getattr(chart, "yearGan", None)
        tbl = GAN_SIHUA.get(year_gan, {}) if year_gan else {}
        # 建「星 → 所在宫」索引
        star_palace = {}
        for pn, pd in chart.palaces.items():
            for s in (pd.get("major", []) or []) + (pd.get("minor", []) or []):
                star_palace.setdefault(s, pn)
        for star, (mut, exp_palace) in EXPECT_SIHUA.items():
            got_palace = star_palace.get(star, "")
            hit = (got_palace == exp_palace)
            ok, fail = (ok + 1, fail) if hit else (ok, fail + 1)
            print(f"  [{'✓' if hit else '✗'}] {star}化{mut}：期望落 {exp_palace}，"
                  f"实得落 {got_palace or '未找到'}")
    except Exception as e:
        print(f"  (四化校对失败: {e})")

    print("\n" + SEP)
    total = ok + fail
    print(f"校对结果：{ok}/{total} 通过，{fail} 不通过")
    if fail == 0:
        print("★ 引擎排盘与文章逐项完全一致")
    else:
        print("⚠ 存在不一致项，见上")
    print(SEP)


if __name__ == "__main__":
    main()
