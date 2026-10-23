# -*- coding: utf-8 -*-
"""三元（sanyuan）推导守卫（2026-10-24）。

**为什么要有这个守卫**
------------------

`sanyuan(year)` 决定**寄宫对象**（原典《遇五寄宫法》）：
上元甲子男艮女坤 / 中元甲子阴男阳女坤、阳男阴女艮 / 下元甲子男离女兑。

寄宫数一变 → 先天卦变 → 元堂变 → 后天卦变 → **全链判词全变**。
而 `sanyuan` 此前**没有任何守卫**：
`grep "sanyuan" tests/` → 0 命中；全仓仅 `audit/audit_probe_ag.py` 引用（仅 print）。

守卫侧只测了「era 作为**入参**时的行为」（`resolve_middle_palace` 的三个分支
逐条断言），**从未验证 era 是怎么被推导出来的** ——
把锚点常数 1864 改成 1863，或把 `<60` 改成 `<59`，寄宫口径偏移一整轮 60 年，
守卫全绿。

**原典依据**
----------

`heluo_adapter.py:76-79` 已记原典回查链（天一阁本《河洛真数·起例卷之上》）：
    1504(上) → 1564(中) → 1624(下) → 1684(上) → 1744(中) → 1804(下)
锚点：1864 上元 → 1924 中元 → 1984 下元 → 2044 上元 → …
公式：offset = (year - 1864) % 180；<60 上元、<120 中元、其余下元。

本守卫**以这条原典链为准**（而非重新推导一套），并另加：
* 180 年周期不变性；
* 三个分界的**边界点**（offset = 59/60、119/120）；
* **端到端**：adapter 走三个锚点年 → `result.era` 与 `sanyuan` 一致，
  且寄宫结果与 `resolve_middle_palace` 直调一致（防 adapter 绕过 sanyuan 硬写 era）；
* **兜底标记**：chart 无 birth_datetime 时 era_source 必须是 "fallback"
  （2026-10-24 审计修：此前静默回落 "zhong" 且不留来源标记）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from heluo_engine.adapter import sanyuan, HeluoAdapter  # noqa: E402
from heluo_engine.engines.heluo.prenatal import resolve_middle_palace  # noqa: E402


class TestSanyuan(unittest.TestCase):
    """三元推导：锚点链 / 周期 / 边界。"""

    def test_original_text_chain(self):
        """原典回查链（heluo_adapter.py:79 自记）：1504→1804 六个锚点。"""
        expected = [
            (1504, "shang"), (1564, "zhong"), (1624, "xia"),
            (1684, "shang"), (1744, "zhong"), (1804, "xia"),
        ]
        for year, want in expected:
            with self.subTest(year=year):
                self.assertEqual(sanyuan(year), want,
                                 f"{year} 应为 {want}（原典回查链）")

    def test_modern_anchors(self):
        """现代锚点：1864 上元 → 1924 中元 → 1984 下元 → 2044 上元。

        **相邻年也要断**：锚点 1864 之前一年（1863）是**下元**、之后一年（1865）
        仍是**上元**。只断锚点年本身不够 —— 把公式里的 1864 改成 1863，
        锚点年 1864 仍会算成 shang（差 1 落在同一档内），
        只断「锚点年 + 相邻年」才能抓住这种偏移。
        """
        for year, want in [(1864, "shang"), (1924, "zhong"),
                           (1984, "xia"), (2044, "shang")]:
            with self.subTest(year=year):
                self.assertEqual(sanyuan(year), want)

    def test_anchor_boundaries(self):
        """锚点分界：锚点年本身与其**前一年**分属两元。

        1864 起上元 → 1863 是下元末尾；1924 起中元 → 1923 是上元末尾；
        1984 起下元 → 1983 是中元末尾；2044 起上元 → 2043 是下元末尾。
        """
        cases = [
            (1863, "xia"), (1864, "shang"),
            (1923, "shang"), (1924, "zhong"),
            (1983, "zhong"), (1984, "xia"),
            (2043, "xia"), (2044, "shang"),
        ]
        for year, want in cases:
            with self.subTest(year=year):
                self.assertEqual(sanyuan(year), want,
                                 f"{year} 应为 {want}（锚点分界）")

    def test_period_180(self):
        """三元 180 年一循环。"""
        for year in (1504, 1564, 1624, 1864, 1924, 1984, 2026):
            with self.subTest(year=year):
                self.assertEqual(sanyuan(year + 180), sanyuan(year),
                                 f"{year} 与 {year+180} 三元应相同")
                self.assertEqual(sanyuan(year - 180), sanyuan(year),
                                 f"{year} 与 {year-180} 三元应相同")

    def test_boundary_points(self):
        """三个分界的边界点（offset = 59/60、119/120、0/179）。"""
        base = 1864
        cases = [
            (base + 0, "shang"), (base + 59, "shang"),
            (base + 60, "zhong"), (base + 119, "zhong"),
            (base + 120, "xia"), (base + 179, "xia"),
            (base - 1, "xia"),        # 上一轮末尾
        ]
        for year, want in cases:
            with self.subTest(year=year, offset=(year - base) % 180):
                self.assertEqual(sanyuan(year), want)

    def test_three_values_only(self):
        """输出只能是三值之一。"""
        for year in range(1800, 2100):
            self.assertIn(sanyuan(year), ("shang", "zhong", "xia"))


class TestSanyuanEndToEnd(unittest.TestCase):
    """端到端：adapter 的 era 必须来自 sanyuan，且寄宫与直调一致。"""

    @staticmethod
    def _adapter():
        return HeluoAdapter()

    def test_result_era_matches_sanyuan(self):
        """有出生时间时 result.era 必须等于 sanyuan(出生年)。"""
        ad = self._adapter()
        for year, want in ((1960, "shang"), (1970, "zhong"), (1990, "xia")):
            with self.subTest(year=year):
                res = ad.compute((year, 6, 15, 14), gender="male",
                                 target_date="2026-10-23")
                self.assertEqual(res.era, sanyuan(year))
                self.assertEqual(res.era_source, "derived",
                                 "有 birth_datetime 时 era_source 应为 derived")

    def test_jigong_matches_direct_call(self):
        """寄宫数必须与 resolve_middle_palace 直调一致（防绕过 sanyuan 硬写）。

        注意 `resolve_middle_palace` **总是**返回 (天卦数, 地卦数)；
        而 `PrenatalHexagram.palace_resolved_gua` 只在**真发生寄宫**
        （天/地归一化数 == 5）时才填，否则为 None。故：
          · 发生寄宫 → 两者必须相等；
          · 未发生寄宫 → 引擎侧必须为 None（不得凭空造一个寄宫）。
        """
        ad = self._adapter()
        for year in (1960, 1970, 1990):
            with self.subTest(year=year):
                res = ad.compute((year, 6, 15, 14), gender="male",
                                 target_date="2026-10-23")
                tian, di = resolve_middle_palace(
                    res.numbers.tian_reduced, res.numbers.di_reduced,
                    gender=res.input.gender,
                    birth_year_yang=(res.bazi[0][0] in "甲丙戊庚壬"),
                    era=res.era,
                )
                if res.prenatal.middle_palace_resolved:
                    self.assertEqual(
                        res.prenatal.palace_resolved_gua, (tian, di),
                        f"{year} 寄宫与 resolve_middle_palace 直调不一致")
                else:
                    self.assertIsNone(
                        res.prenatal.palace_resolved_gua,
                        f"{year} 未发生寄宫，palace_resolved_gua 应为 None")
                    self.assertEqual(
                        (res.numbers.tian_reduced, res.numbers.di_reduced),
                        (tian, di),
                        f"{year} 未发生寄宫时，天/地卦数应原样不变")

    def test_era_source_fallback_marked(self):
        """无出生时间时 era_source 必须是 fallback（不得静默回落成真值）。"""
        from dataclasses import replace
        from heluo_engine.engines.bazi_engine import BaziEngine
        chart = BaziEngine().compute((1990, 6, 15, 14), gender="male")
        # 手工剥掉 birth_datetime，模拟「上游未带出生时间」
        # （BaziChart 是 frozen dataclass，须用 replace 而非赋值）
        chart = replace(chart, birth_datetime=None)
        ad = self._adapter()
        res = ad.compute_from_chart(chart)
        self.assertEqual(res.era, "zhong", "无出生时间时 era 回退中元")
        self.assertEqual(res.era_source, "fallback",
                         "无出生时间时 era_source 必须标记为 fallback")


if __name__ == "__main__":
    unittest.main()
