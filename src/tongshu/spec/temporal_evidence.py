"""
V-Validation V1.2 — Temporal Evidence Schema (Schema 5)

Contract:
  PredictionWindow and EvaluationToleranceWindow are TWO DIFFERENT types.
  TemporalSignal does NOT contain convergence — that lives in TemporalConvergence.
  Phase 1: schema only. No convergence algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ─── TemporalSignal (single-engine time evidence) ────────────────────────────


@dataclass
class TemporalSignal:
    """Single-engine time signal. Contains NO convergence info."""

    signal_id: str            # FK → CanonicalSignal.signal_id
    engine: str               # e.g. "Bazi", "Heluo", …
    year: int
    month: Optional[int] = None
    day: Optional[int] = None
    granularity: str = "YEARLY"

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "engine": self.engine,
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "granularity": self.granularity,
        }



# ─── PredictionWindow (strictly separate from EvaluationToleranceWindow) ─────


@dataclass
class PredictionWindow:
    """Window used by the Calculation Engine to produce a prediction.

    Set by the system BEFORE evaluation. Never modified by Validation.
    """

    start_year: int
    end_year: int
    start_month: Optional[int] = None
    end_month: Optional[int] = None


# ─── EvaluationToleranceWindow (strictly separate from PredictionWindow) ─────


@dataclass
class EvaluationToleranceWindow:
    """Tolerance window around an actual_event for matching against prediction.

    Width depends on severity_class (see V1.2 Schema 6).
    """

    severity_class: str   # LOW|MODERATE|HIGH|CRITICAL
    tolerance_days: int   # e.g. LOW=365, CRITICAL=7


from typing import Union
