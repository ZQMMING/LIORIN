"""Traditional Authority Oracle — Independent Canonical Reference.

This module implements the TRADITIONAL RULE for decadal direction
and palace sequence, completely independent of the production adapter.

It serves as the TRUTH SOURCE for verifying iztro 2.6.0 discrepancy
and adapter correction correctness.

TRADITIONAL RULE (《紫微斗数全书》):
    阳男阴女顺，阴男阳女逆
    (based on heavenly stem yin/yang + gender)

FORWARD (阳男阴女顺):
    命宫 -> 父母 -> 福德 -> 田宅 -> 官禄 -> 仆役 -> 迁移 -> 疾厄 -> 财帛 -> 子女 -> 夫妻 -> 兄弟

REVERSE (阴男阳女逆):
    命宫 -> 兄弟 -> 夫妻 -> 子女 -> 财帛 -> 疾厄 -> 迁移 -> 仆役 -> 官禄 -> 田宅 -> 福德 -> 父母
"""
from __future__ import annotations
import sys
from enum import Enum
from typing import Literal


# ============================================================================
# CONSTANTS (Independent from production code)
# ============================================================================

class TraditionalDirection(Enum):
    """Traditional decadal direction enum."""
    FORWARD = "forward"   # 顺: 阳男阴女
    REVERSE = "reverse"   # 逆: 阴男阳女


HEAVENLY_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
YANG_STEMS = {'甲', '丙', '戊', '庚', '壬'}

EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# Traditional palace sequence (by decadal age order)
# These are the EXPECTED palace names for each canonical direction
TRADITIONAL_FORWARD_SEQUENCE = [
    '命宫', '父母', '福德', '田宅', '官禄', '仆役',
    '迁移', '疾厄', '财帛', '子女', '夫妻', '兄弟'
]

TRADITIONAL_REVERSE_SEQUENCE = [
    '命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄',
    '迁移', '仆役', '官禄', '田宅', '福德', '父母'
]


# ============================================================================
# INDEPENDENT ORACLE FUNCTIONS
# ============================================================================

def compute_traditional_direction(year: int, gender: Literal['male', 'female']) -> TraditionalDirection:
    """Compute expected decadal direction from TRADITIONAL RULE.

    This is the INDEPENDENT TRUTH SOURCE — it implements the traditional
    rule directly, without any reference to iztro or production code.

    Args:
        year: Birth year (solar)
        gender: 'male' or 'female'

    Returns:
        TraditionalDirection.FORWARD or TraditionalDirection.REVERSE
    """
    # Calculate year stem (4 AD = 甲子, index 0)
    stem_idx = (year - 4) % 10
    stem = HEAVENLY_STEMS[stem_idx]

    # Determine yin/yang from stem
    stem_yinyang = 'yang' if stem in YANG_STEMS else 'yin'

    # Apply traditional rule: 阳男阴女顺，阴男阳女逆
    if stem_yinyang == 'yang' and gender == 'male':
        return TraditionalDirection.FORWARD
    elif stem_yinyang == 'yang' and gender == 'female':
        return TraditionalDirection.REVERSE
    elif stem_yinyang == 'yin' and gender == 'male':
        return TraditionalDirection.REVERSE
    else:  # yin + female
        return TraditionalDirection.FORWARD


def get_traditional_palace_sequence(direction: TraditionalDirection) -> list[str]:
    """Get expected palace sequence from traditional rule.

    Args:
        direction: TraditionalDirection.FORWARD or REVERSE

    Returns:
        List of 12 palace names in decadal age order
    """
    if direction == TraditionalDirection.FORWARD:
        return TRADITIONAL_FORWARD_SEQUENCE.copy()
    else:
        return TRADITIONAL_REVERSE_SEQUENCE.copy()


def compute_expected_stem_at_age(starting_stem_idx: int, palace_index: int, starting_age: int = 1) -> str:
    """Compute expected decadal stem for a given palace index.

    The decadal stem increments by 1 for each 10-year period.

    Args:
        starting_stem_idx: Stem index (0-9) for the first decade
        palace_index: Palace index (0-11) in decadal order
        starting_age: Starting age for the first decade (default 1)

    Returns:
        Expected stem character
    """
    # Stem cycles every 10 years, incrementing by 1 per decade
    stem_idx = (starting_stem_idx + palace_index) % 10
    return HEAVENLY_STEMS[stem_idx]


# ============================================================================
# EXPECTED TUPLE GENERATOR
# ============================================================================

def generate_expected_decadal_tuples(
    initial_stem_idx: int,
    branch_order: list[str],
    starting_age: int = 1
) -> list[dict]:
    """Generate expected (range, stem, branch) tuples for all 12 palaces.

    This is used for verifying the adapter's structural output against
    the traditional rule.

    Args:
        initial_stem_idx: Stem index for the first decade
        branch_order: Expected branch sequence for canonical direction
        starting_age: Starting age for the first decade (default 1)

    Returns:
        List of 12 dicts with 'range', 'stem', 'branch' keys
    """
    expected = []
    for i, branch in enumerate(branch_order):
        age_start = starting_age + i * 10
        age_end = age_start + 9
        stem = compute_expected_stem_at_age(initial_stem_idx, i, starting_age)
        expected.append({
            'range': [age_start, age_end],
            'stem': stem,
            'branch': branch,
        })
    return expected


# ============================================================================
# MAIN VERIFICATION (when run as script)
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Traditional Authority Oracle Verification")
    print("=" * 60)

    cases = [
        (2000, 'male', '阳男'),
        (2000, 'female', '阳女'),
        (1999, 'male', '阴男'),
        (1999, 'female', '阴女'),
    ]

    for year, gender, label in cases:
        direction = compute_traditional_direction(year, gender)
        sequence = get_traditional_palace_sequence(direction)

        print(f"\n{label} ({year}, {gender}):")
        print(f"  Traditional direction: {direction.value}")
        print(f"  Expected palace sequence: {sequence}")

    print("\n" + "=" * 60)
    print("Independent oracle verification complete.")
    print("=" * 60)
