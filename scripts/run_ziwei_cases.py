#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲派引擎案例验证 - 紫薇案例.txt"""

import sys
import os
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.chdir(PROJECT_ROOT)

from tongshu.engines.bazi_engine import BaziEngine
from tongshu.engines.blind_bazi_engine import compute_blind_bazi

# 案例数据（从txt提取）
CASES = [
    # 性别, 公历日期(年月日时), 期望四柱(干支), 案例描述
    ("女", (2027, 3, 22, 2), "DING WEI GUI MAO GENG ZI DING CHOU", "案例2: 伤官损官"),
    ("男", (2028, 8, 3, 9), "WU SHEN JI WEI GENG SHEN XIN SI", "案例3: 禄神受损"),
    ("女", (1974, 12, 24, 7), "JIA YIN BING ZI JI HAI WU CHEN", "案例4: 宾主倒置"),
    ("男", (1948, 2, 4, 17), "DING HAI GUI CHOU JI WEI GUI YOU", "案例5: 墓库冲开"),
    ("男", (2010, 2, 18, 3), "GENG YIN WU YIN JI HAI BING YIN", "案例6: 包局得权"),
    ("男", (1968, 7, 22, 13), "WU SHEN JI WEI GUI SI JI WEI", "案例7: 财制印格"),
    ("男", (1965, 9, 4, 13), "YI SI JIA SHEN XIN YOU YI WEI", "案例8: 做功无效"),
    ("女", (1968, 10, 21, 3), "WU SHEN REN XU JIA ZI BING YIN", "案例10: 婚期"),
    ("女", (1950, 9, 20, 9), "GENG YIN YI YOU WU WU DING SI", "案例11: 禄被克坏"),
    ("女", (1947, 4, 20, 3), "DING HAI JIA CHEN JI SI BING YIN", "案例12: 蒋介石"),
    ("女", (1964, 6, 24, 7), "JIA CHEN GENG WU JIA CHEN WU CHEN", "案例13: 离婚"),
    ("女", (1985, 5, 22, 21), "YI CHOU XIN SI XIN YOU JI HAI", "案例14: 一岁丧母"),
    ("女", (2015, 9, 21, 1), "YI WEI YI YOU GENG ZI DING CHOU", "案例15: 16岁死母"),
]

def main():
    print("=" * 70)
    print("盲派引擎案例验证")
    print("=" * 70)

    bazi_engine = BaziEngine()
    passed = 0
    results = []

    for i, (gender, birth, expected, desc) in enumerate(CASES, 1):
        print(f"\n【案例{i}】{desc}")
        print(f"  日期: {birth[0]}-{birth[1]:02d}-{birth[2]:02d} {birth[3]:02d}:00 | 性别: {gender}")
        print(f"  期望: {expected}")

        try:
            # 计算四柱
            chart = bazi_engine.compute(birth, gender=gender)
            pillars = [chart.year_pillar, chart.month_pillar, chart.day_pillar, chart.hour_pillar]
            computed = " ".join([f"{p.heavenly_stem} {p.earthly_branch}" for p in pillars])

            match = computed == expected
            status = "✓ PASS" if match else "✗ FAIL"
            if match:
                passed += 1

            print(f"  计算: {computed} {status}")

            # 盲派分析
            blind = compute_blind_bazi(birth, gender)
            d = blind.to_dict()

            print(f"  包局: has_baoju={blind.has_baoju}, pattern={blind.baoju_pattern!r}")
            print(f"  墓库: closed={blind.muku_closed}, chonged={blind.muku_chonged}")
            print(f"  合化: type={blind.he_type!r}, is_hua={blind.is_hua}")
            print(f"  做功: {len(blind.zuo_gong_methods)}项 → {blind.zuo_gong_methods[:3]}...")

            results.append({
                "case": i,
                "desc": desc,
                "match": match,
                "computed": computed,
                "baoju": blind.has_baoju,
                "muku_chonged": bool(blind.muku_chonged),
                "he_type": blind.he_type,
            })

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({"case": i, "desc": desc, "match": False, "error": str(e)})

    # 汇总
    print("\n" + "=" * 70)
    print("验证结果汇总")
    print("=" * 70)
    print(f"总案例数: {len(CASES)}")
    print(f"四柱匹配: {passed}/{len(CASES)} = {passed/len(CASES)*100:.1f}%")

    # 特性统计
    baoju_count = sum(1 for r in results if r.get("baoju"))
    muku_count = sum(1 for r in results if r.get("muku_chonged"))
    he_count = sum(1 for r in results if r.get("he_type"))

    print(f"\n特性覆盖:")
    print(f"  包局判定: {baoju_count}个案例触发")
    print(f"  墓库冲开: {muku_count}个案例触发")
    print(f"  合化检测: {he_count}个案例触发")

    # 失败详情
    failed = [r for r in results if not r.get("match")]
    if failed:
        print(f"\n失败案例:")
        for r in failed:
            print(f"  案例{r['case']}: {r['desc']}")

    return results

if __name__ == "__main__":
    main()
