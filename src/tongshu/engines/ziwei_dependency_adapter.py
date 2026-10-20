"""Shuntian Ziwei Dependency Adapter.

This module provides a compatibility layer for iztro 2.6.0 decadal direction bug.

BUG DESCRIPTION:
    iztro 2.6.0 palace.js:163 computes decadal direction using:
        GENDER[gender] === earthlyBranch.yinYang ? forward : reverse
    
    Traditional rule (《紫微斗数全书》):
        阳男阴女顺，阴男阳女逆
        (based on heavenly stem yinYang + gender)

ADAPTER PURPOSE:
    Isolate the discrepancy without modifying:
    - ziwei_engine.py (wrapper, should remain thin)
    - node_modules/iztro (upstream dependency)
    - Other calculation logic

ARCHITECTURE:
    iztro raw output
        ↓
    ShuntianZiweiDependencyAdapter
        ↓
    Canonical decadal direction (传统规则)
        ↓
    Signal Layer

UPSTREAM ISSUE:
    See docs/audit/upstream-issue-template.md

--------------------------------------------------------------------------
Z80-H 复核结论（2026-10-15）——本适配器为**防御性审计层（实测 no-op）**：

    Z80-G 全面审核实测 1950–2000 共 100 盘，iztro 原始大限方向与
    「年干阴阳」判定的**差异为 0**。原因（数学必然）：
        六十甲子中天干序与地支序**奇偶恒同**（甲子/乙丑/丙寅…），
        故「阳干」⟺「阳支」，iztro 的 `GENDER===earthlyBranch.yinYang`
        与传统的「阳男阴女顺，阴男阳女逆」**本就等价**。
    实测 1950–2000 共 51 年，干/支阴阳不一致年数 = **0**。

    因此本模块的 `_apply_correction` 在生产中**不会改变任何结果**——
    它保留为「上游一旦改动阴阳口径即可自动纠偏」的**防御性审计层**，
    并在 `enable_audit=True` 时记录 discrepancy 观测。

    注意：该适配器仅在 `full_chart` 路径接入；生产 `ZiweiSolarAdapter`
    路径未接（因其无需纠正）。此处如实标注，避免被误读为「已修正上游 bug」。
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

class Direction(Enum):
    """Decadal direction enum."""
    FORWARD = "forward"  # 顺
    REVERSE = "reverse"  # 逆


# Heavenly stems with yin/yang classification
# 阳干: 甲丙戊庚壬 (positions 0,2,4,6,8)
# 阴干: 乙丁己辛癸 (positions 1,3,5,7,9)
STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
YANG_STEMS = {'甲', '丙', '戊', '庚', '壬'}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass(frozen=True)
class DecadalDirectionResult:
    """Result of decadal direction computation."""
    
    # Input
    year: int
    gender: Literal['male', 'female']
    year_stem: str
    year_branch: str
    
    # iztro raw output (the bug)
    iztro_direction: Direction
    
    # Independent expected (traditional rule)
    expected_direction: Direction
    
    # Adapter correction
    corrected_direction: Direction
    
    # Audit trail
    has_discrepancy: bool
    
    @property
    def is_corrected(self) -> bool:
        """True if adapter had to correct the direction."""
        return self.has_discrepancy
    
    def to_dict(self) -> dict:
        """Serialize for audit logging."""
        return {
            'year': self.year,
            'gender': self.gender,
            'year_stem': self.year_stem,
            'year_branch': self.year_branch,
            'iztro_direction': self.iztro_direction.value,
            'expected_direction': self.expected_direction.value,
            'corrected_direction': self.corrected_direction.value,
            'has_discrepancy': self.has_discrepancy,
        }


# ============================================================================
# INDEPENDENT ORACLE
# ============================================================================

def compute_expected_direction(year: int, gender: Literal['male', 'female']) -> Direction:
    """Compute expected decadal direction from traditional rules.
    
    Rule: 阳男阴女顺，阴男阳女逆
    Based on year stem yin/yang + gender.
    
    Args:
        year: Birth year (solar or lunar, doesn't matter for stem calculation)
        gender: 'male' or 'female'
    
    Returns:
        Direction.FORWARD or Direction.REVERSE
    """
    # Z68: gender 中文兼容（防御：调用方可能直接传 男/女）
    gender = {"男": "male", "女": "female"}.get(gender, gender)
    # Calculate year stem (4 AD = 甲子, index 0)
    stem_idx = (year - 4) % 10
    stem = STEMS[stem_idx]
    
    # Determine yin/yang from stem
    stem_yinyang = 'yang' if stem in YANG_STEMS else 'yin'
    
    # Apply traditional rule
    if stem_yinyang == 'yang' and gender == 'male':
        return Direction.FORWARD
    elif stem_yinyang == 'yang' and gender == 'female':
        return Direction.REVERSE
    elif stem_yinyang == 'yin' and gender == 'male':
        return Direction.REVERSE
    else:  # yin + female
        return Direction.FORWARD


def get_year_stem_branch(year: int) -> tuple[str, str]:
    """Get year stem and branch from year number.
    
    Args:
        year: Solar year
    
    Returns:
        (stem, branch) tuple
    """
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    return STEMS[stem_idx], branches[branch_idx]


# ============================================================================
# ADAPTER CLASS
# ============================================================================

class ShuntianZiweiDependencyAdapter:
    """Adapter for iztro 2.6.0 decadal direction discrepancy.

    This adapter:
    1. Accepts raw iztro output (full_chart dict)
    2. Detects actual direction from palace ordering
    3. Computes independent expected from traditional rule
    4. Returns corrected chart with canonical decadal order
    5. Maintains audit trail for verification
    """

    # Metadata for audit
    DEPENDENCY = 'iztro'
    VERSION = '2.6.0'
    KNOWN_DISCREPANCY = 'decadal_direction'
    POLICY = 'SHUNTIAN_TRADITIONAL'

    # Palace order for direction detection
    PALACE_ORDER = ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄',
                    '迁移', '仆役', '官禄', '田宅', '福德', '父母']

    def __init__(self, enable_audit: bool = True):
        """Initialize adapter.

        Args:
            enable_audit: If True, log discrepancy events
        """
        self.enable_audit = enable_audit
    
    def adapt(
        self,
        year: int,
        gender: Literal['male', 'female'],
        iztro_direction: Direction,
    ) -> DecadalDirectionResult:
        """Apply correction to iztro decadal direction.
        
        Args:
            year: Birth year
            gender: 'male' or 'female'
            iztro_direction: Raw direction from iztro
        
        Returns:
            DecadalDirectionResult with audit trail
        """
        # Compute independent expected
        expected = compute_expected_direction(year, gender)
        
        # Get stem/branch for audit
        stem, branch = get_year_stem_branch(year)
        
        # Check for discrepancy
        has_discrepancy = (iztro_direction != expected)
        
        # Apply correction if needed
        corrected = expected if has_discrepancy else iztro_direction
        
        # Log if needed
        if self.enable_audit and has_discrepancy:
            logger.warning(
                f"[ZiweiAdapter] Decadal direction discrepancy detected: "
                f"year={year}, gender={gender}, stem={stem}, "
                f"iztro={iztro_direction.value}, expected={expected.value}"
            )
        
        return DecadalDirectionResult(
            year=year,
            gender=gender,
            year_stem=stem,
            year_branch=branch,
            iztro_direction=iztro_direction,
            expected_direction=expected,
            corrected_direction=corrected,
            has_discrepancy=has_discrepancy,
        )
    
    def adapt_from_chart(
        self,
        full_chart: dict,
        lunar_date: tuple[int, int, int],
        gender: Literal['male', 'female'],
    ) -> tuple[dict, DecadalDirectionResult]:
        """Adapt full chart output, correcting decadal directions.

        This is the PRODUCTION entry point. It:
        1. Extracts actual direction from palace ordering
        2. Computes independent expected
        3. Applies correction ONLY if discrepancy detected
        4. Returns adapted chart + audit result

        Args:
            full_chart: Raw output from ZiweiEngine.full_chart()
            lunar_date: (year, month, day) tuple
            gender: 'male' or 'female'

        Returns:
            Tuple of (adapted_chart, audit_result)
        """
        year = lunar_date[0]

        # Step 1: Extract actual direction from iztro output
        iztro_direction = self._extract_direction_from_chart(full_chart)

        # Step 2: Apply adapter correction
        result = self.adapt(year, gender, iztro_direction)

        # Step 3: Build corrected chart ONLY if discrepancy detected
        if result.has_discrepancy:
            corrected_chart = self._apply_correction(full_chart, result.corrected_direction)
            return corrected_chart, result
        else:
            # No discrepancy - return original chart
            return full_chart, result

    def _extract_direction_from_chart(self, chart: dict) -> Direction:
        """Extract actual decadal direction from chart palace ordering.

        Logic: If second palace in decadal order is '父母', direction is FORWARD (阳男阴女顺: 命→父母→福德).
        If second palace is '兄弟', direction is REVERSE (阴男阳女逆: 命→兄弟→夫妻).

        Args:
            chart: full_chart dict from iztro

        Returns:
            Direction.FORWARD or Direction.REVERSE
        """
        palaces = chart.get('palaces', {})
        if not palaces:
            return Direction.FORWARD  # fallback

        # Sort palaces by decadal start age
        decadal_info = []
        for pname, pdata in palaces.items():
            dr = pdata.get('decadalRange', [])
            if dr and len(dr) == 2:
                decadal_info.append({'palace': pname, 'range': dr})

        if len(decadal_info) < 2:
            return Direction.FORWARD  # fallback

        decadal_info.sort(key=lambda x: x['range'][0])
        order = [d['palace'] for d in decadal_info]

        # Check second palace in sequence
        second = order[1] if len(order) > 1 else ''
        if second == '父母':
            return Direction.FORWARD
        elif second == '兄弟':
            return Direction.REVERSE
        else:
            # Fallback: check index distance from 命宫
            first_idx = self.PALACE_ORDER.index(order[0]) if order[0] in self.PALACE_ORDER else 0
            second_idx = self.PALACE_ORDER.index(second) if second in self.PALACE_ORDER else 1
            return Direction.FORWARD if second_idx > first_idx else Direction.REVERSE

    def _apply_correction(self, chart: dict, corrected_direction: Direction) -> dict:
        """Apply direction correction via slot rebinding.

        Core algorithm:
        1. Extract raw decadal slots (range, stem, branch) sorted by range.
        2. Build canonical palace traversal order from 命宫 branch.
        3. Rebind: raw_slot[i] → canonical_palace[i].

        This ensures raw age-based slots are correctly mapped to canonical palaces.
        For example, if iztro raw order is 命→父母→福德 (reverse), and canonical
        should be 命→兄弟→夫妻 (forward), we rebind slot[1]=父母's range to 兄弟's branch.

        Note: This method is ONLY called when has_discrepancy=True.
        """
        import copy
        corrected = copy.deepcopy(chart)
        palaces = corrected.get('palaces', {})

        if len(palaces) != 12:
            return corrected

        # Step 1: Extract raw decadal slots sorted by range (chronological order)
        raw_slots = []
        for pname, pdata in palaces.items():
            dr = pdata.get('decadalRange', [])
            if dr and len(dr) == 2:
                raw_slots.append({
                    'range': dr,
                    'stem': pdata.get('decadalStem', ''),
                    'branch': pdata.get('decadalBranch', ''),
                })

        if len(raw_slots) < 12:
            return corrected

        raw_slots.sort(key=lambda x: x['range'][0])

        # Step 2: Build canonical palace order based on corrected_direction
        # Use the corrected_direction to determine if we should go forward or reverse
        BRANCH_ORDER = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        命宫_branch = palaces.get('命宫', {}).get('branch', '')
        命宫_idx = BRANCH_ORDER.index(命宫_branch) if 命宫_branch in BRANCH_ORDER else 0

        # Build canonical order based on target direction
        canonical_palaces = []
        for i in range(12):
            if corrected_direction == Direction.FORWARD:
                # FORWARD: 命宫→父母→福德... (顺时针, +i)
                idx = (命宫_idx + i) % 12
            else:
                # REVERSE: 命宫→兄弟→夫妻... (逆时针, -i)
                idx = (命宫_idx - i) % 12
            canonical_palaces.append(BRANCH_ORDER[idx])

        # Step 3: Rebind raw slots to canonical palaces
        # raw_slot[i] (age slot i) → canonical_palace[i] (branch at position i)
        for i, slot in enumerate(raw_slots):
            target_branch = canonical_palaces[i]
            for pname in palaces:
                if palaces[pname].get('branch') == target_branch:
                    palaces[pname]['decadalRange'] = slot['range']
                    palaces[pname]['decadalStem'] = slot['stem']
                    palaces[pname]['decadalBranch'] = slot['branch']
                    break

        return corrected
    
    def get_metadata(self) -> dict:
        """Return adapter metadata for audit."""
        return {
            'dependency': self.DEPENDENCY,
            'version': self.VERSION,
            'known_discrepancy': self.KNOWN_DISCREPANCY,
            'policy': self.POLICY,
            'description': 'Isolates iztro 2.6.0 decadal direction bug',
        }


# ============================================================================
# MODULE-LEVEL HELPERS
# ============================================================================

# Singleton adapter instance
_adapter: ShuntianZiweiDependencyAdapter | None = None


def get_adapter() -> ShuntianZiweiDependencyAdapter:
    """Get singleton adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = ShuntianZiweiDependencyAdapter()
    return _adapter


def adapt_decadal_direction(
    year: int,
    gender: Literal['male', 'female'],
    iztro_direction: Direction,
) -> DecadalDirectionResult:
    """Convenience function to adapt decadal direction.
    
    Args:
        year: Birth year
        gender: 'male' or 'female'
        iztro_direction: Raw direction from iztro
    
    Returns:
        DecadalDirectionResult with audit trail
    """
    return get_adapter().adapt(year, gender, iztro_direction)


# ============================================================================
# TEST CASES (for verification)
# ============================================================================

CANONICAL_CASES = [
    # (name, year, gender, expected_direction)
    ('阳男甲辰', 2024, 'male', Direction.FORWARD),
    ('阳女甲辰', 2024, 'female', Direction.REVERSE),
    ('阴男乙巳', 2025, 'male', Direction.REVERSE),
    ('阴女乙巳', 2025, 'female', Direction.FORWARD),
]


def verify_canonical_cases() -> list[dict]:
    """Verify adapter against canonical test cases.
    
    Returns:
        List of test result dicts
    """
    results = []
    
    for name, year, gender, expected in CANONICAL_CASES:
        # Simulate iztro output (always opposite for demonstration)
        # In reality, this would come from actual iztro call
        stem = get_year_stem_branch(year)[0]
        stem_yinyang = 'yang' if stem in YANG_STEMS else 'yin'
        
        # iztro would output opposite
        if (stem_yinyang == 'yang' and gender == 'male') or \
           (stem_yinyang == 'yin' and gender == 'female'):
            iztro_dir = Direction.REVERSE  # wrong
        else:
            iztro_dir = Direction.FORWARD  # wrong
        
        # Apply adapter
        result = adapt_decadal_direction(year, gender, iztro_dir)
        
        results.append({
            'name': name,
            'year': year,
            'gender': gender,
            'iztro_direction': iztro_dir.value,
            'expected_direction': expected.value,
            'corrected_direction': result.corrected_direction.value,
            'match': result.corrected_direction == expected,
        })
    
    return results
