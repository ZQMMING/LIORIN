"""
Engine Adapters (Phase 3)

Contract:
  - Adapters only CONVERT, do NOT re-implement engine logic
  - Each adapter wraps existing engine output
  - KnowledgeAdapter MUST carry evidence provenance
  - No new Event Types can be created by adapters
"""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tongshu.signal.canonical_signal import (
    CanonicalSignal,
    CanonicalSignalValidator,
    SignalLayer,
    SourceEngine,
    SignalTemporalScope,
)
from tongshu.spec.event_ontology_v1 import Domain, EventDirection
from tongshu.signal.normalizer import (
    NormalizationResult,
    SignalNormalizer,
    NormalizationStatus,
)


# ─── Adapter Base Class ────────────────────────────────────────────────────────

@dataclass
class AdapterContext:
    """Context passed to adapters for validation."""
    evidence_refs: List[str] = None
    rule_refs: List[str] = None

    def __post_init__(self):
        if self.evidence_refs is None:
            self.evidence_refs = []
        if self.rule_refs is None:
            self.rule_refs = []


class BaseAdapter(metaclass=abc.ABCMeta):
    """
    Base class for all engine adapters.

    Contract:
      - adapt() converts engine output to CanonicalSignal
      - validate() checks preconditions before conversion
      - _normalize() delegates to SignalNormalizer
    """

    engine_name: str = ""
    canonical_engine: SourceEngine = None

    @classmethod
    @abc.abstractmethod
    def adapt(cls, engine_output: Dict[str, Any], context: AdapterContext = None) -> CanonicalSignal:
        """
        Convert engine output to CanonicalSignal.

        Args:
            engine_output: Raw output from engine
            context: Optional adapter context

        Returns:
            CanonicalSignal (validated)

        Raises:
            ValueError: If conversion fails validation
        """
        pass

    @classmethod
    def validate_output(cls, result: NormalizationResult) -> bool:
        """Check if normalization result is valid."""
        return result.status == NormalizationStatus.SUCCESS

    @classmethod
    def build_signal(
        cls,
        signal_id: str,
        result: NormalizationResult,
        strength: float,
        temporal_scope: SignalTemporalScope,
        layer: SignalLayer = SignalLayer.BASELINE,
        evidence_refs: List[str] = None,
        rule_refs: List[str] = None,
        extracted_at: str = "",
    ) -> CanonicalSignal:
        """Build validated CanonicalSignal from normalization result."""
        if evidence_refs is None:
            evidence_refs = []
        if rule_refs is None:
            rule_refs = []

        signal = CanonicalSignal(
            signal_id=signal_id,
            source_engine=cls.canonical_engine,
            event_type=result.canonical_event_type or 'UNKNOWN',
            domain=Domain[result.canonical_domain] if result.canonical_domain else Domain.LIFE_EVENT,
            direction=EventDirection[result.canonical_direction] if result.canonical_direction else EventDirection.UNKNOWN,
            strength=strength,
            temporal_scope=temporal_scope,
            evidence_refs=evidence_refs,
            rule_refs=rule_refs,
            layer=layer,
            extracted_at=extracted_at,
        )

        # Validate the signal
        errors = CanonicalSignalValidator.validate(signal)
        if errors:
            raise ValueError(f"{cls.engine_name} adapter validation failed: {errors}")

        return signal


# ─── Bazi Adapter ──────────────────────────────────────────────────────────────

class BaziAdapter(BaseAdapter):
    """Adapter for Bazi engine output."""

    engine_name = "Bazi"
    canonical_engine = SourceEngine.BAZI

    @classmethod
    def adapt(
        cls,
        engine_output: Dict[str, Any],
        context: AdapterContext = None,
    ) -> CanonicalSignal:
        """
        Adapt Bazi output to CanonicalSignal.

        Expected engine_output format:
          {
            'shenshan': str,
            'pattern': str,
            'year_stem': Optional[str],
            'year_branch': Optional[str],
            'strength': float,
            'temporal_scope': dict
          }
        """
        # Extract parameters
        shenshan = engine_output.get('shenshan', '')
        pattern = engine_output.get('pattern', '')
        year_stem = engine_output.get('year_stem')
        year_branch = engine_output.get('year_branch')

        # Normalize
        result = SignalNormalizer.normalize_bazi(
            shenshan=shenshan,
            pattern=pattern,
            year_stem=year_stem,
            year_branch=year_branch,
        )

        # Validate
        if not cls.validate_output(result):
            raise ValueError(f"Bazi adapter: {result.rejection_reason}")

        # Build signal
        strength = engine_output.get('strength', 0.5)
        temporal_scope = SignalTemporalScope(
            start_year=engine_output.get('start_year', 2026),
            end_year=engine_output.get('end_year'),
            granularity=engine_output.get('granularity', 'YEARLY'),
        )

        return cls.build_signal(
            signal_id=engine_output.get('signal_id', 'BAZI_001'),
            result=result,
            strength=strength,
            temporal_scope=temporal_scope,
            evidence_refs=context.evidence_refs if context else [],
            rule_refs=context.rule_refs if context else [],
            extracted_at=engine_output.get('extracted_at', ''),
        )


