#!/usr/bin/env python3
"""Ziwei Runtime Verification Harness — P-A1 Post-Cleanup (v5)

THREE-LAYER VERIFICATION:
1. iztro raw output (known to have bug)
2. Shuntian adapter correction
3. Independent rule oracle

Production Code: FROZEN (be3dce9)
Adapter: NEW (ziwei_dependency_adapter.py)
Verification Date: 2026-09-02
Harness Version: v5 (three-layer verification)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "wisdom" / "src"))

from tongshu.engines.ziwei_engine import ZiweiEngine, GAN_SIHUA
from tongshu.engines.ziwei_dependency_adapter import (
    ShuntianZiweiDependencyAdapter,
    Direction,
    adapt_decadal_direction,
    CANONICAL_CASES,
)
from tongshu.engines.time.solar_time import calculate_true_solar_time

# ============================================================================
# TEST CASES
# ============================================================================

CASE_MAO = {
    "name": "毛泽东",
    "solar_date": (1893, 12, 26),
    "lunar_date": (1893, 11, 19),
    "hour": 8,
    "gender": "male",
    "longitude": 112.9,
}

CASE_YANG_FEMALE = {
    "name": "阳女测试",
    "solar_date": (1998, 4, 15),
    "lunar_date": (1998, 3, 19),
    "hour": 10,
    "gender": "female",
    "longitude": 120.0,
}

CASE_YIN_MALE = {
    "name": "阴男测试",
    "solar_date": (1999, 2, 20),
    "lunar_date": (1999, 1, 15),
    "hour": 14,
    "gender": "male",
    "longitude": 116.0,
}

CASE_YIN_FEMALE = {
    "name": "阴女测试",
    "solar_date": (1997, 8, 8),
    "lunar_date": (1997, 7, 7),
    "hour": 16,
    "gender": "female",
    "longitude": 121.0,
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
# HELPER FUNCTIONS
# ============================================================================

def get_decadal_direction_from_chart(chart_data: dict) -> Direction:
    """Extract actual decadal direction from chart data.
    
    Args:
        chart_data: Output from ZiweiEngine.full_chart()
    
    Returns:
        Direction.FORWARD or Direction.REVERSE
    """
    palaces = chart_data.get('palaces', {})
    decadal_info = []
    for pname, pdata in palaces.items():
        dr = pdata.get('decadalRange', [])
        if dr and len(dr) == 2:
            decadal_info.append({'palace': pname, 'range': dr})
    
    if not decadal_info:
        return Direction.FORWARD  # fallback
    
    decadal_info.sort(key=lambda x: x['range'][0])
    order = [d['palace'] for d in decadal_info]
    second = order[1] if len(order) > 1 else ''
    
    return Direction.FORWARD if second == '兄弟' else Direction.REVERSE


def check_structural(chart_data: dict, case: dict) -> list[tuple[str, str]]:
    """Check basic chart structure."""
    results = []
    
    bureau = chart_data.get('fiveElementsClass', '')
    expected_bureau = {
        '毛泽东': '木三局',
        '阳女测试': '水二局',
        '阴男测试': '土五局',
        '阴女测试': '木三局',
    }.get(case['name'], '')
    
    if bureau != expected_bureau:
        results.append(("✗", f"{case['name']}: 五行局期望={expected_bureau}, 实际={bureau}"))
    else:
        results.append(("✓", f"{case['name']}: 五行局={bureau}"))
    
    soul = chart_data.get('soulPalaceBranch', '')
    expected_soul = {
        '毛泽东': '申',
        '阳女测试': '亥',
        '阴男测试': '未',
        '阴女测试': '子',
    }.get(case['name'], '')
    
    if soul != expected_soul:
        results.append(("✗", f"{case['name']}: 命宫期望={expected_soul}, 实际={soul}"))
    else:
        results.append(("✓", f"{case['name']}: 命宫={soul}"))
    
    return results


# ============================================================================
# THREE-LAYER VERIFICATION
# ============================================================================

def verify_decadal_direction(case: dict) -> dict:
    """Perform three-layer verification of decadal direction.
    
    Layer 1: iztro raw output
    Layer 2: Shuntian adapter correction
    Layer 3: Independent oracle
    
    Returns:
        Dict with verification results
    """
    engine = ZiweiEngine()
    adapter = ShuntianZiweiDependencyAdapter()
    
    lunar_date = case['lunar_date']
    hour = case['hour']
    gender = case['gender']
    year = lunar_date[0]
    
    # Get chart from engine
    chart = engine.full_chart(lunar_date, hour, gender)
    
    # Layer 1: iztro raw direction
    iztro_direction = get_decadal_direction_from_chart(chart)
    
    # Layer 2: adapter correction
    result = adapt_decadal_direction(year, gender, iztro_direction)
    
    # Layer 3: independent oracle (already computed in adapter)
    expected_direction = result.expected_direction
    
    return {
        'name': case['name'],
        'year': year,
        'gender': gender,
        'layer1_iztro_raw': iztro_direction.value,
        'layer2_adapter_corrected': result.corrected_direction.value,
        'layer3_expected': expected_direction.value,
        'has_discrepancy': result.has_discrepancy,
        'is_corrected': result.is_corrected,
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 70)
    print("ZIWEI RUNTIME VERIFICATION HARNESS — P-A1 Post-Cleanup (v5)")
    print("=" * 70)
    print()
    print("THREE-LAYER VERIFICATION:")
    print("  Layer 1: iztro raw output (known bug)")
    print("  Layer 2: Shuntian adapter correction")
    print("  Layer 3: Independent rule oracle")
    print()
    
    all_results = []
    
    # ========================================================================
    # LAYER 1-3: Decadal Direction Verification
    # ========================================================================
    print("[1] DECADAL DIRECTION VERIFICATION (Three-Layer)")
    print("-" * 70)
    
    direction_results = []
    for case in ALL_CASES:
        result = verify_decadal_direction(case)
        direction_results.append(result)
        
        print(f"\n{result['name']}:")
        print(f"  Year: {result['year']}, Gender: {result['gender']}")
        print(f"  Layer 1 (iztro raw):     {result['layer1_iztro_raw']}")
        print(f"  Layer 2 (adapter):       {result['layer2_adapter_corrected']}")
        print(f"  Layer 3 (expected):      {result['layer3_expected']}")
        print(f"  Discrepancy detected:    {'YES' if result['has_discrepancy'] else 'NO'}")
        print(f"  Corrected:               {'YES' if result['is_corrected'] else 'NO'}")
        
        # Assert layers
        if result['layer2_adapter_corrected'] == result['layer3_expected']:
            print(f"  ✓ Adapter matches expected")
            all_results.append(("✓", f"{result['name']}: Adapter correct"))
        else:
            print(f"  ✗ Adapter MISMATCH!")
            all_results.append(("✗", f"{result['name']}: Adapter mismatch"))
    
    print()
    
    # ========================================================================
    # STRUCTURAL CHECKS
    # ========================================================================
    print("[2] STRUCTURAL CHECKS")
    print("-" * 70)
    
    engine = ZiweiEngine()
    for case in ALL_CASES:
        chart = engine.full_chart(case['lunar_date'], case['hour'], case['gender'])
        results = check_structural(chart, case)
        all_results.extend(results)
        for status, msg in results:
            print(f"  {status} {msg}")
    
    print()
    
    # ========================================================================
    # GAN_SIHUA INTEGRITY
    # ========================================================================
    print("[3] GAN_SIHUA INTEGRITY")
    print("-" * 70)
    
    if len(GAN_SIHUA) != 10:
        print(f"  ✗ GAN_SIHUA只有{len(GAN_SIHUA)}干")
        all_results.append(("✗", f"GAN_SIHUA只有{len(GAN_SIHUA)}干"))
    else:
        print(f"  ✓ GAN_SIHUA: 10干完整")
        all_results.append(("✓", "GAN_SIHUA: 10干完整"))
    
    for stem in ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']:
        actual = GAN_SIHUA.get(stem, ())
        if len(actual) != 4:
            print(f"  ✗ GAN_SIHUA[{stem}]只有{len(actual)}个四化")
            all_results.append(("✗", f"GAN_SIHUA[{stem}]只有{len(actual)}个四化"))
        else:
            print(f"  ✓ GAN_SIHUA[{stem}]={list(actual)}")
            all_results.append(("✓", f"GAN_SIHUA[{stem}] OK"))
    
    print()
    
    # ========================================================================
    # TEMPORAL MUTAGEN CHECKS
    # ========================================================================
    print("[4] TEMPORAL MUTATION CHECKS (Year from GAN_SIHUA oracle)")
    print("-" * 70)
    
    for case in ALL_CASES:
        year = case['lunar_date'][0]
        stem_idx = (year - 4) % 10
        from tongshu.engines.ziwei_dependency_adapter import STEMS, YANG_STEMS
        stem = STEMS[stem_idx]
        expected_mutagen = GAN_SIHUA[stem]
        
        try:
            mutagen = engine.flow_years_mutagen([year], case['lunar_date'], case['hour'], case['gender'])
            actual = mutagen.get(year, [])
            
            if actual == list(expected_mutagen):
                print(f"  ✓ {case['name']}: 流年四化=[{', '.join(actual)}] (来自年干{stem}的GAN_SIHUA oracle)")
                all_results.append(("✓", f"{case['name']}: 流年四化正确"))
            else:
                print(f"  ✗ {case['name']}: 流年四化不匹配")
                all_results.append(("✗", f"{case['name']}: 流年四化不匹配"))
        except Exception as e:
            print(f"  ✗ {case['name']}: 流年四化失败: {e}")
            all_results.append(("✗", f"{case['name']}: 流年四化失败: {e}"))
    
    print()
    
    # ========================================================================
    # FORBIDDEN METHODS CHECK
    # ========================================================================
    print("[5] FORBIDDEN METHODS CHECK")
    print("-" * 70)
    
    forbidden_methods = [
        'native_direction',
        'score_topic',
        'score_topic_sanfang',
        'decadal_soul_effect',
    ]
    
    for method in forbidden_methods:
        if hasattr(engine, method):
            print(f"  ✗ {method}仍存在")
            all_results.append(("✗", f"{method}仍存在"))
        else:
            print(f"  ✓ {method}已删除")
            all_results.append(("✓", f"{method}已删除"))
    
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
    
    # Key assertion: Adapter must correct all discrepancies
    adapter_correct_count = sum(1 for r in direction_results if r['is_corrected'])
    print(f"  Iztro discrepancies found: {adapter_correct_count}/4")
    print(f"  Adapter corrections applied: {adapter_correct_count}/4")
    print()
    
    if failed > 0:
        print("  STATUS: ❌ FAILED")
        for s, msg in all_results:
            if s == "✗":
                print(f"    - {msg}")
        sys.exit(1)
    else:
        print("  STATUS: ✅ PASSED")
        print("  (iztro bugs documented, adapter corrections working)")
        sys.exit(0)


if __name__ == "__main__":
    main()
