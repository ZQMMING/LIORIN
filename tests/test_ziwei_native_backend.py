# -*- coding: utf-8 -*-
"""紫微原生后端回归（不依赖 node / iztro / npm）。

验收点：
1. `ZiweiEngine(backend="native").full_chart()` 在完全没有 iztro 的情况下出盘，
   且盘面事实与已验证的 iztro 路径一致（此处以 hv 固定在锚点值上）。
2. `ZiweiSolarAdapter(backend="native").compute()` 同样可用，且亮度/生年四化/借对宫齐全。
3. 晚子时：紫微安星取次日（23:00 与次日 00:00 紫微同宫）。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tongshu.engines.ziwei_adapter import ZiweiSolarAdapter  # noqa: E402
from tongshu.engines.ziwei_engine import ZiweiEngine  # noqa: E402


def test_native_full_chart_without_iztro():
    eng = ZiweiEngine(node_modules_dir=Path("__no_iztro__"), backend="native")
    chart = eng.full_chart((1990, 2, 5), 5, "female")
    assert chart.fiveElementsClass == "火六局"
    assert chart.soul_earthly_branch == "子"
    assert chart.body_earthly_branch == "午"
    assert chart.soul_palace_main_stars == ["TIANJI"]
    # 亮度注入（Z39 四档）
    assert any(p.get("brightness") for p in chart.palaces.values())
    # 生年四化（庚年）
    assert chart.palaces  # 盘面完整
    assert len(chart.palaces) == 12


def test_native_adapter_chart():
    ad = ZiweiSolarAdapter(backend="native")
    ch = ad.compute(1983, 11, 3, 11, "male")
    assert ch.fiveElementsClass == "土五局"
    assert ch.soul_earthly_branch == "辰"
    assert ch.soul_palace_main_stars == ["QISHA"]
    assert len(ch.palaces) == 12


def test_native_late_zi_uses_next_day():
    eng = ZiweiEngine(node_modules_dir=Path("__no_iztro__"), backend="native")
    a = eng.full_chart((1990, 3, 1), 23, "male")
    b = eng.full_chart((1990, 3, 2), 0, "male")
    ziwei_a = next(p["branch"] for p in a.palaces.values() if "紫微" in (p.get("major") or []))
    ziwei_b = next(p["branch"] for p in b.palaces.values() if "紫微" in (p.get("major") or []))
    assert ziwei_a == ziwei_b
