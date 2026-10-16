"""Theme Engine — re-frames Signals per Life Theme.

Per architecture_decisions_v1.md DECISION-004 and docs/theme_mapping.yaml.
Reads theme_mapping.yaml at runtime. NEVER infers new frames (DECISION-009).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any
import yaml

from ..spec.themes import LIFE_THEMES


class ThemeEngine:
    """Theme Mapping engine.

    Loads theme_mapping.yaml and provides frame lookup.
    """

    def __init__(self, mapping_path: Path):
        self._path = mapping_path
        self._data: dict = {}
        self._frames: dict = {}
        self._load()

    def _load(self):
        with open(self._path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

        # Build lookup: (ontology_type, theme) -> frame
        for entry in self._data.get("frames", []):
            ot = entry["ontology_type"]
            for theme_frame in entry["themes"]:
                key = (ot, theme_frame["theme"])
                self._frames[key] = theme_frame

    def get_frame(self, ontology_type: str, theme: str) -> dict | None:
        """Get frame for (USO type, Life Theme).

        Returns None if not pre-registered (UNRESOLVED per DECISION-009).
        """
        if theme not in LIFE_THEMES:
            return None
        return self._frames.get((ontology_type, theme))

    def reframe_claim(
        self,
        ontology_type: str,
        theme: str,
        direction: str | None = None,
        polarity: str | None = None,
        base_claim: str | None = None,
    ) -> str | None:
        """Re-frame an Atomic Claim for a specific Life Theme (T204).

        Composes the frame's `perspective` (semantic anchor) with its
        `typical_verb` (dominant action), plus the signal's direction / polarity.
        Returns None if no frame is registered for (type, theme).

        Deterministic — never LLM inference (DECISION-004 / DECISION-009).
        """
        frame = self.get_frame(ontology_type, theme)
        if frame is None:
            return None

        perspective = frame.get("perspective", "")
        raw_verb = str(frame.get("typical_verb", ""))
        verb = raw_verb.split(" / ")[0].strip() or raw_verb.strip()

        dir_word = {
            "INCREASE": "增强",
            "STABLE": "平稳",
            "DECREASE": "减弱",
        }.get(direction, "平稳")
        pol_word = {
            "active": "活化",
            "neutral": "中性",
            "restricted": "受限",
        }.get(polarity, "中性")

        if perspective:
            return (
                f"{perspective} 主体在{theme}主题上以「{verb}」为主要取向,"
                f"能量{dir_word}、状态{pol_word}。"
            )
        return (
            f"主体在{theme}主题上以「{verb}」为主要取向,"
            f"能量{dir_word}、状态{pol_word}。"
        )

    @property
    def version(self) -> str:
        return self._data.get("version", "unknown")

    @property
    def frames_count(self) -> int:
        return len(self._frames)
