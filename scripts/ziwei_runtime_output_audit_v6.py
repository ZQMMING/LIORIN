#!/usr/bin/env python3
"""Ziwei Runtime Verification Harness — P-A1 Post-Cleanup (v6)

FOUR-LAYER VERIFICATION:
1. Raw iztro output (direct Node.js call, bypassing adapter)
2. Production output (via ZiweiEngine.full_chart(), with adapter)
3. Independent oracle (from traditional rules)
4. Direction consistency check

Production Code: FROZEN (be3dce9) + Adapter integration (59e27a2)
Verification Date: 2026-09-02
Harness Version: v6 (production integration verified)
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "wisdom" / "src"))

from tongshu.engines.ziwei_engine import ZiweiEngine, GAN_SIHUA
from tongshu.engines.ziwei_dependency_adapter import (
    ShuntianZiweiDependencyAdapter,
    Direction,
    get_adapter,
    compute_expected_direction,
)

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
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_raw_iztro_chart(lunar_date, hour, gender):
    """Get raw iztro output directly (bypassing adapter)."""
    year, month, day = lunar_date
    is_leap = month < 0
    month = abs(month)
    ti = hour // 2
    
    script = '''
    const { byLunar } = require('iztro').astro;
    const a = byLunar('%s-%s-%s', %d, '%s', %s);
    const out = {
        fiveElementsClass: a.fiveElementsClass || '',
        soulPalaceBranch: a.earthlyBranchOfSoulPalace || '',
        bodyPalaceBranch: a.earthlyBranchOfBodyPalace || '',
        palaces: {}
    };
    a.palaces.forEach(p => {
        out.palaces[p.name] = {
            stem: p.heavenlyStem || '',
            branch: p.earthlyBranch || '',
            major: (p.majorStars || []).map(s => s.name),
            minor: (p.minorStars || []).map(s => s.name),
            decadalRange: (p.decadal && p.decadal.range) || [],
            decadalStem: (p.decadal && p.decadal.heavenlyStem) || '',
            decadalBranch: (p.decadal && p.decadal.earthlyBranch) || ''
        };
    });
    process.stdout.write(JSON.stringify(out));
    ''' % (year, month, day, ti, gender, str(is_leap).lower())
    
    proc = subprocess.run(
        ["node", "-e", script],
        capture_output=True, text=True, encoding="utf-8",
        cwd=str(Path(__file__).parent.parent / "node_modules"),
        timeout=20,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"iztro raw call failed: {proc.stderr}")
    return json.loads(proc.stdout)


def extract_direction_from_chart(chart):
    """Extract decadal direction from chart palace ordering."""
    palaces = chart.get('palaces', {})
    decadal_info = []
    for pname, pdata in palaces.items():
        dr = pdata.get('decadalRange', [])
        if dr and len(dr) == 2:
            decadal_info.append({'palace': pname, 'range': dr})
    
    if len(decadal_info) < 2:
        return Direction.FORWARD
    
    decadal_info.sort(key=lambda x: x['range'][0])
    order = [d['palace'] for d in decadal_info]
    second = order[1] if len(order) > 1 else ''
    
    if second == '兄弟':
        return Direction.FORWARD
    elif second == '父母':
        return Direction.REVERSE
    else:
        # Fallback
        return Direction.FORWARD


def check_structural(chart_data, case):
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
# FOUR-LAYER VERIFICATION
# ============================================================================

def verify_four_layers(case):
    """Perform four-layer verification of decadal direction.
    
    Layer 1: Raw iztro output (direct Node.js call)
    Layer 2: Production output (via ZiweiEngine with adapter)
    Layer 3: Independent oracle (traditional rule)
    Layer 4: Consistency check
    """
    engine = ZiweiEngine()
    adapter = get_adapter()
    
    lunar_date = case['lunar_date']
    hour = case['hour']
    gender = case['gender']
    year = lunar_date[0]
    
    results = []
    
    # Layer 1: Raw iztro output
    raw_chart = get_raw_iztro_chart(lunar_date, hour, gender)
    layer1_direction = extract_direction_from_chart(raw_chart)
    
    # Layer 2: Production output (with adapter)
    prod_chart = engine.full_chart(lunar_date, hour, gender)
    layer2_direction = extract_direction_from_chart(prod_chart)
    
    # Layer 3: Independent oracle
    layer3_expected = compute_expected_direction(year, gender)
    
    # Layer 4: Consistency check
    layer4_pass = (layer2_direction == layer3_expected)
    
    # Record results
    results.append((
        case['name'],
        layer1_direction,
        layer2_direction,
        layer3_expected,
        layer4_pass,
    ))
    
    return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 70)
    print("ZIWEI RUNTIME VERIFICATION HARNESS — P-A1 Post-Cleanup (v6)")
    print("=" * 70)
    print()
    print("FOUR-LAYER VERIFICATION:")
    print("  Layer 1: Raw iztro output (direct Node.js call)")
    print("  Layer 2: Production output (via ZiweiEngine with adapter)")
    print("  Layer 3: Independent oracle (traditional rule)")
    print("  Layer 4: Consistency check (Layer 2 == Layer 3)")
    print()
    
    all_results = []
    direction_results = []
    
    # ========================================================================
    # LAYER 1-4: Decadal Direction Verification
    # ========================================================================
    print("[1] DECADAL DIRECTION VERIFICATION (Four-Layer)")
    print("-" * 70)
    
    for case in ALL_CASES:
        cases = verify_four_layers(case)
        direction_results.extend(cases)
        
        for name, l1, l2, l3, l4_pass in cases:
            print(f"\n{name}:")
            print(f"  Layer 1 (raw iztro):     {l1.value}")
            print(f"  Layer 2 (production):    {l2.value}")
            print(f"  Layer 3 (expected):      {l3.value}")
            print(f"  Layer 4 (consistency):   {'PASS' if l4_pass else 'FAIL'}")
            
            if l4_pass:
                print(f"  ✓ Production output matches expected")
                all_results.append(("✓", f"{name}: Production correct"))
            else:
                print(f"  ✗ Production output MISMATCH!")
                all_results.append(("✗", f"{name}: Production mismatch"))
    
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
    
    from tongshu.engines.ziwei_dependency_adapter import STEMS
    for case in ALL_CASES:
        year = case['lunar_date'][0]
        stem_idx = (year - 4) % 10
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
    
    # Count discrepancy corrections
    corrected_count = sum(1 for _, l1, l2, l3, l4 in direction_results if l1 != l2)
    
    print(f"  Passed:   {passed}")
    print(f"  Warnings: {warnings}")
    print(f"  Failed:   {failed}")
    print()
    print(f"  Iztro discrepancies corrected: {corrected_count}/4")
    print()
    
    if failed > 0:
        print("  STATUS: ❌ FAILED")
        for s, msg in all_results:
            if s == "✗":
                print(f"    - {msg}")
        sys.exit(1)
    else:
        print("  STATUS: ✅ PASSED")
        print("  (Production integration verified)")
        sys.exit(0)


if __name__ == "__main__":
    main()
