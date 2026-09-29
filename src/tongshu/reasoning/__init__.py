"""Reasoning layer: standalone bazi slice.

Trimmed to bazi_ten_gods only (single-source ten-god functions used by
BaziEngine). signal_engine / theme_engine / ziping_v3 are NOT part of this
slice and are not imported here.
"""
from .bazi_ten_gods import (
    ten_god,
    hidden_main_stem,
    hidden_stems_all,
    hidden_main_role,
    hidden_main_stem_is_transparent,
    transparent_ten_gods,
    month_hidden_main_ten_god,
)

__all__ = [
    "ten_god",
    "hidden_main_stem",
    "hidden_stems_all",
    "hidden_main_role",
    "hidden_main_stem_is_transparent",
    "transparent_ten_gods",
    "month_hidden_main_ten_god",
]