# ─── Heluo Adapter ─────────────────────────────────────────────────────────────

class HeluoAdapter(BaseAdapter):
    """Adapter for Heluo engine output."""

    engine_name = "Heluo"
    canonical_engine = SourceEngine.HELUO

    @classmethod
    def adapt(
        cls,
        engine_output: Dict[str, Any],
        context: AdapterContext = None,
    ) -> CanonicalSignal:
        """
        Adapt Heluo output to CanonicalSignal.

        Expected engine_output format:
          {
            'gua': str,
            'yao': int,
            'position': str,
            'shi': str,
            'strength': float,
            'temporal_scope': dict
          }
        """
        # Extract parameters
        gua = engine_output.get('gua', '')
        yao = engine_output.get('yao', 1)
        position = engine_output.get('position', '')
        shi = engine_output.get('shi', '')

        # Normalize
        result = SignalNormalizer.normalize_heluo(
            gua=gua,
            yao=yao,
            position=position,
            shi=shi,
        )

        # Validate
        if not cls.validate_output(result):
            raise ValueError(f"Heluo adapter: {result.rejection_reason}")

        # Build signal
        strength = engine_output.get('strength', 0.5)
        temporal_scope = SignalTemporalScope(
            start_year=engine_output.get('start_year', 2026),
            end_year=engine_output.get('end_year'),
            granularity=engine_output.get('granularity', 'YEARLY'),
        )

        return cls.build_signal(
            signal_id=engine_output.get('signal_id', 'HELUO_001'),
            result=result,
            strength=strength,
            temporal_scope=temporal_scope,
            evidence_refs=context.evidence_refs if context else [],
            rule_refs=context.rule_refs if context else [],
            extracted_at=engine_output.get('extracted_at', ''),
        )


# ─── Ziwei Adapter ─────────────────────────────────────────────────────────────

class ZiweiAdapter(BaseAdapter):
    """Adapter for Ziwei engine output."""

    engine_name = "Ziwei"
    canonical_engine = SourceEngine.ZIWEI

    @classmethod
    def adapt(
        cls,
        engine_output: Dict[str, Any],
        context: AdapterContext = None,
    ) -> CanonicalSignal:
        """
        Adapt Ziwei output to CanonicalSignal.

        Expected engine_output format:
          {
            'palace': str,
            'stars': List[str],
            'transformations': List[str],
            'strength': float,
            'temporal_scope': dict
          }
        """
        # Extract parameters
        palace = engine_output.get('palace', '')
        stars = engine_output.get('stars', [])
        transformations = engine_output.get('transformations', [])

        # Normalize
        result = SignalNormalizer.normalize_ziwei(
            palace=palace,
            stars=stars,
            transformations=transformations,
        )

        # Validate
        if not cls.validate_output(result):
            raise ValueError(f"Ziwei adapter: {result.rejection_reason}")

        # Build signal
        strength = engine_output.get('strength', 0.5)
        temporal_scope = SignalTemporalScope(
            start_year=engine_output.get('start_year', 2026),
            end_year=engine_output.get('end_year'),
            granularity=engine_output.get('granularity', 'YEARLY'),
        )

        return cls.build_signal(
            signal_id=engine_output.get('signal_id', 'ZIWEI_001'),
            result=result,
            strength=strength,
            temporal_scope=temporal_scope,
            evidence_refs=context.evidence_refs if context else [],
            rule_refs=context.rule_refs if context else [],
            extracted_at=engine_output.get('extracted_at', ''),
        )


# ─── Huangli Adapter ───────────────────────────────────────────────────────────

class HuangliAdapter(BaseAdapter):
    """Adapter for Huangli engine output."""

    engine_name = "Huangli"
    canonical_engine = SourceEngine.HUANGLI

    @classmethod
    def adapt(
        cls,
        engine_output: Dict[str, Any],
        context: AdapterContext = None,
    ) -> CanonicalSignal:
        """
        Adapt Huangli output to CanonicalSignal.

        Expected engine_output format:
          {
            'day_stems': List[str],
            'day_branches': List[str],
            'yi': List[str],
            'ji': List[str],
            'jieqi': str,
            'strength': float,
            'temporal_scope': dict
          }
        """
        # Extract parameters
        day_stems = engine_output.get('day_stems', [])
        day_branches = engine_output.get('day_branches', [])
        yi = engine_output.get('yi', [])
        ji = engine_output.get('ji', [])
        jieqi = engine_output.get('jieqi', '')

        # Normalize
        result = SignalNormalizer.normalize_huangli(
            day_stems=day_stems,
            day_branches=day_branches,
            yi=yi,
            ji=ji,
            jieqi=jieqi,
        )

        # Validate
        if not cls.validate_output(result):
            raise ValueError(f"Huangli adapter: {result.rejection_reason}")

        # Build signal
        strength = engine_output.get('strength', 0.5)
        temporal_scope = SignalTemporalScope(
            start_day=engine_output.get('start_day'),
            end_day=engine_output.get('end_day'),
            granularity='DAILY',
        )

        return cls.build_signal(
            signal_id=engine_output.get('signal_id', 'HUANGLI_001'),
            result=result,
            strength=strength,
            temporal_scope=temporal_scope,
            evidence_refs=context.evidence_refs if context else [],
            rule_refs=context.rule_refs if context else [],
            extracted_at=engine_output.get('extracted_at', ''),
        )


