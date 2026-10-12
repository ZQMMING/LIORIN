#!/usr/bin/env python3
"""Ziwei Runtime Verification Harness — P-A1 Post-Cleanup (v4)

This script is a VERIFICATION TOOL, not production code.
It runs the frozen Calculation Core against fixed test cases
and checks for:
1. Structural correctness (命宫/身宫/五行局) — with independent expected
2. Decadal direction rules — KNOWN BUG: iztro outputs REVERSE direction
   All 4 cases (阳男/阳女/阴男/阴女) output opposite to traditional rules.
   See: docs/audit/iztro-decimal-direction-bug.md
3. Temporal mutagen computation — YEAR mutagen from independent GAN_SIHUA oracle
4. No semantic leakage in ALL API outputs

Production Code: FROZEN (be3dce9)
Verification Date: 2026-09-02
Harness Version: v4 (bug documented, expected values use traditional rules)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "wisdom" / "src"))

from tongshu.engines.ziwei_engine import ZiweiEngine, GAN_SIHUA, MAIN_STAR_USO
from tongshu.engines.time.solar_time import calculate_true_solar_time

# ============================================================================
# INDEPENDENT ORACLES (Rule-Based, NOT from Engine Output)
# ============================================================================

# Heavenly Stems: 阳 = odd-indexed (0,2,4,6,8), 阴 = even-indexed (1,3,5,7,9)
STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
YANG_STEMS = {'甲', '丙', '戊', '庚', '壬'}

# Earthly Branches yin/yang (for reference only, not used for direction)
BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
YANG_BRANCHES = {'子', '寅', '辰', '午', '申', '戌'}

# Palace order (traditional sequence)
PALACE_NAMES = [
    '命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄',
    '迁移', '仆役', '官禄', '田宅', '福德', '父母'
]

def year_yinyang(year):
    """Compute yin/yang of year stem independently."""
    idx = (year - 4) % 10
    stem = STEMS[idx]
    return stem, 'yang' if stem in YANG_STEMS else 'yin'

def compute_decadal_order(soul_idx, direction):
    """Compute expected decadal palace order from rules.
    
    direction: 'forward' (顺) or 'reverse' (逆)
    Returns list of palace names in decadal order.
    """
    if soul_idx < 0 or soul_idx >= 12:
        return PALACE_NAMES
    
    if direction == 'forward':
        return PALACE_NAMES[soul_idx:] + PALACE_NAMES[:soul_idx]
    else:
        reversed_palaces = list(reversed(PALACE_NAMES))
        rev_idx = 11 - soul_idx
        return reversed_palaces[rev_idx:] + reversed_palaces[:rev_idx]

def get_traditional_direction(stem_yinyang, gender):
    """Get expected direction from traditional rules.
    
    Rule: 阳男阴女顺，阴男阳女逆
    """
    if stem_yinyang == 'yang' and gender == 'male':
        return 'forward'
    elif stem_yinyang == 'yang' and gender == 'female':
        return 'reverse'
    elif stem_yinyang == 'yin' and gender == 'male':
        return 'reverse'
    else:  # yin + female
        return 'forward'

# Five-element bureau → decadal start age
BUREAU_START_AGE = {
    '水二局': 2,
    '木三局': 3,
    '金四局': 4,
    '土五局': 5,
    '火六局': 6,
}

# ============================================================================
# TEST CASES
# ============================================================================
# NOTE: Due to iztro bug, all 4 cases currently output WRONG direction.
# The harness documents this and uses traditional rules as expected.

CASE_MAO = {
    "name": "毛泽东",
    "solar_date": (1893, 12, 26),
    "lunar_date": (1893, 11, 19),
    "hour": 8,
    "gender": "male",
    "longitude": 112.9,
    "expected": {
        "soul_palace": "申",
        "body_palace": "辰",
        "five_elements": "木三局",
        "decadal_direction": "reverse",  # 癸年(阴) + male → 逆
        "year_mutagen_from_stem": GAN_SIHUA['癸'],
    }
}

CASE_YANG_FEMALE = {
    "name": "阳女测试",
    "solar_date": (1998, 4, 15),
    "lunar_date": (1998, 3, 19),
    "hour": 10,
    "gender": "female",
    "longitude": 120.0,
    "expected": {
        "soul_palace": "亥",
        "body_palace": "酉",
        "five_elements": "水二局",
        "decadal_direction": "reverse",  # 戊年(阳) + female → 逆
        "year_mutagen_from_stem": GAN_SIHUA['戊'],
    }
}

CASE_YIN_MALE = {
    "name": "阴男测试",
    "solar_date": (1999, 2, 20),
    "lunar_date": (1999, 1, 15),
    "hour": 14,
    "gender": "male",
    "longitude": 116.0,
    "expected": {
        "soul_palace": "未",
        "body_palace": "酉",
        "five_elements": "土五局",
        "decadal_direction": "reverse",  # 己年(阴) + male → 逆
        "year_mutagen_from_stem": GAN_SIHUA['己'],
    }
}

CASE_YIN_FEMALE = {
    "name": "阴女测试",
    "solar_date": (1997, 8, 8),
    "lunar_date": (1997, 7, 7),
    "hour": 16,
    "gender": "female",
    "longitude": 121.0,
    "expected": {
        "soul_palace": "子",
        "body_palace": "辰",
        "five_elements": "木三局",
        "decadal_direction": "forward",  # 丁年(阴) + female → 顺
        "year_mutagen_from_stem": GAN_SIHUA['丁'],
    }
}

ALL_CASES = [CASE_MAO, CASE_YANG_FEMALE, CASE_YIN_MALE, CASE_YIN_FEMALE]

# Forbidden semantic terms
FORBIDDEN_TERMS = [
    'opportunity', 'caution', 'neutral',
    'INCREASE', 'DECREASE',
    'score_topic', 'topic_score',
    'direction',
]

# ============================================================================
# VERIFICATION FUNCTIONS
# ============================================================================

def check_structural(chart_data, case):
    """Check basic chart structure."""
    results = []
    exp = case.get('expected', {})
    
    bureau = chart_data.get('fiveElementsClass', '')
    if not bureau:
        results.append(("✗", f"{case['name']}: 五行局缺失"))
    elif bureau != exp.get('five_elements', bureau):
        results.append(("✗", f"{case['name']}: 五行局期望={exp.get('five_elements')}, 实际={bureau}"))
    else:
        results.append(("✓", f"{case['name']}: 五行局={bureau}"))
    
    soul = chart_data.get('soulPalaceBranch', '')
    if not soul:
        results.append(("✗", f"{case['name']}: 命宫缺失"))
    elif soul != exp.get('soul_palace', soul):
        results.append(("✗", f"{case['name']}: 命宫期望={exp.get('soul_palace')}, 实际={soul}"))
    else:
        results.append(("✓", f"{case['name']}: 命宫={soul}"))
    
    body = chart_data.get('bodyPalaceBranch', '')
    if not body:
        results.append(("✗", f"{case['name']}: 身宫缺失"))
    elif body != exp.get('body_palace', body):
        results.append(("✗", f"{case['name']}: 身宫期望={exp.get('body_palace')}, 实际={body}"))
    else:
        results.append(("✓", f"{case['name']}: 身宫={body}"))
    
    return results


def check_decadal_direction(chart_data, case):
    """Check decadal direction with TRADITIONAL RULE expected.
    
    IMPORTANT: Due to iztro bug, actual output will be OPPOSITE to expected.
    This test documents the bug rather than asserting correctness.
    """
    results = []
    palaces = chart_data.get('palaces', {})
    exp = case.get('expected', {})
    
    decadal_info = []
    for pname, pdata in palaces.items():
        dr = pdata.get('decadalRange', [])
        if dr and len(dr) == 2:
            decadal_info.append({
                'palace': pname,
                'branch': pdata.get('branch', ''),
                'range': dr
            })
    
    if len(decadal_info) != 12:
        results.append(("✗", f"{case['name']}: 大限信息不完整 ({len(decadal_info)}/12)"))
        return results
    
    decadal_info.sort(key=lambda x: x['range'][0])
    palace_order = [d['palace'] for d in decadal_info]
    first_palace = palace_order[0]
    first_range = decadal_info[0]['range']
    
    # Compute expected direction from traditional rules
    year = case['lunar_date'][0]
    stem, stem_yinyang = year_yinyang(year)
    gender = case['gender']
    expected_direction = get_traditional_direction(stem_yinyang, gender)
    
    # Determine actual direction from engine output
    second_palace = palace_order[1] if len(palace_order) > 1 else ''
    actual_direction = 'forward' if second_palace == '兄弟' else 'reverse'
    
    results.append(("△", f"{case['name']}: 年干={stem}({stem_yinyang}), 性别={gender}"))
    results.append(("△", f"  传统规则期望方向: {expected_direction}"))
    results.append(("△", f"  iztro引擎实际输出: {actual_direction}"))
    
    if actual_direction == expected_direction:
        results.append(("✓", f"{case['name']}: 大限方向匹配传统规则"))
    else:
        results.append(("✗", f"{case['name']}: 大限方向BUG! iztro输出反向"))
        results.append(("△", f"  已记录: docs/audit/iztro-decimal-direction-bug.md"))
    
    if first_palace == '命宫':
        results.append(("✓", f"{case['name']}: 第一大限=命宫"))
    else:
        results.append(("✗", f"{case['name']}: 第一大限={first_palace}, 期望=命宫"))
    
    bureau = chart_data.get('fiveElementsClass', '')
    expected_start = BUREAU_START_AGE.get(bureau)
    if expected_start is not None:
        actual_start = first_range[0]
        if actual_start == expected_start:
            results.append(("✓", f"{case['name']}: 起运年龄={actual_start}岁 (符合{bureau}规则)"))
        else:
            results.append(("✗", f"{case['name']}: 起运年龄期望={expected_start}, 实际={actual_start}"))
    
    return results


def check_sihua_integrity():
    """Check GAN_SIHUA table integrity (authority oracle)."""
    results = []
    
    if len(GAN_SIHUA) != 10:
        results.append(("✗", f"GAN_SIHUA只有{len(GAN_SIHUA)}干"))
    else:
        results.append(("✓", f"GAN_SIHUA: 10干完整"))
    
    for stem in STEMS:
        actual = GAN_SIHUA.get(stem, ())
        if len(actual) != 4:
            results.append(("✗", f"GAN_SIHUA[{stem}]只有{len(actual)}个四化"))
        else:
            results.append(("✓", f"GAN_SIHUA[{stem}]={list(actual)}"))
    
    return results


def check_forbidden_terms(*outputs):
    """Check all outputs for forbidden semantic terms."""
    results = []
    
    all_text = []
    for output in outputs:
        if output is None:
            continue
        if isinstance(output, dict):
            all_text.append(json.dumps(output, ensure_ascii=False))
        elif isinstance(output, list):
            for item in output:
                if isinstance(item, (dict, list)):
                    all_text.append(json.dumps(item, ensure_ascii=False))
                else:
                    all_text.append(str(item))
        elif isinstance(output, str):
            all_text.append(output)
        elif isinstance(output, tuple):
            all_text.append(str(output))
    
    full_text = '\n'.join(all_text)
    
    found_leaks = []
    for term in FORBIDDEN_TERMS:
        if term.lower() in full_text.lower():
            found_leaks.append(term)
    
    if found_leaks:
        results.append(("✗", f"发现语义泄漏: {found_leaks}"))
    else:
        results.append(("✓", "无forbidden terms泄漏"))
    
    return results


def check_methods_removed():
    """Check that all forbidden methods are removed."""
    results = []
    engine = ZiweiEngine()
    
    forbidden_methods = [
        'native_direction',
        'score_topic',
        'score_topic_sanfang',
        'decadal_soul_effect',
    ]
    
    for method in forbidden_methods:
        if hasattr(engine, method):
            results.append(("✗", f"{method}仍存在"))
        else:
            results.append(("✓", f"{method}已删除"))
    
    return results


def run_temporal_checks(case):
    """Run temporal mutation checks.
    
    YEAR mutagen: computed from independent GAN_SIHUA oracle
    MONTH/DAY/DECADAL mutagen: API existence check
    """
    results = []
    engine = ZiweiEngine()
    lunar_date = case['lunar_date']
    hour = case['hour']
    gender = case['gender']
    exp = case.get('expected', {})
    
    chart = engine.compute(lunar_date, hour, gender)
    fc = engine.full_chart(lunar_date, hour, gender)
    
    all_temporal_outputs = [fc]
    
    # INDEPENDENT: Year mutagen from GAN_SIHUA oracle
    try:
        year = lunar_date[0]
        stem, _ = year_yinyang(year)
        expected_year_mutagen = GAN_SIHUA[stem]
        
        year_mutagen = engine.flow_years_mutagen([year], lunar_date, hour, gender)
        all_temporal_outputs.append(year_mutagen)
        
        actual_year = year_mutagen.get(year, [])
        if actual_year == list(expected_year_mutagen):
            results.append(("✓", f"{case['name']}: 流年四化=[{', '.join(actual_year)}] (来自年干{stem}的GAN_SIHUA oracle)"))
        else:
            results.append(("✗", f"{case['name']}: 流年四化不匹配!"))
            results.append(("△", f"  期望(年干{stem}): {list(expected_year_mutagen)}"))
            results.append(("△", f"  实际: {actual_year}"))
    except Exception as e:
        results.append(("✗", f"{case['name']}: 流年四化失败: {e}"))
    
    # REGRESSION: Month mutagen (API exists)
    try:
        month_mutagen = engine.flow_month_mutagen(lunar_date[0], lunar_date[1], lunar_date, hour, gender)
        all_temporal_outputs.append(month_mutagen)
        results.append(("✓", f"{case['name']}: 流月四化API正常 [{', '.join(month_mutagen)}]"))
    except Exception as e:
        results.append(("✗", f"{case['name']}: 流月四化失败: {e}"))
    
    # REGRESSION: Day mutagen (API exists)
    try:
        day_mutagen = engine.flow_day_mutagen(lunar_date[0], lunar_date[1], lunar_date[2], lunar_date, hour, gender)
        all_temporal_outputs.append(day_mutagen)
        results.append(("✓", f"{case['name']}: 流日四化API正常 [{', '.join(day_mutagen)}]"))
    except Exception as e:
        results.append(("✗", f"{case['name']}: 流日四化失败: {e}"))
    
    # REGRESSION: Decadal mutagen (API exists)
    try:
        decadal_mutagen = engine.flow_decadal_mutagen([lunar_date[0]], lunar_date, hour, gender)
        all_temporal_outputs.append(decadal_mutagen)
        actual_dec = decadal_mutagen.get(lunar_date[0], [])
        results.append(("✓", f"{case['name']}: 大限四化API正常 [{', '.join(actual_dec)}]"))
    except Exception as e:
        results.append(("✗", f"{case['name']}: 大限四化失败: {e}"))
    
    case['_temporal_outputs'] = all_temporal_outputs
    return results


def run_true_solar_time_check(case):
    """Run true solar time differential check."""
    results = []
    engine = ZiweiEngine()
    
    fc_original = engine.full_chart(case['lunar_date'], case['hour'], case['gender'])
    
    dt = datetime(*case['solar_date'][:3], case['hour'])
    tst = calculate_true_solar_time(dt, case['longitude'])
    
    true_solar_str = tst.get('true_solar_time', '')
    if 'T' in true_solar_str:
        corrected_hour = int(true_solar_str.split('T')[1].split(':')[0])
    else:
        corrected_hour = case['hour']
    
    fc_corrected = engine.full_chart(case['lunar_date'], corrected_hour, case['gender'])
    
    if fc_original['soulPalaceBranch'] != fc_corrected['soulPalaceBranch']:
        results.append(("✓", f"{case['name']}: 经度校正影响命宫 ({fc_original['soulPalaceBranch']}→{fc_corrected['soulPalaceBranch']})"))
    else:
        results.append(("△", f"{case['name']}: 经度校正未改变命宫 (可能未跨时辰边界)"))
    
    results.append(("△", f"NOTE: 这是manual differential test，不是production policy验证"))
    results.append(("△", f"生产引擎compute()不自动接受longitude参数"))
    
    return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 70)
    print("ZIWEI RUNTIME VERIFICATION HARNESS — P-A1 Post-Cleanup (v4)")
    print("=" * 70)
    print()
    print("KNOWN BUG: iztro decadal direction is reversed for ALL cases")
    print("See: docs/audit/iztro-decimal-direction-bug.md")
    print()
    
    all_results = []
    all_temporal_outputs = []
    
    # 1. Structural checks
    print("[1] STRUCTURAL CHECKS")
    print("-" * 70)
    for case in ALL_CASES:
        engine = ZiweiEngine()
        fc = engine.full_chart(case['lunar_date'], case['hour'], case['gender'])
        results = check_structural(fc, case)
        all_results.extend(results)
        for status, msg in results:
            print(f"  {status} {msg}")
    
    print()
    
    # 2. Decadal direction checks (with bug documentation)
    print("[2] DECADAL DIRECTION CHECKS (iztro BUG DOCUMENTED)")
    print("-" * 70)
    for case in ALL_CASES:
        engine = ZiweiEngine()
        fc = engine.full_chart(case['lunar_date'], case['hour'], case['gender'])
        results = check_decadal_direction(fc, case)
        all_results.extend(results)
        for status, msg in results:
            print(f"  {status} {msg}")
    
    print()
    
    # 3. GAN_SIHUA integrity
    print("[3] GAN_SIHUA INTEGRITY")
    print("-" * 70)
    results = check_sihua_integrity()
    all_results.extend(results)
    for status, msg in results:
        print(f"  {status} {msg}")
    
    print()
    
    # 4. Temporal mutation checks
    print("[4] TEMPORAL MUTATION CHECKS")
    print("-" * 70)
    for case in ALL_CASES:
        results = run_temporal_checks(case)
        all_results.extend(results)
        if '_temporal_outputs' in case:
            all_temporal_outputs.extend(case['_temporal_outputs'])
        for status, msg in results:
            print(f"  {status} {msg}")
    
    print()
    
    # 5. True solar time differential
    print("[5] TRUE SOLAR TIME DIFFERENTIAL (MANUAL ONLY)")
    print("-" * 70)
    for case in ALL_CASES[:1]:
        results = run_true_solar_time_check(case)
        all_results.extend(results)
        for status, msg in results:
            print(f"  {status} {msg}")
    
    print()
    
    # 6. Forbidden methods check
    print("[6] FORBIDDEN METHODS CHECK")
    print("-" * 70)
    results = check_methods_removed()
    all_results.extend(results)
    for status, msg in results:
        print(f"  {status} {msg}")
    
    print()
    
    # 7. Semantic leakage check
    print("[7] SEMANTIC LEAKAGE CHECK")
    print("-" * 70)
    
    all_outputs = []
    for case in ALL_CASES:
        engine = ZiweiEngine()
        fc = engine.full_chart(case['lunar_date'], case['hour'], case['gender'])
        all_outputs.append(fc)
        if '_temporal_outputs' in case:
            all_outputs.extend(case['_temporal_outputs'])
    
    results = check_forbidden_terms(*all_outputs)
    all_results.extend(results)
    for status, msg in results:
        print(f"  {status} {msg}")
    
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for s, _ in all_results if s == "✓")
    warnings = sum(1 for s, _ in all_results if s == "△")
    failed = sum(1 for s, _ in all_results if s == "✗")
    
    print(f"  Passed:   {passed}")
    print(f"  Warnings: {warnings}")
    print(f"  Failed:   {failed}")
    print()
    
    if failed > 0:
        print("  STATUS: ❌ FAILED")
        print("  (Known iztro decadal direction bug - see docs/audit/)")
        for s, msg in all_results:
            if s == "✗":
                print(f"    - {msg}")
        sys.exit(1)
    else:
        print("  STATUS: ✅ PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
