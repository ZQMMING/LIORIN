# -*- coding: utf-8 -*-
"""河洛公开 API 的**签名契约**守卫（2026-10-24）。

**为什么要有这个守卫**
------------------

`HeluoCanonical.calculate` 支持**位置参数**调用，既有调用形如：

    calculate(bazi, gender, birth_hour, era, 2013)     # 2013 是 birth_year

2026-10-24 审计修「era 无来源标记」时，把新参数 `era_source` **插在
`era` 与 `birth_year` 之间** —— 于是上面这行的 `2013` 被当成 `era_source`，
`birth_year` 变成 None → 流年干支整体错位 → **12 年流年卦序列全错**。

该破坏被 `tests/test_heluo_liunian_guji.py::test_case2_full_12_years` 捕获
（既有权威案例守卫）—— 但那是**运气**：若那次审计改的恰好不影响流年，
破坏就会静默通过。

本守卫把「参数顺序」**显式钉成契约**：任何在 `calculate` 中间插入新参数的
改动都会立刻红，而不是等到某个下游案例崩。

**规则**
--------
1. `calculate` 的位置参数顺序固定为：
   `(bazi, gender, birth_hour, era, birth_year, birth_date, ...)`；
2. **新增参数只能追加到末尾**（或做成 keyword-only），
   不得插在既有位置参数之前；
3. 其他河洛公开入口（`sanyuan` / `resolve_middle_palace` /
   `HeluoAdapter.compute` / `HeluoAdapter.compute_from_chart`）同样受此约束。
"""
from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from heluo_engine.engines.heluo.canonical import HeluoCanonical  # noqa: E402
from heluo_engine.adapter import HeluoAdapter, sanyuan  # noqa: E402
from heluo_engine.engines.heluo.prenatal import resolve_middle_palace  # noqa: E402


def _positional_names(fn) -> list[str]:
    """取函数的位置参数名（不含 *args/**kwargs 与 keyword-only，不含 self）。"""
    sig = inspect.signature(fn)
    out = []
    for name, p in sig.parameters.items():
        if p.kind is inspect.Parameter.VAR_POSITIONAL:
            continue
        if p.kind is inspect.Parameter.VAR_KEYWORD:
            continue
        if p.kind is inspect.Parameter.KEYWORD_ONLY:
            continue
        if name == "self":
            continue
        out.append(name)
    return out


class TestCalculateSignature(unittest.TestCase):
    """`calculate` 的位置参数顺序是契约，不得中途插入新参数。"""

    #: 既有位置参数顺序（前 5 位是历史契约，其余按现实现记录）
    EXPECTED_HEAD = ["bazi", "gender", "birth_hour", "era", "birth_year"]

    def test_head_params_order(self):
        got = _positional_names(HeluoCanonical.calculate)
        self.assertEqual(got[:len(self.EXPECTED_HEAD)], self.EXPECTED_HEAD,
                         "calculate 的前 5 个位置参数顺序变了 —— "
                         "既有位置参数调用会被错位（如 calculate(b,g,h,era,2013)）")

    def test_birth_year_is_fifth_positional(self):
        """第 5 个位置参数必须是 birth_year（不是新加的 era_source 等）。"""
        got = _positional_names(HeluoCanonical.calculate)
        self.assertEqual(got[4], "birth_year",
                         "calculate 第 5 位位置参数被换掉了 —— "
                         "流年起点会随之错位")

    def test_positional_call_still_means_birth_year(self):
        """实测：用位置参数传 birth_year，流年必须从该年起算。"""
        bazi = [("癸", "巳"), ("壬", "戌"), ("己", "巳"), ("甲", "戌")]
        r = HeluoCanonical().calculate(bazi, "male", "戌", "zhong", 2013)
        self.assertEqual(r.birth_year, 2013,
                         "位置参数第 5 位的 birth_year 未生效")
        self.assertEqual(r.birth_year_source, "explicit")
        years = [y["year"] for y in r.timeline.yearly_hexagrams]
        self.assertEqual(years[0], 2013, "流年序列应从出生年起算")

    def test_new_params_appended_at_end(self):
        """新增参数（era_source 等）必须在签名末尾，不得插在既有参数中间。"""
        got = _positional_names(HeluoCanonical.calculate)
        self.assertEqual(got[-1], "era_source",
                         "era_source 应在签名末尾；插在中间会错位位置参数调用")


class TestOtherPublicSignatures(unittest.TestCase):
    """其他公开入口同样不得中途插入参数。"""

    def test_sanyuan(self):
        self.assertEqual(_positional_names(sanyuan), ["year"])

    def test_resolve_middle_palace(self):
        self.assertEqual(
            _positional_names(resolve_middle_palace),
            ["tian_reduced", "di_reduced", "gender", "birth_year_yang", "era"])

    def test_adapter_compute_head(self):
        got = _positional_names(HeluoAdapter.compute)
        self.assertEqual(got[:3], ["solar_date", "gender", "birth_datetime"],
                         "HeluoAdapter.compute 的位置参数顺序变了")

    def test_adapter_compute_from_chart_head(self):
        got = _positional_names(HeluoAdapter.compute_from_chart)
        self.assertEqual(got[:2], ["chart", "target_year"],
                         "HeluoAdapter.compute_from_chart 的位置参数顺序变了")


if __name__ == "__main__":
    unittest.main()