# ─── Knowledge Adapter ─────────────────────────────────────────────────────────

class KnowledgeAdapter(BaseAdapter):
    """
    Adapter for Knowledge Engine output.

    Special Contract:
      - MUST carry evidence provenance (evidence_id, claim_id, source_id)
      - Direction defaults to UNKNOWN until manually contextualized
      - Cannot auto-assign confidence > 0.3 without expert review
    """

    engine_name = "Knowledge"
    canonical_engine = SourceEngine.KNOWLEDGE

    @classmethod
    def adapt(
        cls,
        engine_output: Dict[str, Any],
        context: AdapterContext = None,
    ) -> CanonicalSignal:
        """
        Adapt Knowledge output to CanonicalSignal.

        Special requirements:
          - evidence_id is REQUIRED (cannot be empty)
          - direction defaults to UNKNOWN
          - strength capped at 0.3 without expert review

        Expected engine_output format:
          {
            'source_text': str,
            'rule_id': str,
            'evidence_id': str,  # REQUIRED
            'claim_id': Optional[str],
            'source_id': Optional[str],
            'context': Optional[str],
            'strength': float,  # Will be capped at 0.3
            'temporal_scope': dict
          }
        """
        # Extract parameters
        source_text = engine_output.get('source_text', '')
        rule_id = engine_output.get('rule_id', '')
        evidence_id = engine_output.get('evidence_id', '')
        claim_id = engine_output.get('claim_id')
        source_id = engine_output.get('source_id')
        context_text = engine_output.get('context')

        # Knowledge contract: evidence_id is REQUIRED
        if not evidence_id:
            raise ValueError("Knowledge adapter: evidence_id is required")

        # Normalize
        result = SignalNormalizer.normalize_knowledge(
            source_text=source_text,
            rule_id=rule_id,
            evidence_id=evidence_id,
            context=context_text,
        )

        # Knowledge signals are conservative (UNKNOWN direction, low strength)
        # This prevents automatic high-confidence claims from unverified sources
        strength = min(engine_output.get('strength', 0.3), 0.3)

        # Build signal with evidence provenance
        temporal_scope = SignalTemporalScope(
            start_year=engine_output.get('start_year', 2026),
            end_year=engine_output.get('end_year'),
            granularity=engine_output.get('granularity', 'YEARLY'),
        )

        return cls.build_signal(
            signal_id=engine_output.get('signal_id', f'KNOWLEDGE_{evidence_id}'),
            result=result,
            strength=strength,
            temporal_scope=temporal_scope,
            evidence_refs=[evidence_id],  # Must carry evidence ref
            rule_refs=[rule_id] if rule_id else [],
            extracted_at=engine_output.get('extracted_at', ''),
        )


# ─── Adapter Registry ──────────────────────────────────────────────────────────
# V2.1 切片 S0 洞2：BLIND 注册。BlindAdapter 定义在 engines.blind_bazi_engine，
# 顶层 import 会触发 signal.adapters → engines.blind_bazi_engine → signal.adapters
# (BaseAdapter) 循环。用运行时懒加载破环。
def _load_blind_adapter():
    from tongshu.engines.blind_bazi_engine import BlindAdapter
    return BlindAdapter

ADAPTER_REGISTRY: Dict[str, type] = {
    'BAZI': BaziAdapter,
    'HELUO': HeluoAdapter,
    'ZIWEI': ZiweiAdapter,
    'HUANGLI': HuangliAdapter,
    'KNOWLEDGE': KnowledgeAdapter,
}


def get_adapter(engine_name: str) -> type:
    """Get adapter class by engine name."""
    engine = engine_name.upper()
    # 洞2：BLIND 懒加载（破循环依赖）
    if engine == 'BLIND':
        return _load_blind_adapter()
    if engine not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown engine: {engine_name}")
    return ADAPTER_REGISTRY[engine]


def adapt(
    engine_name: str,
    engine_output: Dict[str, Any],
    context: AdapterContext = None,
) -> CanonicalSignal:
    """
    Convenience function to adapt engine output to CanonicalSignal.

    Args:
        engine_name: Engine name (BAZI, HELUO, ZIWEI, HUANGLI, KNOWLEDGE)
        engine_output: Raw engine output
        context: Optional adapter context

    Returns:
        CanonicalSignal
    """
    adapter_cls = get_adapter(engine_name)
    return adapter_cls.adapt(engine_output, context)
